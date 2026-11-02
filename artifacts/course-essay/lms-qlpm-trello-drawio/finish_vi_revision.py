"""Bind real unedited captures and reviewed primary sources to a new report copy."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import hashlib,json,re,shutil
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH as A
from PIL import Image
from wordassistant.operations.citations import (_citation_policy,_ordered_citation_numbers,
 _renumber_citations,_bibliography_entries,_replace_bibliography_content)
from wordassistant.evidence.registry import EvidenceRegistry
from wordassistant.operations.fields import append_caption_content
R=Path(__file__).resolve().parent;L=Path('D:/Download/LMS')
def j(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def save(p,x):(R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=Document(R/'output/LMS_HCMUNRE_Viet_hoa_noi_dung.docx')
registry=j('report-evidence-reviewed.json')
registry['LMS-SOURCE']['title']='Mã nguồn xử lý bài tập, bài nộp và chấm điểm LMS'
sources=[('LMS-ARCH','Kiến trúc ứng dụng LMS','docs/03_ARCHITECTURE.md','**Modular monolith**, phù hợp prototype học phần: một FastAPI backend, một React SPA, một SQL Server database.','Kiến trúc mô-đun nguyên khối, React, FastAPI và SQL Server.'),
 ('LMS-SCHEMA','Lược đồ cơ sở dữ liệu LMS','database/01_schema.sql','CREATE TABLE dbo.Users (','Lược đồ gồm 12 bảng; khóa chính, khóa ngoại và dữ liệu học tập.'),
 ('LMS-ROLES','Vai trò, ca sử dụng và quyền truy cập LMS','docs/02_ROLES_USE_CASES.md','Quản trị tài khoản, khóa học và enrollment. Không mặc định được chỉnh nội dung giảng dạy thay Lecturer.','Ba vai trò, trách nhiệm và ranh giới truy cập theo học phần, ca sử dụng nộp và chấm bài.')]
for eid,title,path,excerpt,claim in sources:
 target=R/'sources'/('reviewed_vi_'+Path(path).name);shutil.copyfile(L/path,target)
 assert excerpt in target.read_text(encoding='utf-8-sig')
 url='https://github.com/TanNguyen234/LMS/blob/72cfa37ce5509286ee3f5990ee9c234adc452184/'+path
 registry[eid]=dict(id=eid,title=title,authors=['Kho mã nguồn LMS'],year=2026,url=url,verified_by='Codex primary source review',synthetic=False,tags=['primary','project'],review_status='reviewed',reviewed_by='Codex primary source review',reviewed_at='2026-10-26',support_location=path,support_excerpt=excerpt,source_file=target.name,source_sha256=sha(target),source_license='User-supplied local project; no public redistribution license asserted',source_url=url,retrieved_at='2026-10-26',claim=claim,language='vi',author_sort_key='Kho mã nguồn LMS',source_version='72cfa37ce5509286ee3f5990ee9c234adc452184',notes='Local primary source inspected; remote byte parity NOT RUN. Design evidence, not production evidence.')
pack=R/'sources/reviewed_vi_ui_and_checks.txt'
paths=['frontend/src/pages/DashboardPage.tsx','frontend/src/pages/GradesPage.tsx','frontend/src/utils/vi.ts','frontend/src/components/layout/AppLayout.tsx','docs/audit/2026-10-26-vietnamese-ui/focused-green.log','docs/audit/2026-10-26-vietnamese-ui/typecheck.log','docs/audit/2026-10-26-vietnamese-ui/build.log','docs/audit/2026-10-26-vietnamese-ui/lint.log']
pack.write_text('\n\n'.join('SOURCE: '+p+'\n'+(L/p).read_text(encoding='utf-8-sig') for p in paths),encoding='utf-8')
excerpt='Điểm trung bình tạm tính từ các điểm đã ghi nhận, chưa áp dụng trọng số học phần. Kết quả này chưa xác định việc đạt học phần.'
assert excerpt in pack.read_text(encoding='utf-8')
registry['LMS-UI-VI']=dict(id='LMS-UI-VI',title='Giao diện LMS tiếng Việt và nhật ký kiểm tra ngày 26 tháng 10 năm 2026',authors=['Kho mã nguồn LMS'],year=2026,url='http://127.0.0.1:5174/',verified_by='Codex local source and UI review',synthetic=False,tags=['primary','project'],review_status='reviewed',reviewed_by='Codex local source and UI review',reviewed_at='2026-10-26',support_location='Local working-tree snapshot: '+', '.join(paths),support_excerpt=excerpt,source_file=pack.name,source_sha256=sha(pack),source_license='User-authorized local project and verification logs; no public redistribution license asserted',source_url='http://127.0.0.1:5174/',retrieved_at='2026-10-26',claim='Vietnamese presentation, provisional grade explanation, role links and four focused passing tests plus static verification; no full UAT asserted.',language='vi',author_sort_key='Kho mã nguồn LMS',source_version='Local uncommitted frontend snapshot 2026-10-26',notes='Local URL is a demo entry point, not a public publication. Exact source bytes and logs are stored alongside this registry. Screenshots have separate hashes and timestamps.')
save('report-evidence-vietnamese-reviewed.json',registry)
reg=EvidenceRegistry(R/'report-evidence-vietnamese-reviewed.json')
for record in registry.values():reg.assert_citable(record,require_reviewed=True)
def cite(p,eid):
 p.add_run(' ');s=OxmlElement('w:sdt');pr=OxmlElement('w:sdtPr')
 for name,value in [('alias','Citation '+eid),('tag','wordassistant:citation:'+eid)]:
  node=OxmlElement('w:'+name);node.set(qn('w:val'),value);pr.append(node)
 content=OxmlElement('w:sdtContent');r=OxmlElement('w:r');t=OxmlElement('w:t');t.text='[1]';r.append(t);content.append(r);s.extend([pr,content]);p._p.append(s)
def rewrite(p,text,ids):
 p.clear();p.add_run(text)
 for eid in ids:cite(p,eid)
for p in d.paragraphs:
 if p.text.startswith('Thiết kế giúp đội dự án chuyển phạm vi'):
  rewrite(p,'Thiết kế chuyển phạm vi dự án thành các thành phần và quy tắc có thể kiểm tra. Hồ sơ kiến trúc mô tả một ứng dụng giao diện React và TypeScript, một dịch vụ FastAPI cùng cơ sở dữ liệu SQL Server. Cách tổ chức này xác định ranh giới giữa trình bày, xử lý nghiệp vụ và lưu trữ, phù hợp với sản phẩm mẫu của học phần. Sơ đồ trình bày thiết kế; các quan sát giao diện ở phần sau chỉ xác nhận những trạng thái cụ thể đã mở trên hệ thống cục bộ.', ['LMS-ARCH'])
 elif p.text.startswith('ERD LMS_12 trình bày 12 bảng'):
  rewrite(p,'Mô hình dữ liệu LMS_12 trình bày 12 bảng; số bảng được đối chiếu với các lệnh tạo bảng trong lược đồ SQL. Khóa chính và khóa ngoại hỗ trợ theo dõi quan hệ giữa người dùng, học phần, ghi danh, bài tập, bài nộp và điểm. Một số quan hệ trên hình được giản lược theo hồ sơ sơ đồ. Phụ lục D bổ sung ca sử dụng, luồng nộp bài, trình tự chấm bài, lớp miền và trạng thái bài nộp; các quy tắc cập nhật bài nộp và chấm điểm được kiểm tra riêng trong mã xử lý bài tập.', ['LMS-SCHEMA','LMS-SOURCE'])
 elif p.text=='Kiến trúc là thiết kế trong repo, không phải runtime.':
  p.text='Các thành phần trên hình là mô tả kiến trúc; trạng thái vận hành cần bằng chứng giám sát và kiểm thử riêng.'
 elif p.text.startswith('Draw.io giữ source.drawio/XML'):
  rewrite(p,'Tệp nguồn Draw.io/XML được giữ để chỉnh sửa, còn bản PNG dùng để trình bày trong Word. Tài liệu chính thức mô tả các định dạng xuất và tùy chọn PNG. Việc có hình tĩnh không xác nhận người thực hiện đã chụp thao tác trong trình biên tập Draw.io.', ['DRAWIO-FORMATS','DRAWIO-PNG'])
 elif p.text.startswith(('Lần rà soát giao diện ngày','Quan sát trực tiếp sử dụng','Phạm vi kiểm chứng vì vậy','Ở vai trò quản trị,','Ở vai trò giảng viên,','Ở vai trò sinh viên,','Giao diện được khảo sát')):cite(p,'LMS-UI-VI')

cfg=j('reviewed-captures.json');raw=j('captures/2026-10-26-vi/ui-captures.json')['captures'];byid={c['capture_id']:c for c in raw}
assert set(['L01','L02','L03','L03b','L04','L05','L08','L10','L12','L13'])<=set(byid)
for item in cfg['screens']:
 if not item['id'].startswith('L'):continue
 c=byid[item['id']];path=Path(c['screenshot_path']);assert sha(path)==c['screenshot_sha256']
 cap=next(p for p in d.paragraphs if p.style.name=='Caption' and p.text.endswith(item['caption']))
 node=cap._p.getprevious()
 while node is not None and not node.xpath('.//a:blip'):node=node.getprevious()
 assert node is not None
 blip=node.xpath('.//a:blip')[0];rid,_=d.part.get_or_add_image(str(path));blip.set(qn('r:embed'),rid)
 for rect in node.xpath('.//a:srcRect'):rect.getparent().remove(rect)
 w,h=Image.open(path).size;width=Cm(16);height=int(width*h/w)
 for ex in node.xpath('.//wp:extent')+node.xpath('.//a:xfrm/a:ext'):ex.set('cx',str(width));ex.set('cy',str(height))
 for dp in node.xpath('.//wp:docPr'):dp.set('descr',c['note'])
 item['file']=path.name
 if item['id']=='L03':item['text']=item['text'].replace('trạng thái PUBLISHED','trạng thái Đã giao')
 if item['id']=='L05':item['text']='Bảng điểm AI310 hiển thị điểm thành phần 10/10 và trọng số 10% đã lưu trước lần chụp. Giao diện giải thích trung bình chỉ là tạm tính, chưa áp dụng trọng số học phần và chưa xác định việc đạt học phần. Không thực hiện bài kiểm tra hoặc thay đổi điểm để tạo hình minh chứng.'
 # Exact associated prose, not global document replacement.
 heading=next(p for p in d.paragraphs if p.style.name=='Heading 3' and p.text==item['caption'])
 nxt=heading._p.getnext()
 if nxt is not None:
  from docx.text.paragraph import Paragraph
  body=Paragraph(nxt,heading._parent)
  if not body._p.xpath('.//w:drawing'):body.text=item['text']

# Add selected observed screens before the managed bibliography; keep native SEQ captions.
bib=next(p for p in d.paragraphs if p.style.name=='Heading 1' and p.text=='TÀI LIỆU THAM KHẢO')
template=next(p for p in d.paragraphs if p.style.name=='Heading 3' and p.text=='Bảng điểm cá nhân trên dữ liệu kiểm thử')
extra=[('L08','Trang tổng quan của quản trị viên','Tổng quan hiển thị số liệu tài khoản và khóa học từ dữ liệu mẫu. Ô theo dõi hệ thống ghi rõ chưa có dữ liệu giám sát; không hiển thị kết luận máy chủ hoạt động bình thường khi chưa có phép đo.'),
 ('L10','Hộp thư thông báo của quản trị viên','Tài khoản quản trị hiện chưa có thông báo. Ảnh ghi nhận trạng thái rỗng thực tế, không bổ sung thông báo giả hoặc đánh dấu đã đọc để chuẩn bị ảnh.'),
 ('L12','Danh sách bài kiểm tra theo học phần','Giảng viên xem các bài kiểm tra của WEB220. Nhãn chức năng và trạng thái dùng tiếng Việt; tiêu đề và nội dung bài mẫu giữ nguyên. Không tạo câu hỏi, xuất bản hoặc bắt đầu lượt làm bài trong lần quan sát.'),
 ('L13','Bảng điểm trên màn hình điện thoại','Khung xem 390 × 844 cho thấy các thẻ điểm xếp thành một cột và phần đầu trang được thu gọn. Bảng dữ liệu có vùng cuộn riêng. Ảnh phản ánh một kích thước kiểm tra; chưa thay được đánh giá trên nhiều thiết bị hoặc kiểm thử khả năng tiếp cận.')]
for cid,title,text in extra:
 c=byid[cid];path=Path(c['screenshot_path']);assert sha(path)==c['screenshot_sha256']
 h=bib.insert_paragraph_before(title,style='Heading 3');h._p.remove(h._p.get_or_add_pPr())
 h._p.insert(0,deepcopy(template._p.get_or_add_pPr()))
 h.paragraph_format.page_break_before=True;h.paragraph_format.keep_with_next=True
 p=bib.insert_paragraph_before(text,style='Normal');p.paragraph_format.keep_with_next=True
 pic=bib.insert_paragraph_before('',style='Normal');pic.alignment=A.CENTER
 pic.add_run().add_picture(str(path),width=Cm(7.6) if cid=='L13' else Cm(16));pic.paragraph_format.keep_with_next=True
 cap=bib.insert_paragraph_before('',style='Caption');append_caption_content(d,cap,'HÌNH',title,'Hinh');cap.alignment=A.CENTER;cap.paragraph_format.keep_with_next=True
 note=bib.insert_paragraph_before('Nguồn: Ảnh chụp trực tiếp website LMS ngày 26/10/2026; dữ liệu dùng thử giữ nguyên.',style='WA Source Note' if 'WA Source Note' in d.styles else 'Normal')
 cfg['screens'].append(dict(id=cid,file=path.name,caption=title,text=text))
cfg['introduction']+=' Các ảnh website trong bản sửa này được chụp lại sau khi Việt hóa; dữ liệu mẫu được giữ nguyên, không thêm lớp che hoặc ghép nội dung. Bốn ảnh Trello được giữ từ lần quan sát trước.'
p=next(p for p in d.paragraphs if p.text.startswith('Các ảnh trong phụ lục được chụp trực tiếp'));p.text=cfg['introduction']
save('reviewed-captures-vietnamese.json',cfg)

# Restore source-specific citations below architecture and ERD figures.
lastcap=''
for p in d.paragraphs:
 if p.style.name=='Caption':lastcap=p.text
 elif p.text.startswith('Nguồn:') and 'Kiến trúc LMS theo hồ sơ' in lastcap:
  rewrite(p,'Nguồn: Hồ sơ kiến trúc và lược đồ cơ sở dữ liệu LMS; kiểm tra thành phần giao diện theo bản mã nguồn cục bộ.', ['LMS-ARCH','LMS-SCHEMA','LMS-UI-VI']);lastcap=''
 elif p.text.startswith('Nguồn:') and ('Kiến trúc hệ thống LMS' in lastcap or 'Mô hình dữ liệu LMS' in lastcap):
  rewrite(p,'Nguồn: Hồ sơ sơ đồ LMS do người dùng cung cấp; đối chiếu kiến trúc hoặc lược đồ dữ liệu của dự án.', ['LMS-ARCH' if 'Kiến trúc' in lastcap else 'LMS-SCHEMA']);lastcap=''
 elif p.text.startswith('Nguồn:') and any(t in lastcap for t in ['Ca sử dụng LMS theo vai trò','lớp khái niệm','Luồng sinh viên nộp bài','Trạng thái nộp và chấm bài']):
  ids=['LMS-ROLES'] if 'Ca sử dụng' in lastcap else ['LMS-SCHEMA','LMS-SOURCE']
  rewrite(p,'Nguồn: Hồ sơ sơ đồ LMS do người dùng cung cấp; đối chiếu vai trò, dữ liệu và quy tắc nghiệp vụ tương ứng.',ids);lastcap=''
policy=_citation_policy(d);nums=_ordered_citation_numbers(d,reg,policy,repair=True)
_renumber_citations(d,nums,reg,'hcmunre_numeric');_replace_bibliography_content(d,'TÀI LIỆU THAM KHẢO',_bibliography_entries(reg,nums,'hcmunre_numeric',require_reviewed=True))
for p in d.paragraphs:
 if re.match(r'^\[\d+\]',p.text):
  p.alignment=A.LEFT;p.paragraph_format.keep_with_next=False
  if any(url in p.text for url in ['support.atlassian.com','www.drawio.com']):
   for r in p.runs:
    if r.text=='2026':r.text='không ghi năm; truy cập ngày 26/10/2026'
 elif p.text in ['Tiếng Việt:','Tiếng Anh:']:p.paragraph_format.keep_with_next=True
used={b.get(qn('r:embed')) for b in d.element.xpath('.//a:blip')}
for rid,rel in list(d.part.rels.items()):
 if rel.reltype.endswith('/image') and rid not in used:d.part.drop_rel(rid)
d.save(R/'output/LMS_HCMUNRE_Viet_hoa_truoc_cap_nhat_truong.docx')

old=j('captures/2026-10-26/capture-manifest.json');records=[c for c in old['captures'] if c['capture_id'].startswith('T')]
roles={'L01':'Mở trang đăng nhập qua nút Đăng xuất.','L02':'Đăng nhập quản trị; menu Người dùng; bộ lọc Tất cả vai trò.','L08':'Quản trị: menu Tổng quan.','L10':'Quản trị: menu Thông báo.','L03':'Đăng xuất; chọn demo Giảng viên TS. Nam; Đăng nhập; menu Bài tập; WEB220.','L03b':'Giảng viên: WEB220; nút Xem & Chấm bài.','L12':'Giảng viên: đóng danh sách bài nộp; menu Bài kiểm tra; WEB220.','L04':'Đăng xuất; chọn demo Sinh viên Nguyễn An; Đăng nhập; menu Bài tập; AI310.','L05':'Sinh viên: menu Bảng điểm; AI310.','L13':'Sinh viên: bảng điểm AI310; đổi khung xem 390 × 844; tải lại.'}
logs=j('captures/2026-10-26-vi/browser-console.json')
for c in raw:
 p=Path(c['screenshot_path']);rel=p.relative_to(R).as_posix();item=next(x for x in cfg['screens'] if x['id']==c['capture_id'])
 # Earlier HMR error is retained separately. No errors were recorded after the first final capture.
 relevant=[x for x in logs if x['timestamp']>=c['captured_at']]
 records.append(dict(capture_id=c['capture_id'],route=c['resolved_url'],resolved_url=c['resolved_url'],screenshot_path=rel,screenshot_sha256=sha(p),captured_at_local=datetime.fromisoformat(c['captured_at'].replace('Z','+00:00')).astimezone(timezone(timedelta(hours=7))).isoformat(),page_title=item['caption'],acceptance_status='ACCEPTED_UI_CLICKTHROUGH_CAPTURE',capture_method='visible UI click-through in ChatGPT in-app browser',arrival={'from':'http://127.0.0.1:5174/','local_file_open_for_this_capture':False,'direct_route_load_for_this_capture':False,'ui_steps':[roles[c['capture_id']]],'note':'Summarized from observed tool interactions; raw arrival_history is retained separately and contains earlier exploration.'},external_side_effect=False,http_status=None,network={'document_status':None,'note':'Original main-document status not exposed; UNKNOWN.'},console={'errors':[x for x in relevant if x['level']=='error'],'warnings':[x for x in relevant if x['level']=='warn'],'historical_log_file':'browser-console.json'},page_state_review={'status':'PASS','summary':item['text'],'reviewed_by':'Codex actual screenshot visual review','reviewed_at':'2026-10-26','screenshot_path':rel,'screenshot_sha256':sha(p)},viewport=list(Image.open(p).size)))
old['captures']=records;old['verification_limit']='Original document HTTP status remains UNKNOWN. Historical HMR AuthProvider error at 03:45:17Z is preserved in browser-console.json; final captures begin 03:57Z after reload and show loaded screens. No new console errors recorded during final capture sequence. No full UAT claimed.'
save('captures/2026-10-26-vi/capture-manifest.json',old)
save('qa/vietnamese-ui/authoring-provenance.json',dict(input='output/LMS_HCMUNRE_day_du.docx',input_sha256=sha(R/'output/LMS_HCMUNRE_day_du.docx'),output='output/LMS_HCMUNRE_Viet_hoa_truoc_cap_nhat_truong.docx',output_sha256=sha(R/'output/LMS_HCMUNRE_Viet_hoa_truoc_cap_nhat_truong.docx'),registry_sha256=sha(R/'report-evidence-vietnamese-reviewed.json'),citation_numbers=nums,source_files={p:sha(L/p) for p in paths},embedded_web_images='10 freshly captured unredacted real UI images; old 6 replaced and 4 added',source_integrity='Input report and VietLex reference preserved.'))
print('Saved authored copy,',len(nums),'reviewed references and',len(records),'real captures.')
