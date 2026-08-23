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
    save_project_config,
    set_project_config_value,
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
        print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))
    else:
        if isinstance(obj, str):
            print(obj)
        else:
            print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))

def _resolve_evidence_registry(path_or_ws: str | None = None) -> Path:
    if path_or_ws:
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
        return p
    wa = find_workspace()
    if wa and (wa / 'evidence.json').exists():
        return wa / 'evidence.json'
    return Path('.wordassistant/evidence.json')

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

    # advanced (subcommands: status)
    adv_p = sp.add_parser('advanced', help='Advanced backend facade operations')
    adv_sp = adv_p.add_subparsers(dest='advanced_action', required=True)
    adv_s = adv_sp.add_parser('status', help='Report truthful operational backend status')
    adv_s.add_argument('--json', action='store_true')

    # config (subcommands: show, set)
    cfg_p = sp.add_parser('config', help='Inspect or update workspace configuration')
    cfg_sp = cfg_p.add_subparsers(dest='config_action', required=True)
    cfg_show = cfg_sp.add_parser('show', help='Show workspace configuration')
    cfg_show.add_argument('--json', action='store_true')
    cfg_set = cfg_sp.add_parser('set', help='Set workspace configuration key')
    cfg_set.add_argument('key', help='Configuration key to set')
    cfg_set.add_argument('value', help='Configuration value')
    cfg_set.add_argument('--json', action='store_true')

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
    pv.add_argument('name_or_path')
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
    c.add_argument('--max-tokens', type=int, default=None)
    c.add_argument('--section')
    c.add_argument('--json', action='store_true')

    # scaffold
    s = sp.add_parser('scaffold', help='Generate a new DOCX scaffold from profile')
    s.add_argument('output')
    s.add_argument('--profile', default=None)
    s.add_argument('--variant', default=None)
    s.add_argument('--title', default=None)
    s.add_argument('--student', default=None)
    s.add_argument('--supervisor', default=None)
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
    v.add_argument('--profile', default=None)
    v.add_argument('--variant', default=None)
    v.add_argument('--tolerance', type=float, default=0.08)
    v.add_argument('--json', action='store_true')

    # verify
    ver = sp.add_parser('verify', help='Run full document verification with optional render')
    ver.add_argument('file')
    ver.add_argument('--profile', default=None)
    ver.add_argument('--variant', default=None)
    ver.add_argument('--tolerance', type=float, default=0.08)
    ver.add_argument('--render', action='store_true')
    ver.add_argument('--json', action='store_true')

    # render
    r = sp.add_parser('render', help='Render DOCX to PDF using LibreOffice')
    r.add_argument('file')
    r.add_argument('--output')
    r.add_argument('--timeout', type=int, default=60)
    r.add_argument('--json', action='store_true')

    # evidence
    ev = sp.add_parser('evidence', help='Manage verified source evidence registry')
    ev_sp = ev.add_subparsers(dest='evidence_action', required=True)
    
    ev_add = ev_sp.add_parser('add', help='Add verified evidence record')
    ev_add.add_argument('registry', nargs='?', default=None)
    ev_add.add_argument('--id', required=True)
    ev_add.add_argument('--title', required=True)
    ev_add.add_argument('--authors', required=True, help='Comma-separated authors')
    ev_add.add_argument('--year', type=int, required=True)
    ev_add.add_argument('--url', required=True)
    ev_add.add_argument('--verified-by', required=True)
    ev_add.add_argument('--quote')
    ev_add.add_argument('--claim')
    ev_add.add_argument('--replace', action='store_true')
    ev_add.add_argument('--json', action='store_true')

    ev_get = ev_sp.add_parser('get', help='Get verified evidence record')
    ev_get.add_argument('registry', nargs='?', default=None)
    ev_get.add_argument('key', nargs='?', default=None)
    ev_get.add_argument('--key')
    ev_get.add_argument('--json', action='store_true')

    ev_rm = ev_sp.add_parser('remove', help='Remove verified evidence record')
    ev_rm.add_argument('registry', nargs='?', default=None)
    ev_rm.add_argument('key', nargs='?', default=None)
    ev_rm.add_argument('--key')
    ev_rm.add_argument('--json', action='store_true')

    ev_list = ev_sp.add_parser('list', help='List evidence records')
    ev_list.add_argument('registry', nargs='?', default=None)
    ev_list.add_argument('--json', action='store_true')

    ev_val = ev_sp.add_parser('validate', help='Validate evidence registry records')
    ev_val.add_argument('registry', nargs='?', default=None)
    ev_val.add_argument('--json', action='store_true')

    return p

