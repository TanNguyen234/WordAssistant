from __future__ import annotations
from pathlib import Path
import shutil
from importlib.resources import files as resource_files
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from wordassistant.profiles.loader import DocumentProfile

def scaffold_document(output:str|Path, profile:DocumentProfile, variant_name:str, *, title:str='UNTITLED DOCUMENT', student:str='', supervisor:str='')->Path:
    v=profile.variant(variant_name); out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    # For an official proposal template, preserve the supplied source layout exactly.
    if v.template_asset:
        root=Path(__file__).resolve().parents[3]
        asset=root/v.template_asset
        if not asset.exists():
            rel=v.template_asset.split('use_cases/',1)[-1]
            asset=Path(str(resource_files('wordassistant').joinpath('data','use_cases',rel)))
        if asset.exists(): shutil.copy2(asset,out); return out
    d=Document(); _apply_page(d,v); _apply_styles(d,v)
    p=d.add_paragraph(); p.style='Title'; p.add_run(title)
    if profile.profile_id.startswith('hcmunre') and variant_name=='report':
        p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run('TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP.HCM').bold=True
        p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run('KHOA CÔNG NGHỆ THÔNG TIN').bold=True
        if student: d.add_paragraph(f'Sinh viên thực hiện: {student}')
        if supervisor: d.add_paragraph(f'Giảng viên hướng dẫn: {supervisor}')
        d.add_page_break()
    for item in v.front_matter:
        d.add_heading(_front_title(item),level=1); d.add_paragraph('[Điền nội dung theo yêu cầu]'); d.add_page_break()
    for sec in v.section_blueprint:
        d.add_heading(str(sec['title']),level=max(1,min(9,int(sec.get('level',1))))); d.add_paragraph('[Nội dung]')
    d.save(out); return out

def _apply_page(d,v):
    for s in d.sections:
        s.page_width=Cm(v.page.width_cm); s.page_height=Cm(v.page.height_cm)
        s.top_margin=Cm(v.page.margins.top_cm); s.bottom_margin=Cm(v.page.margins.bottom_cm); s.left_margin=Cm(v.page.margins.left_cm); s.right_margin=Cm(v.page.margins.right_cm)

def _apply_styles(d,v):
    normal=d.styles['Normal']; normal.font.name=v.typography.body_font; normal.font.size=Pt(v.typography.body_size_pt)
    normal._element.rPr.rFonts.set(qn('w:eastAsia'),v.typography.body_font)
    pf=normal.paragraph_format
    if v.typography.line_spacing: pf.line_spacing=v.typography.line_spacing
    for key,stylename in [('title','Title'),('heading1','Heading 1'),('heading2','Heading 2'),('heading3','Heading 3')]:
        spec=v.typography.styles.get(key)
        if not spec: continue
        st=d.styles[stylename]; st.font.name=v.typography.body_font; st._element.rPr.rFonts.set(qn('w:eastAsia'),v.typography.body_font)
        if 'size_pt' in spec: st.font.size=Pt(float(spec['size_pt']))
        if 'bold' in spec: st.font.bold=bool(spec['bold'])

def _front_title(x):
    return {'cover':'TRANG BÌA','inner_cover':'TRANG BÌA TRONG','acknowledgements':'LỜI CẢM ƠN','declaration':'LỜI CAM ĐOAN','supervisor_review':'NHẬN XÉT CỦA GIẢNG VIÊN HƯỚNG DẪN','reviewer_review':'NHẬN XÉT CỦA NGƯỜI PHẢN BIỆN','work_schedule':'LỊCH LÀM VIỆC','abstract':'TÓM TẮT','table_of_contents':'MỤC LỤC','list_of_figures':'DANH MỤC SƠ ĐỒ, HÌNH','list_of_tables':'DANH MỤC BẢNG','abbreviations':'KÍ HIỆU CÁC CỤM TỪ VIẾT TẮT'}.get(x,x.replace('_',' ').upper())
