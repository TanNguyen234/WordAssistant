"""Repair observed cover/table alignment and source-note pagination defects."""
from pathlib import Path
from copy import deepcopy
from docx import Document
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH as A
from docx.shared import Pt,Cm
R=Path(__file__).resolve().parent
d=Document(R/'output/user-correction-refined.docx')
old=Document(R/'qa/final-before-user-correction-20261026.docx')
before=[]
for p in old.paragraphs:
    if p.style.name=='Heading 1':break
    before.append(p)
assert all(a.text==b.text for a,b in zip(before,d.paragraphs))
for src,dst in zip(before,d.paragraphs):
    if dst._p.pPr is not None:dst._p.remove(dst._p.pPr)
    if src._p.pPr is not None:dst._p.insert(0,deepcopy(src._p.pPr))
    for run in dst.runs:
        run.font.name='Times New Roman'
        run.font.size=Pt(18 if dst.style.name=='Title' else 16 if dst.text=='TIỂU LUẬN MÔN HỌC' else 13)
    if dst.style.name=='Title':dst.alignment=A.CENTER

for t in d.tables:
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                p.alignment=A.CENTER if p.text.replace('.','').replace(',','').replace('%','').isdigit() else A.LEFT
                p.paragraph_format.keep_with_next=False

model_headings={'Vai trò và Use Case','Luồng nộp bài','Trình tự chấm bài','Các lớp miền của bài tập','Trạng thái bài nộp'}
active='';landscape=False
for i,p in enumerate(d.paragraphs):
    if p.style.name.startswith('Heading '):active=p.text
    if i>=len(before) and not p.text and not p._p.xpath('.//w:drawing'):
        p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0)
        p.paragraph_format.line_spacing=Pt(1);p.paragraph_format.keep_with_next=False
        for r in p.runs:r.font.size=Pt(1)
    if active in model_headings and p._p.xpath('.//wp:inline'):
        wide=active in {'Vai trò và Use Case','Trình tự chấm bài','Các lớp miền của bài tập'}
        for shape in p._p.xpath('.//wp:inline'):
            ext=shape.find(qn('wp:extent'));w=int(ext.get('cx'));h=int(ext.get('cy'))
            scale=min(1,int(Cm(8 if wide else 12.2))/h,int(Cm(22 if wide else 16))/w)
            w=int(w*scale);h=int(h*scale);ext.set('cx',str(w));ext.set('cy',str(h))
            for e in shape.xpath('.//a:xfrm/a:ext'):e.set('cx',str(w));e.set('cy',str(h))
    if p.style.name=='Caption' and p.text.startswith('HÌNH'):
        p.paragraph_format.keep_with_next=True
    if p.text.startswith('Nguồn:'):
        p.alignment=A.LEFT;p.paragraph_format.keep_with_next=False
        p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(6)
        p.paragraph_format.line_spacing=1.5
    if p.text=='Closure chỉ PASS khi gate được review và người có thẩm quyền xác nhận. Thiếu bằng chứng thì ghi kế hoạch/chưa nghiệm thu.':
        p.text='Quyết định đóng dự án chỉ được xác nhận sau khi các điều kiện bàn giao được kiểm tra và người có thẩm quyền chấp thuận. Những bằng chứng còn thiếu phải được ghi thành công việc tồn đọng, có người xử lý rõ ràng.'
    if p.text=='Kiểm đủ 10 AC và Must-have, defect P0/P1, dữ liệu, hướng dẫn, known issues và tồn đọng được chấp nhận. Kịch bản chưa chạy vẫn NOT RUN.':
        p.text='Nghiệm thu cần kiểm tra đủ mười kịch bản chấp nhận, các chức năng bắt buộc, tình trạng lỗi nghiêm trọng, dữ liệu và hướng dẫn sử dụng. Những vấn đề còn mở phải được ghi nhận cùng quyết định chấp thuận hoặc yêu cầu sửa. Kịch bản chưa thực hiện vẫn giữ trạng thái chưa chạy.'
out=R/'output/user-correction-layout-checked.docx';d.save(out)
print('Restored cover layout; left-aligned table prose; kept source notes with figures; resized models to fit page.')
