"""Apply a reviewed, hash-bound section revision without rebuilding a DOCX.

Content is supplied in JSON; this helper contains no subject or institution facts.
Native fields, captions, images and final QA remain WordAssistant CLI operations.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm

from wordassistant.document.edit import _detect_complex_elements
from wordassistant.operations.common import atomic_save
from wordassistant.operations.text import _replace_spans


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def unique_heading(doc, text):
    matches = [p for p in doc.paragraphs if p.style.name.startswith('Heading ') and p.text == text]
    if len(matches) != 1:
        raise ValueError(f'Heading must be unique: {text!r}; found {len(matches)}')
    return matches[0]


def section_paragraphs(doc, heading):
    found = False
    result = []
    for p in doc.paragraphs:
        if p._p is heading._p:
            found = True
        elif found:
            if p.style.name.startswith('Heading '):
                break
            result.append(p)
    return result


def replace_plain(p, new_text):
    old = p.text
    if _detect_complex_elements(p._p):
        raise ValueError('Replacement contains a field, drawing or other complex Word content')
    if re.findall(r'\[\d+\]', old) != re.findall(r'\[\d+\]', new_text):
        raise ValueError('Revision must preserve citation markers and their order')
    if old:
        _replace_spans(p, [(0, len(old), new_text)])
    else:
        p.add_run(new_text)


def editable_run_indices(paragraph):
    """Exclude field instructions/results as well as complex inline structures."""
    result, depth = set(), 0
    for index, run in enumerate(paragraph.runs):
        chars = run._r.xpath('.//w:fldChar')
        for char in chars:
            kind = char.get(qn('w:fldCharType'))
            if kind == 'begin':
                depth += 1
            elif kind == 'end':
                depth = max(0, depth - 1)
        if not depth and not chars and not _detect_complex_elements(run._r):
            result.add(index)
    return result


def set_heading_level(doc, p, level):
    if level not in (1, 2, 3):
        raise ValueError('Heading level must be 1, 2 or 3')
    p.style = doc.styles[f'Heading {level}']
    props = p._p.get_or_add_pPr()
    numbering = props.find(qn('w:numPr'))
    if numbering is not None:
        ilvl = numbering.find(qn('w:ilvl'))
        if ilvl is not None:
            ilvl.set(qn('w:val'), str(level - 1))
    outline = props.find(qn('w:outlineLvl'))
    if outline is not None:
        outline.set(qn('w:val'), str(level - 1))


def prepare(input_path: Path, spec: dict) -> dict:
    """Resolve an authored editorial specification into exact, reviewable edits."""
    if spec.get('input_sha256') != sha256(input_path):
        raise ValueError('Editorial specification has a stale input hash')
    doc = Document(input_path)
    start = unique_heading(doc, spec['scope_start'])
    end = unique_heading(doc, spec['scope_end'])
    protected = re.compile(r'https?://\S+|(?:\b(?:app|docs|scripts|assets|tests|qa)[/\\]|(?<!\w)[/\\])[\w./\\{}-]+|\b[\w.-]+\.(?:py|json|html|csv|md|docx)\b|`[^`]+`|\bno-(?:store|cache|evidence|candidate)\b')
    glossary = sorted(spec.get('glossary', []), key=lambda x: len(x['find']), reverse=True)
    lookup = {item['find']: item['replace'] for item in glossary}
    expression = r'(?<![\w])(?:' + '|'.join(re.escape(k) for k in lookup) + r')(?![\w])' if lookup else None

    def translate(text):
        parts, position = [], 0
        for match in protected.finditer(text):
            part = text[position:match.start()]
            parts.append(re.sub(expression, lambda m: lookup[m.group()], part) if expression else part)
            parts.append(match.group())
            position = match.end()
        part = text[position:]
        parts.append(re.sub(expression, lambda m: lookup[m.group()], part) if expression else part)
        return ''.join(parts)

    rewrites = {(x['section'], x['paragraph_index']): x['text'] for x in spec.get('rewrites', [])}
    edits, run_edits, skipped, seen = [], [], [], set()
    active, section, index = False, None, 0
    for p in doc.paragraphs:
        if p._p is end._p:
            break
        if p._p is start._p:
            active = True
        if p.style.name.startswith('Heading '):
            section, index = p.text, 0
            continue
        if not active:
            continue
        key = (section, index)
        index += 1
        if p.style.name == 'Caption':
            continue
        if _detect_complex_elements(p._p):
            if key in rewrites:
                raise ValueError('Authored rewrite targets complex content')
            if p.text:
                skipped.append({'section': section, 'paragraph_index': key[1]})
            allowed_runs = editable_run_indices(p)
            for run_index, run in enumerate(p.runs):
                if run_index not in allowed_runs:
                    continue
                new = translate(run.text)
                if new != run.text:
                    run_edits.append({'section': section, 'paragraph_index': key[1],
                        'expected_text_sha256': text_hash(p.text), 'run_index': run_index,
                        'expected_run_sha256': text_hash(run.text), 'text': new})
            continue
        if key in rewrites:
            new = rewrites[key]
            seen.add(key)
        else:
            new = translate(p.text)
        if new != p.text:
            edits.append({'section': section, 'paragraph_index': key[1],
                          'expected_text_sha256': text_hash(p.text), 'text': new})
    if set(rewrites) != seen:
        raise ValueError(f'Unresolved authored rewrites: {set(rewrites) - seen}')
    return {'schema_version': 1, 'input_sha256': sha256(input_path),
            'first_line_indent_cm': spec.get('first_line_indent_cm', 0), 'edits': edits, 'run_edits': run_edits,
            'insertions': spec.get('insertions', []), 'headings': spec.get('headings', []),
            'caption_titles': spec.get('caption_titles', []),
            'require_complete_hierarchy': spec.get('require_complete_hierarchy', True),
            'skipped_complex_paragraphs': skipped}


def revise(input_path: Path, output_path: Path, plan: dict, *, dry_run=False):
    input_path, output_path = input_path.resolve(), output_path.resolve()
    if input_path == output_path or output_path.exists():
        raise ValueError('Use a distinct, non-existing output path')
    if plan.get('schema_version') != 1 or plan.get('input_sha256') != sha256(input_path):
        raise ValueError('Revision plan has an unsupported schema or stale input hash')
    doc = Document(input_path)
    edits = []
    heading_map, paragraph_map = {}, {}
    active = None
    for p in doc.paragraphs:
        if p.style.name.startswith('Heading '):
            heading_map.setdefault(p.text, []).append(p)
            active = p.text
            paragraph_map.setdefault(active, [])
        elif active is not None:
            paragraph_map[active].append(p)

    def heading(text):
        matches = heading_map.get(text, [])
        if len(matches) != 1:
            raise ValueError(f'Heading must be unique: {text!r}; found {len(matches)}')
        return matches[0]

    # Resolve/verify against the original section map before any hierarchy changes.
    for item in plan.get('edits', []):
        heading(item['section'])
        paragraphs = paragraph_map[item['section']]
        index = item['paragraph_index']
        if index < 0 or index >= len(paragraphs):
            raise ValueError('Section paragraph index is out of range')
        p = paragraphs[index]
        if text_hash(p.text) != item['expected_text_sha256']:
            raise ValueError('Stale paragraph text in revision plan')
        edits.append((p, item['text']))
    for p, text in edits:
        replace_plain(p, text)
    resolved_runs = []
    for item in plan.get('run_edits', []):
        heading(item['section'])
        p = paragraph_map[item['section']][item['paragraph_index']]
        if text_hash(p.text) != item['expected_text_sha256']:
            raise ValueError('Stale field-bearing paragraph')
        run = p.runs[item['run_index']]
        if (item['run_index'] not in editable_run_indices(p)
                or text_hash(run.text) != item['expected_run_sha256']):
            raise ValueError('Stale or complex inline run')
        if re.findall(r'\[\d+\]', run.text) != re.findall(r'\[\d+\]', item['text']):
            raise ValueError('Inline revision must preserve citation markers')
        resolved_runs.append((run, item['text']))
    for run, text in resolved_runs:
        run.text = text
    for item in plan.get('insertions', []):
        anchor_heading = heading(item['before_heading'])
        for block in item['blocks']:
            kind, text = block['kind'], block['text']
            if kind == 'heading':
                level = block['level']
                p = anchor_heading.insert_paragraph_before(text, style=f'Heading {level}')
                template = heading(block['numbering_from'])
                num = template._p.get_or_add_pPr().find(qn('w:numPr'))
                if num is not None:
                    p._p.get_or_add_pPr().append(deepcopy(num))
                set_heading_level(doc, p, level)
                p.paragraph_format.keep_with_next = True
            elif kind == 'paragraph':
                p = anchor_heading.insert_paragraph_before(text, style='Normal')
                p.paragraph_format.first_line_indent = Cm(plan.get('first_line_indent_cm', 0))
                p.paragraph_format.keep_with_next = False
            else:
                raise ValueError(f'Unsupported block kind: {kind}')
    for item in plan.get('headings', []):
        p = heading(item['text'])
        if item.get('remove_heading_only'):
            if p._p.find('.//' + qn('w:sectPr')) is not None:
                raise ValueError('Cannot remove a section boundary')
            p._p.getparent().remove(p._p)
            continue
        if 'new_text' in item:
            replace_plain(p, item['new_text'])
        if 'level' in item:
            set_heading_level(doc, p, item['level'])
    for item in plan.get('caption_titles', []):
        matches = [p for p in doc.paragraphs if p.style.name == 'Caption' and p.text.endswith(item['old'])]
        if len(matches) != 1:
            raise ValueError('Caption title must match exactly one caption')
        p = matches[0]
        start = len(p.text) - len(item['old'])
        offset = 0
        for run in p.runs:
            if offset + len(run.text) > start and (run._r.xpath('.//w:fldChar') or run._r.xpath('.//w:instrText')):
                raise ValueError('Caption title overlaps a field')
            offset += len(run.text)
        _replace_spans(p, [(start, len(p.text), item['new'])])
    if plan.get('require_complete_hierarchy', True):
        previous = 0
        for p in doc.paragraphs:
            match = re.fullmatch(r'Heading ([1-9])', p.style.name)
            if match:
                level = int(match.group(1))
                if level > previous + 1:
                    raise ValueError(f'Heading hierarchy skips a level before {p.text!r}')
                previous = level
    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_save(doc, output_path)
    return {'status': 'DRY_RUN' if dry_run else 'SUCCESS', 'input_sha256': sha256(input_path),
            'output': str(output_path), 'output_sha256': None if dry_run else sha256(output_path),
            'edits': len(edits), 'insertions': len(plan.get('insertions', [])),
            'heading_changes': len(plan.get('headings', []))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--prepare', action='store_true', help='Resolve editorial specification to a hash-bound plan JSON')
    args = parser.parse_args()
    spec = json.loads(args.plan.read_text(encoding='utf-8-sig'))
    if args.prepare:
        if args.output.exists():
            raise FileExistsError(args.output)
        result = prepare(args.input, spec)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        result = {'status': 'PREPARED', 'edits': len(result['edits']), 'output': str(args.output)}
    else:
        result = revise(args.input, args.output, spec, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
