from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from .doctor import status
from .document.structure import index_docx, inspect_document
from .context.retrieve import build_context
from .profiles.loader import (
    load_profile,
    discover_profiles,
    resolve_profile,
    validate_profile_dict,
    ProfileError,
)
from .document.scaffold import scaffold_document
from .document.validate import validate_document
from .document.render import render_pdf
from .evidence.registry import EvidenceRegistry, EvidenceError
from .workspace import (
    init_workspace,
    find_workspace,
    get_workspace_status,
    load_project_config,
    get_cached_document_index,
    put_cached_document_index,
)
from .backends.status import get_backend_status
from .document.edit import replace_text

def _ensure_utf8() -> None:
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def _print(obj: Any, json_mode: bool = False) -> None:
    _ensure_utf8()
    if json_mode:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    else:
        if isinstance(obj, str):
            print(obj)
        else:
            print(json.dumps(obj, ensure_ascii=False, indent=2))

def _resolve_evidence_registry(path_or_ws: str) -> Path:
    p = Path(path_or_ws)
    if p.is_file():
        return p
    if p.is_dir():
        wa_ev = p / '.wordassistant' / 'evidence.json'
        if wa_ev.exists():
            return wa_ev
        if (p / 'evidence.json').exists():
            return p / 'evidence.json'
        return p / '.wordassistant' / 'evidence.json'
    wa = find_workspace()
    if wa and (wa / 'evidence.json').exists():
        return wa / 'evidence.json'
    return p

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='wordassistant', description='Deterministic profile-driven DOCX engineering toolkit')
    sp = p.add_subparsers(dest='cmd', required=True)

    # doctor
    d = sp.add_parser('doctor', help='Check environment health and dependencies')
    d.add_argument('--json', action='store_true')

    # status
    st = sp.add_parser('status', help='Report workspace configuration and status')
    st.add_argument('--json', action='store_true')

    # capabilities
    cap = sp.add_parser('capabilities', help='Explain core vs optional advanced capabilities')
    cap.add_argument('--json', action='store_true')

    # profiles
    pr = sp.add_parser('profiles', help='List discovered document profiles')
    pr.add_argument('--json', action='store_true')

    # profile (subcommands: show, validate)
    prof_p = sp.add_parser('profile', help='Profile management operations')
    prof_sp = prof_p.add_subparsers(dest='profile_action', required=True)
    
    ps = prof_sp.add_parser('show', help='Show detailed profile structure')
    ps.add_argument('name_or_path')
    ps.add_argument('--json', action='store_true')
    
    pv = prof_sp.add_parser('validate', help='Strictly validate profile schema')
    pv.add_argument('path')
    pv.add_argument('--json', action='store_true')

    # init
    init = sp.add_parser('init', help='Initialize a WordAssistant workspace')
    init.add_argument('path')
    init.add_argument('--json', action='store_true')

    # inspect
    i = sp.add_parser('inspect', help='Generate detailed inventory of a DOCX file')
    i.add_argument('file')
    i.add_argument('--json', action='store_true')

    # context
    c = sp.add_parser('context', help='Retrieve token-bounded lexical context from DOCX')
    c.add_argument('file')
    c.add_argument('--query', required=True)
    c.add_argument('--max-tokens', type=int, default=12000)
    c.add_argument('--section')
    c.add_argument('--json', action='store_true')

    # scaffold
    s = sp.add_parser('scaffold', help='Generate a new DOCX scaffold from profile')
    s.add_argument('output')
    s.add_argument('--profile', default='generic')
    s.add_argument('--variant', default='default')
    s.add_argument('--title', default='UNTITLED DOCUMENT')
    s.add_argument('--student', default='')
    s.add_argument('--supervisor', default='')
    s.add_argument('--json', action='store_true')

    # replace
    rep = sp.add_parser('replace', help='Perform safe text replacement in DOCX')
    rep.add_argument('file')
    rep.add_argument('--old', required=True)
    rep.add_argument('--new', required=True)
    rep.add_argument('--output')
    rep.add_argument('--dry-run', action='store_true')
    rep.add_argument('--json', action='store_true')

    # validate
    v = sp.add_parser('validate', help='Validate document against profile specification')
    v.add_argument('file')
    v.add_argument('--profile', default='generic')
    v.add_argument('--variant', default='default')
    v.add_argument('--tolerance', type=float, default=0.08)
    v.add_argument('--json', action='store_true')

    # render
    r = sp.add_parser('render', help='Render DOCX to PDF via LibreOffice in isolation')
    r.add_argument('file')
    r.add_argument('--outdir')
    r.add_argument('--json', action='store_true')

    # evidence
    e = sp.add_parser('evidence', help='Manage verified evidence citations')
    esp = e.add_subparsers(dest='evidence_action', required=True)
    
    el = esp.add_parser('list', help='List evidence records')
    el.add_argument('registry')
    el.add_argument('--json', action='store_true')

    eg = esp.add_parser('get', help='Get single evidence record')
    eg.add_argument('registry')
    eg.add_argument('id')
    eg.add_argument('--json', action='store_true')

    ea = esp.add_parser('add', help='Add evidence record')
    ea.add_argument('registry')
    ea.add_argument('--id', required=True)
    ea.add_argument('--title', required=True)
    ea.add_argument('--authors', required=True, help='Comma-separated author names')
    ea.add_argument('--year', type=int, required=True)
    ea.add_argument('--url', required=True)
    ea.add_argument('--verified-by', required=True)
    ea.add_argument('--quote', default='')
    ea.add_argument('--claim', default='')
    ea.add_argument('--replace', action='store_true')
    ea.add_argument('--json', action='store_true')

    er = esp.add_parser('remove', help='Remove evidence record')
    er.add_argument('registry')
    er.add_argument('id')
    er.add_argument('--json', action='store_true')

    ev = esp.add_parser('validate', help='Validate all evidence records in registry')
    ev.add_argument('registry')
    ev.add_argument('--json', action='store_true')

    # verify
    ver = sp.add_parser('verify', help='Orchestrator command: inspect, validate, and optionally render')
    ver.add_argument('file')
    ver.add_argument('--profile', default='generic')
    ver.add_argument('--variant', default='default')
    ver.add_argument('--tolerance', type=float, default=0.08)
    ver.add_argument('--render', action='store_true')
    ver.add_argument('--json', action='store_true')

    return p

