from __future__ import annotations
from pathlib import Path
import shutil
import tempfile
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
    try:
        normal = d.styles['Normal']
        normal.font.name = v.typography.body_font
        normal.font.size = Pt(v.typography.body_size_pt)
        if v.typography.line_spacing is not None:
            normal.paragraph_format.line_spacing = v.typography.line_spacing
    except Exception:
        pass
        
    for s_name, s_spec in v.typography.styles.items():
        try:
            style_obj = None
            if s_name == 'title':
                style_obj = d.styles['Title']
            elif s_name == 'heading1':
                style_obj = d.styles['Heading 1']
            elif s_name == 'heading2':
                style_obj = d.styles['Heading 2']
            elif s_name == 'heading3':
                style_obj = d.styles['Heading 3']
                
            if style_obj:
                if 'font' in s_spec:
                    style_obj.font.name = s_spec['font']
                else:
                    style_obj.font.name = v.typography.body_font
                    
                if 'size_pt' in s_spec:
                    style_obj.font.size = Pt(s_spec['size_pt'])
                if 'bold' in s_spec:
                    style_obj.font.bold = s_spec['bold']
                if 'italic' in s_spec:
                    style_obj.font.italic = s_spec['italic']
                if 'alignment' in s_spec:
                    align_map = {
                        'left': WD_ALIGN_PARAGRAPH.LEFT,
                        'center': WD_ALIGN_PARAGRAPH.CENTER,
                        'right': WD_ALIGN_PARAGRAPH.RIGHT,
                        'justify': WD_ALIGN_PARAGRAPH.JUSTIFY
                    }
                    if s_spec['alignment'] in align_map:
                        style_obj.paragraph_format.alignment = align_map[s_spec['alignment']]
        except Exception:
            pass

_DEFAULT_FRONT_TITLES = {
    'acknowledgements': 'ACKNOWLEDGEMENTS',
    'declaration': 'DECLARATION',
    'supervisor_review': 'SUPERVISOR REVIEW',
    'reviewer_review': 'REVIEWER REVIEW',
    'work_schedule': 'WORK SCHEDULE',
    'abstract': 'ABSTRACT',
    'table_of_contents': 'TABLE OF CONTENTS',
    'list_of_figures': 'LIST OF FIGURES',
    'list_of_tables': 'LIST OF TABLES',
    'abbreviations': 'ABBREVIATIONS'
}

def _render_cover_page(d: Document, v: Variant, title_text: str, student: str, supervisor: str):
    cover_spec = v.cover
    inst_lines = cover_spec.get('institution_lines', [])
    for line in inst_lines:
        p_top = d.add_paragraph()
        p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p_top.add_run(line)
        r.bold = True
        r.font.size = Pt(13)
        
    doc_type = cover_spec.get('document_type', '')
    if doc_type:
        p_dt = d.add_paragraph(f"\n\n{doc_type}")
        p_dt.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if p_dt.runs:
            p_dt.runs[0].bold = True
            p_dt.runs[0].font.size = Pt(16)
            
    prefix = cover_spec.get('title_prefix', '')
    p_title = d.add_paragraph("\n\n")
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if prefix:
        r_pre = p_title.add_run(f"{prefix}\n")
        r_pre.bold = True
        r_pre.font.size = Pt(14)
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
    student: str | None = None,
    supervisor: str | None = None,
    dry_run: bool = False
) -> Path:
    v = profile.variant(variant_name)
    out = Path(output)
    if not dry_run:
        out.parent.mkdir(parents=True, exist_ok=True)
        
    eff_student = student or ''
    eff_supervisor = supervisor or ''
    
    # Template asset clone path (e.g. for official proposal template)
    if v.template_asset:
        root = Path(__file__).resolve().parents[3]
        asset = root / v.template_asset
        if not asset.exists():
            rel = v.template_asset.split('use_cases/', 1)[-1]
            asset = Path(str(resource_files('wordassistant').joinpath('data', 'use_cases', rel)))
        if asset.exists():
            if not dry_run:
                shutil.copy2(asset, out)
                if title is not None or eff_student or eff_supervisor:
                    _fill_template_metadata(out, title=title or '', student=eff_student, supervisor=eff_supervisor)
            return out
            
    effective_title = title if title is not None else 'UNTITLED DOCUMENT'
    d = Document()
    _apply_section_page(d.sections[0], v)
    _apply_styles(d, v)
    
    # 1. Front matter & Covers
    has_covers = any(x in v.front_matter for x in ('cover', 'inner_cover', 'proposal_cover'))
    non_cover_front = [x for x in v.front_matter if x not in ('cover', 'inner_cover', 'proposal_cover')]
    
    if has_covers:
        _render_cover_page(d, v, effective_title, eff_student, eff_supervisor)
        if 'inner_cover' in v.front_matter:
            d.add_page_break()
            _render_cover_page(d, v, effective_title, eff_student, eff_supervisor)
            
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
        
        usable_width_cm = max(5.0, v.page.width_cm - v.page.margins.left_cm - v.page.margins.right_cm)
        
        hf = v.header_footer
        if hf:
            hp = body_sec.header.paragraphs[0]
            header_l = effective_title if hf.get('header_left') == 'topic' else (eff_supervisor if hf.get('header_left') == 'supervisor' else '')
            header_r = f"GVHD: {eff_supervisor}" if (hf.get('header_right') == 'supervisor' and eff_supervisor) else (effective_title if hf.get('header_right') == 'topic' else '')
            if header_l or header_r:
                hp.text = f"{header_l}\t{header_r}".strip()
                hp.paragraph_format.tab_stops.add_tab_stop(Cm(usable_width_cm), WD_TAB_ALIGNMENT.RIGHT)
                
            fp = body_sec.footer.paragraphs[0]
            foot_l = eff_student if hf.get('footer_left') == 'student' else ''
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
        
    if not dry_run:
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
