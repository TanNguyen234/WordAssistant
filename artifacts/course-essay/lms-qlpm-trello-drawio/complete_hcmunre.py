"""Apply full selected HCMUNRE front matter, preserving the reviewed LMS body."""
from pathlib import Path
from copy import deepcopy
import json,hashlib
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt,Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH as A
from docx.enum.style import WD_STYLE_TYPE
from wordassistant.operations.tables import normalize_table_geometry
R=Path(__file__).resolve().parent
d=Document(R/'output/LMS_Tieu_luan_QLDA_ban_sua.docx')
sc=Document(R/'output/hcmunre-full-scaffold.docx')
guide=Document(R.parents[2]/'use_cases/hcmunre_dacn_2026_2027/assets/huong_dan_trinh_bay_dacn_2026_2027.docx')
intro=next(p for p in d.paragraphs if p.text=='MỞ ĐẦU' and p.style.name=='Heading 1')
TOPIC='Quản lý dự án xây dựng hệ thống quản lý học tập trực tuyến (LMS) cho trường đại học'
abstract=[];gloss=[];active=''
for p in d.paragraphs:
    if p==intro:break
    if p.style.name.startswith('Heading'):active=p.text
    elif active=='TÓM TẮT' and p.text:abstract.append(deepcopy(p._p))
    elif active=='DANH MỤC TỪ VIẾT TẮT' and p.text:gloss.append(p.text)
# Existing document owns citation SDTs, numbering, images and custom properties.
# Only the scaffold's front matter is copied; its temporary relationship IDs are removed.
prefix=[]
for el in sc.element.body:
    if el.tag==qn('w:p') and ''.join(el.xpath('.//w:t/text()'))=='MỞ ĐẦU':break
    prefix.append(deepcopy(el))
for el in list(d.element.body):
    if el is intro._p:break
    d.element.body.remove(el)
for el in prefix:
    for ref in el.xpath('.//w:headerReference | .//w:footerReference'):ref.getparent().remove(ref)
    intro._p.addprevious(el)
# Exact user-provided topic; add the actual bundled university logo, keeping media relations local.
for p in list(d.paragraphs):
    if 'QUẢN LÝ DỰ ÁN PHẦN MỀM XÂY DỰNG HỆ THỐNG LMS' in p.text:
        p.clear();p.alignment=A.CENTER
        r=p.add_run('ĐỀ TÀI:\n');r.bold=True;r.font.size=Pt(14)
        r=p.add_run('Quản lý dự án xây dựng hệ thống\nquản lý học tập trực tuyến (LMS)\ncho trường đại học');r.bold=True;r.font.size=Pt(18)
    if p.text=='KHOA CÔNG NGHỆ THÔNG TIN':
        logo=d.add_paragraph();logo.alignment=A.CENTER
        logo.add_run().add_picture(str(R.parents[2]/'use_cases/hcmunre_dacn_2026_2027/assets/university_logo.png'),width=Cm(2.6))
        p._p.addnext(logo._p)
for st in sc.styles.element:
    sid=st.get(qn('w:styleId'))
    if sid and sid not in [x.get(qn('w:styleId')) for x in d.styles.element]:d.styles.element.append(deepcopy(st))
for fld in d.element.xpath('//w:fldSimple'):
    instr=fld.get(qn('w:instr'),'')
    if '\\c "Table"' in instr:fld.set(qn('w:instr'),instr.replace('"Table"','"Bang"'))

def section(title):
    ps=d.paragraphs
    start=next(i for i,p in enumerate(ps) if p.text==title)
    end=next((i for i in range(start+1,len(ps)) if ps[i].style.name in {'WA Front Matter Title','Heading 1'}),len(ps))
    return ps[start],ps[start+1:end]
def insert_after(anchor,text='',style=None):
    p=d.add_paragraph(text,style);anchor.addnext(p._p);return p._p
def replace_section(title,texts):
    h,ps=section(title)
    for p in ps:
        # A section boundary must survive replacement.
        if p._p.xpath('./w:pPr/w:sectPr'):continue
        p._p.getparent().remove(p._p)
    at=h._p
    for t in texts:at=insert_after(at,t)
    return h

replace_section('LỜI CẢM ƠN',[
    'Bản tiểu luận được xây dựng từ hồ sơ dự án LMS, hướng dẫn trình bày và các tài liệu tham khảo được dẫn trong bài. Phần ghi nhận sự hỗ trợ cụ thể dành cho giảng viên, thành viên nhóm và đơn vị liên quan do sinh viên hoàn thiện trước khi nộp, theo đúng những đóng góp thực tế.',
    'Người được cảm ơn và nội dung hỗ trợ:',
    'Sinh viên thực hiện:'])