def run(args: list[str] | None = None) -> int:
    _ensure_utf8()
    p = parser()
    a = p.parse_args(args)

    try:
        if a.cmd == 'doctor':
            s = status()
            _print(s, a.json)
            return 0 if s['core_ready'] else 1

        if a.cmd == 'status':
            _print(get_workspace_status(), a.json)
            return 0

        if a.cmd == 'capabilities':
            _print(get_backend_status(), a.json)
            return 0

        if a.cmd == 'advanced':
            if a.advanced_action == 'status':
                _print(get_backend_status(), a.json)
                return 0

        if a.cmd == 'config':
            if a.config_action == 'show':
                _print(load_project_config(), a.json)
                return 0
            if a.config_action == 'set':
                updated = set_project_config_value(None, a.key, a.value)
                _print(updated, a.json)
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
                prof = resolve_profile(a.name_or_path)
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
            
            ws_cfg = load_project_config(doc_file)
            effective_max_tokens = a.max_tokens or ws_cfg.get('context_budget', 12000)
            
            sections = get_cached_document_index(doc_file, doc_sha)
            if sections is None:
                sections = index_docx(doc_file)
                put_cached_document_index(doc_file, doc_sha, sections)
                
            res = build_context(sections, a.query, max_tokens=effective_max_tokens, target_section_id=a.section)
            data = {
                'query': a.query,
                'max_tokens': effective_max_tokens,
                'target_section': a.section,
                'total_doc_sections': len(sections),
                'selected_sections_count': len(res.sections),
                'estimated_tokens': res.estimated_tokens,
                'truncated': res.truncated,
                'context': res.text,
                'sections': [
                    {'id': s.section_id, 'title': s.title, 'level': s.level}
                    for s in res.sections
                ]
            }
            _print(data, a.json)
            return 0

        if a.cmd == 'scaffold':
            ws_cfg = load_project_config(Path(a.output).parent)
            eff_prof = a.profile or ws_cfg.get('profile', 'generic')
            eff_var = a.variant or ws_cfg.get('variant', 'default')
            eff_title = a.title if a.title is not None else ws_cfg.get('title', 'UNTITLED DOCUMENT')
            eff_student = a.student if a.student is not None else ws_cfg.get('author', '')
            eff_supervisor = a.supervisor if a.supervisor is not None else ws_cfg.get('supervisor', '')
            
            prof = resolve_profile(eff_prof)
            out_file = scaffold_document(
                a.output,
                prof,
                eff_var,
                title=eff_title,
                student=eff_student,
                supervisor=eff_supervisor
            )
            _print({'output': str(out_file), 'profile': prof.profile_id, 'variant': eff_var}, a.json)
            return 0

        if a.cmd == 'replace':
            res = replace_text(a.file, old=a.old, new=a.new, output_path=a.output, dry_run=a.dry_run)
            res_dict = {
                'output': str(res.output),
                'replacements': res.replacements,
                'status': res.status,
                'dry_run': res.dry_run,
                'complex_structures_detected': list(res.complex_structures_detected),
                'advanced_backend_required': res.advanced_backend_required,
                'error': res.error
            }
            _print(res_dict, a.json)
            return 0 if res.status in ('SUCCESS', 'DRY_RUN', 'NO_MATCH') else 1

        if a.cmd == 'validate':
            ws_cfg = load_project_config(Path(a.file).parent)
            eff_prof = a.profile or ws_cfg.get('profile', 'generic')
            eff_var = a.variant or ws_cfg.get('variant', 'default')
            
            prof = resolve_profile(eff_prof)
            res = validate_document(a.file, prof, eff_var, tolerance_cm=a.tolerance, verify_mode=False)
            data = {
                'file': str(a.file),
                'profile': prof.profile_id,
                'variant': eff_var,
                'valid': res.valid,
                'issues': [asdict(x) for x in res.issues]
            }
            _print(data, a.json)
            return 0 if res.valid else 2

        if a.cmd == 'verify':
            ws_cfg = load_project_config(Path(a.file).parent)
            eff_prof = a.profile or ws_cfg.get('profile', 'generic')
            eff_var = a.variant or ws_cfg.get('variant', 'default')
            
            prof = resolve_profile(eff_prof)
            inv = inspect_document(a.file)
            val_res = validate_document(a.file, prof, eff_var, tolerance_cm=a.tolerance, verify_mode=True)
            
            render_info = None
            render_status = "SKIPPED"
            render_ok = True
            if a.render:
                try:
                    r_res = render_pdf(a.file)
                    render_status = "PASS"
                    render_info = {
                        'pdf': str(r_res.pdf_path),
                        'size_bytes': r_res.file_size_bytes,
                        'duration_seconds': r_res.duration_seconds
                    }
                except Exception as r_err:
                    render_status = "FAIL"
                    render_ok = False
                    render_info = {'error': str(r_err)}
                    
            validation_status = "PASS" if val_res.valid else "FAIL"
            overall_pass = val_res.valid and render_ok
            overall_status = "PASS" if overall_pass else "FAIL"
            has_warnings = any(i.severity == 'warning' for i in val_res.issues)
            manual_review_required = not overall_pass or has_warnings or inv.get('advanced_backend_recommended', False)
            
            summary = {
                'file': str(a.file),
                'profile': prof.profile_id,
                'variant': eff_var,
                'overall_status': overall_status,
                'validation_status': validation_status,
                'render_status': render_status,
                'manual_review_required': manual_review_required,
                'valid': overall_pass,
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
            return 0 if overall_pass else 2

        if a.cmd == 'render':
            res = render_pdf(a.file, output_path=a.output, timeout_seconds=a.timeout)
            _print({
                'pdf': str(res.pdf_path),
                'size_bytes': res.file_size_bytes,
                'duration_seconds': res.duration_seconds
            }, a.json)
            return 0

        if a.cmd == 'evidence':
            reg_path = _resolve_evidence_registry(a.registry)
            reg = EvidenceRegistry(reg_path)
            if a.evidence_action == 'add':
                authors_list = [x.strip() for x in a.authors.split(',') if x.strip()]
                rec = {
                    'id': a.id,
                    'title': a.title,
                    'authors': authors_list,
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
                
            if a.evidence_action == 'get':
                if a.key:
                    reg_path = _resolve_evidence_registry(a.registry)
                    key = a.key
                else:
                    reg_path = _resolve_evidence_registry(None)
                    key = a.registry
                reg = EvidenceRegistry(reg_path)
                rec = reg.get(key)
                _print(rec, a.json)
                return 0

            if a.evidence_action == 'remove':
                if a.key:
                    reg_path = _resolve_evidence_registry(a.registry)
                    key = a.key
                else:
                    reg_path = _resolve_evidence_registry(None)
                    key = a.registry
                reg = EvidenceRegistry(reg_path)
                ok = reg.remove(key)
                _print({'removed': ok, 'id': key, 'registry': str(reg_path)}, a.json)
                return 0 if ok else 1

            if a.evidence_action == 'list':
                records = reg.list()
                _print({'records': records, 'total': len(records), 'registry': str(reg_path)}, a.json)
                return 0
                
            if a.evidence_action == 'validate':
                errs = reg.validate_all()
                _print({'valid': len(errs) == 0, 'errors': errs, 'registry': str(reg_path)}, a.json)
                return 0 if len(errs) == 0 else 1

    except Exception as exc:
        _print({'error': str(exc)}, getattr(a, 'json', False))
        return 1

    return 0

def main() -> None:
    sys.exit(run())

if __name__ == '__main__':
    main()
