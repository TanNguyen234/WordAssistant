"""Apply reviewed citations, live screenshot pages and persistent Word styles.

This task artifact preserves the input and does not edit WordAssistant or LMS.
"""
import hashlib, json, re, shutil
from copy import deepcopy
from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION, WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH as A
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph
from PIL import Image
from wordassistant.operations.fields import append_caption_content
from wordassistant.operations.citations import _set_citation_policy
from wordassistant.evidence.registry import EvidenceRegistry

R=Path(__file__).resolve().parent
L=Path('D:/Download/LMS')
src=R/'output/user-correction-prose.docx'
assert hashlib.sha256(src.read_bytes()).hexdigest()=='6945d2cc5bdec50d87e685140c88acd555fdcd864f1307593ad93a1905731b89'
d=Document(src)
registry=json.loads((R/'report-evidence.json').read_text(encoding='utf-8-sig'))
project_refs=[
('LMS-CHARTER','Điều lệ dự án LMS','docs/project-management/01_PROJECT_CHARTER.md','Baseline, business case, scope and assumptions.'),
('LMS-RECON','Hồ sơ đối soát kế hoạch quản lý dự án LMS','docs/audit/06_PM_DOCUMENT_RECONCILIATION.md','Reconciled 20-week/1.2-billion/8.5-FTE baseline and CPM.'),
('LMS-RACI','Ma trận phân công trách nhiệm RACI','docs/project-management/03_RACI_MATRIX.md','One accountable role per selected activity and separation of sign-off.'),
('LMS-SOURCE','Mã nguồn luồng bài tập và cấu trúc dữ liệu LMS','backend/app/api/routes/assignments.py','Submission and grading guards, updates and notifications.'),
('LMS-RISK','Sổ rủi ro của dự án LMS','docs/project-management/08_RISK_REGISTER.md','Risk priorities, triggers and response plans.'),
('LMS-QUALITY','Tiêu chí chất lượng và các cổng kiểm soát LMS','docs/project-management/09_QUALITY_PLAN_AND_GATES.md','Quality conditions, planned gates and Definition of Done.')
]
for eid,title,path,claim in project_refs:
    target=R/'sources'/('project_'+Path(path).name)
    shutil.copyfile(L/path,target)
    text=target.read_text(encoding='utf-8-sig')
    url='https://github.com/TanNguyen234/LMS/blob/72cfa37ce5509286ee3f5990ee9c234adc452184/'+path
    registry[eid]=dict(id=eid,title=title,authors=['Kho mã nguồn LMS'],year=2026,url=url,
        verified_by='Codex source review',synthetic=False,tags=['primary','project'],review_status='reviewed',
        reviewed_by='Codex source review',reviewed_at='2026-10-26T00:00:00+07:00',
        support_location=path+'; local commit 72cfa37ce5509286ee3f5990ee9c234adc452184',
        support_excerpt=text[:500].strip(),source_file=target.name,
        source_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        source_license='User-supplied project; local reference use; no public reuse license asserted',source_url=url,
        retrieved_at='2026-10-26',claim=claim,language='vi',author_sort_key='Kho mã nguồn LMS',
        source_version='72cfa37ce5509286ee3f5990ee9c234adc452184',
        notes='Content reviewed from local checkout; GitHub URL identifies the repository, remote byte parity NOT RUN. Not an external scholarly publication.')
for eid in ['TRELLO-CARDS','TRELLO-CHECKS','DRAWIO-FORMATS','DRAWIO-PNG']:
    registry[eid]['notes']='Undated web documentation. Registry year is access-year for schema compatibility, not publication year; visible bibliography must state no publication year and access date.'
    registry[eid]['year']=2026