replace_section('LỜI CAM ĐOAN',[
    'Phần cam đoan dành cho sinh viên xác nhận sau khi kiểm tra toàn bộ nội dung, nguồn trích dẫn và phạm vi hỗ trợ trong quá trình biên soạn. Bản hiện tại chưa có xác nhận hoặc chữ ký của sinh viên.',
    'Công cụ hỗ trợ đã sử dụng: WordAssistant và Codex để tổng hợp hồ sơ, biên tập, định dạng và kiểm tra tài liệu. Ảnh minh chứng được chụp trực tiếp từ Trello và website LMS; dữ liệu mô phỏng, kế hoạch và kết quả quan sát được phân biệt trong bài.',
    'Nội dung cam đoan của sinh viên:',
    'Ngày xác nhận:', 'Sinh viên ký và ghi rõ họ tên:'])
criteria={}
for title,lo,hi in [('NHẬN XÉT CỦA GIẢNG VIÊN HƯỚNG DẪN',11,16),('NHẬN XÉT CỦA NGƯỜI PHẢN BIỆN',16,19)]:
    texts=[p.text for p in guide.paragraphs[lo:hi] if p.text]
    criteria[title]=texts
    replace_section(title,texts+['Nội dung nhận xét:', '', '', '', 'Ngày nhận xét:', 'Người nhận xét ký và ghi rõ họ tên:'])
    # Empty editable space is intentional; no assessment is authored on behalf of staff.
    _,ps=section(title)
    for p in ps:
        if not p.text:p.paragraph_format.space_after=Pt(24)

h,ps=section('TÓM TẮT')
for p in ps:
    if not p._p.xpath('./w:pPr/w:sectPr'):p._p.getparent().remove(p._p)
at=h._p
for el in abstract:at.addnext(el);at=el
# Full guide's glossary title and a populated editable native table.
h,ps=section('KÍ HIỆU CÁC CỤM TỪ VIẾT TẮT')
after=h._p.getnext()
if after.tag==qn('w:tbl'):
    d.element.body.remove(after)
t=d.add_table(rows=1,cols=3);t.style='Table Grid'
for c,tx in zip(t.rows[0].cells,['STT','Ký hiệu','Giải thích']):c.text=tx
for i,text in enumerate(gloss,1):
    key,_,meaning=text.partition(':');cells=t.add_row().cells
    for c,tx in zip(cells,[str(i),key,meaning.strip()]):c.text=tx
h._p.addnext(t._tbl)
# The work schedule is explicitly planned, not retroactive attendance evidence.
h,_=section('LỊCH LÀM VIỆC')
tab=h._p.getnext()
while tab is not None and tab.tag!=qn('w:tbl'):tab=tab.getnext()
if tab is not None:
    from docx.table import Table
    t=Table(tab,d._body)
    schedule=[('1','Khởi tạo, phạm vi và các bên liên quan','Tháng 10/2026'),('2','Phân rã công việc, tiến độ và ngân sách','Tháng 10/2026'),('3','Theo dõi công việc trên Trello','Tháng 10–11/2026'),('4','Mô hình hóa và đối chiếu mã nguồn','Tháng 10–11/2026'),('5','Kiểm thử chấp nhận và xử lý tồn đọng','Tháng 11/2026'),('6','Hoàn thiện báo cáo và đề nghị nghiệm thu','Cuối tháng 11/2026')]
    for row,values in zip(t.rows[1:],schedule):
        for cell,tx in zip(row.cells,(*values,'')):cell.text=tx
    p=d.add_paragraph('Lịch dự kiến theo hồ sơ kế hoạch tháng 10–11/2026; cột xác nhận để trống. Các mốc tương lai không được xem là công việc đã hoàn tất.')
    tab.addnext(p._p)

# Make the two covers separate sections so only the outer cover carries a border.
first_break=next(p for p in d.paragraphs if p._p.xpath('.//w:br[@w:type="page"]'))
base=deepcopy(d.sections[0]._sectPr)
for el in list(base):
    if el.tag in {qn('w:headerReference'),qn('w:footerReference'),qn('w:pgNumType'),qn('w:pgBorders')}:base.remove(el)
