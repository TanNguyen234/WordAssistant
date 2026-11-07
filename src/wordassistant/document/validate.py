from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from wordassistant.document.code_blocks import is_code_paragraph
from wordassistant.profiles.loader import DocumentProfile, Variant

@dataclass(frozen=True)
class Issue:
    severity: str  # 'error', 'warning', 'info'
    code: str
    message: str

@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    issues: tuple[Issue, ...]

GENERIC_DRAFT_PLACEHOLDERS = (
    "[front matter content]",
    "[section content...]",
    "[list of figures]",
    "[list of tables]",
    "[document content]",
    "untitled document",
)

_BRACKETED_TEXT = re.compile(r"\[([^\[\]\r\n]{2,120})\]")
_PLACEHOLDER_HINT = re.compile(
    r"\b(?:todo|tbd|tbc|tba|placeholder|insert|replace|fill(?:\s+in)?|"
    r"to\s+be\s+(?:completed|filled|confirmed)|your\s+(?:name|title|date)|"
    r"name|student\s+(?:name|id)|advisor|supervisor|signature|date|"
    r"điền|tự\s*điền|bổ\s*sung|mô\s*tả|họ\s*tên|tên\s*(?:sinh\s*viên|giảng\s*viên|người)|"
    r"ngày(?:\s*tháng)?|chữ\s*ký|người\s*/?\s*đơn\s*vị|nội\s*dung\s*hỗ\s*trợ)\b",
    re.IGNORECASE,
)
_TEMPLATE_TOKEN = re.compile(
    r"^(?:TODO|TBD|TBC|TBA|PLACEHOLDER|"
    r"(?=[A-Z0-9_ -]*(?:STUDENT|AUTHOR|SUPERVISOR|ADVISOR|SIGNATURE|DATE|TITLE|TOPIC|NAME|CLASS|MSSV|GVHD))"
    r"[A-Z0-9]+(?:[_ -][A-Z0-9]+)+)$",
    re.IGNORECASE,
)
_CHAPTER_HEADING = re.compile(r"^\s*(?:chapter|chương)\s+(\d+)\b", re.IGNORECASE)
_NUMBER_MARKER = re.compile(r"%([1-9])")

def _normalize_text(s: str) -> str:
    if not s:
        return ""
    norm = unicodedata.normalize('NFC', s)
    return " ".join(norm.split()).casefold()

def _find_draft_placeholders(d: Document, v: Variant) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    check_set = {_normalize_text(value) for value in GENERIC_DRAFT_PLACEHOLDERS}
    
    # Add defaults from profile metadata fields if they have draft brackets or angle brackets
    if 'metadata_fields' in v.cover:
        for mf in v.cover['metadata_fields']:
            d_val = mf.get('default')
            if d_val and (d_val.startswith('[') or d_val.startswith('<')):
                check_set.add(_normalize_text(d_val))
                
    def contains_placeholder(text: str) -> bool:
        normalized = _normalize_text(text)
        if any(placeholder in normalized for placeholder in check_set):
            return True
        for match in _BRACKETED_TEXT.finditer(text):
            candidate = match.group(1).strip()
            if _PLACEHOLDER_HINT.search(candidate) or _TEMPLATE_TOKEN.fullmatch(candidate):
                return True
        return False

    def table_texts(tables):
        for table in tables:
            for row in table.rows:
                for cell in row.cells:
                    yield cell.text
                    yield from table_texts(cell.tables)

    # Review body paragraphs and nested table cells without treating ordinary
    # bracket citations such as [1] as draft placeholders.
    # Verbatim code listings may contain bracket subscripts or Jinja markers; skip them.
    prose_texts = [p.text for p in d.paragraphs if not is_code_paragraph(p)]
    for text in prose_texts + list(table_texts(d.tables)):
        candidate = text.strip()
        if candidate and contains_placeholder(candidate):
            excerpt = candidate[:80]
            if excerpt not in seen:
                seen.add(excerpt)
                found.append(excerpt)
    return found

def _extract_cover_metadata(d: Document, v: Variant) -> dict[str, str]:
    meta: dict[str, str] = {}
    cover_lines: list[str] = []
    
    front_titles = [t.casefold() for t in v.front_matter_titles.values() if len(t) > 3]
    blueprint_titles = [sec['title'].casefold() for sec in v.section_blueprint[:2]]
    
    for p in d.paragraphs[:50]:
        txt = p.text.strip()
        if not txt:
            continue
        txt_lower = txt.lower()
        if any(ft in txt_lower for ft in front_titles):
            break
        if any(bt in txt_lower for bt in blueprint_titles):
            break
        for line in txt.split('\n'):
            clean_line = line.strip()
            if clean_line:
                cover_lines.append(clean_line)
                
    # Match metadata fields from profile cover declarations
    for line in cover_lines:
        line_norm = _normalize_text(line)
        for mf in v.cover.get('metadata_fields', []):
            label = mf.get('label', '').strip()
            key = mf.get('value_key', '')
            if label and key:
                label_norm = _normalize_text(label)
                if label_norm in line_norm:
                    idx = line.lower().find(label.lower())
                    if idx != -1:
                        val = line[idx + len(label):].strip().lstrip(':').strip()
                        if val and not (val.startswith('[') and val.endswith(']')) and not (val.startswith('<') and val.endswith('>')):
                            meta[key] = val
                            
    # Extract topic from document_type
    doc_type = v.cover.get('document_type', '').strip()
    if doc_type:
        doc_type_norm = _normalize_text(doc_type)
        dt_idx = None
        for i, line in enumerate(cover_lines):
            if doc_type_norm in _normalize_text(line):
                dt_idx = i
                break
        if dt_idx is not None:
            title_lines = []
            for next_line in cover_lines[dt_idx + 1:]:
                nl_norm = _normalize_text(next_line)
                if any(_normalize_text(mf.get('label', '')) in nl_norm for mf in v.cover.get('metadata_fields', []) if mf.get('label')):
                    break
                if v.cover.get('location_year') and _normalize_text(v.cover['location_year']) in nl_norm:
                    break
                if any(_normalize_text(inst) in nl_norm for inst in v.cover.get('institution_lines', [])):
                    break
                title_lines.append(next_line)
            if title_lines:
                topic_str = " ".join(title_lines).strip()
                t_prefix = v.cover.get('title_prefix', '').strip()
                if t_prefix and topic_str.lower().startswith(t_prefix.lower()):
                    topic_str = topic_str[len(t_prefix):].strip().lstrip(':').strip()
                meta['topic'] = topic_str
                
    return meta

