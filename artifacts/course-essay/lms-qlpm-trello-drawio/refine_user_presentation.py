"""Bound presentation refinements; preserve embedded screenshot bytes and fields."""
from pathlib import Path
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH as A
import hashlib,json
R=Path(__file__).resolve().parent
d=Document(R/'output/user-correction-prefields.docx')
renames={
'Business case và mục tiêu':'Cơ sở đề xuất và mục tiêu dự án',
'Sổ stakeholder':'Các bên liên quan và phương án tham gia',
'RACI và escalation':'Phân công trách nhiệm và xử lý vượt thẩm quyền',
'Ranh giới và acceptance':'Ranh giới phạm vi và điều kiện chấp nhận',
'Work breakdown':'Phân rã công việc theo sản phẩm bàn giao',
'Resource breakdown':'Phân bổ nguồn lực theo vai trò',
'Gate và DoD':'Cổng chất lượng và điều kiện hoàn tất',
'UAT và triage':'Kiểm thử chấp nhận và phân loại lỗi',
'Luồng board và quy ước':'Luồng công việc và quy ước sử dụng Trello',
'Lessons learned và hướng phát triển':'Bài học kinh nghiệm và hướng phát triển'}
for p in d.paragraphs:
    if p.style.name.startswith('Heading ') and p.text in renames:
        text=renames[p.text];p.clear();p.add_run(text)
summary=next(p for p in d.paragraphs if p.text.startswith('Báo cáo trình bày kế hoạch quản lý cho dự án học thuật'))
summary.text='Bài tiểu luận phân tích kế hoạch quản lý dự án xây dựng hệ thống quản lý học tập (Learning Management System, LMS) cho bối cảnh đại học. Nội dung làm rõ mối liên hệ giữa mục tiêu, phạm vi, phân công trách nhiệm, tiến độ, ngân sách, rủi ro và điều kiện nghiệm thu. Trello được sử dụng để theo dõi công việc; Draw.io biểu diễn cấu trúc và quy tắc nghiệp vụ của sản phẩm.'

for i,p in enumerate(d.paragraphs):
    if p.style.name=='Caption' and any(key in p.text for key in ['Mô tả và checklist của thẻ WBS','Thẻ nghiệm thu được ghi rõ là mô phỏng']):
        prev=p._p.getprevious()
        shape=prev.xpath('.//wp:inline')[0]
        fill=shape.xpath('.//pic:blipFill')[0]
        sr=OxmlElement('a:srcRect')
        for k,v in dict(l='31563',r='31563',t='4800',b='14800').items():sr.set(k,v)
        stretch=fill.find(qn('a:stretch'))
        fill.insert(list(fill).index(stretch),sr)
        width=Cm(11.5);height=int(width*804/590)
        extent=shape.find(qn('wp:extent'));extent.set('cx',str(width));extent.set('cy',str(height))
        for ext in shape.xpath('.//a:xfrm/a:ext'):ext.set('cx',str(width));ext.set('cy',str(height))
        shape.docPr.set('descr','Vùng hộp thoại từ ảnh chụp toàn cảnh gốc, chỉ cắt bố cục trong Word; không chỉnh sửa nội dung ảnh. Ảnh toàn cảnh được giữ trong thư mục captures.')

# Header follows the borrowed presentation rule; absent supervisor/student names stay absent.
seen=set()
for i,sec in enumerate(d.sections):
    if i<2:continue
    header=sec.header
    if id(header._element) in seen:continue
    seen.add(id(header._element))
    p=header.paragraphs[0];p.clear();p.add_run('Quản lý dự án xây dựng hệ thống LMS')
    p.alignment=A.LEFT;p.paragraph_format.line_spacing=1
    for run in p.runs:run.font.name='Times New Roman';run.font.size=Pt(13);run.font.color.rgb=RGBColor(0,0,0)

# Abbreviations are explained where used; a compact front-matter glossary aids readers.
intro=next(p for p in d.paragraphs if p.text=='MỞ ĐẦU' and p.style.name=='Heading 1')
gloss=d.add_paragraph('DANH MỤC TỪ VIẾT TẮT',style='Heading 1');gloss.paragraph_format.page_break_before=True
intro._p.addprevious(gloss._p)
for text in [
'API: Giao diện lập trình ứng dụng.',
'CPM: Phương pháp đường găng trong lập kế hoạch tiến độ.',
'CR: Đề nghị thay đổi phạm vi hoặc đường cơ sở.',
'EVM: Phương pháp theo dõi giá trị đạt được; các số liệu trong bài là ví dụ giả định.',
'FTE: Nhân sự toàn thời gian quy đổi theo khối lượng lao động.',
'LMS: Hệ thống quản lý học tập.',
'PM: Người quản lý dự án; BA: người phân tích nghiệp vụ; QA: bảo đảm chất lượng.',
'RACI: Ma trận người thực hiện, người chịu trách nhiệm cuối cùng, người được tham vấn và người được thông báo.',
'RBAC: Kiểm soát truy cập theo vai trò.',
'UAT: Kiểm thử chấp nhận người dùng.',
'WBS: Cấu trúc phân chia công việc theo sản phẩm bàn giao.'
]:
    p=d.add_paragraph(text);intro._p.addprevious(p._p)
intro.paragraph_format.page_break_before=True

out=R/'output/user-correction-refined.docx';d.save(out)
(R/'qa/presentation-refinements.json').write_text(json.dumps({'input':'output/user-correction-prefields.docx','output':str(out),'heading_renames':renames,'screenshot_crop':'Word layout only; all original image bytes retained','source_images_unchanged':True},ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved reviewed heading terminology, glossary, headers and two readable screenshot crops.')
