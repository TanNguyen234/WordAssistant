from __future__ import annotations
from pathlib import Path
import shutil
from importlib.resources import files as resource_files
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.section import WD_SECTION_START
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from wordassistant.profiles.loader import DocumentProfile, Variant

def _add_page_number_field(paragraph):
    p = paragraph._p
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), 'PAGE')
    p.append(fldSimple)

def _add_toc_field(paragraph):
    p = paragraph._p
    r1 = OxmlElement('w:r')
    fld1 = OxmlElement('w:fldChar')
    fld1.set(qn('w:fldCharType'), 'begin')
    r1.append(fld1)
    p.append(r1)
    
    r2 = OxmlElement('w:r')
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = 'TOC \\o "1-3" \\h \\z \\u'
    r2.append(instr)
    p.append(r2)
    
    r3 = OxmlElement('w:r')
    fld2 = OxmlElement('w:fldChar')
    fld2.set(qn('w:fldCharType'), 'separate')
    r3.append(fld2)
    p.append(r3)
    
    r4 = OxmlElement('w:r')
    fld3 = OxmlElement('w:fldChar')
    fld3.set(qn('w:fldCharType'), 'end')
    r4.append(fld3)
    p.append(r4)

def _set_section_page_restart(section, start_num: int = 1):
    sectPr = section._sectPr
    pgNumType = OxmlElement('w:pgNumType')
    pgNumType.set(qn('w:start'), str(start_num))
    sectPr.append(pgNumType)

def _apply_section_page(section, v: Variant):
    section.page_width = Cm(v.page.width_cm)
    section.page_height = Cm(v.page.height_cm)
    section.top_margin = Cm(v.page.margins.top_cm)
    section.bottom_margin = Cm(v.page.margins.bottom_cm)
    section.left_margin = Cm(v.page.margins.left_cm)
    section.right_margin = Cm(v.page.margins.right_cm)

def _apply_styles(d: Document, v: Variant):
    normal = d.styles['Normal']
    normal.font.name = v.typography.body_font
    normal.font.size = Pt(v.typography.body_size_pt)
    if hasattr(normal._element, 'rPr') and normal._element.rPr is not None:
        normal._element.rPr.get_or_add_rFonts().set(qn('w:eastAsia'), v.typography.body_font)
    
    pf = normal.paragraph_format
    if v.typography.line_spacing is not None:
        pf.line_spacing = v.typography.line_spacing
    if v.typography.paragraph_spacing_before_pt is not None:
        pf.space_before = Pt(v.typography.paragraph_spacing_before_pt)
    if v.typography.paragraph_spacing_after_pt is not None:
        pf.space_after = Pt(v.typography.paragraph_spacing_after_pt)
        
    for key, stylename in [('title', 'Title'), ('heading1', 'Heading 1'), ('heading2', 'Heading 2'), ('heading3', 'Heading 3')]:
        spec = v.typography.styles.get(key)
        if not spec or stylename not in d.styles:
            continue
        st = d.styles[stylename]
        st.font.name = v.typography.body_font
        if hasattr(st._element, 'rPr') and st._element.rPr is not None:
            st._element.rPr.get_or_add_rFonts().set(qn('w:eastAsia'), v.typography.body_font)
        if 'size_pt' in spec:
            st.font.size = Pt(float(spec['size_pt']))
        if 'bold' in spec:
            st.font.bold = bool(spec['bold'])
        if 'italic' in spec:
            st.font.italic = bool(spec['italic'])

_DEFAULT_FRONT_TITLES = {
    'cover': 'COVER PAGE',
    'inner_cover': 'INNER COVER',
    'acknowledgements': 'ACKNOWLEDGEMENTS',
    'declaration': 'DECLARATION',
    'supervisor_review': 'SUPERVISOR REVIEW',
    'reviewer_review': 'REVIEWER REVIEW',
    'work_schedule': 'WORK SCHEDULE',
    'abstract': 'ABSTRACT',
    'table_of_contents': 'TABLE OF CONTENTS',
    'list_of_figures': 'LIST OF FIGURES',
    'list_of_tables': 'LIST OF TABLES',
    'abbreviations': 'ABBREVIATIONS',
    'proposal_cover': 'PROPOSAL COVER',
    'proposal_title_page': 'PROPOSAL TITLE PAGE'
}