def run(argv: list[str] | None = None) -> int:
    _ensure_utf8()
    a = parser().parse_args(argv)
    try:
        if a.cmd == 'doctor':
            _print(status(), a.json)
            return 0

        if a.cmd == 'status':
            _print(get_workspace_status(), a.json)
            return 0

        if a.cmd == 'capabilities':
            _print(get_backend_status(), a.json)
            return 0

        if a.cmd == 'profiles':
            discovered = discover_profiles()
            items = [
                {
                    'id': p.profile_id,
                    'name': p.name,
                    'version': p.version,
                    'variants': sorted(p.variants.keys()),
                    'source_policy': p.source_policy
                }
                for p in discovered
            ]
            _print({'profiles': items}, a.json)
            return 0

        if a.cmd == 'profile':
            if a.profile_action == 'show':
                prof = resolve_profile(a.name_or_path)
                data = {
                    'id': prof.profile_id,
                    'name': prof.name,
                    'version': prof.version,
                    'source_policy': prof.source_policy,
                    'variants': {
                        v_name: {
                            'page': asdict(v.page),
                            'typography': {
                                'body_font': v.typography.body_font,
                                'body_size_pt': v.typography.body_size_pt,
                                'line_spacing': v.typography.line_spacing,
                                'styles': dict(v.typography.styles)
                            },
                            'front_matter': list(v.front_matter),
                            'section_blueprint': list(v.section_blueprint),
                            'citations': dict(v.citations),
                            'header_footer': dict(v.header_footer),
                            'template_asset': v.template_asset
                        }
                        for v_name, v in prof.variants.items()
                    }
                }
                _print(data, a.json)
                return 0
            if a.profile_action == 'validate':
                p_file = Path(a.path)
                prof = load_profile(p_file)
                _print({'valid': True, 'profile_id': prof.profile_id, 'version': prof.version, 'variants': list(prof.variants.keys())}, a.json)
                return 0

        if a.cmd == 'init':
            wa = init_workspace(a.path)
            _print({'workspace': str(wa), 'project_config': str(wa / 'project.json')}, a.json)
            return 0

        if a.cmd == 'inspect':
            inv = inspect_document(a.file)
            _print(inv, a.json)
            return 0

        if a.cmd == 'context':
            doc_file = Path(a.file).resolve()
            doc_bytes = doc_file.read_bytes()
            doc_sha = hashlib.sha256(doc_bytes).hexdigest()
            
            # Check cache in workspace
            sections = get_cached_document_index(None, doc_sha)
            if sections is None:
                sections = index_docx(doc_file)
                put_cached_document_index(None, doc_sha, sections)
                
            b = build_context(sections, a.query, a.max_tokens, a.section)
            _print({
                'file': str(doc_file),
                'query': a.query,
                'estimated_tokens': b.estimated_tokens,
                'max_tokens': b.max_tokens,
                'sections': [{'id': s.section_id, 'title': s.title, 'level': s.level} for s in b.sections],
                'context': b.text
            }, a.json)
            return 0

        if a.cmd == 'scaffold':
            prof = resolve_profile(a.profile)
            out = scaffold_document(
                a.output,
                prof,
                a.variant,
                title=a.title,
                student=a.student,
                supervisor=a.supervisor
            )
            _print({'output': str(out), 'profile': prof.profile_id, 'variant': a.variant}, a.json)
            return 0

        if a.cmd == 'replace':
            rr = replace_text(a.file, a.old, a.new, a.output, dry_run=a.dry_run)
            _print({
                'output': str(rr.output),
                'replacements': rr.replacements,
                'dry_run': rr.dry_run,
                'complex_structures_detected': list(rr.complex_structures_detected),
                'advanced_backend_recommended': rr.advanced_backend_recommended
            }, a.json)
            return 0

        if a.cmd == 'validate':
            prof = resolve_profile(a.profile)
            res = validate_document(a.file, prof, a.variant, tolerance_cm=a.tolerance)
            _print({
                'valid': res.valid,
                'issues': [asdict(x) for x in res.issues]
            }, a.json)
            return 0 if res.valid else 2

        if a.cmd == 'render':
            res = render_pdf(a.file, a.outdir)
            _print({
                'pdf': str(res.pdf_path),
                'size_bytes': res.file_size_bytes,
                'engine': res.engine,
                'duration_seconds': res.duration_seconds
            }, a.json)
            return 0

        if a.cmd == 'evidence':
            reg_path = _resolve_evidence_registry(a.registry)
            reg = EvidenceRegistry(reg_path)
            
            if a.evidence_action == 'list':
                _print({'registry': str(reg_path), 'records': reg.list()}, a.json)
                return 0
            if a.evidence_action == 'get':
                rec = reg.get(a.id)
                _print(rec, a.json)
                return 0
            if a.evidence_action == 'add':
                authors = [x.strip() for x in a.authors.split(',') if x.strip()]
                rec = {
                    'id': a.id,
                    'title': a.title,
                    'authors': authors,
                    'year': a.year,
                    'url': a.url,
                    'verified_by': a.verified_by
                }
                if a.quote:
                    rec['quote'] = a.quote
                if a.claim:
                    rec['claim'] = a.claim
                reg.add(rec, replace=a.replace)
                _print({'status': 'added', 'id': a.id, 'registry': str(reg_path)}, a.json)
                return 0
            if a.evidence_action == 'remove':
                removed = reg.remove(a.id)
                _print({'status': 'removed' if removed else 'not_found', 'id': a.id}, a.json)
                return 0 if removed else 2
            if a.evidence_action == 'validate':
                errors = reg.validate_all()
                _print({'valid': len(errors) == 0, 'errors': errors}, a.json)
                return 0 if len(errors) == 0 else 2

        if a.cmd == 'verify':
            prof = resolve_profile(a.profile)
            inv = inspect_document(a.file)
            val_res = validate_document(a.file, prof, a.variant, tolerance_cm=a.tolerance)
            
            render_info = None
            if a.render:
                try:
                    r_res = render_pdf(a.file)
                    render_info = {
                        'pdf': str(r_res.pdf_path),
                        'size_bytes': r_res.file_size_bytes,
                        'duration_seconds': r_res.duration_seconds
                    }
                except Exception as r_err:
                    render_info = {'error': str(r_err)}
                    
            summary = {
                'file': str(a.file),
                'profile': prof.profile_id,
                'variant': a.variant,
                'valid': val_res.valid,
                'issues': [asdict(x) for x in val_res.issues],
                'inventory': {
                    'paragraphs': inv['paragraphs'],
                    'tables': inv['tables'],
                    'sections': inv['sections'],
                    'images': inv['images'],
                    'fields': inv['fields']
                },
                'render': render_info
            }
            _print(summary, a.json)
            return 0 if val_res.valid else 2

    except Exception as exc:
        print(json.dumps({'error': type(exc).__name__, 'message': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 2

def main() -> None:
    raise SystemExit(run())

if __name__ == '__main__':
    main()
