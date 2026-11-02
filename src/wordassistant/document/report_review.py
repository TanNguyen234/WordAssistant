"""Hash-bound editorial and model-coverage records, separate from Word layout QA.

This verifies review evidence and declared coverage, not the quality of prose or
the meaning of an image. A reviewer must examine the actual content first.
"""
from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from docx import Document

SOFTWARE_DECISIONS = {'use_case', 'data', 'class', 'activity', 'sequence', 'state', 'component', 'deployment'}


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assess_content_review(directory: Path, project: dict) -> dict:
    checks = []

    def add(name, status, detail):
        checks.append({'check': name, 'status': status, 'detail': detail})

    def resolve(value):
        path = Path(str(value))
        return path if path.is_absolute() else directory / path

    def reviewed(item):
        try:
            valid_date = date.fromisoformat(str(item.get('review_date', '')))
        except ValueError:
            return False
        return bool(item.get('reviewer') and valid_date and item.get('status') == 'REVIEWED')

    plan_name = project.get('content_review_plan_file')
    if not plan_name:
        return {'status': 'INCOMPLETE', 'checks': [{'check': 'content_review_plan', 'status': 'INCOMPLETE',
                'detail': 'Record a subject-specific content review plan before claiming content completeness.'}]}
    try:
        plan = json.loads(resolve(plan_name).read_text(encoding='utf-8-sig'))
        if not isinstance(plan, dict):
            raise ValueError('Content review plan must be an object.')
        output = resolve(project['output_docx'])
        current_hash = _hash(output)
        doc = Document(output)
    except (OSError, KeyError, ValueError) as exc:
        return {'status': 'INCOMPLETE', 'checks': [{'check': 'content_review_plan', 'status': 'INCOMPLETE', 'detail': str(exc)}]}
    if plan.get('schema_version') != 1:
        add('content_review_schema', 'FAIL', 'Unsupported content review schema.')
    if plan.get('document_sha256') != current_hash:
        add('content_review_hash', 'FAIL', 'Content review is stale for the current DOCX.')
    else:
        add('content_review_hash', 'PASS', 'Review binds the current DOCX SHA-256.')
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith('Heading ')]
    previous_level = 0
    for p in doc.paragraphs:
        if p.style.name in {'Heading 1', 'Heading 2', 'Heading 3'}:
            level = int(p.style.name[-1])
            if level > previous_level + 1:
                add('heading_hierarchy', 'FAIL', f'Heading level jumps before {p.text!r}.')
            previous_level = level
    captions = [p.text for p in doc.paragraphs if p.style.name == 'Caption']
    with ZipFile(output) as package:
        media_hashes = {hashlib.sha256(package.read(n)).hexdigest() for n in package.namelist() if n.startswith('word/media/')}
    decisions = plan.get('model_decisions', [])
    if not isinstance(decisions, list) or any(not isinstance(x, dict) for x in decisions):
        return {'status': 'FAIL', 'checks': [{'check': 'model_decisions', 'status': 'FAIL',
                'detail': 'Model decisions must be an array of objects.'}]}
    dims = [x.get('dimension') for x in decisions]
    if len(dims) != len(set(dims)):
        add('model_dimensions', 'FAIL', 'Model dimensions must be unique.')
    if plan.get('domain') == 'software':
        missing = SOFTWARE_DECISIONS - set(dims)
        add('software_model_scope', 'INCOMPLETE' if missing else 'PASS',
            f'Each basic model must be required or explicitly inapplicable; missing={sorted(missing)}.')
    elif not plan.get('model_scope_reason'):
        add('model_scope', 'INCOMPLETE', 'Explain the subject-specific model scope; UML is not universal.')
    for item in decisions:
        name = 'model_' + str(item.get('dimension'))
        if not reviewed(item) or not item.get('reason') or not item.get('authority'):
            add(name, 'INCOMPLETE', 'Model scope needs a reviewed rationale and controlling authority.')
            continue
        if item.get('disposition') == 'NOT_APPLICABLE':
            add(name, 'PASS', 'Explicitly reviewed as inapplicable: ' + item['reason'])
            continue
        if item.get('disposition') != 'REQUIRED' or not item.get('assets'):
            add(name, 'INCOMPLETE', 'Required model has no verified assets.')
            continue
        for asset in item['assets']:
            errors = []
            for file_key, hash_key in [('editable_file', 'editable_sha256'), ('rendered_file', 'rendered_sha256')]:
                path = resolve(asset.get(file_key, ''))
                if not path.is_file() or _hash(path) != asset.get(hash_key):
                    errors.append(f'{file_key} is missing or stale')
            if asset.get('rendered_sha256') not in media_hashes:
                errors.append('rendered image is not embedded in this DOCX')
            title = str(asset.get('caption_title', '')).strip()
            if not title or not any(text.endswith(title) for text in captions):
                errors.append('caption not found')
            if not asset.get('sources'):
                errors.append('no implementation/requirement source evidence')
            for source in asset.get('sources', []):
                path = resolve(source.get('file', ''))
                if not path.is_file() or _hash(path) != source.get('sha256'):
                    errors.append('source evidence is missing or stale')
            if not asset.get('semantic_review') or not asset.get('notation_review'):
                errors.append('record model meaning and notation review')
            add(name, 'FAIL' if errors else 'PASS', '; '.join(errors) or asset['caption_title'])
    reviews = plan.get('section_reviews', [])
    if not reviews:
        add('section_reviews', 'INCOMPLETE', 'No argument/prose reviews are recorded.')
    for item in reviews:
        errors = []
        if headings.count(item.get('heading')) != 1:
            errors.append('section heading is missing or ambiguous')
        if not reviewed(item):
            errors.append('reviewer/date/status missing')
        for key in ('argument', 'evidence', 'terminology', 'sufficiency'):
            if not str(item.get(key, '')).strip():
                errors.append(key + ' review missing')
        add('section_' + str(item.get('heading')), 'INCOMPLETE' if errors else 'PASS',
            '; '.join(errors) or 'Argument, evidence, terminology and sufficiency were explicitly reviewed.')
    status = 'FAIL' if any(x['status'] == 'FAIL' for x in checks) else (
        'INCOMPLETE' if any(x['status'] == 'INCOMPLETE' for x in checks) else 'PASS')
    return {'status': status, 'document_sha256': current_hash, 'checks': checks,
            'limits': 'Checks verify recorded review and provenance; they do not infer prose quality or image meaning.'}
