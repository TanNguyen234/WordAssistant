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

def _get_paragraph_font(p, default_font: str | None) -> str | None:
    for r in p.runs:
        if r.font and r.font.name:
            return r.font.name
    if p.style and hasattr(p.style, 'font') and p.style.font and p.style.font.name:
        return p.style.font.name
    return default_font

def _get_paragraph_size(p, default_size: float | None) -> float | None:
    for r in p.runs:
        if r.font and r.font.size:
            return r.font.size.pt
    if p.style and hasattr(p.style, 'font') and p.style.font and p.style.font.size:
        return p.style.font.size.pt
    return default_size

def validate_document(
    path: str | Path,
    profile: DocumentProfile,
    variant_name: str,
    tolerance_cm: float = 0.08
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
                    
    # 2. Typography Validation (Body Font & Size in Content Sections)
    try:
        normal_style = d.styles['Normal']
        doc_default_font = normal_style.font.name if normal_style and normal_style.font else None
        doc_default_size = normal_style.font.size.pt if normal_style and normal_style.font and normal_style.font.size else None
    except Exception:
        doc_default_font = None
        doc_default_size = None
        
    # If template_asset is present, the template geometry and layout are official source
    is_template_clone = bool(v.template_asset)
    
    # Determine body section start: after covers/front-matter
    # Filter out cover paragraphs, headings, titles, and table text
    body_paragraphs = []
    in_body = False or len(d.sections) == 1 or not any(x in v.front_matter for x in ('cover', 'inner_cover'))
    
    for p in d.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue
        # Check if we crossed into body section (e.g. MỞ ĐẦU or Introduction)
        if any(sec['title'].lower() in txt.lower() for sec in v.section_blueprint[:2]):
            in_body = True
        if not in_body:
            continue
        if p.style.name.startswith('Heading') or p.style.name in ('Title', 'Subtitle', 'Header', 'Footer'):
            continue
        # Exclude placeholder notes
        if txt.startswith('[') and txt.endswith(']'):
            continue
        body_paragraphs.append(p)
        
    expected_font = v.typography.body_font.lower()
    expected_size = v.typography.body_size_pt
    
    font_mismatches = 0
    size_mismatches = 0
    
    for p in body_paragraphs[:30]:
        actual_font = _get_paragraph_font(p, doc_default_font or v.typography.body_font)
        if actual_font and actual_font.lower() != expected_font:
            font_mismatches += 1
            
        actual_size = _get_paragraph_size(p, doc_default_size or expected_size)
        if actual_size is not None and abs(actual_size - expected_size) > 0.6:
            size_mismatches += 1
            
    if font_mismatches > 0 and not is_template_clone:
        issues.append(
            Issue(
                'error',
                'typography_font',
                f"Body font mismatch detected in {font_mismatches} sampled paragraph(s); expected '{v.typography.body_font}'."
            )
        )
        
    if size_mismatches > 0 and not is_template_clone:
        issues.append(
            Issue(
                'error',
                'typography_size',
                f"Body font size mismatch detected in {size_mismatches} sampled paragraph(s); expected {expected_size} pt."
            )
        )
        
    # 3. Line Spacing Validation
    if v.typography.line_spacing is not None and body_paragraphs and not is_template_clone:
        expected_ls = v.typography.line_spacing
        ls_mismatches = 0
        for p in body_paragraphs[:10]:
            p_ls = p.paragraph_format.line_spacing
            if p_ls is not None and isinstance(p_ls, (int, float)):
                if abs(p_ls - expected_ls) > 0.15:
                    ls_mismatches += 1
        if ls_mismatches > 3:
            issues.append(
                Issue(
                    'warning',
                    'line_spacing',
                    f"Line spacing mismatch in {ls_mismatches} paragraph(s); expected {expected_ls}."
                )
            )
            
    # 4. Header & Footer Requirements
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
                        'warning',
                        'missing_page_number_field',
                        "Profile specifies footer page numbering, but no PAGE field was detected in footers."
                    )
                )
                
    # 5. Front Matter & Section Blueprint Presence
    doc_text_full = "\n".join(p.text for p in d.paragraphs)
    doc_headings = [p.text.strip().casefold() for p in d.paragraphs if p.style.name.startswith('Heading') or p.style.name == 'Title']
    
    if v.section_blueprint:
        missing_blueprint = []
        for sec in v.section_blueprint:
            target_title = str(sec['title']).casefold()
            if not any(target_title in h or h in target_title for h in doc_headings) and target_title not in doc_text_full.casefold():
                missing_blueprint.append(str(sec['title']))
        if missing_blueprint:
            # If blueprint is missing in template clone, report as warning / advisory, else error
            sev = 'warning' if is_template_clone else 'error'
            issues.append(
                Issue(
                    sev,
                    'missing_blueprint_sections',
                    f"Missing required section(s) from profile blueprint: {', '.join(missing_blueprint[:5])}."
                )
            )
            
    # 6. TOC Field Validation
    if ('table_of_contents' in v.front_matter or 'table_of_contents' in v.field_requirements) and not is_template_clone:
        doc_xml = d._element.xml
        if 'TOC' not in doc_xml:
            issues.append(
                Issue(
                    'warning',
                    'missing_toc_field',
                    "Profile includes table_of_contents front-matter, but no TOC field code was found."
                )
            )
            
    # 7. Bibliography Count
    minrefs = v.citations.get('minimum_references')
    if isinstance(minrefs, int):
        count = sum(
            1 for ln in doc_text_full.splitlines()
            if ln.strip().startswith('[') and ']' in ln
        )
        if count and count < minrefs:
            issues.append(
                Issue(
                    'warning',
                    'reference_count',
                    f"Found {count} reference item(s); profile recommends at least {minrefs}."
                )
            )
            
    valid = not any(i.severity == 'error' for i in issues)
    return ValidationResult(valid=valid, issues=tuple(issues))