def _resolve_run_font(run, p, doc_default_font: str | None) -> tuple[str | None, bool]:
    if hasattr(run, 'font') and run.font and run.font.name:
        return run.font.name, True
    if p.style and hasattr(p.style, 'font') and p.style.font and p.style.font.name:
        return p.style.font.name, True
    if doc_default_font:
        return doc_default_font, True
    return None, False

def _resolve_run_size(run, p, doc_default_size: float | None) -> tuple[float | None, bool]:
    if hasattr(run, 'font') and run.font and run.font.size:
        return run.font.size.pt, True
    if p.style and hasattr(p.style, 'font') and p.style.font and p.style.font.size:
        return p.style.font.size.pt, True
    if doc_default_size:
        return doc_default_size, True
    return None, False

def _resolve_line_spacing(p, doc_default_ls: float | None) -> tuple[float | None, bool]:
    if p.paragraph_format.line_spacing is not None:
        ls = p.paragraph_format.line_spacing
        if isinstance(ls, (int, float)):
            return float(ls), True
    if p.style and hasattr(p.style, 'paragraph_format') and p.style.paragraph_format.line_spacing is not None:
        ls = p.style.paragraph_format.line_spacing
        if isinstance(ls, (int, float)):
            return float(ls), True
    if doc_default_ls:
        return doc_default_ls, True
    return None, False


def _profile_style_name(style_key: str) -> str:
    key = style_key.strip()
    heading_match = re.fullmatch(r"heading\s*([1-9])", key, re.IGNORECASE)
    if heading_match:
        return f"Heading {heading_match.group(1)}"
    if key.casefold() == "title":
        return "Title"
    return key


def _effective_style_size(style) -> float | None:
    # Word may remove a redundant size and inherit it through basedOn on save.
    seen = set()
    while style is not None and style.style_id not in seen:
        seen.add(style.style_id)
        if style.font.size is not None:
            return style.font.size.pt
        style = style.base_style
    return None


def _effective_style_alignment(style, document):
    seen = set()
    while style is not None and style.style_id not in seen:
        seen.add(style.style_id)
        if style.paragraph_format.alignment is not None:
            return style.paragraph_format.alignment
        style = style.base_style
    defaults = document.styles.element.xpath('./w:docDefaults/w:pPrDefault/w:pPr/w:jc')
    if defaults:
        return {'left': WD_ALIGN_PARAGRAPH.LEFT, 'center': WD_ALIGN_PARAGRAPH.CENTER,
                'right': WD_ALIGN_PARAGRAPH.RIGHT, 'both': WD_ALIGN_PARAGRAPH.JUSTIFY}.get(
                    defaults[0].get(qn('w:val')))
    return WD_ALIGN_PARAGRAPH.LEFT


def _starts_new_page(document: Document, paragraph_index: int) -> bool:
    paragraph = document.paragraphs[paragraph_index]
    if paragraph.paragraph_format.page_break_before is True:
        return True

    previous = document.paragraphs[paragraph_index - 1] if paragraph_index > 0 else None
    for candidate in (previous, paragraph):
        if candidate is None:
            continue
        if any(
            node.get(qn("w:type")) == "page"
            for node in candidate._p.iter(qn("w:br"))
        ):
            return True
        p_pr = candidate._p.pPr
        section_properties = p_pr.sectPr if p_pr is not None else None
        if section_properties is not None:
            section_type = section_properties.type
            if section_type is None or section_type.val in {"nextPage", "oddPage", "evenPage"}:
                return True
    return False


def _paragraph_numbering(paragraph) -> tuple[int, int] | None:
    properties = paragraph._p.pPr
    numbering = properties.numPr if properties is not None else None
    if numbering is None and paragraph.style is not None:
        style_properties = paragraph.style._element.pPr
        numbering = style_properties.numPr if style_properties is not None else None
    if numbering is None or numbering.numId is None:
        return None
    try:
        number_id = int(numbering.numId.val)
        level = int(numbering.ilvl.val) if numbering.ilvl is not None else 0
    except (TypeError, ValueError):
        return None
    return number_id, level