(R/'report-evidence-reviewed.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2),encoding='utf-8')
reg=EvidenceRegistry(R/'report-evidence-reviewed.json')
for record in registry.values():reg.assert_citable(record,require_reviewed=True)

def pafter(p,text='',style='Normal'):
    node=OxmlElement('w:p');p._p.addnext(node);out=Paragraph(node,p._parent);out.style=style
    if text:out.add_run(text)
    return out
def cite(p,eid):
    # Same editable citation content-control semantics as WordAssistant.
    p.add_run(' ')
    s=OxmlElement('w:sdt');pr=OxmlElement('w:sdtPr')
    for name,value in [('alias','Citation '+eid),('tag','wordassistant:citation:'+eid)]:
        node=OxmlElement('w:'+name);node.set(qn('w:val'),value);pr.append(node)
    content=OxmlElement('w:sdtContent');run=OxmlElement('w:r');t=OxmlElement('w:t');t.text='['+str(list(registry).index(eid)+1)+']';run.append(t);content.append(run);s.extend([pr,content]);p._p.append(s)
def sectionparas(title):
    result=[];active=False
    for p in d.paragraphs:
        if p.style.name.startswith('Heading '):
            if active:break
            active=p.text==title
        elif active:result.append(p)
    return result

# Rewrite around existing citation controls rather than deleting their evidence IDs.
for item in json.loads((R/'user-correction-citation-paragraphs.json').read_text(encoding='utf-8')):
    p=sectionparas(item['section'])[item['paragraph_index']]
    controls=[deepcopy(x) for x in p._p.findall(qn('w:sdt'))]
    p.clear();p.add_run(re.sub(r'\s*\[\d+\]','',item['text']))
    for s in controls:p.add_run(' ');p._p.append(s)

_set_citation_policy(d,{'style':'hcmunre_numeric','order':'vietnamese_given_name_then_english_family_name',
                          'require_reviewed':True,'heading':'TÀI LIỆU THAM KHẢO'})

# Project-source citations are visible next to the claims, not only in QA files.
links={
'MỞ ĐẦU':['LMS-CHARTER','LMS-RECON'],
'CHƯƠNG 1. TỔNG QUAN VÀ KHỞI TẠO DỰ ÁN':['LMS-CHARTER'],
'Business case và mục tiêu':['LMS-CHARTER','LMS-QUALITY'],
'Giả định và ràng buộc':['LMS-RECON'],
'RACI và escalation':['LMS-RACI'],
'CHƯƠNG 3. QUẢN LÝ PHẠM VI VÀ WBS':['LMS-CHARTER','LMS-RECON'],
'Ranh giới và acceptance':['LMS-SOURCE'],
'CHƯƠNG 4. QUẢN LÝ TIẾN ĐỘ VÀ CPM':['LMS-RECON'],
'CHƯƠNG 5. QUẢN LÝ NGUỒN LỰC VÀ CHI PHÍ':['LMS-RECON'],
'CHƯƠNG 6. QUẢN LÝ RỦI RO':['LMS-RISK'],
'CHƯƠNG 7. QUẢN LÝ CHẤT LƯỢNG VÀ KIỂM THỬ':['LMS-QUALITY'],
'Gate và DoD':['LMS-QUALITY'],
'CHƯƠNG 9. THIẾT KẾ VÀ BIỂU ĐỒ DRAW.IO':['LMS-SOURCE'],
'CHƯƠNG 10. NGHIỆM THU VÀ ĐÓNG DỰ ÁN':['LMS-QUALITY','LMS-RECON']}
for h,ids in links.items():
    ps=[p for p in sectionparas(h) if p.text and p.style.name!='Caption' and not p._p.xpath('.//w:drawing')]
    for index,eid in enumerate(ids):cite(ps[min(index,len(ps)-1)],eid)

# Replace stale universal missing-capture statements with observed status.
replacements={
'Guide nêu T01–T05, D01–D03, L01–L07. Tất cả hiện CHƯA CHỤP — NOT RUN. Khi capture, lưu ảnh gốc, thời điểm, URL/route hoặc click path, trạng thái trang, hash và reviewer. Không dùng API aggregate thay T01, PNG thay UI Draw.io hay diagram thay LMS runtime.':
'Hướng dẫn yêu cầu các nhóm ảnh T01–T05, D01–D03 và L01–L07. Ngày 26/10/2026 đã bổ sung ảnh trực tiếp của board, thẻ WBS, mốc lịch, thẻ mô phỏng và website LMS theo ba vai trò tại Phụ lục E. Calendar/Timeline, ảnh thao tác editor Draw.io, API 403 và terminal kiểm thử vẫn cần bằng chứng riêng nếu giảng viên yêu cầu.',
'Checklist hướng dẫn không thay ảnh; mọi capture hiện chưa thực hiện.':'Bảng dưới đây phân biệt ảnh đã chụp với những minh chứng chưa thực hiện; ảnh tĩnh xuất từ Draw.io vẫn được quản lý riêng với ảnh giao diện editor.',
'UAT, EVM, ký duyệt và trạng thái hoàn tất trong tài liệu kế hoạch là mô phỏng/chưa chạy. PNG Draw.io là hình tĩnh đi cùng source .drawio, không thay ảnh giao diện Draw.io/LMS. Checklist T01–T05, D01–D03, L01–L07 được đưa vào phụ lục; ảnh thật chưa có nên trạng thái là NOT RUN.':
'Báo cáo bổ sung ảnh chụp trực tiếp board Trello, checklist WBS và website LMS theo ba vai trò ngày 26/10/2026. Quan sát này làm rõ trạng thái công cụ và giao diện trên dữ liệu kiểm thử. Các biểu mẫu UAT, EVM và ký duyệt vẫn được phân biệt với kết quả thực tế; những minh chứng chưa thực hiện được liệt kê tại phụ lục.'}
for p in d.paragraphs:
    if p.text in replacements:p.text=replacements[p.text]

# Compact explanatory repetition becomes useful analysis instead of repeated warnings.
replace_short={
'WBS là cấu trúc công việc, không chứng minh gói việc đã hoàn tất.':'Bảng WBS nối nhóm công việc với đầu ra để làm căn cứ ước lượng và giao trách nhiệm.',
'Mạng LMS_14 không gán ngày; bảng này là nguồn duration/float baseline.':'Bảng tính cho phép đối chiếu thời điểm sớm, thời điểm muộn và khả năng dịch chuyển từng hoạt động.',
'LMS_14 không gán ngày; bảng CPM mới là nguồn duration/float.':'Sơ đồ dưới đây bổ sung góc nhìn quan hệ giữa các nhóm công việc.',
'Risk register là kế hoạch mô phỏng; score không chứng minh sự kiện.':'Bảng ưu tiên giúp chọn rủi ro cần theo dõi trước và biện pháp tương ứng.',
'Cards/lists/checklists hỗ trợ công việc; approval/evidence vẫn riêng.':'Quy ước dưới đây giúp thẻ công việc chứa đủ thông tin cho người thực hiện và người kiểm tra.',
'Dữ liệu API không phải ảnh UI và không chứng minh Done.':'Bảng sau lưu số liệu snapshot ngày 23/10/2026; ảnh giao diện ngày 26/10/2026 nằm ở Phụ lục E.',
'Snapshot không chứng minh phần việc đã hoàn thành.':'Ảnh board cho thấy việc tổ chức công việc đã có, nhưng trạng thái thực hiện cần tiếp tục được cập nhật theo bằng chứng.'}
for p in d.paragraphs:
    if p.text in replace_short:p.text=replace_short[p.text]

# Add explicit sources below every existing figure and native table.
for p in list(d.paragraphs):
    if p.style.name=='Caption' and p.text.startswith('HÌNH'):
        source=pafter(p,'Nguồn: ' + ('Tổng hợp snapshot Trello ngày 23/10/2026; không phải ảnh giao diện.' if 'snapshot API' in p.text else 'Hồ sơ Draw.io do người dùng cung cấp; đối chiếu nguồn dự án LMS.'))
        if any(t in p.text for t in ['Use Case','nộp bài','chấm bài','lớp khái niệm','trạng thái','Trạng thái','dữ liệu','Kiến trúc']):cite(source,'LMS-SOURCE')
        source.style='WA Source Note' if 'WA Source Note' in d.styles else 'Normal'
for i,table in enumerate(d.tables):
    following=table._tbl.getnext()
    node=OxmlElement('w:p');table._tbl.addnext(node);note=Paragraph(node,d._body)
    note.add_run('Nguồn: ')
    if i in [12]:note.add_run('Snapshot Trello ngày 23/10/2026 trong hồ sơ người dùng cung cấp.')
    elif i in [16,17,18]:note.add_run('Hồ sơ đề tài và hướng dẫn chụp ảnh do người dùng cung cấp; cập nhật quan sát ngày 26/10/2026.')
    else:
        eid='LMS-RACI' if i==2 else 'LMS-RISK' if i==9 else 'LMS-QUALITY' if i in [10,11] else 'LMS-CHARTER' if i in [0,3] else 'LMS-SOURCE' if i==14 else 'LMS-RECON'
        note.add_run('Hồ sơ dự án LMS, bản đối chiếu tại commit 72cfa37.');cite(note,eid)

checklist=next(t for t in d.tables if any(c.text=='T01' for row in t.rows for c in row.cells))
statuses={'T01':'ĐÃ CHỤP; Phụ lục E','T02':'ĐÃ CHỤP; checklist 0/7','T03':'Đã chụp mốc; chưa Calendar','T04':'ĐÃ CHỤP thẻ mô phỏng','T05':'Đã quan sát Done trống','D01-D03':'CHƯA CHỤP editor','L01-L07':'L01–L05 đã chụp; L06–L07 chưa'}
for row in checklist.rows[1:]:
    key=row.cells[0].text
    if key in statuses:row.cells[-1].text=statuses[key]

# Temporarily detach the old bibliography; CLI will rebuild and sort it at the end.
bib=next(p for p in d.paragraphs if p.text=='TÀI LIỆU THAM KHẢO' and p.style.name.startswith('Heading'))
block=[];node=bib._p
while node is not None:
    nxt=node.getnext()
    if node is not bib._p and node.tag==qn('w:p'):
        p=Paragraph(node,d._body)
        if p.style.name=='Heading 1':break
    block.append(node);node=nxt
for node in block:node.getparent().remove(node)

cfg=json.loads((R/'reviewed-captures.json').read_text(encoding='utf-8'))
section=d.add_section(WD_SECTION.NEW_PAGE)
section.orientation=WD_ORIENT.PORTRAIT;section.page_width=Cm(21);section.page_height=Cm(29.7)
section.left_margin=Cm(3);section.right_margin=Cm(2);section.top_margin=section.bottom_margin=Cm(2)
for x in section._sectPr.findall(qn('w:pgNumType')):x.attrib.pop(qn('w:start'),None)
h=d.add_paragraph(cfg['heading'],style='Heading 2');h.paragraph_format.page_break_before=False
def suppress_numbering(p):
    pr=p._p.get_or_add_pPr();num=OxmlElement('w:numPr');v=OxmlElement('w:numId');v.set(qn('w:val'),'0');num.append(v);pr.append(num)
suppress_numbering(h)
d.add_paragraph(cfg['introduction'])
for i,item in enumerate(cfg['screens']):
    h=d.add_paragraph(item['caption'],style='Heading 3');suppress_numbering(h)
    h.paragraph_format.page_break_before=i>0
    d.add_paragraph(item['text'])
    p=d.add_paragraph();p.alignment=A.CENTER;p.paragraph_format.keep_with_next=True
    p.add_run().add_picture(str(R/'captures/2026-10-26'/item['file']),width=Cm(16))
    cap=d.add_paragraph(style='Caption');cap.alignment=A.CENTER
    append_caption_content(d,cap,'HÌNH',item['caption'],'Hinh')
    note=d.add_paragraph('Nguồn: Ảnh chụp trực tiếp ngày 26/10/2026; '+('Trello, bảng sLfApXgV.' if item['id'].startswith('T') else 'website LMS cục bộ, tài khoản demo.'))
    note.paragraph_format.space_before=Pt(3)
    note.add_run(' Mã minh chứng '+item['id']+'.')

for node in block:d.element.body.insert(len(d.element.body)-1,node)

# Persistent styles plus reconciliation of conflicting direct overrides.
for name,size in [('Normal',13),('Title',18),('Heading 1',16),('Heading 2',14),('Heading 3',13),('Caption',13)]:
    s=d.styles[name];s.font.name='Times New Roman';s.font.size=Pt(size);s.font.color.rgb=RGBColor(0,0,0)
    s.paragraph_format.line_spacing=1.5
    if name.startswith('Heading'):
        s.font.bold=True;s.paragraph_format.alignment=A.LEFT;s.paragraph_format.left_indent=Cm(0);s.paragraph_format.first_line_indent=Cm(0)
    elif name=='Caption':s.paragraph_format.alignment=A.CENTER
for p in d.paragraphs:
    style=p.style.name
    if style.startswith('toc '):continue
    heading=style.startswith('Heading ')
    cap=style=='Caption'
    picture=bool(p._p.xpath('.//w:drawing'))
    if heading:
        p.alignment=A.LEFT;p.paragraph_format.left_indent=Cm(0);p.paragraph_format.first_line_indent=Cm(0)
        p.paragraph_format.keep_with_next=True
    elif cap:
        p.alignment=A.CENTER if p.text.startswith('HÌNH') else A.LEFT
        p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.space_before=Pt(4);p.paragraph_format.space_after=Pt(4)
        p.paragraph_format.keep_with_next=p.text.startswith('BẢNG')
    elif not picture and p.text and not style.startswith(('Title','WA Cover')):
        p.alignment=A.JUSTIFY;p.paragraph_format.first_line_indent=Cm(0)
        p.paragraph_format.space_after=Pt(6)
    p.paragraph_format.line_spacing=1 if picture else 1.5
    size=16 if style=='Heading 1' else 14 if style=='Heading 2' else 18 if style=='Title' else 13
    for r in p.runs:
        if r._r.xpath('.//w:drawing'):continue
        r.font.name='Times New Roman';r.font.size=Pt(size);r.font.color.rgb=RGBColor(0,0,0)
        if heading:r.bold=True
for table in d.tables:
    for row in table.rows:
        for c in row.cells:
            for p in c.paragraphs:
                p.paragraph_format.line_spacing=1.15
                for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(13);r.font.color.rgb=RGBColor(0,0,0)
for sec in d.sections:
    for p in sec.footer.paragraphs:
        p.alignment=A.RIGHT
        for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(13)

out=R/'output/user-correction-layout.docx';d.save(out)
print(json.dumps({'status':'SUCCESS','output':str(out),'new_screenshots':len(cfg['screens']),'citation_records':len(registry)},ensure_ascii=False))