def _render_cover_page(d: Document, v: Variant, title: str, student: str, supervisor: str):
    cover_spec = v.cover
    inst_lines = cover_spec.get('institution_lines', [])
    if inst_lines:
        p_inst = d.add_paragraph()
        p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_inst = p_inst.add_run('\n'.join(inst_lines))
        r_inst.bold = True
        r_inst.font.size = Pt(14)
        
    d.add_paragraph('\n\n')
    
    doc_type = cover_spec.get('document_type', '')
    title_prefix = cover_spec.get('title_prefix', '')
    
    p_title = d.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if doc_type:
        r_type = p_title.add_run(f"{doc_type}\n\n")
        r_type.bold = True
        r_type.font.size = Pt(16)
        
    title_text = f"{title_prefix}\n{title.upper()}\n\n" if title_prefix else f"{title.upper()}\n\n"
    r_t = p_title.add_run(title_text)
    r_t.bold = True
    r_t.font.size = Pt(18)
    
    meta_fields = cover_spec.get('metadata_fields', [])
    if meta_fields:
        p_meta = d.add_paragraph()
        p_meta.paragraph_format.left_indent = Cm(3.0)
        for mf in meta_fields:
            lbl = mf.get('label', '')
            val_key = mf.get('value_key')
            val = mf.get('value')
            default_val = mf.get('default', '')
            if val_key == 'student':
                res_val = student or default_val
            elif val_key == 'supervisor':
                res_val = supervisor or default_val
            else:
                res_val = val or default_val
            p_meta.add_run(f"{lbl}:\t{res_val}\n")
    elif student or supervisor:
        p_meta = d.add_paragraph()
        p_meta.paragraph_format.left_indent = Cm(3.0)
        if student:
            p_meta.add_run(f"Author:\t{student}\n")
        if supervisor:
            p_meta.add_run(f"Supervisor:\t{supervisor}\n")
            
    loc_year = cover_spec.get('location_year', '')
    if loc_year:
        p_bottom = d.add_paragraph(f"\n\n\n{loc_year}")
        p_bottom.alignment = WD_ALIGN_PARAGRAPH.CENTER