typ=base.find(qn('w:type'))
if typ is None:typ=OxmlElement('w:type');base.insert(0,typ)
typ.set(qn('w:val'),'nextPage')
border=OxmlElement('w:pgBorders');border.set(qn('w:offsetFrom'),'text')
for edge in ['top','left','bottom','right']:
    x=OxmlElement('w:'+edge)
    for k,v in {'val':'single','sz':'12','space':'18','color':'000000'}.items():x.set(qn('w:'+k),v)
    border.append(x)
source_border=next((s._sectPr.find(qn('w:pgBorders')) for s in guide.sections if s._sectPr.find(qn('w:pgBorders')) is not None),None)
base.append(deepcopy(source_border) if source_border is not None else border)
first_break.clear();first_break._p.get_or_add_pPr().append(base)
for i,sec in enumerate(d.sections):
    if i<3:
        sec.header.is_linked_to_previous=False;sec.footer.is_linked_to_previous=False
        for part in [sec.header,sec.footer]:
            for p in part.paragraphs:p.clear()
        num=sec._sectPr.find(qn('w:pgNumType'))
        if num is not None:sec._sectPr.remove(num)
        if i>0:
            b=sec._sectPr.find(qn('w:pgBorders'))
            if b is not None:sec._sectPr.remove(b)
    else:
        # Original body section boundaries and landscape pages are retained.
        sec.header.is_linked_to_previous=False
        hp=sec.header.paragraphs[0];hp.text='Quản lý dự án xây dựng hệ thống quản lý học tập\ntrực tuyến (LMS) cho trường đại học\tGVHD:'
        hp.paragraph_format.tab_stops.clear_all()
        hp.paragraph_format.tab_stops.add_tab_stop(Cm(16 if sec.page_width<sec.page_height else 24.7),2)
        hp.alignment=A.LEFT
        hp.paragraph_format.line_spacing=1
        hp.paragraph_format.space_before=Pt(0);hp.paragraph_format.space_after=Pt(0)
        sec.header_distance=Cm(.3)
        for run in hp.runs:run.font.name='Times New Roman';run.font.size=Pt(13)
intro.paragraph_format.page_break_before=False

# Repair observed table pagination; retain native headers and editable cells.
for t in d.tables:
    if t is d.tables[0] or t is d.tables[1]:pass
    for ri,row in enumerate(t.rows):
        for cell in row.cells:
            tcpr=cell._tc.get_or_add_tcPr();m=tcpr.find(qn('w:tcMar'))
            if m is None:m=OxmlElement('w:tcMar');tcpr.append(m)
            for edge in ['top','bottom']:
                e=m.find(qn('w:'+edge))
                if e is None:e=OxmlElement('w:'+edge);m.append(e)
                e.set(qn('w:w'),'60');e.set(qn('w:type'),'dxa')
            for p in cell.paragraphs:
                p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0)
                p.paragraph_format.line_spacing=1.15
                p.paragraph_format.keep_with_next=ri in {0,len(t.rows)-1}
                p.alignment=A.LEFT
                if p.text=='Lệch WBS/CPM/budget':p.text='Lệch WBS, CPM hoặc ngân sách'
                for run in p.runs:run.font.name='Times New Roman';run.font.size=Pt(13)
        if ri==0:
            pr=row._tr.get_or_add_trPr()
            if pr.find(qn('w:tblHeader')) is None:pr.append(OxmlElement('w:tblHeader'))
# Normalize the two added form tables and give explanations the usable width.
for t,widths in zip(d.tables[:2],[[1.3,7.6,4.2,2.9],[1.3,2,12.7]]):
    normalize_table_geometry(d,t)
    twips=[int(Cm(w).twips) for w in widths];twips[-1]=sum(int(x.get(qn('w:w'))) for x in t._tbl.tblGrid.gridCol_lst)-sum(twips[:-1])
    for col,w in zip(t._tbl.tblGrid.gridCol_lst,twips):col.set(qn('w:w'),str(w))
    for row in t.rows:
        for c,w in zip(row.cells,twips):c._tc.get_or_add_tcPr().find(qn('w:tcW')).set(qn('w:w'),str(w))

