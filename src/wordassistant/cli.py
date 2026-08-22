from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from importlib.resources import files as resource_files
from dataclasses import asdict
from .doctor import status
from .document.structure import index_docx
from .context.retrieve import build_context
from .profiles.loader import load_profile,ProfileError
from .document.scaffold import scaffold_document
from .document.validate import validate_document
from .document.render import render_pdf
from .evidence.registry import EvidenceRegistry
from .workspace import init_workspace
from .capabilities import capabilities
from .document.edit import replace_text

def _root(): return Path(__file__).resolve().parents[2]
def _resolve_profile(name):
    p=Path(name)
    if p.exists():return p
    filename=name if name.endswith('.json') else name+'.json'
    candidate=_root()/'profiles'/filename
    if candidate.exists():return candidate
    packaged=resource_files('wordassistant').joinpath('data','profiles',filename)
    if packaged.is_file(): return Path(str(packaged))
    raise ProfileError(f'Profile not found: {name}')
def _ensure_utf8():
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def _print(obj,json_mode=False):
    _ensure_utf8()
    if json_mode: print(json.dumps(obj,ensure_ascii=False,indent=2))
    else:
        if isinstance(obj,str):print(obj)
        else:print(json.dumps(obj,ensure_ascii=False,indent=2))


def parser():
    p=argparse.ArgumentParser(prog='wordassistant',description='Deterministic profile-driven DOCX toolkit')
    sp=p.add_subparsers(dest='cmd',required=True)
    d=sp.add_parser('doctor'); d.add_argument('--json',action='store_true')
    cap=sp.add_parser('capabilities'); cap.add_argument('--json',action='store_true')
    pr=sp.add_parser('profiles'); pr.add_argument('--json',action='store_true')
    init=sp.add_parser('init'); init.add_argument('path'); init.add_argument('--json',action='store_true')
    i=sp.add_parser('inspect'); i.add_argument('file'); i.add_argument('--json',action='store_true')
    c=sp.add_parser('context'); c.add_argument('file'); c.add_argument('--query',required=True); c.add_argument('--max-tokens',type=int,default=12000); c.add_argument('--section'); c.add_argument('--json',action='store_true')
    s=sp.add_parser('scaffold'); s.add_argument('output'); s.add_argument('--profile',default='generic'); s.add_argument('--variant',default='default'); s.add_argument('--title',default='UNTITLED DOCUMENT'); s.add_argument('--student',default=''); s.add_argument('--supervisor',default=''); s.add_argument('--json',action='store_true')
    rep=sp.add_parser('replace'); rep.add_argument('file'); rep.add_argument('--old',required=True); rep.add_argument('--new',required=True); rep.add_argument('--output'); rep.add_argument('--json',action='store_true')
    v=sp.add_parser('validate'); v.add_argument('file'); v.add_argument('--profile',default='generic'); v.add_argument('--variant',default='default'); v.add_argument('--json',action='store_true')
    r=sp.add_parser('render'); r.add_argument('file'); r.add_argument('--outdir'); r.add_argument('--json',action='store_true')
    e=sp.add_parser('evidence'); esp=e.add_subparsers(dest='action',required=True); el=esp.add_parser('list'); el.add_argument('registry'); el.add_argument('--json',action='store_true')
    return p

def run(argv=None):
    _ensure_utf8()
    a=parser().parse_args(argv)
    try:
        if a.cmd=='doctor':_print(status(),a.json); return 0
        if a.cmd=='capabilities':_print(capabilities(),a.json); return 0
        if a.cmd=='profiles':
            items=[]
            for name in ('generic','hcmunre_dacn_2026_2027'):
                p=load_profile(_resolve_profile(name)); items.append({'id':p.profile_id,'name':p.name,'version':p.version,'variants':sorted(p.variants)})
            _print({'profiles':items},a.json); return 0
        if a.cmd=='init':
            wa=init_workspace(a.path); _print({'workspace':str(wa)},a.json); return 0
        if a.cmd=='inspect':
            ss=index_docx(a.file); _print({'file':str(a.file),'section_count':len(ss),'sections':[{'id':s.section_id,'title':s.title,'level':s.level,'chars':len(s.text)} for s in ss]},a.json); return 0
        if a.cmd=='context':
            b=build_context(index_docx(a.file),a.query,a.max_tokens,a.section); _print({'file':str(a.file),'query':a.query,'estimated_tokens':b.estimated_tokens,'max_tokens':b.max_tokens,'sections':[{'id':s.section_id,'title':s.title,'level':s.level} for s in b.sections],'context':b.text},a.json); return 0
        if a.cmd=='scaffold':
            p=load_profile(_resolve_profile(a.profile)); out=scaffold_document(a.output,p,a.variant,title=a.title,student=a.student,supervisor=a.supervisor); _print({'output':str(out),'profile':p.profile_id,'variant':a.variant},a.json); return 0
        if a.cmd=='replace':
            rr=replace_text(a.file,a.old,a.new,a.output); _print({'output':str(rr.output),'replacements':rr.replacements},a.json); return 0
        if a.cmd=='validate':
            p=load_profile(_resolve_profile(a.profile)); res=validate_document(a.file,p,a.variant); _print({'valid':res.valid,'issues':[asdict(x) for x in res.issues]},a.json); return 0 if res.valid else 2
        if a.cmd=='render':
            out=render_pdf(a.file,a.outdir); _print({'pdf':str(out)},a.json); return 0
        if a.cmd=='evidence' and a.action=='list':_print({'records':EvidenceRegistry(a.registry).list()},a.json); return 0
    except Exception as exc:
        print(json.dumps({'error':type(exc).__name__,'message':str(exc)},ensure_ascii=False),file=sys.stderr); return 2
    return 2

def main(): raise SystemExit(run())

if __name__ == '__main__':
    main()
