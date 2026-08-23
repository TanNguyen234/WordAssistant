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
from .capabilities import capabilities
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
            cand = p / '.wordassistant' / 'evidence.json'
            if cand.exists():
                return cand
            cand_direct = p / 'evidence.json'
            if cand_direct.exists():
                return cand_direct
            return p / 'evidence.json'
    wa = find_workspace()
    if wa:
        return wa / 'evidence.json'
    return Path.cwd() / 'evidence.json'

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='wordassistant',
        description='WordAssistant V2: Deterministic, profile-driven Word DOCX automation and bounded-context toolkit.'
    )
    sp = p.add_subparsers(dest='cmd', required=True)

    # doctor
    doc = sp.add_parser('doctor', help='Check system environment and runtime tools')
    doc.add_argument('--json', action='store_true')

    # status
    st = sp.add_parser('status', help='Show workspace status and cache stats')
    st.add_argument('--json', action='store_true')

    # capabilities
    cap = sp.add_parser('capabilities', help='List core and optional backend capabilities')
    cap.add_argument('--json', action='store_true')

    # advanced
    adv = sp.add_parser('advanced', help='Query advanced Word backend status')
    adv_sp = adv.add_subparsers(dest='advanced_action', required=True)
    adv_st = adv_sp.add_parser('status', help='Show advanced backend operational status')
    adv_st.add_argument('--json', action='store_true')

    # config
    cfg = sp.add_parser('config', help='View or update workspace configuration')
    cfg_sp = cfg.add_subparsers(dest='config_action', required=True)
    cfg_show = cfg_sp.add_parser('show', help='Show workspace project configuration')
    cfg_show.add_argument('--json', action='store_true')
    cfg_set = cfg_sp.add_parser('set', help='Set workspace configuration value')
    cfg_set.add_argument('key', help='Configuration key')
    cfg_set.add_argument('value', help='Configuration value')
    cfg_set.add_argument('--json', action='store_true')

    # profiles
    profs = sp.add_parser('profiles', help='List all available document profiles')
    profs.add_argument('--json', action='store_true')

    # profile
    prof = sp.add_parser('profile', help='Inspect or validate a document profile')
    prof_sp = prof.add_subparsers(dest='profile_action', required=True)
    
    prof_show = prof_sp.add_parser('show', help='Show full details of a profile')
    prof_show.add_argument('name_or_path', help='Profile ID or JSON file path')
    prof_show.add_argument('--json', action='store_true')
    
    prof_val = prof_sp.add_parser('validate', help='Validate profile JSON schema')
    prof_val.add_argument('name_or_path', help='Profile ID or JSON file path')
    prof_val.add_argument('--json', action='store_true')

    # init
    ini = sp.add_parser('init', help='Initialize .wordassistant workspace')
    ini.add_argument('path', nargs='?', default='.')
    ini.add_argument('--json', action='store_true')

    # inspect
    ins = sp.add_parser('inspect', help='Inspect DOCX structure and package parts')
    ins.add_argument('file')
    ins.add_argument('--json', action='store_true')

    # context
    ctx = sp.add_parser('context', help='Retrieve bounded context for a query')
    ctx.add_argument('file')
    ctx.add_argument('--query', required=True)
    ctx.add_argument('--max-tokens', type=int, default=None)
    ctx.add_argument('--active-section-id', '--section', dest='active_section_id', default=None)
    ctx.add_argument('--json', action='store_true')

    # scaffold
    scaf = sp.add_parser('scaffold', help='Generate compliant DOCX from profile')
    scaf.add_argument('output')
    scaf.add_argument('--profile', default=None)
    scaf.add_argument('--variant', default=None)
    scaf.add_argument('--title', default=None)
    scaf.add_argument('--author', '--student', dest='student', default=None)
    scaf.add_argument('--supervisor', default=None)
    scaf.add_argument('--dry-run', action='store_true')
    scaf.add_argument('--json', action='store_true')

    # replace
    rep = sp.add_parser('replace', help='Perform safe text replacement across document')
    rep.add_argument('file')
    rep.add_argument('--old', required=True)
    rep.add_argument('--new', required=True)
    rep.add_argument('--output', default=None)
    rep.add_argument('--count', type=int, default=None)
    rep.add_argument('--dry-run', action='store_true')
    rep.add_argument('--json', action='store_true')

    # validate
    val = sp.add_parser('validate', help='Validate document against profile specification')
    val.add_argument('file')
    val.add_argument('--profile', default=None)
    val.add_argument('--variant', default=None)
    val.add_argument('--tolerance', type=float, default=0.08)
    val.add_argument('--json', action='store_true')

    # verify
    ver = sp.add_parser('verify', help='Full audit: inspect + validate + optional render')
    ver.add_argument('file')
    ver.add_argument('--profile', default=None)
    ver.add_argument('--variant', default=None)
    ver.add_argument('--tolerance', type=float, default=0.08)
    ver.add_argument('--render', action='store_true')
    ver.add_argument('--json', action='store_true')

    # render
    r = sp.add_parser('render', help='Render DOCX to PDF using LibreOffice')
    r.add_argument('file')
    r.add_argument('--outdir', '--output', dest='outdir', default=None, help='Output directory for generated PDF')
    r.add_argument('--timeout', type=int, default=180, help='Render timeout in seconds')
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
            _print(capabilities(), a.json)
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
                    'id': prof.profile_id,
                    'name': prof.name,
                    'version': prof.version,
                    'variants': sorted(prof.variants.keys()),
                    'source_policy': prof.source_policy
                }
                for prof in discovered
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
            effective_max_tokens = int(a.max_tokens if a.max_tokens is not None else ws_cfg.get('context_budget', 12000))
            
            sections = get_cached_document_index(doc_file, doc_sha)
            if not sections:
                sections = index_docx(doc_file)
                put_cached_document_index(doc_file, doc_sha, sections)
                
            bundle = build_context(
                sections,
                query=a.query,
                max_tokens=effective_max_tokens,
                active_section_id=a.active_section_id
            )
            data = {
                'query': bundle.query,
                'sections': [
                    {'id': s.section_id, 'title': s.title, 'level': s.level}
                    for s in bundle.sections
                ],
                'text': bundle.text,
                'estimated_tokens': bundle.estimated_tokens,
                'max_tokens': bundle.max_tokens,
                'truncated': bundle.truncated
            }
            _print(data, a.json)
            return 0

        if a.cmd == 'scaffold':
            ws_cfg = load_project_config(Path(a.output).parent)
            eff_prof = a.profile or ws_cfg.get('profile', 'generic')
            eff_var = a.variant or ws_cfg.get('variant', 'default')
            eff_title = a.title if a.title is not None else ws_cfg.get('title')
            eff_student = a.student if a.student is not None else (ws_cfg.get('author') or ws_cfg.get('student'))
            eff_supervisor = a.supervisor if a.supervisor is not None else ws_cfg.get('supervisor')
            
            prof = resolve_profile(eff_prof, start_path=Path(a.output).parent)
            res = scaffold_document(
                a.output,
                prof,
                eff_var,
                title=eff_title,
                student=eff_student,
                supervisor=eff_supervisor,
                dry_run=a.dry_run
            )
            _print({
                'status': 'SUCCESS' if not a.dry_run else 'DRY_RUN',
                'output': str(a.output),
                'profile': eff_prof,
                'variant': eff_var,
                'path': str(res)
            }, a.json)
            return 0

        if a.cmd == 'replace':
            res = replace_text(
                a.file,
                a.old,
                a.new,
                output_path=a.output,
                count=a.count,
                dry_run=a.dry_run
            )
            _print(asdict(res), a.json)
            return 0 if res.status in ('SUCCESS', 'DRY_RUN') else 1

        if a.cmd == 'validate':
            ws_cfg = load_project_config(Path(a.file).parent)
            eff_prof = a.profile or ws_cfg.get('profile', 'generic')
            eff_var = a.variant or ws_cfg.get('variant', 'default')
            
            prof = resolve_profile(eff_prof, start_path=Path(a.file).parent)
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
            
            prof = resolve_profile(eff_prof, start_path=Path(a.file).parent)
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
            res = render_pdf(a.file, output_dir=a.outdir, timeout_seconds=a.timeout)
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
