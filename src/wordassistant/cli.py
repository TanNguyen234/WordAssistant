from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

from .doctor import status
from .document.structure import index_docx, inspect_document
from .document.captions import audit_captions
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
from .document.render import render_document
from .document.verify import _render_via_execution_service, verify_document
from .document.integrity import audit_integrity, build_provenance_manifest
from .document.compose import compose_document
from .evidence.registry import EvidenceRegistry, EvidenceError
from .evidence.research import (
    SourceResearchError,
    download_open_access_pdf,
    find_open_access,
    import_crossref_doi,
    review_downloaded_source,
    search_crossref,
    search_source_excerpts,
)
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
from .cli_contracts import OPERATION_ALIASES
from .selectors import SELECTOR_HELP
from .facade import WordDocument
from .operations.comments import comment_operation
from .operations.revisions import revision_operation
from .operations.compare import compare_documents, merge_documents
from .backends.word_native.backend import WordNativeBackend
from .operations.models import BatchExecutionError, BatchPlan, OperationRequest
from .operations.models import OperationUnavailable
from .execution import ExecutionService

# Compatibility injection point retained for existing integrations/tests.
render_pdf = render_document


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)

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


def _write_json_atomic(path: str | Path, payload: Any) -> Path:
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            newline='\n',
            prefix=f'.{destination.name}.',
            suffix='.tmp',
            dir=destination.parent,
            delete=False,
        ) as stream:
            temporary_name = stream.name
            json.dump(payload, stream, ensure_ascii=False, indent=2, default=str)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, destination)
        return destination
    finally:
        if temporary_name and Path(temporary_name).exists():
            Path(temporary_name).unlink()


def _assert_report_output_is_distinct(
    report_output: str | Path,
    source: str | Path,
    report: dict,
    reuse_report: str | Path | None = None,
) -> None:
    destination = Path(report_output).expanduser().resolve()
    protected = {Path(source).expanduser().resolve()}
    if reuse_report:
        protected.add(Path(reuse_report).expanduser().resolve())
    render = report.get('render') or {}
    if render.get('pdf_path'):
        protected.add(Path(render['pdf_path']).expanduser().resolve())
    protected.update(
        Path(image).expanduser().resolve()
        for image in render.get('page_images', [])
    )
    normalized = {os.path.normcase(str(path)) for path in protected}
    if os.path.normcase(str(destination)) in normalized:
        raise ValueError(
            "--report-output must not overwrite the source DOCX, reuse report, "
            "rendered PDF, or rendered page image."
        )
def _resolve_evidence_registry(path_or_ws: str | None = None) -> Path:
    if path_or_ws:
        p = Path(path_or_ws)
        if p.is_file() or p.name.endswith('.json') or p.suffix == '.json':
            return p
        if p.is_dir():
            cand = p / '.wordassistant' / 'evidence.json'
            if cand.exists():
                return cand
            cand_direct = p / 'evidence.json'
            if cand_direct.exists():
                return cand_direct
            return p / 'evidence.json'
        return p
    wa = find_workspace()
    if wa:
        return wa / 'evidence.json'
    return Path.cwd() / 'evidence.json'

