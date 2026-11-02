from pathlib import Path
import hashlib,shutil
from docx import Document
from docx.shared import Cm
from docx.oxml.ns import qn
root=Path(r'D:\Download\ProfessionalLegalRAG\artifacts\course-essay-vietlex-20261020')
src=root/'output/VietLex_DoAnChuyenNganh_RubricCriteria_FinalQA_20261025_v5.docx'
out=root/'output/VietLex_DoAnChuyenNganh_RubricCriteria_FinalQA_20261025_v6.docx'
expected='382cf9351599db29b010be89dacce7103a2d0f0c2bca2ca436b61619460a8c30'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)==expected, f'input v5 hash changed: {sha(src)}'
assert out.exists() and sha(out)==expected, f'v6 pre-edit copy does not match verified v5 input: {sha(out) if out.exists() else "missing"}'
doc=Document(out)

def one(starts,style=None):
 matches=[p for p in doc.paragraphs if p.text.startswith(starts) and (style is None or p.style.name==style)]
 assert len(matches)==1, (starts,style,len(matches))
 return matches[0]

def set_start(starts,text,style=None):
 p=one(starts,style); old=p.text; p.text=text
 return {'anchor':starts,'before':old,'after':text}
changes=[]
changes.append(set_start('Phần này được dành để sinh viên ghi nhận sự hỗ trợ thực tế',
'''Phần này để sinh viên tự ghi nhận sự hỗ trợ thực tế đã nhận trong quá trình thực hiện đồ án. Chỉ điền thông tin có thể xác nhận: người hoặc đơn vị được cảm ơn, vai trò và đóng góp cụ thể.\n\nNgười/đơn vị: [sinh viên tự điền sau khi xác nhận]\n\nNội dung hỗ trợ: [mô tả đóng góp thực tế]\n\nTrước khi sử dụng, xóa hướng dẫn trong ngoặc vuông và viết lại bằng lời của sinh viên.'''))
changes.append(set_start('Đây là bản thảo hỗ trợ biên tập.',
'''Đây là phần để sinh viên tự viết lời cam đoan theo yêu cầu của đơn vị đào tạo sau khi rà soát nội dung, nguồn, kết quả và quy định về sử dụng công cụ hỗ trợ. Bản thảo này không thay cho lời xác nhận của sinh viên.\n\nLời cam đoan do sinh viên tự viết: [hoàn thiện sau khi rà soát]\n\nHọ và tên: [sinh viên tự điền]\nNgày: [sinh viên tự điền]\nChữ ký: [ký nếu được yêu cầu]'''))
changes.append(set_start('Kết quả cho thấy VietLex không chỉ là một chatbot:',
'''Kết quả cho thấy VietLex không chỉ là một chatbot: hệ thống kết hợp tìm kiếm theo metadata/toàn văn, đọc văn bản, hồ sơ nghiên cứu, truy xuất evidence, sinh câu trả lời và kiểm tra một số điều kiện an toàn. Kiến trúc giữ hai tuyến retrieval khác nhau, có bước giới hạn evidence/context, tùy chọn mở rộng điều khoản có kiểm hash và cơ chế cache có điều kiện. Các sơ đồ phân tích được dựng từ source; ba ảnh giao diện trong DOCX được chọn từ lượt clickthrough ẩn danh ngày 23/10/2026, lần lượt ghi nhận trang hỏi đáp, kết quả tra cứu và trang đọc văn bản. Revision triển khai chưa được xác nhận độc lập.'''))
changes.append(set_start('Khoảng trống còn lại là chưa có rubric chính thức,',
'''Hướng dẫn HCMUNRE cung cấp tiêu chí nhận xét chính thức nhưng không nêu thang điểm hoặc trọng số. Trong phạm vi hồ sơ hiện có, chưa nhận được đề bài hay rubric chấm điểm riêng của học phần; việc con người duyệt báo cáo theo tiêu chí hướng dẫn vẫn đang chờ. Benchmark VietLex mới và adjudication pháp lý hiện hành cũng chưa có trong lượt phân tích. Vì vậy mục tiêu là mô tả bằng chứng sẵn có, không xác nhận tuân thủ học phần hoặc khả năng dùng hệ thống để tư vấn pháp luật.'''))
changes.append(set_start('Do không có đề bài/rubric chính thức,',
'''Hướng dẫn HCMUNRE có tiêu chí nhận xét nhưng không quy định thang điểm; trong hồ sơ hiện có chưa thấy đề bài hoặc rubric chấm điểm riêng. Vì vậy, mã CAP dưới đây là yêu cầu phân tích nội bộ được tái dựng từ route, template và handbook, không phải rubric hay yêu cầu đã được giảng viên xác nhận. Mỗi hàng có bằng chứng về handler hoặc view được khai báo; trạng thái runtime và chất lượng kết quả được đánh giá riêng.'''))
changes.append(set_start('Ở mức cao, VietLex chia thành bốn nhóm:',
'''Sơ đồ Hình 2.1 phân loại các route GET trả về trang HTML theo nhóm chức năng. GET / là màn hình hỏi đáp; POST /chat chỉ trả fragment vào vùng hội thoại nên được ghi ở nhóm hành động. Các trang tra cứu, tài liệu, workspace, tài khoản, thông tin và quản trị được ánh xạ theo handler; alias được gộp khi cùng một view. POST, JSON, redirect và partial không được tính là màn hình độc lập. Danh sách route, template và trạng thái bảo vệ nằm trong screen-inventory-v14.json.'''))
changes.append(set_start('Ví dụ, body search cần kiểm tra metadata/body',
'''Ví dụ, body search cần kiểm tra metadata/body và cảnh báo coverage; official research cần kiểm hash, owner, giới hạn trang và partial; chat cần kiểm text citation và answer. Muốn công bố hiệu quả cần gold set, denominators và human adjudication. CAP là tiêu chí phân tích kỹ thuật nội bộ vì hướng dẫn HCMUNRE không cung cấp thang điểm; chúng không được trình bày như tiêu chí chấm điểm chính thức.'''))
changes.append(set_start('Ngày 23/10/2026, ứng dụng tại https://vietlex-legal-rag.vercel.app',
'''Bộ capture ngày 23/10/2026 được ghi trong tab trình duyệt hiển thị, phiên ẩn danh, viewport 1440 × 1000 CSS px. Manifest có 13 lần chụp trên 11 route; từng trạng thái được chụp sau khi điều hướng qua UI, gồm trang chủ → thẻ Tra cứu → nhập số hiệu 45/2019/QH14 → gửi form GET → mở kết quả Bộ luật Lao động 2019. Manifest lưu URL cuối, click path, timestamp +07:00, HTTP/document status, console, page_state_review và SHA-256. DOCX chỉ chọn ba ảnh chứng minh luồng chính: GET /, kết quả GET /search và GET /documents/333670. Không mở local UI/file hoặc tải route đích trực tiếp. Không gửi POST/chat/AI, đăng nhập, gửi form tài khoản hoặc tạo workspace. Revision triển khai chưa được xác nhận độc lập.'''))
changes.append(set_start('Sơ đồ UML mô tả cấu trúc source;',
'''Sơ đồ UML mô tả cấu trúc source; ba ảnh runtime được đối chiếu với route/template và manifest ngày 23/10/2026. Chúng ghi nhận UI trong phiên ẩn danh tại thời điểm đó, không đại diện cho POST/API, quyền tài khoản, chất lượng câu trả lời hay toàn bộ trạng thái động.'''))
changes.append(set_start('Các lưu ý về mốc hiệu lực và phạm vi corpus',
'''Các lưu ý về mốc hiệu lực và phạm vi corpus là phần cần giữ vì giúp ngăn suy luận sai. Cải thiện tiếp theo nên làm nổi bật trạng thái mốc ngày ngay cạnh kết quả, phân biệt nhãn đã duyệt sự kiện với kết luận, cho biết body index có khả dụng hay không, và đưa đường dẫn về nguồn gốc bên cạnh citation. Với câu trả lời chat, cần bố cục để người dùng mở đoạn evidence trước khi dựa vào câu chữ tổng hợp.'''))
changes.append(set_start('Ảnh chụp được ghi nhận ngày 23/10/2026 tại viewport desktop',
'''Ba ảnh được chọn từ lượt clickthrough ngày 23/10/2026 tại viewport desktop 1440 × 1000 CSS px bằng tab trình duyệt hiển thị. Manifest đối chiếu từng ảnh với route/template và lưu URL cuối, bước UI, HTTP/document status, tiêu đề trang, lỗi/cảnh báo console và SHA-256. Ảnh hỗ trợ nhận xét về bố cục, nhãn và nội dung nhìn thấy; không xác nhận khả năng responsive, khả năng truy cập hoặc trạng thái động sau thao tác khác. Revision triển khai chưa được xác nhận độc lập.'''))
changes.append(set_start('Ảnh chụp runtime các trang VietLex',
'''Ảnh chụp runtime: luồng tra cứu chính''',style='Heading 2'))
changes.append(set_start('Các hình giao diện trong phần này là ảnh chụp runtime thật',
'''DOCX giữ ba ảnh runtime đã chọn trong cùng một luồng: trang hỏi đáp tại GET /, kết quả tìm Bộ luật Lao động 2019 sau khi gửi form GET tại /search, và trang đọc văn bản sau khi bấm kết quả tại /documents/333670. Ảnh được chụp riêng sau clickthrough trong phiên ẩn danh ngày 23/10/2026; mỗi caption dùng trường SEQ Word và route tương ứng. Các ảnh về trang hiệu lực, evaluation lab, workspace, tài khoản và chính sách không được chèn vì không bổ sung bằng chứng trực tiếp cho hành trình tìm và mở văn bản.'''))
changes.append(set_start('Ảnh chỉ xác nhận nội dung giao diện tại thời điểm truy cập;',
'''Các capture chỉ ghi nhận UI tại thời điểm truy cập; không chứng minh API/POST, quyền tài khoản, chất lượng câu trả lời hay tính đúng hiện hành của luật. Manifest còn có ảnh /legal-status, /evaluation-lab, /workspaces và các trang tài khoản/chính sách; chúng được giữ làm bằng chứng lưu trữ nhưng không chèn vì không trực tiếp minh họa luồng tra cứu. /settings cần session, /admin cần role admin, /verify-email và /reset-password cần token, chi tiết workspace cần workspace thuộc người dùng; /sessions là dữ liệu riêng nên không mở. Các trạng thái bảo vệ/token tiếp tục NOT_RUN.'''))
changes.append(set_start('Trong lượt làm báo cáo này không khởi chạy app cục bộ,',
'''Trong lượt làm báo cáo này không khởi chạy app cục bộ, truy vấn DB, gọi provider, chạy benchmark hay suite test mới. Có mở deployment công khai trong phiên ẩn danh bằng GET qua UI; một form GET tìm số hiệu 45/2019/QH14 được gửi để ghi nhận trang kết quả, sau đó mở trang chi tiết văn bản. DOCX giữ ba ảnh đại diện cho luồng đó. Không gửi POST/chat/câu hỏi AI, đăng nhập, gửi form tài khoản hoặc truy cập dữ liệu phiên riêng. Nguồn không kiểm runtime được ghi là snapshot/source evidence hoặc NOT_RUN.'''))
changes.append(set_start('Kết luận phù hợp là report có thể mô tả/phân tích source snapshot;',
'''Kết luận phù hợp là report có thể mô tả/phân tích source snapshot; bằng chứng chưa đủ chứng nhận legal-quality acceptance, full-corpus coverage hay production readiness. Cần benchmark có nguồn/gold, xác minh triển khai, human review theo bốn tiêu chí của hướng dẫn HCMUNRE và adjudication pháp lý hiện hành trong phạm vi được cấp phép.'''))
changes.append(set_start('Bản phân tích dựa trên source snapshot có ghi hash;',
'''Bản phân tích dựa trên source snapshot dirty có ghi hash; hướng dẫn HCMUNRE cung cấp tiêu chí nhận xét chính thức nhưng không nêu thang điểm/trọng số, còn đề bài hoặc rubric riêng của học phần chưa có trong hồ sơ. Lượt này không khởi chạy app cục bộ, truy vấn database/index, gọi provider, xác minh deployment, chạy benchmark mới hoặc kiểm tra hiệu lực luật hiện hành; chỉ ghi nhận ba trang công khai qua GET clickthrough trong phiên ẩn danh ngày 23/10/2026. Các giới hạn này không cho phép xác nhận chất lượng pháp lý hay mức sẵn sàng nộp bài.'''))
changes.append(set_start('Trước hết cần nhận đề bài/rubric chính thức',
'''Trước hết xác nhận học phần có đề bài hoặc rubric chấm điểm riêng hay không; hướng dẫn HCMUNRE đã cung cấp tiêu chí nhận xét nhưng không có thang điểm/trọng số. Sau đó đóng băng cấu hình, pipeline fingerprint, index snapshot, dataset và gold labels. Chạy retrieval-only eval có verified denominator, báo recall ở document/article/clause, MRR/nDCG nếu phù hợp, candidate survival, technical error, latency và coverage. Chạy answer eval trên cùng evidence với exact match/token metric, groundedness/citation check và human legal review tách biệt. Mọi run lưu log không chứa secret/PII và source hash.'''))
changes.append(set_start('Chuẩn bị cần nhận rubric,',
'''Chuẩn bị cần xác nhận có rubric riêng của học phần hay không, đồng thời đóng băng source/config/corpus, lưu revision và dirty diff hash, tạo dataset manifest và chốt question/gold với người chuyên môn. Hướng dẫn HCMUNRE cung cấp tiêu chí nhận xét nhưng không có scoring scale. Gold item nên có câu hỏi, task type, scope, target document/article/clause, citation text, ngày áp dụng, ngoại lệ, supporting URL/hash/page và quyết định adjudication. Ghi skip khi nhãn chưa đủ; không lấp bằng output của model.'''))
changes.append(set_start('Các giới hạn về rubric, runtime, benchmark mới',
'''Các giới hạn về thang điểm, human rubric review, runtime, benchmark mới và thẩm định nguồn pháp lý vẫn giữ nguyên; vì vậy báo cáo không tuyên bố submission readiness hoặc legal-quality acceptance.'''))
changes.append(set_start('Ma trận dưới đây là bản đồ evidence của báo cáo,',
'''Ma trận dưới đây là bản đồ evidence của báo cáo, không thay thế rubric. Các record src-vietlex-* là review nội bộ trên source snapshot dirty được ghi ngày 25/10/2026; hash và vị trí của các file đã đọc nằm trong claim-evidence-v14.csv và qa/source-snapshot-v14.json. Git không liệt kê được ba thư mục temporary evaluation do quyền truy cập, nên phạm vi snapshot bị giới hạn. Các record doi-* trỏ tới PDF học thuật đã tải và review đoạn hỗ trợ. Không có record nào ở đây xác nhận luật hiện hành hoặc deployment runtime.'''))
changes.append(set_start('Nguồn chủ chốt: app/main.py',
'''Nguồn chủ chốt gồm app/main.py và app/templates/index.html cho màn hình hỏi đáp; app/api/legal_routes.py và legal_search.html cho tra cứu; app/api/routes.py cho POST /chat; app/services/rag_pipeline.py cho điều phối RAG; app/services/retrieval.py, vertex_qdrant_retrieval.py và v3_article_expansion.py cho retrieval/evidence; app/ingestion/legal_text.py cho EvidenceChunk; docs/CURRENT_ARCHITECTURE.md cho contract/config/capacity; docs/evaluation/CURRENT_STATUS.md cho số liệu có ngày. Hash và vị trí kiểm tra hiện hành nằm trong claim-evidence-v14.csv cùng qa/source-snapshot-v14.json. Các claim này mô tả source snapshot, không chứng minh source đã deploy.'''))
changes.append(set_start('Ma trận CAP-01…CAP-12 dưới đây',
'''Ma trận CAP-01…CAP-12 dưới đây là yêu cầu nội bộ rút ra từ source; các dòng giữ trạng thái source reviewed, runtime/acceptance NOT_RUN trừ khi có receipt cụ thể. Hướng dẫn HCMUNRE có tiêu chí nhận xét chính thức và đã được đưa đầy đủ vào hai trang nhận xét, nhưng chưa có human review; rubric chấm điểm riêng của học phần (nếu có) chưa được cung cấp. Guide không nêu điểm hoặc trọng số; capability từ source không được gọi là rubric đã được GVHD duyệt.'''))
changes.append(set_start('Danh mục hình trong bài gồm phân cấp GET screens',
'''Danh mục hình trong bài gồm phân cấp GET screens và POST actions, use case, mô hình lớp rút gọn, kiến trúc retrieval theo hai cấu hình, sequence POST /chat, pipeline nạp dữ liệu, sequence đọc nguồn chính thức và ba ảnh runtime cho luồng tra cứu. Caption ảnh ghi rõ route; số thứ tự hình dùng trường SEQ Word.'''))
changes.append(set_start('Source .puml được giữ trong assets/uml/;',
'''Source .puml được giữ trong assets/uml/; PlantUML 1.2026.8 đã render các sơ đồ. Ba ảnh runtime được chọn từ 13 lần chụp trên 11 route công khai an toàn truy cập được trong phiên ẩn danh ngày 23/10/2026, viewport 1440 × 1000 CSS px. Manifest ghi từng route, tiêu đề, H1, bước điều hướng, timestamp +07:00, HTTP/document status, console, page_state_review và hash ảnh; ảnh được chụp sau clickthrough, không mở route đích trực tiếp. Luồng minh họa gồm gửi một form GET tra cứu và mở kết quả; không gửi POST/chat/AI hoặc dùng phiên đăng nhập cá nhân. Trang quản trị, /settings, chi tiết workspace và route cần token không được truy cập; /sessions không được mở vì có thể chứa lịch sử riêng. Revision deployment so với source dirty chưa được xác nhận.'''))
changes.append(set_start('UML D01–D05 được giữ',
'''UML D01–D07 được giữ vì có mục tiêu và source evidence tương ứng; D01 dùng sơ đồ phân cấp GET screens, POST actions và route không phải màn hình. Ba ảnh tại Hình 3.2–3.4 là runtime captures của /, kết quả /search và /documents/333670. Các ảnh còn lại trong manifest về hiệu lực, evaluation, workspace, đăng nhập/đăng ký/khôi phục mật khẩu, quyền riêng tư và điều khoản được giữ ngoài DOCX vì không trực tiếp chứng minh luồng tra cứu. Route admin, /settings, /verify-email, /reset-password, workspace detail và /sessions không được chụp; lý do được ghi trong manifest.'''))
# Remove only the screenshot material after the retained document-detail image/caption and before its limitations note.
paras=doc.paragraphs
start_caption=next(i for i,p in enumerate(paras) if p.style.name=='Caption' and p.text.startswith('HÌNH 3.6. Tra cứu sự kiện hiệu lực'))
start=next(i for i in range(start_caption-1,-1,-1) if paras[i]._p.xpath('.//w:drawing'))
end=next(i for i,p in enumerate(paras) if p.text.startswith('Các capture chỉ ghi nhận UI tại thời điểm truy cập;'))
assert start_caption-start<=2 and start>end-30 and end-start>=10, (start,start_caption,end)
for p in list(doc.paragraphs[start:end]):
 p._element.getparent().remove(p._element)
# Body-only first-line indentation. Use explicit Word paragraph properties, not tabs or spaces.
paras=doc.paragraphs
start_candidates=[i for i,p in enumerate(paras) if p.style.name=='Heading 1' and p.text.strip()=='MỞ ĐẦU' and i>200]
end_candidates=[i for i,p in enumerate(paras) if p.style.name=='Heading 1' and p.text.strip()=='DANH MỤC TÀI LIỆU THAM KHẢO']
assert len(start_candidates)==1 and len(end_candidates)==1, (start_candidates,end_candidates)
lo,hi=start_candidates[0],end_candidates[0]
indented=[]
for p in paras[lo+1:hi]:
 if p.style.name in ('Normal','Body Text') and p.text.strip() and not p._p.xpath('.//w:drawing'):
  p.paragraph_format.first_line_indent=Cm(1)
  indented.append(p.text[:70])
assert indented, 'no body paragraphs were indented'
doc.save(out)
print({'output':str(out),'initial_hash':sha(src),'removed_screenshot_paragraphs':end-start,'body_indent_paragraphs':len(indented),'first_line_indent_cm':1,'edits':changes,'paragraph_count':len(doc.paragraphs),'inline_shape_count':len(doc.inline_shapes),'new_sha256':sha(out)})
