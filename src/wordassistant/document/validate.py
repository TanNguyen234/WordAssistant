from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from docx import Document
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

def _resolve_run_font(run, p, doc_default_font: str | None) -> tuple[str | None, bool]:
    # Returns (font_name, is_resolved)
    if run.font and run.font.name:
        return run.font.name, True
    if p.style and hasattr(p.style, 'font') and p.style.font and p.style.font.name:
        return p.style.font.name, True
    if doc_default_font:
        return doc_default_font, True
    return None, False

def _resolve_run_size(run, p, doc_default_size: float | None) -> tuple[float | None, bool]:
    # Returns (size_pt, is_resolved)
    if run.font and run.font.size:
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
    
    # 1. Section & Page Geometry Validation
    if not d.sections:
        issues.append(Issue('error', 'no_sections', "Document has no sections."))
    else:
        for i, s in enumerate(d.sections):
            checks = [
                ('width', s.page_width.cm, v.page.width_cm),
                ('height', s.page_height.cm, v.page.height_cm),
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
    
    # Identify content body paragraphs (skipping cover page paragraphs)
    body_paragraphs = []
    in_body = False or len(d.sections) == 1 or not any(x in v.front_matter for x in ('cover', 'inner_cover'))
    
    for p in d.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue
        if any(sec['title'].lower() in txt.lower() for sec in v.section_blueprint[:2]):
            in_body = True
        if not in_body:
            continue
        if p.style.name.startswith('Heading') or p.style.name in ('Title', 'Subtitle', 'Header', 'Footer'):
            continue
        if txt.startswith('[') and txt.endswith(']'):
            continue
        body_paragraphs.append(p)
        
    font_errors = 0
    size_errors = 0
    ls_errors = 0
    unresolved_warnings = 0
    
    if not is_template_clone:
        for p in body_paragraphs:
            # Check line spacing
            if expected_ls is not None:
                actual_ls, ls_ok = _resolve_line_spacing(p, doc_default_ls)
                if ls_ok and actual_ls is not None and abs(actual_ls - expected_ls) > 0.15:
                    ls_errors += 1
                    
            # Check runs
            runs_to_check = [r for r in p.runs if r.text.strip()]
            if not runs_to_check and p.text.strip():
                # Paragraph without explicit runs
                font_name, font_ok = _resolve_run_font(p, p, doc_default_font or v.typography.body_font)
                if font_ok and font_name and font_name.lower() != expected_font:
                    font_errors += 1
                size_val, size_ok = _resolve_run_size(p, p, doc_default_size or expected_size)
                if size_ok and size_val is not None and abs(size_val - expected_size) > 0.6:
                    size_errors += 1
            else:
                for r in runs_to_check:
                    font_name, font_ok = _resolve_run_font(r, p, doc_default_font or v.typography.body_font)
                    if not font_ok:
                        unresolved_warnings += 1
                    elif font_name and font_name.lower() != expected_font:
                        font_errors += 1
                        
                    size_val, size_ok = _resolve_run_size(r, p, doc_default_size or expected_size)
                    if not size_ok:
                        unresolved_warnings += 1
                    elif size_val is not None and abs(size_val - expected_size) > 0.6:
                        size_errors += 1

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
                    f"Unresolvable formatting properties in {unresolved_warnings} run(s)."
                )
            )

    # 3. Front Matter Presence & Sequential Order
    headings_in_doc: list[tuple[int, str]] = []
    for idx, p in enumerate(d.paragraphs):
        if p.style.name.startswith('Heading') or p.style.name == 'Title':
            headings_in_doc.append((idx, p.text.strip()))
            
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
            if match_idx is not None:
                if match_idx < last_idx:
                    issues.append(
                        Issue(
                            'error',
                            'front_matter_order',
                            f"Front matter section '{item}' appears out of order in document."
                        )
                    )
                last_idx = match_idx

    # 4. Section Blueprint Presence & Sequential Order
    if v.section_blueprint:
        missing_blueprint = []
        blueprint_indices: list[int] = []
        
        for sec in v.section_blueprint:
            target_title = str(sec['title']).casefold()
            match_idx = None
            for p_idx, h_text in headings_in_doc:
                if target_title in h_text.casefold() or h_text.casefold() in target_title:
                    match_idx = p_idx
                    break
            if match_idx is None:
                # Also check full text
                doc_full_text = "\n".join(p.text for p in d.paragraphs)
                if target_title not in doc_full_text.casefold():
                    missing_blueprint.append(str(sec['title']))
            else:
                blueprint_indices.append(match_idx)
                
        if missing_blueprint:
            sev = 'warning' if is_template_clone else 'error'
            issues.append(
                Issue(
                    sev,
                    'missing_blueprint_sections',
                    f"Missing required section(s) from profile blueprint: {', '.join(missing_blueprint[:5])}."
                )
            )
            
        # Check that found blueprint sections appear in strictly increasing order
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
        if hf.get('footer_right') == 'page_number':
            has_page_field = False
            for s in d.sections:
                f_xml = s.footer._element.xml
                if 'w:instr="PAGE"' in f_xml or 'PAGE' in f_xml:
                    has_page_field = True
                    break
            if not has_page_field:
                issues.append(
                    Issue(
                        'warning' if not verify_mode else 'error',
                        'missing_page_number_field',
                        "Profile specifies footer page numbering, but no PAGE field was detected in footers."
                    )
                )

    # 6. TOC Field Validation
    if ('table_of_contents' in v.front_matter or 'table_of_contents' in v.field_requirements) and not is_template_clone:
        doc_xml = d._element.xml
        if 'TOC' not in doc_xml:
            issues.append(
                Issue(
                    'warning' if not verify_mode else 'error',
                    'missing_toc_field',
                    "Profile includes table_of_contents front-matter, but no TOC field code was found."
                )
            )

    # 7. Bibliography / Reference Count
    minrefs = v.citations.get('minimum_references')
    if isinstance(minrefs, int) and minrefs > 0 and not is_template_clone:
        import re
        ref_pattern = re.compile(r'^\[\d+\]')
        doc_lines = [p.text.strip() for p in d.paragraphs if p.text.strip()]
        count = sum(1 for ln in doc_lines if ref_pattern.match(ln))
        
        # Also check if any paragraphs under bibliography chapter exist
        if count == 0:
            in_bib = False
            for p in d.paragraphs:
                txt = p.text.strip()
                if ('tài liệu tham khảo' in txt.lower() or 'references' in txt.lower() or 'bibliography' in txt.lower()) and p.style.name.startswith('Heading'):
                    in_bib = True
                    continue
                if in_bib and p.style.name.startswith('Heading'):
                    in_bib = False
                if in_bib and txt and not (txt.startswith('[') and txt.endswith(']')):
                    count += 1
                    
        if count == 0:
            issues.append(
                Issue(
                    'error' if verify_mode else 'warning',
                    'missing_references',
                    f"Found 0 reference items in document; profile requires at least {minrefs}."
                )
            )
        elif count < minrefs:
            issues.append(
                Issue(
                    'error' if verify_mode else 'warning',
                    'insufficient_references',
                    f"Found {count} reference item(s); profile requires at least {minrefs}."
                )
            )

    valid = not any(i.severity == 'error' for i in issues)
    return ValidationResult(valid=valid, issues=tuple(issues))