def scaffold_document(
    output: str | Path,
    profile: DocumentProfile,
    variant_name: str,
    *,
    title: str | None = None,
    student: str = '',
    supervisor: str = ''
) -> Path:
    v = profile.variant(variant_name)
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    
    # Template asset clone path (e.g. for official proposal template)
    if v.template_asset:
        root = Path(__file__).resolve().parents[3]
        asset = root / v.template_asset
        if not asset.exists():
            rel = v.template_asset.split('use_cases/', 1)[-1]
            asset = Path(str(resource_files('wordassistant').joinpath('data', 'use_cases', rel)))
        if asset.exists():
            shutil.copy2(asset, out)
            # If user explicitly supplied metadata, replace placeholders in cloned doc
            if title is not None or student or supervisor:
                _fill_template_metadata(out, title=title or '', student=student, supervisor=supervisor)
            return out
            
    effective_title = title if title is not None else 'UNTITLED DOCUMENT'
    d = Document()
    _apply_section_page(d.sections[0], v)
    _apply_styles(d, v)
    
    # 1. Front matter & Covers
    has_covers = any(x in v.front_matter for x in ('cover', 'inner_cover', 'proposal_cover'))
    non_cover_front = [x for x in v.front_matter if x not in ('cover', 'inner_cover', 'proposal_cover')]
    
    if has_covers:
        _render_cover_page(d, v, effective_title, student, supervisor)
        if 'inner_cover' in v.front_matter:
            d.add_page_break()
            _render_cover_page(d, v, effective_title, student, supervisor)
            
    if non_cover_front:
        front_sec = d.add_section(WD_SECTION_START.NEW_PAGE)
        _apply_section_page(front_sec, v)
        front_sec.header.is_linked_to_previous = False
        front_sec.footer.is_linked_to_previous = False
        
        for idx, item in enumerate(non_cover_front):
            title_text = v.front_matter_titles.get(item, _DEFAULT_FRONT_TITLES.get(item, item.replace('_', ' ').upper()))
            h = d.add_heading(title_text, level=1)
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            if item == 'table_of_contents':
                p_toc = d.add_paragraph()
                _add_toc_field(p_toc)
            elif item == 'list_of_figures':
                d.add_paragraph("[List of figures]")
            elif item == 'list_of_tables':
                d.add_paragraph("[List of tables]")
            else:
                d.add_paragraph("[Front matter content]")
                
            if idx < len(non_cover_front) - 1:
                d.add_page_break()
                
    # 2. Main Body Section
    if v.section_blueprint:
        body_sec = d.add_section(WD_SECTION_START.NEW_PAGE)
        _apply_section_page(body_sec, v)
        body_sec.header.is_linked_to_previous = False
        body_sec.footer.is_linked_to_previous = False
        
        # Calculate usable text width for right-aligned tab stop
        usable_width_cm = max(5.0, v.page.width_cm - v.page.margins.left_cm - v.page.margins.right_cm)
        
        hf = v.header_footer
        if hf:
            # Header
            hp = body_sec.header.paragraphs[0]
            header_l = effective_title if hf.get('header_left') == 'topic' else (supervisor if hf.get('header_left') == 'supervisor' else '')
            header_r = f"GVHD: {supervisor}" if (hf.get('header_right') == 'supervisor' and supervisor) else (effective_title if hf.get('header_right') == 'topic' else '')
            if header_l or header_r:
                hp.text = f"{header_l}\t{header_r}".strip()
                hp.paragraph_format.tab_stops.add_tab_stop(Cm(usable_width_cm), WD_TAB_ALIGNMENT.RIGHT)
                
            # Footer
            fp = body_sec.footer.paragraphs[0]
            foot_l = student if hf.get('footer_left') == 'student' else ''
            fp.text = f"{foot_l}\t" if foot_l else "\t"
            fp.paragraph_format.tab_stops.add_tab_stop(Cm(usable_width_cm), WD_TAB_ALIGNMENT.RIGHT)
            if hf.get('footer_right') == 'page_number':
                _add_page_number_field(fp)
                
            if hf.get('page_number_start') in ('introduction', '1', 1):
                _set_section_page_restart(body_sec, 1)
                
        for sec in v.section_blueprint:
            sec_title = str(sec['title'])
            sec_level = max(1, min(9, int(sec.get('level', 1))))
            d.add_heading(sec_title, level=sec_level)
            d.add_paragraph("[Section content...]")
            
    elif not has_covers:
        p = d.add_paragraph()
        p.style = 'Title'
        p.add_run(effective_title)
        d.add_paragraph("[Document content]")
        
    d.save(out)
    return out

def _fill_template_metadata(doc_path: Path, title: str, student: str, supervisor: str):
    from wordassistant.document.edit import replace_text
    unresolved = []
    
    if title:
        count = 0
        for old_pat in ('<TÊN ĐỀ TÀI>', '[TÊN ĐỀ TÀI]', 'TÊN ĐỀ TÀI', '<ĐỀ TÀI>', '[ĐỀ TÀI]'):
            res = replace_text(doc_path, old=old_pat, new=title, output_path=doc_path)
            count += res.replacements
        if count == 0:
            unresolved.append('title')
            
    if student:
        count = 0
        for old_pat in ('<TÊN SINH VIÊN>', '<SINH VIÊN>', '[Họ và tên sinh viên]', '[SINH VIÊN]', 'Tên sinh viên'):
            res = replace_text(doc_path, old=old_pat, new=student, output_path=doc_path)
            count += res.replacements
        if count == 0:
            unresolved.append('student')
            
    if supervisor:
        count = 0
        for old_pat in ('Học vị. Tên giảng viên hướng dẫn', 'Tên giảng viên hướng dẫn', '<CÁN BỘ HƯỚNG DẪN>', '<GIẢNG VIÊN HƯỚNG DẪN>', '<GIẢNG VIÊN>', '[Họ và tên GVHD]', '[CÁN BỘ HƯỚNG DẪN]'):
            res = replace_text(doc_path, old=old_pat, new=supervisor, output_path=doc_path)
            count += res.replacements
        if count == 0:
            unresolved.append('supervisor')
            
    if unresolved:
        raise ValueError(f"Could not resolve template placeholder(s) for explicitly provided metadata: {', '.join(unresolved)}")
