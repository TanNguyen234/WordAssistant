from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
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

DRAFT_PLACEHOLDERS = [
    "[front matter content]",
    "[section content...]",
    "[list of figures]",
    "[list of tables]",
    "[document content]",
    "untitled document",
    "[họ và tên sinh viên - mssv]",
    "[họ và tên cbhd]",
    "[họ và tên sinh viên]",
    "[họ và tên gvhd]",
    "<tên đề tài>",
    "[tên đề tài]",
    "<tên sinh viên>",
    "<sinh viên>",
    "<cán bộ hướng dẫn>",
    "<giảng viên hướng dẫn>",
    "[tên sinh viên]",
    "[tên gvhd]",
]

def _find_draft_placeholders(d: Document) -> list[str]:
    found = []
    # Check paragraphs
    for p in d.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue
        txt_lower = txt.lower()
        for pl in DRAFT_PLACEHOLDERS:
            if pl in txt_lower:
                found.append(txt[:80])
                break
    # Check tables
    for table in d.tables:
        for row in table.rows:
            for cell in row.cells:
                c_txt = cell.text.strip().lower()
                for pl in DRAFT_PLACEHOLDERS:
                    if pl in c_txt:
                        found.append(cell.text.strip()[:80])
                        break
    return found

def _extract_cover_metadata(d: Document, v: Variant) -> dict[str, str]:
    meta: dict[str, str] = {}
    cover_text = []
    for p in d.paragraphs[:35]:
        t = p.text.strip()
        if t:
            cover_text.append(t)
            
    for line in cover_text:
        l_lower = line.lower()
        if any(k in l_lower for k in ("sinh viên thực hiện:", "svth:", "sinh viên:")):
            val = line.split(":", 1)[-1].strip()
            if val:
                meta['student'] = val
        elif any(k in l_lower for k in ("giảng viên hướng dẫn:", "cán bộ hướng dẫn:", "gvhd:", "cbhd:")):
            val = line.split(":", 1)[-1].strip()
            if val:
                meta['supervisor'] = val
                
    doc_type = v.cover.get('document_type', '').casefold()
    if doc_type:
        for idx, line in enumerate(cover_text):
            if doc_type in line.casefold():
                title_parts = []
                for next_line in cover_text[idx + 1:]:
                    nl_lower = next_line.lower()
                    if any(k in nl_lower for k in ("sinh viên", "svth", "giảng viên", "gvhd", "cán bộ", "tp. hồ chí minh", "tp.", "năm")):
                        break
                    title_parts.append(next_line)
                if title_parts:
                    meta['topic'] = " ".join(title_parts).strip()
                break
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
    placeholders = _find_draft_placeholders(d)
    if placeholders:
        sev = 'error' if verify_mode else 'warning'
        issues.append(
            Issue(
                sev,
                'draft_placeholder_detected',
                f"Unresolved draft placeholder(s) detected in document ({len(placeholders)} item(s)): {', '.join(placeholders[:3])}."
            )
        )
    
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
            if expected_ls is not None:
                actual_ls, ls_ok = _resolve_line_spacing(p, doc_default_ls)
                if not ls_ok:
                    unresolved_warnings += 1
                elif actual_ls is not None and abs(actual_ls - expected_ls) > 0.15:
                    ls_errors += 1
                    
            runs_to_check = [r for r in p.runs if r.text.strip()]
            if not runs_to_check and p.text.strip():
                font_name, font_ok = _resolve_run_font(p, p, doc_default_font)
                if not font_ok:
                    unresolved_warnings += 1
                elif font_name and font_name.lower() != expected_font:
                    font_errors += 1
                size_val, size_ok = _resolve_run_size(p, p, doc_default_size)
                if not size_ok:
                    unresolved_warnings += 1
                elif size_val is not None and abs(size_val - expected_size) > 0.6:
                    size_errors += 1
            else:
                for r in runs_to_check:
                    font_name, font_ok = _resolve_run_font(r, p, doc_default_font)
                    if not font_ok:
                        unresolved_warnings += 1
                    elif font_name and font_name.lower() != expected_font:
                        font_errors += 1
                        
                    size_val, size_ok = _resolve_run_size(r, p, doc_default_size)
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
            
    # Check Cover Signals
    if 'cover' in v.front_matter and not is_template_clone:
        cover_text_full = "\n".join(p.text for p in d.paragraphs[:35])
        inst_lines = v.cover.get('institution_lines', [])
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
        
        for sec in v.section_blueprint:
            target_title = str(sec['title']).casefold()
            expected_level = sec.get('level', 1)
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
                
        if missing_blueprint:
            sev = 'warning' if (is_template_clone and not verify_mode) else 'error'
            issues.append(
                Issue(
                    sev,
                    'missing_blueprint_sections',
                    f"Missing required section(s) from profile blueprint: {', '.join(missing_blueprint[:5])}."
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
        # Check PAGE number field
        if hf.get('footer_right') == 'page_number':
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
            
            if hf.get('header_left'):
                if not header_text:
                    issues.append(
                        Issue('error', 'missing_header_topic', f"Profile requires header '{hf['header_left']}', but header is empty.")
                    )
                elif expected_topic:
                    topic_clean = expected_topic.replace("\n", " ").strip()
                    if topic_clean.lower() not in header_text.lower() and not any(w in header_text.lower() for w in topic_clean.lower().split() if len(w) > 4):
                        issues.append(
                            Issue('error', 'header_topic_mismatch', f"Header text does not match document topic: '{header_text}' vs expected '{expected_topic}'.")
                        )
                elif "untitled" in header_text.lower() or any(p in header_text.lower() for p in DRAFT_PLACEHOLDERS):
                    issues.append(
                        Issue('error', 'header_topic_placeholder', f"Header topic contains draft placeholder: '{header_text}'.")
                    )

            if hf.get('header_right') == 'supervisor':
                found_sup = False
                if expected_sup:
                    sup_clean = expected_sup.lower()
                    if sup_clean in header_text.lower() or any(part in header_text.lower() for part in sup_clean.split() if len(part) > 3):
                        found_sup = True
                elif header_text and '\t' in header_text:
                    right_part = header_text.split('\t')[-1].strip()
                    if right_part and right_part != header_text.split('\t')[0].strip() and not any(p in right_part.lower() for p in DRAFT_PLACEHOLDERS):
                        found_sup = True
                if not found_sup:
                    issues.append(
                        Issue('error', 'missing_header_supervisor', "Profile requires supervisor in header_right, but supervisor was missing or mismatched.")
                    )

            if hf.get('footer_left') == 'student':
                if not footer_text:
                    issues.append(
                        Issue('error', 'missing_footer_student', "Profile requires footer student info, but footer is empty.")
                    )
                elif expected_student:
                    stu_clean = expected_student.lower()
                    if stu_clean not in footer_text.lower() and not any(part in footer_text.lower() for part in stu_clean.split() if len(part) > 3):
                        issues.append(
                            Issue('error', 'footer_student_mismatch', f"Footer student text '{footer_text}' does not match cover student '{expected_student}'.")
                        )
                elif any(p in footer_text.lower() for p in DRAFT_PLACEHOLDERS):
                    issues.append(
                        Issue('error', 'footer_student_placeholder', f"Footer student contains placeholder: '{footer_text}'.")
                    )

    # 6. TOC Field Validation
    if ('table_of_contents' in v.front_matter or 'table_of_contents' in v.field_requirements) and not is_template_clone:
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
        
        # Locate bibliography section heading
        bib_start_idx = None
        bib_level = 1
        for idx, p in enumerate(d.paragraphs):
            txt = p.text.strip()
            if not txt:
                continue
            if ('tài liệu tham khảo' in txt.lower() or 'tai lieu tham khao' in txt.lower() or 
                'references' in txt.lower() or 'bibliography' in txt.lower()):
                if p.style.name.startswith('Heading') or p.style.name == 'Title' or any(sec['title'].lower() in txt.lower() for sec in v.section_blueprint):
                    bib_start_idx = idx
                    if p.style.name.startswith('Heading '):
                        try:
                            bib_level = int(p.style.name.replace('Heading ', '').strip())
                        except ValueError:
                            bib_level = 1
                    break
                    
        count = 0
        if bib_start_idx is not None:
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
                    count += 1
                elif txt and not (txt.startswith('[') and txt.endswith(']')) and len(txt) > 10:
                    count += 1
                    
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
