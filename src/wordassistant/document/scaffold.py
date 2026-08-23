from __future__ import annotations
from pathlib import Path
import shutil
from importlib.resources import files as resource_files
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from wordassistant.profiles.loader import DocumentProfile, Variant

def _add_page_number_field(run):
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), 'PAGE')
    run._r.append(fldSimple)

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

_FRONT_TITLES = {
    'cover': 'TRANG BÌA',
    'inner_cover': 'TRANG BÌA TRONG',
    'acknowledgements': 'LỜI CẢM ƠN',
    'declaration': 'LỜI CAM ĐOAN',
    'supervisor_review': 'NHẬN XÉT CỦA GIẢNG VIÊN HƯỚNG DẪN',
    'reviewer_review': 'NHẬN XÉT CỦA NGƯỜI PHẢN BIỆN',
    'work_schedule': 'LỊCH LÀM VIỆC',
    'abstract': 'TÓM TẮT',
    'table_of_contents': 'MỤC LỤC',
    'list_of_figures': 'DANH MỤC SƠ ĐỒ, HÌNH',
    'list_of_tables': 'DANH MỤC BẢNG',
    'abbreviations': 'KÍ HIỆU CÁC CỤM TỪ VIẾT TẮT',
    'proposal_cover': 'BÌA ĐỀ CƯƠNG',
    'proposal_title_page': 'TRANG THÔNG TIN ĐỀ CƯƠNG'
}