def _heading_level(paragraph) -> int | None:
    if paragraph.style is None:
        return None
    match = re.fullmatch(r"Heading\s+(\d+)", paragraph.style.name, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def _automatic_heading_number_markers(document: Document, paragraph) -> set[int]:
    number_info = _paragraph_numbering(paragraph)
    if number_info is None:
        return set()
    number_id, level_index = number_info
    numbering = document.part.numbering_part.element
    num = next(
        (item for item in numbering.findall(qn("w:num")) if item.get(qn("w:numId")) == str(number_id)),
        None,
    )
    abstract_id = None
    if num is not None:
        reference = num.find(qn("w:abstractNumId"))
        if reference is not None:
            abstract_id = reference.get(qn("w:val"))
    abstract = next(
        (
            item
            for item in numbering.findall(qn("w:abstractNum"))
            if item.get(qn("w:abstractNumId")) == abstract_id
        ),
        None,
    )
    level = None
    if num is not None:
        override = next(
            (
                item
                for item in num.findall(qn("w:lvlOverride"))
                if item.get(qn("w:ilvl")) == str(level_index)
            ),
            None,
        )
        if override is not None:
            level = override.find(qn("w:lvl"))
    if level is None and abstract is not None:
        level = next(
            (
                item
                for item in abstract.findall(qn("w:lvl"))
                if item.get(qn("w:ilvl")) == str(level_index)
            ),
            None,
        )
    if level is None:
        return set()
    number_format = level.find(qn("w:numFmt"))
    level_text = level.find(qn("w:lvlText"))
    if (
        number_format is None
        or number_format.get(qn("w:val")) not in {"decimal", "decimalZero"}
        or level_text is None
        or not (level_text.get(qn("w:val")) or "").strip()
    ):
        return set()
    return {int(marker) for marker in _NUMBER_MARKER.findall(level_text.get(qn("w:val")) or "")}


def _chapter_heading_numbering_findings(document: Document) -> list[str]:
    findings: list[str] = []
    paragraphs = document.paragraphs
    for index, chapter in enumerate(paragraphs):
        if _heading_level(chapter) != 1:
            continue
        chapter_match = _CHAPTER_HEADING.match(chapter.text.strip())
        if chapter_match is None:
            continue
        chapter_number = chapter_match.group(1)
        missing: list[str] = []
        for heading in paragraphs[index + 1 :]:
            heading_level = _heading_level(heading)
            if heading_level == 1:
                break
            if heading_level not in {2, 3}:
                continue
            visible_prefix = re.compile(
                rf"^\s*{re.escape(chapter_number)}(?:\.\d+){{{heading_level - 1}}}[.)]?\s+"
            )
            automatic_markers = _automatic_heading_number_markers(document, heading)
            if not visible_prefix.match(heading.text) and not set(range(1, heading_level + 1)).issubset(automatic_markers):
                missing.append(f"Heading {heading_level}: {heading.text.strip()[:70]}")
        if missing:
            findings.append(
                f"Chapter {chapter_number} has unnumbered child heading(s): {', '.join(missing[:5])}"
            )
    return findings


def _check_cover_logo(
    d: Document,
    v: Variant,
    issues: list[Issue],
    verify_mode: bool,
    is_template_clone: bool = False
) -> None:
    cover_data = v.cover if isinstance(v.cover, dict) else {}
    logo_asset = cover_data.get('logo_asset')
    
    # Check if document has cover headers
    has_cover_text = any(
        any(k in p.text.casefold() for k in ('tài nguyên và môi trường', 'khoa công nghệ thông tin'))
        for p in d.paragraphs[:30]
    )
    if not logo_asset and not has_cover_text:
        return
        
    expected_w = cover_data.get('logo_width_cm', 3.59)
    expected_h = cover_data.get('logo_height_cm', 3.59)
    tolerance = 0.35  # Allow +/- 0.35 cm
    
    stop_markers = ['lời cảm ơn', 'lời cam đoan', 'mở đầu', 'chương 1', 'mục lục', 'tóm tắt']
    cover_drawings = []
    
    for idx, p in enumerate(d.paragraphs[:50]):
        txt = p.text.strip().casefold()
        if any(marker in txt for marker in stop_markers):
            break
        drawings = p._p.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing')
        for drawing in drawings:
            extents = drawing.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent')
            cx = int(extents[0].get('cx')) if extents else None
            cy = int(extents[0].get('cy')) if extents else None
            jc = p._p.pPr.jc.get(qn('w:val')) if p._p.pPr is not None and p._p.pPr.jc is not None else None
            cover_drawings.append({
                'paragraph_index': idx,
                'cx': cx,
                'cy': cy,
                'alignment': jc
            })
            
    cover_inst_count = sum(
        1 for p in d.paragraphs[:50]
        if any(k in p.text.casefold() for k in ('tài nguyên và môi trường', 'khoa công nghệ thông tin'))
        and not any(marker in p.text.strip().casefold() for marker in stop_markers)
    )
    has_inner_cover = ('inner_cover' in v.front_matter) or (cover_inst_count >= 2)
    expected_logos = 2 if has_inner_cover else 1
    
    if len(cover_drawings) < expected_logos and not is_template_clone:
        issues.append(
            Issue(
                'error' if verify_mode else 'warning',
                'missing_cover_logo',
                f"Document has {'both outer and inner covers' if has_inner_cover else 'a cover'}, expected {expected_logos} university logo(s), but found {len(cover_drawings)}."
            )
        )
        
    for item in cover_drawings:
        if item['cx'] and item['cy']:
            actual_w = item['cx'] / 360000
            actual_h = item['cy'] / 360000
            if abs(actual_w - expected_w) > tolerance or abs(actual_h - expected_h) > tolerance:
                issues.append(
                    Issue(
                        'error' if verify_mode else 'warning',
                        'cover_logo_dimension_mismatch',
                        f"Cover logo at paragraph {item['paragraph_index']} dimensions ({actual_w:.2f} x {actual_h:.2f} cm) do not match expected standard ({expected_w:.2f} x {expected_h:.2f} cm, ~3.6 cm square) from presentation guide."
                    )
                )
        if item['alignment'] not in ('center', None):
            issues.append(
                Issue(
                    'warning',
                    'cover_logo_alignment_mismatch',
                    f"Cover logo at paragraph {item['paragraph_index']} must be centered (found alignment: '{item['alignment']}')."
                )
            )

def validate_document(
    path: str | Path,
    profile: DocumentProfile,
    variant_name: str,
    tolerance_cm: float = 0.08,
    verify_mode: bool = False
) -> ValidationResult:
    v = profile.variant(variant_name)
    try:
        d = Document(path)
    except Exception as exc:
        return ValidationResult(
            valid=False,
            issues=(Issue('error', 'unreadable_document', f"Cannot open document: {exc}"),)
        )
        
    issues: list[Issue] = []
    is_template_clone = bool(v.template_asset)
    
    # 0. Draft Placeholder Detection
    placeholders = _find_draft_placeholders(d, v)
    if placeholders:
        placeholder_policy = v.content_review.get(
            'unresolved_placeholders', 'strict_on_verify'
        )
        sev = (
            'error'
            if verify_mode and placeholder_policy == 'strict_on_verify'
            else 'warning'
        )
        issues.append(
            Issue(
                sev,
                'draft_placeholder_detected',
                f"Unresolved draft placeholder(s) detected in document ({len(placeholders)} item(s)): {', '.join(placeholders[:3])}."
            )
        )

    chapter_numbering_policy = v.content_review.get(
        'chapter_heading_numbering', 'review'
    )
    for finding in _chapter_heading_numbering_findings(d):
        issues.append(
            Issue(
                "error"
                if verify_mode and chapter_numbering_policy == "required"
                else "warning",
                "chapter_heading_numbering_missing",
                finding,
            )
        )
    
    # 1. Section & Page Geometry Validation
    if not d.sections:
        issues.append(Issue('error', 'no_sections', "Document has no sections."))
    else:
        for i, s in enumerate(d.sections):
            expected_width = v.page.width_cm
            expected_height = v.page.height_cm
            is_landscape = s.page_width.cm > s.page_height.cm
            profile_is_landscape = expected_width > expected_height
            if v.page.allow_mixed_orientation and is_landscape != profile_is_landscape:
                expected_width, expected_height = expected_height, expected_width
            checks = [
                ('width', s.page_width.cm, expected_width),
                ('height', s.page_height.cm, expected_height),
                ('top_margin', s.top_margin.cm, v.page.margins.top_cm),
                ('bottom_margin', s.bottom_margin.cm, v.page.margins.bottom_cm),
                ('left_margin', s.left_margin.cm, v.page.margins.left_cm),
                ('right_margin', s.right_margin.cm, v.page.margins.right_cm),
            ]
            for label, actual, expected in checks:
                if abs(actual - expected) > tolerance_cm:
                    issues.append(
                        Issue(
                            'error',
                            'page_geometry',
                            f"Section {i+1} {label}: measured {actual:.2f} cm, expected {expected:.2f} cm."
                        )
                    )
                    
    # 2. Typography & Line Spacing Validation
    try:
        normal_style = d.styles['Normal']
        doc_default_font = normal_style.font.name if normal_style and normal_style.font else None
        doc_default_size = normal_style.font.size.pt if normal_style and normal_style.font and normal_style.font.size else None
        doc_default_ls = normal_style.paragraph_format.line_spacing if normal_style and normal_style.paragraph_format else None
        if not isinstance(doc_default_ls, (int, float)):
            doc_default_ls = None
    except Exception:
        doc_default_font = None
        doc_default_size = None
        doc_default_ls = None

    expected_font = v.typography.body_font.lower()
    expected_size = v.typography.body_size_pt
    expected_ls = v.typography.line_spacing
    
    body_paragraphs: list[tuple[int, object]] = []
    in_body = len(d.sections) <= 1 and not any(x in v.front_matter for x in ('cover', 'inner_cover'))
    
    for paragraph_index, p in enumerate(d.paragraphs):
        txt = p.text.strip()
        if not txt:
            continue
        canonical_starts = [sec['title'].lower() for sec in v.section_blueprint[:2]]
        canonical_starts.extend(['mở đầu', 'chương 1', 'chapter 1', 'introduction'])
        if any(marker in txt.lower() for marker in canonical_starts):
            in_body = True
        if not in_body:
            continue
        style_name = p.style.name if p.style is not None else ""
        if (
            style_name.startswith('Heading')
            or style_name.startswith('TOC ')
            or style_name.startswith('toc ')
            or style_name in (
                'Title', 'Subtitle', 'Header', 'Footer', 'Caption', 'Bibliography',
                'FigureCaptionList', 'TableCaptionList',
                'Form Prompt', 'Form Info', 'Signature Block',
                'Cover Title', 'Cover Subtitle', 'Cover Organization', 'Cover Department'
            )
        ):
            continue
        if txt.startswith('[') and txt.endswith(']'):
            continue
        # Code listings follow their own (monospace) face and size; they are not body prose.
        if is_code_paragraph(p):
            continue
        body_paragraphs.append((paragraph_index, p))
        
    font_errors = 0
    size_errors = 0
    ls_errors = 0
    unresolved_warnings = 0
    unresolved_examples: list[str] = []
    
    if not is_template_clone:
        for paragraph_index, p in body_paragraphs:
            unresolved_properties: set[str] = set()
            if expected_ls is not None:
                actual_ls, ls_ok = _resolve_line_spacing(p, doc_default_ls)
                if not ls_ok:
                    unresolved_warnings += 1
                    unresolved_properties.add('line spacing')
                elif actual_ls is not None and abs(actual_ls - expected_ls) > 0.15:
                    ls_errors += 1
                    
            runs_to_check = [r for r in p.runs if r.text.strip()]
            if not runs_to_check and p.text.strip():
                font_name, font_ok = _resolve_run_font(p, p, doc_default_font)
                if not font_ok:
                    unresolved_warnings += 1
                    unresolved_properties.add('font')
                elif font_name and font_name.lower() != expected_font:
                    font_errors += 1
                size_val, size_ok = _resolve_run_size(p, p, doc_default_size)
                if not size_ok:
                    unresolved_warnings += 1
                    unresolved_properties.add('size')
                elif size_val is not None and abs(size_val - expected_size) > 0.6:
                    size_errors += 1
            else:
                for r in runs_to_check:
                    font_name, font_ok = _resolve_run_font(r, p, doc_default_font)
                    if not font_ok:
                        unresolved_warnings += 1
                        unresolved_properties.add('font')
                    elif font_name and font_name.lower() != expected_font:
                        font_errors += 1
                        
                    size_val, size_ok = _resolve_run_size(r, p, doc_default_size)
                    if not size_ok:
                        unresolved_warnings += 1
                        unresolved_properties.add('size')
                    elif size_val is not None and abs(size_val - expected_size) > 0.6:
                        size_errors += 1

            if unresolved_properties and len(unresolved_examples) < 5:
                style_name = p.style.name if p.style is not None else 'Unknown style'
                unresolved_examples.append(
                    f"paragraph {paragraph_index} [{style_name}]: {', '.join(sorted(unresolved_properties))}"
                )

        if font_errors > 0:
            issues.append(
                Issue(
                    'error',
                    'typography_font',
                    f"Body font mismatch detected in {font_errors} text run(s); expected '{v.typography.body_font}'."
                )
            )
        if size_errors > 0:
            issues.append(
                Issue(
                    'error',
                    'typography_size',
                    f"Body font size mismatch detected in {size_errors} text run(s); expected {expected_size} pt."
                )
            )
        if ls_errors > 0:
            issues.append(
                Issue(
                    'error',
                    'line_spacing',
                    f"Line spacing mismatch detected in {ls_errors} paragraph(s); expected {expected_ls}."
                )
            )
        if unresolved_warnings > 0:
            issues.append(
                Issue(
                    'warning',
                    'unresolvable_formatting',
                    f"Could not resolve {unresolved_warnings} expected text-formatting value(s). "
                    f"Examples (zero-based paragraph indexes): {'; '.join(unresolved_examples)}."
                )
            )

    # 2a. Explicit Word-style requirements (not only body-run defaults).
    for style_key, style_spec in v.typography.styles.items():
        style_name = _profile_style_name(style_key)
        try:
            style = d.styles[style_name]
        except KeyError:
            issues.append(
                Issue(
                    'error' if verify_mode else 'warning',
                    'profile_style_missing',
                    f"Profile configures style '{style_name}', but that Word style is missing.",
                )
            )
            continue

        styled_paragraphs = [
            paragraph for paragraph in d.paragraphs
            if paragraph.style is not None and paragraph.style.style_id == style.style_id
        ]
        expected_alignment = style_spec.get('alignment')
        if expected_alignment is not None and styled_paragraphs:
            expected = {'left': WD_ALIGN_PARAGRAPH.LEFT, 'center': WD_ALIGN_PARAGRAPH.CENTER,
                        'right': WD_ALIGN_PARAGRAPH.RIGHT, 'justify': WD_ALIGN_PARAGRAPH.JUSTIFY}[expected_alignment]
            persistent = _effective_style_alignment(style, d)
            overrides = sum(p.alignment is not None and p.alignment != expected for p in styled_paragraphs)
            if persistent != expected or overrides:
                issues.append(Issue('error' if verify_mode else 'warning', 'style_alignment_mismatch',
                    f"Style '{style_name}' must align {expected_alignment}; persistent style={persistent}, "
                    f"conflicting paragraph overrides={overrides}."))
        expected_size = style_spec.get('size_pt')
        if expected_size is not None:
            style_size = _effective_style_size(style)
            mismatch_count = int(style_size is None or abs(style_size - expected_size) > 0.6)
            for paragraph in styled_paragraphs:
                for run in paragraph.runs:
                    if run.text.strip() and run.font.size is not None and abs(run.font.size.pt - expected_size) > 0.6:
                        mismatch_count += 1
            if mismatch_count:
                actual = 'unset' if style_size is None else f'{style_size:g} pt'
                issues.append(
                    Issue(
                        'error' if verify_mode else 'warning',
                        'style_size_mismatch',
                        f"Style '{style_name}' font size is {actual}; expected {expected_size:g} pt. "
                        f"{max(0, mismatch_count - int(style_size is None or abs(style_size - expected_size) > 0.6))} direct run override(s) also differ.",
                    )
                )

        expected_color = style_spec.get('font_color')
        if expected_color is not None:
            expected_color = str(expected_color).lstrip('#').upper()
            style_color = str(style.font.color.rgb).upper() if style.font.color.rgb is not None else None
            mismatched_runs = 0
            for paragraph in styled_paragraphs:
                for run in paragraph.runs:
                    if not run.text.strip():
                        continue
                    color = run.font.color.rgb
                    if color is not None and str(color).upper() != expected_color:
                        mismatched_runs += 1
                    elif color is None and run.font.color.theme_color is not None:
                        mismatched_runs += 1
            if style_color != expected_color or mismatched_runs:
                actual = style_color or 'unset'
                issues.append(
                    Issue(
                        'error' if verify_mode else 'warning',
                        'style_color_mismatch',
                        f"Style '{style_name}' font color is {actual}; expected #{expected_color}. "
                        f"{mismatched_runs} direct run override(s) differ or use an unresolved theme color.",
                    )
                )

        expected_indents = {
            'left_indent_pt': style_spec.get('left_indent_pt'),
            'first_line_indent_pt': style_spec.get('first_line_indent_pt'),
        }
        indent_mismatches = []
        for attribute, expected in expected_indents.items():
            if expected is None:
                continue
            actual_value = getattr(style.paragraph_format, attribute.removesuffix('_pt'))
            actual = actual_value.pt if actual_value is not None else 0.0
            if abs(actual - expected) > 0.6:
                indent_mismatches.append(f"{attribute}={actual:g} pt (expected {expected:g} pt)")
        if indent_mismatches:
            issues.append(
                Issue(
                    'error' if verify_mode else 'warning',
                    'style_indent_mismatch',
                    f"Style '{style_name}' indentation mismatch: {', '.join(indent_mismatches)}.",
                )
            )

    figure_alignment = v.captions.get('figure_alignment')
    if figure_alignment:
        expected = {'left': WD_ALIGN_PARAGRAPH.LEFT, 'center': WD_ALIGN_PARAGRAPH.CENTER,
                    'right': WD_ALIGN_PARAGRAPH.RIGHT, 'justify': WD_ALIGN_PARAGRAPH.JUSTIFY}[figure_alignment]
        labels = [item['display'] for item in v.captions.get('figure_labels', [])]
        for p in d.paragraphs:
            if p.style.name != 'Caption' or not any(
                re.match(r'^\s*' + re.escape(label) + r'(?=\s|\d|$)', p.text, re.IGNORECASE) for label in labels
            ):
                continue
            actual = p.alignment if p.alignment is not None else _effective_style_alignment(p.style, d)
            if actual != expected:
                issues.append(Issue('error' if verify_mode else 'warning', 'figure_caption_alignment_mismatch',
                                    f"Figure caption must align {figure_alignment}: {p.text[:100]}"))

    # 3. Front Matter Presence & Sequential Order
    headings_in_doc: list[tuple[int, str]] = []
    front_matter_title_keys = {
        _normalize_text(title)
        for title in v.front_matter_titles.values()
        if isinstance(title, str) and title.strip()
    }
    for idx, p in enumerate(d.paragraphs):
        normalized_text = _normalize_text(p.text.strip())
        if (
            p.style.name.startswith('Heading')
            or p.style.name == 'Title'
            or normalized_text in front_matter_title_keys
        ):
            headings_in_doc.append((idx, p.text.strip()))
            
    # Check Cover Signals
    front_titles = [t.casefold() for t in v.front_matter_titles.values() if len(t) > 3]
    blueprint_titles = [sec['title'].casefold() for sec in v.section_blueprint[:2]]
    
    if 'cover' in v.front_matter and not is_template_clone:
        cover_paras = []
        for p in d.paragraphs[:50]:
            t = p.text.strip()
            if not t:
                continue
            if any(ft in t.casefold() for ft in front_titles):
                break
            if any(bt in t.casefold() for bt in blueprint_titles):
                break
            cover_paras.append(t)
            
        cover_text_full = "\n".join(cover_paras)
        inst_lines = v.cover.get('institution_lines', [])

        border_spec = v.cover.get('border')
        if border_spec:
            actual_border = d.sections[0]._sectPr.find(qn('w:pgBorders'))
            if actual_border is None:
                issues.append(
                    Issue(
                        'error' if verify_mode else 'warning',
                        'cover_border_missing',
                        "Profile requires a page frame, but the first section has no page border.",
                    )
                )
            else:
                expected_offset = border_spec.get('offset_from', 'page')
                actual_offset = actual_border.get(qn('w:offsetFrom'), 'page')
                actual_display = actual_border.get(qn('w:display'))
                if actual_offset != expected_offset or actual_display != border_spec.get('display'):
                    issues.append(
                        Issue(
                            'error' if verify_mode else 'warning',
                            'cover_border_configuration',
                            f"Cover frame uses offset '{actual_offset}' and display '{actual_display}'; "
                            f"expected '{expected_offset}' and '{border_spec.get('display')}'.",
                        )
                    )
                for edge, edge_spec in border_spec.get('edges', {}).items():
                    actual_edge = actual_border.find(qn(f'w:{edge}'))
                    try:
                        actual_space = int(actual_edge.get(qn('w:space'))) if actual_edge is not None else 0
                    except (TypeError, ValueError):
                        actual_space = 0
                    expected_space = int(edge_spec.get('space_points', 0))
                    if actual_space < expected_space:
                        issues.append(
                            Issue(
                                'error' if verify_mode else 'warning',
                                'cover_border_inset',
                                f"Cover frame {edge} inset is {actual_space} pt; expected at least {expected_space} pt from the page edge.",
                            )
                        )

        if inst_lines:
            missing_inst = False
            for line in inst_lines:
                if line.casefold() not in cover_text_full.casefold():
                    missing_inst = True
                    break
            if missing_inst:
                issues.append(
                    Issue(
                        'error' if verify_mode else 'warning',
                        'missing_cover_institution',
                        "Required cover institution header lines are missing or altered."
                    )
                )
                
        doc_type = v.cover.get('document_type', '')
        if doc_type and doc_type.casefold() not in cover_text_full.casefold():
            issues.append(
                Issue(
                    'error' if verify_mode else 'warning',
                    'missing_cover_document_type',
                    f"Required cover document type line '{doc_type}' is missing."
                )
            )
            
        # Inner Cover Verification
        if 'inner_cover' in v.front_matter:
            cover_count = 0
            anchor = ""
            if doc_type and doc_type.casefold() in cover_text_full.casefold():
                anchor = doc_type
                cover_count = cover_text_full.casefold().count(doc_type.casefold())
            elif inst_lines and any(inst.casefold() in cover_text_full.casefold() for inst in inst_lines):
                anchor = [inst for inst in inst_lines if inst.casefold() in cover_text_full.casefold()][0]
                cover_count = cover_text_full.casefold().count(anchor.casefold())
            else:
                for marker in ["tiểu luận", "báo cáo", "đồ án", "khoa công nghệ thông tin"]:
                    if marker in cover_text_full.casefold():
                        anchor = marker
                        cover_count = cover_text_full.casefold().count(marker)
                        break
            if not anchor:
                anchor = doc_type or (inst_lines[0] if inst_lines else '')
                if doc_type:
                    cover_count = cover_text_full.casefold().count(doc_type.casefold())
                elif inst_lines:
                    cover_count = cover_text_full.casefold().count(inst_lines[0].casefold())
                
            if cover_count < 2:
                issues.append(
                    Issue(
                        'error' if verify_mode else 'warning',
                        'missing_inner_cover',
                        "Profile specifies both cover and inner_cover, but inner cover page/block was not found."
                    )
                )
            elif v.cover.get('require_distinct_inner_cover'):
                # The document type often appears again near the middle of
                # each cover. Check the page break at the start of the second
                # cover block (normally the institution line) instead.
                distinct_anchor = next(
                    (
                        institution
                        for institution in inst_lines
                        if institution
                        and cover_text_full.casefold().count(institution.casefold()) >= 2
                    ),
                    '',
                )
                distinct_anchor = distinct_anchor or anchor or doc_type or (
                    inst_lines[0] if inst_lines else ''
                )
                anchor_paragraphs = [
                    index
                    for index, paragraph in enumerate(d.paragraphs[:50])
                    if distinct_anchor
                    and distinct_anchor.casefold() in paragraph.text.casefold()
                ]
                if len(anchor_paragraphs) < 2 or not _starts_new_page(d, anchor_paragraphs[1]):
                    issues.append(
                        Issue(
                            'error' if verify_mode else 'warning',
                            'inner_cover_not_distinct',
                            "Profile requires a separate inner cover page, but the second cover block does not start on a new page.",
                        )
                    )
            
    # Cover Logo Validation
    _check_cover_logo(d, v, issues, verify_mode, is_template_clone)

    non_cover_front = [x for x in v.front_matter if x not in ('cover', 'inner_cover', 'proposal_cover')]
    if non_cover_front and not is_template_clone:
        last_idx = -1
        for item in non_cover_front:
            item_title = v.front_matter_titles.get(item, item.replace('_', ' ')).casefold()
            match_idx = None
            for p_idx, h_text in headings_in_doc:
                if item_title in h_text.casefold() or h_text.casefold() in item_title:
                    match_idx = p_idx
                    break
            if match_idx is None and verify_mode:
                issues.append(
                    Issue(
                        'error',
                        'missing_front_matter',
                        f"Missing required front-matter section: '{item}' ('{v.front_matter_titles.get(item, item)}')."
                    )
                )
            elif match_idx is not None:
                if match_idx < last_idx:
                    issues.append(
                        Issue(
                            'error',
                            'front_matter_order',
                            f"Front matter section '{item}' appears out of order in document."
                        )
                    )
                last_idx = match_idx

    # 4. Section Blueprint Presence, Level & Sequential Order
    if v.section_blueprint:
        missing_blueprint = []
        blueprint_indices: list[int] = []
        numbering_missing: list[str] = []
        numbering_invalid: list[str] = []
        numbered_headings: list[tuple[str, int, int, int]] = []
        
        for sec in v.section_blueprint:
            target_title = str(sec['title']).casefold()
            expected_level = sec.get('level', 1)
            is_required = sec.get('required', True)
            matched_p = None
            match_idx = None
            
            for p_idx, p in enumerate(d.paragraphs):
                h_text = p.text.strip()
                if (p.style.name.startswith('Heading') or p.style.name == 'Title') and (target_title in h_text.casefold() or h_text.casefold() in target_title):
                    match_idx = p_idx
                    matched_p = p
                    break
                    
            if match_idx is None:
                doc_full_text = "\n".join(p.text for p in d.paragraphs)
                if target_title not in doc_full_text.casefold():
                    if is_required:
                        missing_blueprint.append(str(sec['title']))
            else:
                blueprint_indices.append(match_idx)
                if matched_p is not None and not is_template_clone:
                    style_name = matched_p.style.name
                    actual_level = None
                    if style_name.startswith('Heading '):
                        try:
                            actual_level = int(style_name.replace('Heading ', '').strip())
                        except ValueError:
                            actual_level = None
                    elif style_name == 'Title':
                        actual_level = 1
                        
                    if actual_level is not None:
                        if actual_level != expected_level:
                            issues.append(
                                Issue(
                                    'error' if verify_mode else 'warning',
                                    'blueprint_heading_level_mismatch',
                                    f"Section '{sec['title']}' has heading level {actual_level} ('{style_name}'), expected level {expected_level}."
                                )
                            )
                    else:
                        issues.append(
                            Issue(
                                'warning',
                                'blueprint_heading_level_unresolvable',
                                f"Section '{sec['title']}' uses custom style '{style_name}'; heading level could not be deterministically verified."
                            )
                        )

                    if sec.get('page_break_before') and not _starts_new_page(d, match_idx):
                        issues.append(
                            Issue(
                                'error' if verify_mode else 'warning',
                                'blueprint_page_break_missing',
                                f"Section '{sec['title']}' is required to start on a new page, but no page break was found before its heading.",
                            )
                        )

                    if sec.get('numbered'):
                        number_info = _paragraph_numbering(matched_p)
                        if number_info is None:
                            numbering_missing.append(str(sec['title']))
                        else:
                            number_id, number_level = number_info
                            expected_number_level = expected_level - 1
                            if number_level != expected_number_level:
                                numbering_invalid.append(
                                    f"{sec['title']} (level {number_level + 1}, expected {expected_level})"
                                )
                            else:
                                numbered_headings.append(
                                    (str(sec['title']), expected_level, number_id, number_level)
                                )
                
        if missing_blueprint:
            sev = 'warning' if (is_template_clone and not verify_mode) else 'error'
            issues.append(
                Issue(
                    sev,
                    'missing_blueprint_sections',
                    f"Missing required section(s) from profile blueprint: {', '.join(missing_blueprint[:5])}."
                )
            )

        if numbering_missing:
            issues.append(
                Issue(
                    'error' if verify_mode else 'warning',
                    'blueprint_heading_numbering_missing',
                    f"Required automatic heading numbering is missing for: {', '.join(numbering_missing[:5])}.",
                )
            )

        if numbered_headings:
            number_ids = {item[2] for item in numbered_headings}
            required_levels = {item[3] for item in numbered_headings}
            if len(number_ids) != 1:
                numbering_invalid.append("required headings do not share one multilevel list")
            else:
                number_id = next(iter(number_ids))
                numbering_part = d.part.numbering_part.element
                abstract_id = None
                for number in numbering_part.findall(qn('w:num')):
                    if number.get(qn('w:numId')) == str(number_id):
                        abstract_ref = number.find(qn('w:abstractNumId'))
                        if abstract_ref is not None:
                            abstract_id = abstract_ref.get(qn('w:val'))
                        break
                abstract = next(
                    (
                        item for item in numbering_part.findall(qn('w:abstractNum'))
                        if item.get(qn('w:abstractNumId')) == abstract_id
                    ),
                    None,
                )
                multi_level = abstract.find(qn('w:multiLevelType')) if abstract is not None else None
                actual_levels = {
                    int(item.get(qn('w:ilvl')))
                    for item in abstract.findall(qn('w:lvl'))
                    if item.get(qn('w:ilvl')) is not None
                } if abstract is not None else set()
                if (
                    multi_level is None
                    or multi_level.get(qn('w:val')) not in {'multilevel', 'hybridMultilevel'}
                    or not required_levels.issubset(actual_levels)
                ):
                    numbering_invalid.append("numbering definition is not a complete multilevel list for the required heading levels")

            if numbering_invalid:
                issues.append(
                    Issue(
                        'error' if verify_mode else 'warning',
                        'blueprint_heading_numbering_invalid',
                        f"Required heading numbering is not a valid shared multilevel list: {', '.join(numbering_invalid[:5])}.",
                    )
                )
            
        if len(blueprint_indices) >= 2 and not is_template_clone:
            if blueprint_indices != sorted(blueprint_indices):
                issues.append(
                    Issue(
                        'error',
                        'blueprint_order',
                        "Blueprint sections appear out of sequence in document."
                    )
                )

    # 5. Header & Footer Requirements
    hf = v.header_footer
    if hf:
        req_page = v.field_requirements.get('page_number')
        if (hf.get('footer_right') == 'page_number' or req_page is True) and req_page is not False:
            has_page_field = False
            for s in d.sections:
                f_xml = s.footer._element.xml
                if 'w:fldSimple' in f_xml and ('PAGE' in f_xml or 'w:instr="PAGE"' in f_xml):
                    has_page_field = True
                    break
                if '<w:instrText' in f_xml and 'PAGE' in f_xml:
                    has_page_field = True
                    break
            if not has_page_field:
                issues.append(
                    Issue(
                        'error' if verify_mode else 'warning',
                        'missing_page_number_field',
                        "Profile specifies footer page numbering, but no PAGE field was detected in footers."
                    )
                )
                
        # Check page_number_start restart
        p_start = hf.get('page_number_start')
        if p_start is not None and verify_mode and not is_template_clone:
            has_pg_restart = False
            for s in d.sections:
                s_xml = s._sectPr.xml
                if 'w:pgNumType' in s_xml and ('w:start=' in s_xml or 'w:start' in s_xml):
                    has_pg_restart = True
                    break
            if not has_pg_restart:
                issues.append(
                    Issue(
                        'error',
                        'missing_page_number_restart',
                        f"Profile specifies page_number_start={p_start}, but no section with pgNumType restart was found."
                    )
                )
                
        # In verify_mode, check semantic roles
        if verify_mode and not is_template_clone:
            body_section = d.sections[-1]
            header_paras = [p for p in body_section.header.paragraphs if p.text.strip()]
            footer_paras = [p for p in body_section.footer.paragraphs if p.text.strip()]
            header_text = " ".join(p.text.strip() for p in header_paras)
            footer_text = " ".join(p.text.strip() for p in footer_paras)
            
            cover_meta = _extract_cover_metadata(d, v)
            expected_topic = cover_meta.get('topic')
            expected_sup = cover_meta.get('supervisor')
            expected_student = cover_meta.get('student')
            
            header_norm = _normalize_text(header_text)
            footer_norm = _normalize_text(footer_text)
            
            if hf.get('header_left'):
                role = hf['header_left']
                if role == 'topic':
                    if not header_text:
                        issues.append(Issue('error', 'missing_header_topic', "Profile requires header topic, but header is empty."))
                    elif expected_topic:
                        exp_topic_norm = _normalize_text(expected_topic)
                        if exp_topic_norm not in header_norm:
                            issues.append(Issue('error', 'header_topic_mismatch', f"Header text does not match document topic: '{header_text}' vs expected '{expected_topic}'."))
                    elif "untitled" in header_norm or any(_normalize_text(p) in header_norm for p in GENERIC_DRAFT_PLACEHOLDERS):
                        issues.append(Issue('error', 'header_topic_placeholder', f"Header topic contains draft placeholder: '{header_text}'."))

            if hf.get('header_right') == 'supervisor':
                if not header_text:
                    issues.append(Issue('error', 'missing_header_supervisor', "Profile requires supervisor in header_right, but header is empty."))
                elif expected_sup:
                    exp_sup_norm = _normalize_text(expected_sup)
                    if '\t' in header_text:
                        right_part = header_text.split('\t')[-1].strip()
                        right_norm = _normalize_text(right_part)
                        if right_norm != exp_sup_norm and exp_sup_norm not in header_norm:
                            issues.append(Issue('error', 'header_supervisor_mismatch', f"Header supervisor '{right_part}' does not match cover supervisor '{expected_sup}'."))
                    elif exp_sup_norm not in header_norm:
                        issues.append(Issue('error', 'header_supervisor_mismatch', f"Header text does not contain cover supervisor '{expected_sup}'."))
                else:
                    if '\t' not in header_text or len(header_text.split('\t')[-1].strip()) < 3:
                        issues.append(Issue('error', 'missing_header_supervisor', "Profile requires supervisor in header_right, but supervisor was missing."))

            if hf.get('footer_left') == 'student':
                if not footer_text:
                    issues.append(Issue('error', 'missing_footer_student', "Profile requires footer student info, but footer is empty."))
                elif expected_student:
                    exp_stu_norm = _normalize_text(expected_student)
                    if '\t' in footer_text:
                        left_part = footer_text.split('\t')[0].strip()
                        left_norm = _normalize_text(left_part)
                        if left_norm != exp_stu_norm and exp_stu_norm not in footer_norm:
                            issues.append(Issue('error', 'footer_student_mismatch', f"Footer student text '{left_part}' does not match cover student '{expected_student}'."))
                    elif exp_stu_norm not in footer_norm:
                        issues.append(Issue('error', 'footer_student_mismatch', f"Footer text does not contain cover student '{expected_student}'."))
                else:
                    if any(_normalize_text(p) in footer_norm for p in GENERIC_DRAFT_PLACEHOLDERS):
                        issues.append(Issue('error', 'footer_student_placeholder', f"Footer student contains placeholder: '{footer_text}'."))

    # 6. TOC Field Validation
    req_toc = v.field_requirements.get('table_of_contents')
    if (('table_of_contents' in v.front_matter or req_toc is True) and req_toc is not False) and not is_template_clone:
        doc_xml = d._element.xml
        has_toc = ('w:fldSimple' in doc_xml and 'TOC' in doc_xml) or ('<w:instrText' in doc_xml and 'TOC' in doc_xml)
        if not has_toc:
            issues.append(
                Issue(
                    'error' if verify_mode else 'warning',
                    'missing_toc_field',
                    "Profile includes table_of_contents front-matter, but no TOC field code was found."
                )
            )

    # 7. Bibliography / Reference Count (Scoped strictly under Bibliography section)
    minrefs = v.citations.get('minimum_references')
    if isinstance(minrefs, int) and minrefs > 0 and not is_template_clone:
        ref_pattern = re.compile(r'^\[\d+\]')
        
        bibliography_sections: list[tuple[int, int]] = []
        for idx, p in enumerate(d.paragraphs):
            txt = p.text.strip()
            if not txt:
                continue
            txt_norm = _normalize_text(txt)
            if ('tài liệu tham khảo' in txt_norm or 'tai lieu tham khao' in txt_norm or 
                'references' in txt_norm or 'bibliography' in txt_norm):
                if p.style.name.startswith('Heading') or p.style.name == 'Title' or any(_normalize_text(sec['title']) in txt_norm for sec in v.section_blueprint):
                    bib_level = 1
                    if p.style.name.startswith('Heading '):
                        try:
                            bib_level = int(p.style.name.replace('Heading ', '').strip())
                        except ValueError:
                            bib_level = 1
                    bibliography_sections.append((idx, bib_level))

        section_counts: list[int] = []
        for bib_start_idx, bib_level in bibliography_sections:
            section_count = 0
            for p in d.paragraphs[bib_start_idx + 1:]:
                txt = p.text.strip()
                if not txt:
                    continue
                if p.style.name.startswith('Heading '):
                    try:
                        lvl = int(p.style.name.replace('Heading ', '').strip())
                        if lvl <= bib_level:
                            break
                    except ValueError:
                        pass
                if ref_pattern.match(txt):
                    section_count += 1
                elif txt and not (txt.startswith('[') and txt.endswith(']')) and len(txt) > 10:
                    section_count += 1
            section_counts.append(section_count)

        # A stale empty bibliography heading must not mask a later populated
        # duplicate. Each candidate remains bounded by the next peer heading.
        count = max(section_counts, default=0)
                    
        if count == 0:
            issues.append(
                Issue(
                    'error' if verify_mode else 'warning',
                    'missing_references',
                    f"Found 0 reference items in bibliography section; profile requires at least {minrefs}."
                )
            )
        elif count < minrefs:
            issues.append(
                Issue(
                    'error' if verify_mode else 'warning',
                    'insufficient_references',
                    f"Found {count} reference item(s) in bibliography section; profile requires at least {minrefs}."
                )
            )

    valid = not any(i.severity == 'error' for i in issues)
    return ValidationResult(valid=valid, issues=tuple(issues))