def parser() -> argparse.ArgumentParser:
    p = _ArgumentParser(
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
    ins.add_argument('--summary', action='store_true', help='Omit paragraph text and detailed object inventories')
    ins.add_argument('--json', action='store_true')

    # context
    ctx = sp.add_parser('context', help='Retrieve bounded context for a query')
    ctx.add_argument('file')
    ctx.add_argument('--query', required=True)
    ctx.add_argument('--max-tokens', type=int, default=None)
    ctx.add_argument('--active-section-id', '--section', dest='active_section_id', default=None)
    ctx.add_argument('--only-section', dest='target_section_id', default=None, help='Restrict returned context to exactly one indexed section')
    ctx.add_argument('--json', action='store_true')

    # scaffold
    scaf = sp.add_parser('scaffold', help='Generate compliant DOCX from profile')
    scaf.add_argument('output')
    scaf.add_argument('--profile', default=None)
    scaf.add_argument('--variant', default=None)
    scaf.add_argument('--title', default=None)
    scaf.add_argument('--author', '--student', dest='student', default=None)
    scaf.add_argument('--supervisor', default=None)
    scaf.add_argument('--cover-metadata', default=None, help='JSON file with editable cover fields such as student_id, class, cohort, month, and year')
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
    ver.add_argument('--engine', choices=('auto', 'word', 'libreoffice'), default='auto')
    ver.add_argument('--native-fields', action='store_true', help='Reopen, update, and persist fields through Microsoft Word during verification')
    ver.add_argument('--visual-reviewed', action='store_true', help='Attest that every rendered page image was reviewed after a successful content audit')
    ver.add_argument('--visual-review-token', default=None, help='Token from the current visual_review_challenge; binds review to exact page-image hashes')
    ver.add_argument('--reuse-render-report', default=None, help='Reuse verified PDF/page artifacts from a prior full verify report (no render)')
    ver.add_argument('--report-output', default=None, help='Write the complete verify report atomically to this path')
    ver.add_argument('--summary', action='store_true', help='Print a compact summary; requires --report-output')
    ver.add_argument('--delivery', action='store_true', help='Require the complete native render and visual-review delivery gate')
    ver.add_argument('--json', action='store_true')

    # render
    r = sp.add_parser('render', help='Render DOCX to PDF using LibreOffice')
    r.add_argument('file')
    r.add_argument('--outdir', '--output', dest='outdir', default=None, help='Output directory for generated PDF')
    r.add_argument('--timeout', type=int, default=180, help='Render timeout in seconds')
    r.add_argument('--engine', choices=('auto', 'word', 'libreoffice'), default='auto')
    r.add_argument('--json', action='store_true')

    # integrity
    integrity = sp.add_parser(
        'integrity',
        help='Audit academic integrity and create provenance bound to exact file hashes',
    )
    integrity_sp = integrity.add_subparsers(dest='integrity_action', required=True)
    integrity_audit = integrity_sp.add_parser(
        'audit',
        help='Run deterministic citation, evidence, Unicode, placeholder, and style-review gates',
    )
    integrity_audit.add_argument('file')
    integrity_audit.add_argument('--evidence', default=None, help='Evidence registry JSON path')
    integrity_audit.add_argument('--profile', default=None)
    integrity_audit.add_argument('--variant', default=None)
    integrity_audit.add_argument('--fail-on-warn', action='store_true')
    integrity_audit.add_argument('--json', action='store_true')

    integrity_manifest = integrity_sp.add_parser(
        'provenance',
        help='Write an atomic provenance manifest bound to the DOCX and evidence registry',
    )
    integrity_manifest.add_argument('file')
    integrity_manifest.add_argument('--output', required=True)
    integrity_manifest.add_argument('--evidence', default=None, help='Evidence registry JSON path')
    integrity_manifest.add_argument('--profile', default=None)
    integrity_manifest.add_argument('--variant', default=None)
    integrity_manifest.add_argument('--disclosure', default=None)
    integrity_manifest.add_argument('--audit-report', default=None)
    integrity_manifest.add_argument('--json', action='store_true')

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
    evidence_kind = ev_add.add_mutually_exclusive_group(required=True)
    evidence_kind.add_argument('--verified-real-source', action='store_true', help='Confirm the source was independently checked and is not synthetic')
    evidence_kind.add_argument('--synthetic', action='store_true', help='Mark a QA fixture that must remain visibly labeled as synthetic')
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

    # Academic source discovery is opt-in; search results stay candidates until
    # a downloaded source passage has been checked and reviewed.
    research = sp.add_parser('research', help='Discover, download, and review academic sources')
    research_sp = research.add_subparsers(dest='research_action', required=True)
    research_search = research_sp.add_parser('search', help='Search Crossref metadata; results are discovery leads')
    research_search.add_argument('--query', required=True)
    research_search.add_argument('--limit', type=int, default=10)
    research_search.add_argument('--json', action='store_true')
    research_import = research_sp.add_parser('import-doi', help='Import Crossref DOI metadata as a non-citable candidate')
    research_import.add_argument('doi')
    research_import.add_argument('--registry', default=None)
    research_import.add_argument('--json', action='store_true')
    research_oa = research_sp.add_parser('open-access', help='Find an explicitly licensed OA PDF for a DOI candidate')
    research_oa.add_argument('id')
    research_oa.add_argument('--registry', default=None)
    research_oa.add_argument('--email-env', default='UNPAYWALL_EMAIL', help='Environment variable holding the required Unpaywall email; its value is never stored or printed')
    research_oa.add_argument('--json', action='store_true')
    research_download = research_sp.add_parser('download', help='Download an explicitly licensed OA PDF into .wordassistant/sources')
    research_download.add_argument('id')
    research_download.add_argument('--registry', default=None)
    research_download.add_argument('--json', action='store_true')
    research_excerpt = research_sp.add_parser('excerpt', help='Return bounded matching passages from a downloaded source')
    research_excerpt.add_argument('id')
    research_excerpt.add_argument('--registry', default=None)
    research_excerpt.add_argument('--query', required=True)
    research_excerpt.add_argument('--limit', type=int, default=5)
    research_excerpt.add_argument('--context-chars', type=int, default=300)
    research_excerpt.add_argument('--json', action='store_true')
    research_review = research_sp.add_parser('review', help='Verify a source excerpt and mark a source record reviewed')
    research_review.add_argument('id')
    research_review.add_argument('--registry', default=None)
    research_review.add_argument('--claim', required=True)
    research_review.add_argument('--support-excerpt', required=True)
    research_review.add_argument('--support-location', required=True, help='Page, section, table, or figure in the downloaded source')
    research_review.add_argument('--reviewed-by', required=True)
    research_review.add_argument('--language', choices=('vi', 'en'), default=None, help='Verified source language; required when Crossref metadata has no supported language')
    research_review.add_argument('--confirm-support', action='store_true', required=True, help='Confirm that you checked this passage and it supports the stated claim')
    research_review.add_argument('--quote', action='store_true', help='Record the exact excerpt as a direct quotation')
    research_review.add_argument('--json', action='store_true')

    # Compact universal-core surface. Existing V2 commands above remain
    # compatibility aliases; these are the canonical agent-facing families.
    create = sp.add_parser('create', help='Create a DOCX from a profile')
    create.add_argument('output')
    create.add_argument('--profile', default=None)
    create.add_argument('--variant', default=None)
    create.add_argument('--title', default=None)
    create.add_argument('--author', '--student', dest='student', default=None)
    create.add_argument('--supervisor', default=None)
    create.add_argument('--cover-metadata', default=None, help='JSON file with editable cover fields such as student_id, class, cohort, month, and year')
    create.add_argument('--dry-run', action='store_true')
    create.add_argument('--json', action='store_true')

    apply = sp.add_parser('apply', help='Atomically apply an ordered operation plan')
    apply.add_argument('file', help='Input DOCX path')
    apply.add_argument('--output', required=True, help='Final output DOCX path')
    apply.add_argument('--plan', required=True, help='Version-1 operation plan JSON')
    apply.add_argument('--checkpoint', nargs='?', const='auto', default=None)
    apply.add_argument('--json', action='store_true')

    compose = sp.add_parser(
        'compose',
        help='Populate a scaffold from a bounded version-1 content JSON file',
    )
    compose.add_argument('file', help='Input scaffold DOCX path')
    compose.add_argument('--output', required=True, help='Final output DOCX path')
    compose.add_argument('--content', required=True, help='Version-1 content JSON path')
    compose.add_argument('--evidence', default=None, help='Evidence registry JSON path')
    compose.add_argument('--profile', default=None, help='Selected profile; supplies citation style, ordering, and bibliography heading defaults')
    compose.add_argument('--variant', default=None)
    compose.add_argument('--min-visible-characters', type=int, default=None)
    compose.add_argument('--max-visible-characters', type=int, default=None)
    compose.add_argument('--dry-run', action='store_true')
    compose.add_argument('--json', action='store_true')

    generic_families = {
        'edit': 'Edit document text',
        'format': 'Format runs, paragraphs, or styles',
        'list': 'Create and edit lists or heading numbering',
        'table': 'Create and edit tables',
        'image': 'Insert and edit images',
        'section': 'Create and edit sections',
        'page-number': 'Configure or inspect page numbering',
        'field': 'Insert, inspect, update, lock, or remove fields',
        'toc': 'Insert or update TOC, LOF, or LOT fields',
        'caption': 'Audit captions or insert Word captions',
        'reference': 'Manage bookmarks, hyperlinks, cross-references, and citations',
        'comment': 'Manage Word-native comments',
        'revision': 'Manage Word-native tracked changes',
        'protect': 'Inspect or configure document protection',
        'properties': 'Inspect or update document properties',
        'mail-merge': 'Execute Word-native mail merge',
    }
    for family_name, family_help in generic_families.items():
        family = sp.add_parser(family_name, help=family_help)
        family.add_argument('action', help='High-level action, for example create, insert, inspect, or update')
        family.add_argument('file', help='Input DOCX path')
        family.add_argument('--output', default=None)
        family.add_argument('--selector', default=None, help=SELECTOR_HELP)
        family.add_argument('--options', default='{}', help='Operation options as a JSON object')
        family.add_argument('--dry-run', action='store_true')
        family.add_argument('--checkpoint', nargs='?', const='auto', default=None)
        family.add_argument('--json', action='store_true')

    for family_name, family_help in (
        ('compare', 'Compare two DOCX files using Microsoft Word'),
        ('merge', 'Combine revisions from two DOCX files using Microsoft Word'),
    ):
        family = sp.add_parser(family_name, help=family_help)
        family.add_argument('file')
        family.add_argument('other')
        family.add_argument('--output', required=True)
        family.add_argument('--json', action='store_true')

    return p

def run(args: list[str] | None = None) -> int:
    _ensure_utf8()
    p = parser()
    try:
        a = p.parse_args(args)
    except ValueError as exc:
        values = list(args) if args is not None else sys.argv[1:]
        _print(
            {
                'status': 'ERROR',
                'error': {
                    'code': 'ARGUMENT_ERROR',
                    'message': str(exc),
                },
            },
            '--json' in values,
        )
        return 2

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
            if a.summary:
                summary_keys = (
                    'file', 'file_name', 'size_bytes', 'paragraphs', 'tables',
                    'sections', 'images', 'hyperlinks', 'bookmarks', 'comments',
                    'footnotes', 'endnotes', 'content_controls',
                    'document_protection', 'revisions', 'fields',
                    'advanced_backend_recommended', 'sections_detail',
                )
                outline = inv.get('outline', [])
                inv = {key: inv[key] for key in summary_keys if key in inv}
                inv['outline_count'] = len(outline)
                inv['outline_preview'] = outline[:100]
                inv['outline_preview_truncated'] = len(outline) > 100
            _print(inv, a.json)
            return 0

        if a.cmd == 'caption' and a.action == 'audit':
            if (
                a.output is not None
                or a.selector is not None
                or a.options != '{}'
                or a.dry_run
                or a.checkpoint is not None
            ):
                raise ValueError(
                    "caption audit is read-only and does not accept mutation options"
                )
            _print(audit_captions(a.file), a.json)
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
                active_section_id=a.active_section_id,
                target_section_id=a.target_section_id,
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

        if a.cmd in {'scaffold', 'create'}:
            ws_cfg = load_project_config(Path(a.output).parent)
            eff_prof = a.profile or ws_cfg.get('profile', 'generic')
            eff_var = a.variant or ws_cfg.get('variant', 'default')
            eff_title = a.title if a.title is not None else ws_cfg.get('title')
            eff_student = a.student if a.student is not None else (ws_cfg.get('author') or ws_cfg.get('student'))
            eff_supervisor = a.supervisor if a.supervisor is not None else ws_cfg.get('supervisor')
            cover_metadata = ws_cfg.get('cover_metadata', {})
            if not isinstance(cover_metadata, dict):
                raise ValueError('Workspace cover_metadata must be a JSON object')
            if getattr(a, 'cover_metadata', None):
                try:
                    cover_metadata = json.loads(Path(a.cover_metadata).read_text(encoding='utf-8'))
                except (OSError, json.JSONDecodeError) as exc:
                    raise ValueError(f'Could not read cover metadata JSON: {exc}') from exc
                if not isinstance(cover_metadata, dict) or any(
                    not isinstance(key, str) or not isinstance(value, (str, int, float))
                    for key, value in cover_metadata.items()
                ):
                    raise ValueError('Cover metadata JSON must be an object of string keys and scalar values')
                cover_metadata = {key: str(value) for key, value in cover_metadata.items()}
            
            prof = resolve_profile(eff_prof, start_path=Path(a.output).parent)
            res = scaffold_document(
                a.output,
                prof,
                eff_var,
                title=eff_title,
                student=eff_student,
                supervisor=eff_supervisor,
                cover_metadata=cover_metadata,
                dry_run=a.dry_run
            )
            _print({
                'status': 'SUCCESS' if not a.dry_run else 'DRY_RUN',
                'output': str(a.output) if not a.dry_run else None,
                'profile': eff_prof,
                'variant': eff_var,
                'path': str(res) if not a.dry_run else None
            }, a.json)
            return 0

        if a.cmd == 'apply':
            plan_path = Path(a.plan)
            try:
                plan_data = json.loads(plan_path.read_text(encoding='utf-8'))
            except json.JSONDecodeError as exc:
                raise ValueError(f'Invalid batch plan JSON: {exc}') from exc
            plan = BatchPlan.from_dict(plan_data)
            result = ExecutionService.default().execute_batch(
                Path(a.file),
                Path(a.output),
                plan,
                checkpoint=a.checkpoint,
            )
            _print(result.to_dict(), a.json)
            return 0

        if a.cmd == 'compose':
            content_path = Path(a.content)
            try:
                content = json.loads(content_path.read_text(encoding='utf-8'))
            except json.JSONDecodeError as exc:
                raise ValueError(f'Invalid composition JSON: {exc}') from exc
            result = compose_document(
                a.file,
                output_path=a.output,
                content=content,
                evidence_registry=a.evidence,
                profile=a.profile,
                variant_name=a.variant,
                min_visible_characters=a.min_visible_characters,
                max_visible_characters=a.max_visible_characters,
                dry_run=a.dry_run,
            )
            _print(result, a.json)
            return 0

        if a.cmd in {
            'edit', 'format', 'list', 'table', 'image', 'section',
            'page-number', 'field', 'toc', 'caption', 'reference',
            'comment', 'revision', 'protect', 'properties',
            'mail-merge'
        }:
            try:
                options = json.loads(a.options)
                if not isinstance(options, dict):
                    raise ValueError('--options must decode to a JSON object')
                selector = json.loads(a.selector) if a.selector else None
                reserved = {'input_path', 'output_path', 'selector', 'dry_run', 'checkpoint'} & set(options)
                if reserved:
                    raise ValueError(
                        '--options contains reserved keys: ' + ', '.join(sorted(reserved))
                    )
            except json.JSONDecodeError as exc:
                raise ValueError(f'Invalid JSON operation argument: {exc}') from exc

            action = a.action.replace('-', '_')
            operation = OPERATION_ALIASES.get((a.cmd, action), f'{a.cmd}.{action}')
            if a.cmd == 'edit':
                options['action'] = action
            if (a.cmd, action) in {('section', 'header_text'), ('section', 'footer_text')}:
                options.setdefault('story', 'header' if action == 'header_text' else 'footer')
            result = ExecutionService.default().execute(
                OperationRequest(
                    operation,
                    input_path=Path(a.file),
                    output_path=Path(a.output) if a.output else None,
                    selector=selector,
                    options=options,
                    dry_run=a.dry_run,
                    checkpoint=a.checkpoint,
                )
            )
            payload = result.to_dict() if hasattr(result, 'to_dict') else {
                'status': 'SUCCESS', 'operation': f'{a.cmd}.{action}', 'data': result
            }
            _print(payload, a.json)
            return 0

        if a.cmd in {'compare', 'merge'}:
            result = ExecutionService.default().execute(
                OperationRequest(
                    f'{a.cmd}.documents',
                    input_path=Path(a.file),
                    output_path=Path(a.output),
                    options={'other_path': a.other},
                )
            )
            _print(result.to_dict(), a.json)
            return 0

        if a.cmd == 'replace':
            if not a.output:
                raise ValueError('replace requires --output; in-place mutation is disabled')
            res = ExecutionService.default().execute(
                OperationRequest(
                    'text.edit',
                    input_path=Path(a.file),
                    output_path=Path(a.output),
                    options={
                        'action': 'replace',
                        'pattern': a.old,
                        'replacement': a.new,
                        'max_count': a.count,
                    },
                    dry_run=a.dry_run,
                )
            )
            _print(res.to_dict(), a.json)
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
            if a.summary and not a.report_output:
                raise ValueError("--summary requires --report-output")
            if a.visual_reviewed and not a.render and not a.reuse_render_report:
                raise ValueError("--visual-reviewed requires --render or --reuse-render-report")
            if a.visual_review_token and not a.visual_reviewed:
                raise ValueError("--visual-review-token requires --visual-reviewed")
            ws_cfg = load_project_config(Path(a.file).parent)
            eff_prof = a.profile or ws_cfg.get('profile', 'generic')
            eff_var = a.variant or ws_cfg.get('variant', 'default')
            
            prof = resolve_profile(eff_prof, start_path=Path(a.file).parent)
            inv = inspect_document(a.file)
            if a.engine == 'auto' and render_pdf is render_document:
                # Preserve the default renderer inside verify_document so it
                # can combine native field verification and PDF export.
                verify_renderer = None
            elif a.engine == 'auto':
                # Compatibility hook used by callers that inject cli.render_pdf.
                verify_renderer = render_pdf
            else:
                verify_renderer = lambda path, output_dir=None: _render_via_execution_service(
                    path, output_dir=output_dir, engine=a.engine
                )
            summary = verify_document(
                a.file, profile=prof, variant_name=eff_var, render=a.render,
                renderer=verify_renderer, native_fields=a.native_fields,
                visual_reviewed=a.visual_reviewed,
                visual_review_token=a.visual_review_token,
                reuse_render_report=a.reuse_render_report,
            )
            summary.update({
                'file': str(a.file),
                'profile': prof.profile_id,
                'variant': eff_var,
                'validation_status': summary['format_status'],
                'valid': summary['overall_status'] == 'PASS',
                'delivery_valid': summary['delivery_status'] == 'PASS',
                'inventory': {
                    'paragraphs': inv['paragraphs'], 'tables': inv['tables'],
                    'sections': inv['sections'], 'images': inv['images'],
                    'fields': inv['fields']
                },
            })
            if not a.render and summary['render_status'] == 'NOT_REQUESTED':
                summary['render_status'] = 'SKIPPED'
            if a.report_output:
                _assert_report_output_is_distinct(
                    a.report_output, a.file, summary, a.reuse_render_report
                )
                report_path = _write_json_atomic(a.report_output, summary)
                report_bytes = report_path.read_bytes()
                if a.summary:
                    compact = {
                        key: summary.get(key) for key in (
                            'overall_status', 'delivery_status', 'delivery_gates',
                            'structural_status', 'format_status', 'numbering_status',
                            'table_geometry_status', 'field_structure_status',
                            'field_freshness_status', 'field_evaluation_status',
                            'render_status', 'native_word_status', 'visual_status',
                            'manual_review_required', 'issues', 'inventory', 'render',
                            'visual_review_challenge', 'visual_review_reuse',
                            'render_reuse_manifest',
                        ) if key in summary
                    }
                    compact.pop('render_reuse_manifest', None)
                    if 'render' in compact and isinstance(compact['render'], dict):
                        compact['render'] = {k: v for k, v in compact['render'].items() if k != 'page_images' and k != 'page_content_audit'}
                    if 'visual_review_challenge' in compact:
                        challenge = compact['visual_review_challenge']
                        compact['visual_review_challenge'] = {
                            key: challenge.get(key)
                            for key in ('token', 'page_count', 'token_scope')
                            if key in challenge
                        }
                    compact.update({'report_path': str(report_path), 'report_sha256': hashlib.sha256(report_bytes).hexdigest()})
                    _print(compact, True)
                else:
                    _print(summary, a.json)
            else:
                _print(summary, a.json)
            final_status = (
                summary['delivery_status'] if a.delivery else summary['overall_status']
            )
            return 0 if final_status == 'PASS' else 2

        if a.cmd == 'render':
            if render_pdf is not render_document and a.engine == 'auto':
                res = render_pdf(a.file, output_dir=a.outdir, timeout_seconds=a.timeout)
            else:
                res = _render_via_execution_service(
                    a.file,
                    output_dir=a.outdir,
                    engine=a.engine,
                    timeout_seconds=a.timeout,
                )
            _print({
                'pdf': str(res.pdf_path),
                'engine': res.engine,
                'page_count': res.page_count,
                'size_bytes': res.file_size_bytes,
                'duration_seconds': res.duration_seconds
            }, a.json)
            return 0

        if a.cmd == 'integrity':
            ws_cfg = load_project_config(Path(a.file).parent)
            eff_prof = a.profile or ws_cfg.get('profile', 'generic')
            eff_var = a.variant or ws_cfg.get('variant', 'default')
            prof = resolve_profile(eff_prof, start_path=Path(a.file).parent)
            # Resolve the requested variant before auditing so an unknown variant
            # fails closed instead of silently applying another policy.
            prof.variant(eff_var)
            evidence_path = Path(a.evidence).expanduser().resolve() if a.evidence else None

            if a.integrity_action == 'audit':
                report = audit_integrity(
                    a.file,
                    evidence_registry_path=evidence_path,
                    profile=prof,
                    variant_name=eff_var,
                )
                _print(report, a.json)
                if report['status'] == 'FAIL':
                    return 2
                if a.fail_on_warn and report['status'] == 'WARN':
                    return 2
                return 0

            audit_report = None
            if a.audit_report:
                audit_report = json.loads(Path(a.audit_report).read_text(encoding='utf-8'))
                if not isinstance(audit_report, dict):
                    raise ValueError('--audit-report must contain a JSON object')
            manifest = build_provenance_manifest(
                a.file,
                evidence_registry_path=evidence_path,
                profile=prof,
                disclosure=a.disclosure,
                audit_report=audit_report,
                variant_name=eff_var,
            )
            output = _write_json_atomic(a.output, manifest)
            _print(
                {
                    'status': 'SUCCESS',
                    'output': str(output),
                    'document_sha256': manifest['document']['sha256'],
                    'evidence_sha256': (
                        manifest.get('source_registry', {})
                        .get('evidence', {})
                        .get('sha256')
                        if isinstance(manifest.get('source_registry', {}).get('evidence'), dict)
                        else None
                    ),
                    'audit_status': manifest['audit_summary']['status'],
                },
                a.json,
            )
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
                    'verified_by': a.verified_by,
                    'synthetic': bool(a.synthetic),
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

        if a.cmd == 'research':
            if a.research_action == 'search':
                candidates = search_crossref(a.query, limit=a.limit)
                _print({
                    'status': 'CANDIDATES',
                    'provider': 'Crossref',
                    'total': len(candidates),
                    'records': candidates,
                    'note': 'Metadata search results are discovery leads, not verified claim support.',
                }, a.json)
                return 0
            reg_path = _resolve_evidence_registry(getattr(a, 'registry', None))
            if a.research_action == 'import-doi':
                record = import_crossref_doi(a.doi, evidence_registry=reg_path)
                _print({
                    'status': 'CANDIDATE_IMPORTED',
                    'id': record['id'],
                    'doi': record['doi'],
                    'review_status': record['review_status'],
                    'registry': str(reg_path),
                }, a.json)
                return 0
            if a.research_action == 'open-access':
                email = os.environ.get(a.email_env, '')
                access = find_open_access(
                    a.id,
                    evidence_registry=reg_path,
                    email=email,
                )
                _print({'status': 'OA_LOCATION_FOUND', **access}, a.json)
                return 0
            if a.research_action == 'download':
                downloaded = download_open_access_pdf(
                    a.id,
                    evidence_registry=reg_path,
                )
                _print({'status': 'DOWNLOADED_CANDIDATE', **downloaded}, a.json)
                return 0
            if a.research_action == 'excerpt':
                excerpts = search_source_excerpts(
                    a.id,
                    evidence_registry=reg_path,
                    query=a.query,
                    limit=a.limit,
                    context_chars=a.context_chars,
                )
                _print(excerpts, a.json)
                return 0
            if a.research_action == 'review':
                reviewed = review_downloaded_source(
                    a.id,
                    evidence_registry=reg_path,
                    claim=a.claim,
                    support_excerpt=a.support_excerpt,
                    support_location=a.support_location,
                    reviewed_by=a.reviewed_by,
                    confirm_support=a.confirm_support,
                    quote=a.quote,
                    language=a.language,
                )
                _print({'status': 'REVIEWED', **reviewed}, a.json)
                return 0

    except BatchExecutionError as exc:
        _print(
            {
                'status': 'ERROR',
                'operation': 'batch.apply',
                'error': exc.to_dict(),
            },
            getattr(a, 'json', False),
        )
        return 1
    except OperationUnavailable as exc:
        _print(
            {
                'status': 'ERROR',
                'error': exc.error.to_dict(),
            },
            getattr(a, 'json', False),
        )
        return 1
    except Exception as exc:
        _print(
            {
                'status': 'ERROR',
                'error': {
                    'code': 'OPERATION_FAILED',
                    'message': str(exc),
                    'backend_required': None,
                    'suggested_action': 'Check command options and run wordassistant capabilities --json.',
                },
            },
            getattr(a, 'json', False),
        )
        return 1

    return 0

def main() -> None:
    sys.exit(run())

if __name__ == '__main__':
    main()