def scaffold_document(
    output: str | Path,
    profile: DocumentProfile,
    variant_name: str,
    *,
    title: str = 'UNTITLED DOCUMENT',
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
            # If user supplied metadata for template, replace placeholders in cloned doc
            if title or student or supervisor:
                _fill_template_metadata(out, title=title, student=student, supervisor=supervisor)
            return out
            
    d = Document()
    _apply_section_page(d.sections[0], v)
    _apply_styles(d, v)
    
    # 1. Front matter & Covers
    has_covers = any(x in v.front_matter for x in ('cover', 'inner_cover', 'proposal_cover'))
    non_cover_front = [x for x in v.front_matter if x not in ('cover', 'inner_cover', 'proposal_cover')]
    
    if has_covers:
        # Cover Section
        p = d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run("TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP.HCM\nKHOA CÔNG NGHỆ THÔNG TIN")
        r.bold = True
        r.font.size = Pt(14)
        
        p_spacer = d.add_paragraph("\n\n")
        
        p_title = d.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_type = p_title.add_run("BÁO CÁO ĐỒ ÁN CHUYÊN NGÀNH\n\n")
        r_type.bold = True
        r_type.font.size = Pt(16)
        
        r_t = p_title.add_run(f"ĐỀ TÀI:\n{title.upper()}\n\n")
        r_t.bold = True
        r_t.font.size = Pt(18)
        
        p_meta = d.add_paragraph()
        p_meta.paragraph_format.left_indent = Cm(3.0)
        p_meta.add_run(f"Sinh viên thực hiện:\t{student or '[Họ và tên sinh viên - MSSV]'}\n")
        p_meta.add_run(f"Giảng viên hướng dẫn:\t{supervisor or '[Họ và tên CBHD]'}\n")
        p_meta.add_run("Khóa học:\t\t2023 - 2027\n")
        p_meta.add_run("Ngành:\t\t\tCông nghệ thông tin\n")
        
        p_bottom = d.add_paragraph("\n\n\nTP. HỒ CHÍ MINH, 2027")
        p_bottom.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        if 'inner_cover' in v.front_matter:
            d.add_page_break()
            # Inner cover page
            p_in = d.add_paragraph()
            p_in.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_in = p_in.add_run("TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP.HCM\nKHOA CÔNG NGHỆ THÔNG TIN")
            r_in.bold = True
            r_in.font.size = Pt(14)
            
            p_in_title = d.add_paragraph("\n\n")
            p_in_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_in_t = p_in_title.add_run(f"ĐỀ TÀI:\n{title.upper()}\n\n")
            r_in_t.bold = True
            r_in_t.font.size = Pt(18)
            
            p_in_meta = d.add_paragraph()
            p_in_meta.paragraph_format.left_indent = Cm(3.0)
            p_in_meta.add_run(f"Sinh viên thực hiện:\t{student or '[Họ và tên sinh viên - MSSV]'}\n")
            p_in_meta.add_run(f"Giảng viên hướng dẫn:\t{supervisor or '[Họ và tên CBHD]'}\n")
            
            p_in_bot = d.add_paragraph("\n\n\nTP. HỒ CHÍ MINH, 2027")
            p_in_bot.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
    if non_cover_front:
        # Create Front Matter Section
        front_sec = d.add_section(WD_SECTION_START.NEW_PAGE)
        _apply_section_page(front_sec, v)
        front_sec.header.is_linked_to_previous = False
        front_sec.footer.is_linked_to_previous = False
        
        for idx, item in enumerate(non_cover_front):
            title_text = _FRONT_TITLES.get(item, item.replace('_', ' ').upper())
            h = d.add_heading(title_text, level=1)
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            if item == 'table_of_contents':
                p_toc = d.add_paragraph()
                _add_toc_field(p_toc)
            elif item == 'list_of_figures':
                p_lof = d.add_paragraph("[Danh mục hình vẽ tự động]")
            elif item == 'list_of_tables':
                p_lot = d.add_paragraph("[Danh mục bảng biểu tự động]")
            else:
                d.add_paragraph("[Nội dung phần đầu theo quy định]")
                
            if idx < len(non_cover_front) - 1:
                d.add_page_break()
                
    # 2. Main Body Section
    if v.section_blueprint:
        body_sec = d.add_section(WD_SECTION_START.NEW_PAGE)
        _apply_section_page(body_sec, v)
        body_sec.header.is_linked_to_previous = False
        body_sec.footer.is_linked_to_previous = False
        
        # Configure Header & Footer
        hf = v.header_footer
        if hf:
            # Header
            hp = body_sec.header.paragraphs[0]
            header_l = title if hf.get('header_left') == 'topic' else (supervisor if hf.get('header_left') == 'supervisor' else '')
            header_r = f"GVHD: {supervisor}" if hf.get('header_right') == 'supervisor' else (title if hf.get('header_right') == 'topic' else '')
            if header_l or header_r:
                hp.text = f"{header_l}\t{header_r}".strip()
                hp.paragraph_format.tab_stops.add_tab_stop(Cm(16.0))
                
            # Footer
            fp = body_sec.footer.paragraphs[0]
            foot_l = student if hf.get('footer_left') == 'student' else ''
            fp.text = f"{foot_l}\t" if foot_l else "\t"
            fp.paragraph_format.tab_stops.add_tab_stop(Cm(16.0))
            if hf.get('footer_right') == 'page_number':
                r_num = fp.add_run()
                _add_page_number_field(r_num)
                
            if hf.get('page_number_start') in ('introduction', '1', 1):
                _set_section_page_restart(body_sec, 1)
                
        for sec in v.section_blueprint:
            sec_title = str(sec['title'])
            sec_level = max(1, min(9, int(sec.get('level', 1))))
            d.add_heading(sec_title, level=sec_level)
            d.add_paragraph("[Nội dung chi tiết của phần này...]")
            
    elif not has_covers:
        # Fallback generic single section document
        p = d.add_paragraph()
        p.style = 'Title'
        p.add_run(title)
        d.add_paragraph("[Nội dung văn bản]")
        
    d.save(out)
    return out

def _fill_template_metadata(doc_path: Path, title: str, student: str, supervisor: str):
    from wordassistant.document.edit import replace_text
    try:
        if title:
            for old_pat in ('<TÊN ĐỀ TÀI>', '[TÊN ĐỀ TÀI]', 'TÊN ĐỀ TÀI', '<ĐỀ TÀI>', '[ĐỀ TÀI]'):
                replace_text(doc_path, old=old_pat, new=title, output_path=doc_path)
        if student:
            for old_pat in ('<TÊN SINH VIÊN>', '<SINH VIÊN>', '[Họ và tên sinh viên]', '[SINH VIÊN]'):
                replace_text(doc_path, old=old_pat, new=student, output_path=doc_path)
        if supervisor:
            for old_pat in ('<CÁN BỘ HƯỚNG DẪN>', '<GIẢNG VIÊN HƯỚNG DẪN>', '<GIẢNG VIÊN>', '[Họ và tên GVHD]', '[CÁN BỘ HƯỚNG DẪN]'):
                replace_text(doc_path, old=old_pat, new=supervisor, output_path=doc_path)
    except Exception:
        pass