replacements={
'Frontend/API/database là lớp thiết kế. HTTP/JSON/JWT, RBAC và transaction cần đối chiếu code/API/test. ERD là góc nhìn; schema là nguồn chi tiết.':'Kiến trúc LMS được xem xét qua ba phần: giao diện người dùng, dịch vụ xử lý nghiệp vụ và cơ sở dữ liệu. Việc phân chia này giúp nhận diện nơi thực hiện kiểm soát quyền và lưu trữ kết quả học tập. Sơ đồ chỉ thể hiện các quan hệ cần phân tích; cấu trúc dữ liệu và hành vi xử lý cụ thể phải được đối chiếu với mã nguồn, lược đồ cơ sở dữ liệu và bằng chứng kiểm thử.',
}
for p in d.paragraphs:
    if p.text in replacements:p.text=replacements[p.text]
    elif p.text.startswith('Chọn câu hỏi; mở source; kiểm title/node/connector/arrow/note;'):
        p.text='Mỗi sơ đồ được xây dựng để trả lời một câu hỏi cụ thể về hệ thống. Khi rà soát, cần kiểm tra tên đối tượng, quan hệ, điều kiện rẽ nhánh và chú thích dựa trên hồ sơ nghiệp vụ hoặc mã nguồn. Tệp Draw.io được lưu cùng bản xuất ảnh để có thể sửa và kiểm tra lại khi phạm vi thay đổi. Cách làm này giúp phát hiện sự không thống nhất giữa kế hoạch quản lý và sản phẩm được mô tả.'
    if p.style.name=='Caption':p.paragraph_format.keep_with_next=True
for p in d.paragraphs:
    if p.style.name=='WA Front Matter Title':
        p.alignment=A.LEFT;p.paragraph_format.keep_with_next=True
        for run in p.runs:run.font.name='Times New Roman';run.font.size=Pt(16);run.bold=True;run.italic=False
# Keep official covers comfortably within one A4 page each.
cover_end=next(i for i,p in enumerate(d.paragraphs) if p.text=='LỜI CẢM ƠN')
for p in d.paragraphs[:cover_end]:
    p.paragraph_format.line_spacing=1.5
    p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0)
    if p.text.startswith('\n\n\nTP.'):
        for run in p.runs:run.text=run.text.replace('\n\n\n','\n')
    if p.text.startswith('Môn học:'):p.alignment=A.LEFT
    if 'TIỂU LUẬN MÔN HỌC' in p.text:
        for run in p.runs:run.text=run.text.replace('\n\n','')
front_titles=set(sc_p.text for sc_p in sc.paragraphs if sc_p.style.name=='Heading 1' and sc_p.text!='MỞ ĐẦU')
if 'WA Front Matter Title' not in d.styles:
    st=d.styles.add_style('WA Front Matter Title',WD_STYLE_TYPE.PARAGRAPH);st.base_style=d.styles['Normal']
else:st=d.styles['WA Front Matter Title']
st.font.name='Times New Roman';st.font.size=Pt(16);st.font.bold=True
st.paragraph_format.alignment=A.LEFT;st.paragraph_format.keep_with_next=True
lev=OxmlElement('w:outlineLvl');lev.set(qn('w:val'),'9');st.element.get_or_add_pPr().append(lev)
for p in d.paragraphs:
    if p.text in front_titles:
        p.style=d.styles['Subtitle'];p.alignment=A.LEFT
        p.paragraph_format.keep_with_next=True
        for run in p.runs:run.font.name='Times New Roman';run.font.size=Pt(16);run.bold=True
    if p.style.name=='Heading 1' and p.text.startswith('CHƯƠNG'):p.paragraph_format.page_break_before=True
for toc_style in d.styles:
    if toc_style.name.casefold() in {'toc 1','toc 2','toc 3'}:
        f=toc_style.paragraph_format;f.line_spacing=1.15;f.space_before=Pt(0);f.space_after=Pt(0)
# Ensure Arabic numbering starts at Introduction, not glossary.
bodysec=d.sections[3]
num=bodysec._sectPr.find(qn('w:pgNumType'))
if num is None:num=OxmlElement('w:pgNumType');bodysec._sectPr.append(num)
num.set(qn('w:fmt'),'decimal');num.set(qn('w:start'),'1')
out=R/'output/LMS_HCMUNRE_day_du_prefields.docx';d.save(out)
(R/'qa/full-profile-authoring.json').write_text(json.dumps({'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'front_matter':'12 profile components; outer border; inner cover; no front page numbers; Introduction page 1','criteria':criteria,'personal_fields':'blank, unsigned, unassessed','source_body':'LMS_Tieu_luan_QLDA_ban_sua.docx','screenshots_preserved':10,'bibliography_reviewed_sources':11},ensure_ascii=False,indent=2),encoding='utf-8')
print(out)
