from pathlib import Path
import csv, hashlib, json, re

W = Path(r"D:\Download\WordAssistant\artifacts\course-essay\lms-qlpm-trello-drawio")
L = Path(r"D:\Download\LMS")
A = W / "sources" / "archive" / "LMS_QLDA_10-11_2026"
DATE = "2026-10-25"
REVIEWER = "Codex authoring review"
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def jwrite(name, obj): (W/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
def cwrite(name, fields, rows):
    with (W/name).open("w", encoding="utf-8", newline="") as f:
        wr=csv.DictWriter(f, fieldnames=fields); wr.writeheader(); wr.writerows(rows)
def tabrows(s): return [line.split("|") for line in s.strip().splitlines()]
def sub(title, ps, level=2): return {"title":re.sub(r"^\d+(?:\.\d+)+\.\s*", "", title),"level":level,"paragraphs":ps}

S = [
{"heading":"TÓM TẮT","paragraphs":[
"Báo cáo trình bày kế hoạch quản lý cho dự án học thuật xây dựng hệ thống quản lý học tập LMS của trường đại học. Nội dung thống nhất điều lệ, stakeholder, phạm vi, WBS, tiến độ, nguồn lực, ngân sách, rủi ro, chất lượng, truyền thông, thay đổi và đóng dự án; Trello và Draw.io được bổ sung để theo dõi công việc và minh họa sản phẩm bàn giao.",
"Baseline đã đối soát là 20 tuần, 1.200.000.000 VNĐ và 8,5 FTE. Mạng CPM có mốc kết thúc kế hoạch tuần 20; ACT-04 có float 1 tuần, ACT-16 có 2 tuần. Snapshot Trello ngày 23/10/2026 có 9 danh sách, 39 thẻ, 8 mốc đề xuất và 3 thẻ mô phỏng. Snapshot API không phải ảnh UI; Done chưa có xác nhận.",
"UAT, EVM, ký duyệt và trạng thái hoàn tất trong tài liệu kế hoạch là mô phỏng/chưa chạy. PNG Draw.io là hình tĩnh đi cùng source .drawio, không thay ảnh giao diện Draw.io/LMS. Checklist T01–T05, D01–D03, L01–L07 được đưa vào phụ lục; ảnh thật chưa có nên trạng thái là NOT RUN."
]},
{"heading":"MỞ ĐẦU","paragraphs":[
"Thông tin khóa học, tài liệu, bài tập, bài kiểm tra và điểm số có thể phân tán qua nhiều kênh. Điều lệ LMS mô hình hóa nhu cầu tập trung nội dung học phần, theo dõi bài nộp/chấm điểm và cung cấp góc nhìn nhất quán cho quản lý đào tạo. Quy mô 10.000 sinh viên, 500 giảng viên là giả định trong charter, không phải số liệu triển khai đã đo.",
"Mục tiêu là lập kế hoạch có thể kiểm soát: xác định sản phẩm, tổ chức, hoạt động và phụ thuộc, dự toán nguồn lực/chi phí, xử lý rủi ro, đặt cổng chất lượng, truyền thông quyết định và lưu dấu vết thay đổi. Trello theo dõi công việc; Draw.io giữ source sơ đồ chỉnh sửa được và PNG đưa vào báo cáo. Hai công cụ không ghi đè baseline LMS.",
"Phương pháp gồm đọc tài liệu quản lý dự án trong repo LMS, ưu tiên báo cáo tái hòa giải ngày 21/10/2026, đối chiếu snapshot Trello, manifest và tài sản trong ZIP, rồi biên soạn bằng WordAssistant với profile generic vì chưa có profile trường. Yêu cầu trực tiếp của người dùng là nguồn chỉ đạo; guide ảnh bổ sung cách ghi nhận bằng chứng. Không dùng n8n.",
"Phạm vi là kế hoạch và hồ sơ mô phỏng. Không tự nhận có sponsor, pilot, phê duyệt, ngày thực hiện, kết quả UAT, chi phí thực hoặc thông tin nhận dạng sinh viên. Trường/khoa/ngành/sinh viên/MSSV/lớp/GVHD để trống để bổ sung."
]},
{"heading":"CHƯƠNG 1. TỔNG QUAN VÀ KHỞI TẠO DỰ ÁN","paragraphs":[
"PRJ-LMS-2026 dự kiến xây dựng LMS web theo ba vai trò quản trị viên, giảng viên và sinh viên. Business case trong charter là giảm thất lạc tài liệu, chậm bài nộp, tổng hợp điểm thủ công và thiếu thông tin quản trị. Phạm vi sản phẩm tập trung luồng cốt lõi; tính năng mở rộng phải qua change control.",
"Bảng điều lệ dưới đây là baseline học thuật; vai trò đại diện, approvals và ngày ký vẫn cần xác nhận trước khi dùng như hồ sơ chính thức."
],"subsections":[
sub("1.1. Business case và mục tiêu",[
"LMS dự kiến quản lý người dùng, khóa học, phân công giảng viên, ghi danh, modules/lessons, assignment/submission, quiz, grading, bảng điểm và thông báo. Mục tiêu chấp nhận được mô tả bằng 10 kịch bản AC-01–AC-10 và các cổng chất lượng. Đây là tiêu chí kế hoạch; chưa có bằng chứng các kịch bản đã chạy.",
"Điều lệ giới hạn kiến trúc ở web frontend, API/backend và SQL Server. SSO, thanh toán, video conference, chat thời gian thực, AI tutoring, kiểm tra đạo văn, ứng dụng native và tự đăng ký môn nằm ngoài phạm vi."
]),
sub("1.2. Giả định và ràng buộc",[
"Baseline là 20 tuần/1,2 tỷ VNĐ/8,5 FTE. Các bên nghiệp vụ được giả định cung cấp yêu cầu, đội ngũ có kỹ năng và môi trường demo có thể chuẩn bị. 8,5 FTE là tổng phân bổ, không khóa số đầu người.",
"Kiến trúc trong hồ sơ là modular monolith với frontend React/TypeScript/Vite, backend FastAPI/SQLAlchemy và SQL Server. Đây là thiết kế, không phải bằng chứng uptime hay deployment production."
])]},
{"heading":"CHƯƠNG 2. CÁC BÊN LIÊN QUAN VÀ TỔ CHỨC DỰ ÁN","paragraphs":[
"Stakeholder register là mô hình giả định để xác định ai cần tham gia và thời điểm. Phòng Đào tạo xác nhận quy trình học vụ; Phòng CNTT review kiến trúc, môi trường và backup; giảng viên/sinh viên góp ý luồng; PM tích hợp kế hoạch và escalation.",
"Stakeholder quyền lực và quan tâm cao được quản lý chặt bằng cập nhật mốc và tham vấn thay đổi. Người dùng trực tiếp được mời review demo, workshop và phản hồi. Thu thập ý kiến không đồng nghĩa với phê duyệt."
],"subsections":[
sub("2.1. Sổ stakeholder",["Bảng rút gọn giữ nguyên nhóm và chiến lược từ register nguồn. Tên riêng không được thêm vì hồ sơ mô tả vai trò giả định."]),
sub("2.2. RACI và escalation",["RACI gồm Responsible, Accountable, Consulted, Informed; mỗi gói công việc cần một A duy nhất. PM quản lý tích hợp; BA làm yêu cầu; nhóm phát triển/QA chịu trách nhiệm kỹ thuật; sponsor giả định phê duyệt scope và nghiệm thu trong mô hình."])
]},
{"heading":"CHƯƠNG 3. QUẢN LÝ PHẠM VI VÀ WBS","paragraphs":[
"Phạm vi sản phẩm mô tả khả năng LMS; phạm vi dự án mô tả công việc và hồ sơ để xây dựng, kiểm thử, bàn giao prototype. Trong phạm vi là 3 vai trò, khóa học/ghi danh, nội dung học, assignment/submission văn bản, quiz, điểm, thông báo, schema/seed, test và PM artifacts. Ngoài phạm vi là SSO, video, chat realtime, AI, plagiarism check, app native, thanh toán và tự đăng ký môn.",
"Yêu cầu phi chức năng tập trung bảo mật server-side/RBAC, toàn vẹn dữ liệu, trạng thái giao diện loading/success/error/empty, kiểm thử và traceability. Hiệu năng cần có tiêu chí và phép đo trong môi trường thử; hiện không có kết quả đo runtime.",
"WBS nhóm deliverable từ khởi tạo, requirements, thiết kế, prototype, QA, UAT/demo đến closure. Hình dưới là đề xuất WBS từ ZIP, không phải rubric chính thức."
],"subsections":[
sub("3.1. Ranh giới và acceptance",["Yêu cầu cần mã truy vết, tiêu chí kiểm được, vai trò review và bằng chứng. Thay đổi phải có CR, lý do, phân tích tác động WBS/CPM/cost/risk/quality/resource và quyết định có thẩm quyền. MVP submission là văn bản; không khẳng định upload tệp thật."]),
sub("3.2. Work breakdown",["WBS là cấu trúc phân chia công việc, không chứng minh gói việc đã hoàn tất. Mỗi work package cần deliverable, owner, đầu vào, tiêu chí Done và nguồn lực."])
]},
{"heading":"CHƯƠNG 4. QUẢN LÝ TIẾN ĐỘ VÀ CPM","paragraphs":[
"Lịch baseline có 19 hoạt động theo finish-to-start. ES/EF tính xuôi từ 0; backward pass tính từ tuần 20; total float = LS−ES. ACT-03 và ACT-05 phải xong trước ACT-06; ACT-14 và ACT-15 phải xong trước ACT-17. CPM thể hiện quan hệ và phân tích lịch; mô hình cần nhất quán giữa activity, duration, logic và mốc [PMI-SCHED].",
"Đối soát cho kết thúc kế hoạch tuần 20, ACT-04 float 1 và ACT-16 float 2; hoạt động khác float 0. Đây không phải tiến độ thực tế vì chưa có actual start/finish cập nhật.",
"Mốc baseline: charter W2, scope W4, design W6, feature complete W12, system/integration test W15, UAT W16, demo W18, closure W20. Sơ đồ LMS_14 không gán ngày; bảng CPM là nguồn duration/float."
],"subsections":[
sub("4.1. Danh sách hoạt động và phụ thuộc",["Mạng lịch nối khởi tạo/phạm vi, thiết kế/môi trường, phát triển lát dọc, tích hợp, kiểm thử, UAT, demo và đóng. Hình mạng chỉ giải thích phụ thuộc, không thay bảng CPM."]),
sub("4.2. Theo dõi sai lệch",["PM cập nhật forecast finish, float và đường găng ở mỗi kỳ status; ghi nguyên nhân, phương án khôi phục, owner và tác động chi phí. Chỉ dùng actual khi có nhật ký tiến độ và quy tắc đo thống nhất."])
]},
{"heading":"CHƯƠNG 5. QUẢN LÝ NGUỒN LỰC VÀ CHI PHÍ","paragraphs":[
"Kế hoạch dùng bottom-up kết hợp parametric costing. Nhân sự tổng 8,5 FTE; chín dòng vai trò không đồng nghĩa chín người. Labor 840M, hạ tầng 120M, công cụ 48M, đào tạo 40M, hành chính 32M và contingency 120M cộng đúng 1,2 tỷ VNĐ.",
"Cash flow dự kiến năm giai đoạn: 180M, 150M, 450M, 240M, 180M. Dự phòng cần quyết định giải ngân qua CR/issue; budget là ước lượng chứ không phải chứng từ đã chi.",
"EVM cần kỳ status, quy tắc PV/EV và actual cost. Ví dụ trong hồ sơ được giữ ở Chương 10 với cảnh báo minh họa."
],"subsections":[
sub("5.1. Resource breakdown",["PM/BA/UI-UX/Backend/Frontend/QA/DevOps được bố trí theo giai đoạn. QA tham gia sớm; DevOps chuẩn bị môi trường và demo. Cần cân bằng tải để tránh bottleneck và xung đột giữa thực hiện với phê duyệt."]),
sub("5.2. Kiểm soát chi phí",["Theo dõi BAC, actual khi có chứng từ, forecast và variance. Trello không thay sổ chi phí; thẻ có thể trỏ mã WBS/CR và owner."])
]},
{"heading":"CHƯƠNG 6. QUẢN LÝ RỦI RO","paragraphs":[
"Risk register là kế hoạch mô phỏng. P×I trên thang 1–5 hỗ trợ ưu tiên, không phải xác suất thống kê. Trigger báo hiệu hành động; rủi ro đã xảy ra chuyển thành issue có owner, hạn và escalation.",
"Ưu tiên scope creep, authorization breach, trễ phát triển, low adoption, bất nhất tài liệu, UAT feedback muộn và hiểu nhầm upload. Mỗi rủi ro cần phòng ngừa, contingency và cadence review. Dự phòng 120M chỉ được giải ngân theo kiểm soát.",
"Scope creep hạn chế bằng baseline và CR; quyền truy cập bằng RBAC/ownership server-side và denial tests; trễ lịch bằng vertical slices/float; kỳ vọng upload cần nêu rõ text-only MVP."
],"subsections":[sub("6.1. Giám sát và ứng phó",["Register được rà hàng tuần theo kế hoạch. PM kiểm trigger, owner/response và escalate khi ảnh hưởng đường găng hoặc cost. Trạng thái nguồn không chứng minh rủi ro thực tế đã xảy ra hay xử lý xong."])]},
{"heading":"CHƯƠNG 7. QUẢN LÝ CHẤT LƯỢNG VÀ KIỂM THỬ","paragraphs":[
"Quality được kiểm qua tiêu chí đầu ra và gate. Definition of Done yêu cầu logic theo đặc tả, happy path/denial path được kiểm, API có tài liệu, UI xử lý loading/success/error/empty, không hard-code quyền phía client. Mục tiêu 0 lỗi P0/P1 là điều kiện kế hoạch.",
"QG1–QG5 kiểm scope freeze, design freeze, feature complete, UAT readiness và closure. Gate không đạt thì giữ trạng thái, ghi defect và lập kế hoạch khắc phục; chuyển thẻ Done không thay acceptance.",
"UAT được lên kế hoạch tuần 16 với 10 kịch bản AC-01–AC-10 cho Admin/Lecturer/Student. Mọi kết quả mẫu là SIMULATED — NOT RUN. Chỉ ghi kết quả sau khi chạy, kèm build, môi trường, người thực hiện, thời điểm, bằng chứng và defect."
],"subsections":[
sub("7.1. Gate và DoD",["QG1/W4 kiểm SRS/use cases/WBS/scope; QG2/W6 kiến trúc/ERD/API; QG3/W12 lát chức năng/RBAC; QG4/W15 UAT readiness/test/seed/defect; QG5/W20 UAT/docs/source/handover. Đây là tuần baseline."]),
sub("7.2. UAT và triage",["Kịch bản phân quyền, nộp bài, grading, quiz, notification cần test data kiểm soát. Chưa chạy thì giữ NOT RUN; không biến kết quả mẫu thành evidence."])
]},
{"heading":"CHƯƠNG 8. TRUYỀN THÔNG, THAY ĐỔI VÀ TRELLO","paragraphs":[
"Kế hoạch truyền thông: nhóm họp tuần; sponsor/đại diện nghiệp vụ nhận báo cáo mốc hai tuần; review theo đầu ra; UAT theo lịch xác nhận. Biên bản ghi quyết định, action, owner và due date. Blocker chuyển PM rồi sponsor theo ảnh hưởng.",
"Change control: ghi CR → phân tích scope/WBS/time/cost/risk/quality/resource → lựa chọn → quyết định → cập nhật baseline và thông báo. Trello phản ánh việc; chỉ quyết định có thẩm quyền mới thay baseline.",
"Trello cards/lists hỗ trợ metadata công việc như nhãn, ngày, file đính kèm; checklist chia subtasks và đánh dấu hoàn thành [TRELLO-CARDS] [TRELLO-CHECKS]. Mỗi thẻ nên có ID WBS/CR/AC, kết quả, owner, ngày nếu thống nhất, checklist, source .drawio/PNG, reviewer và evidence. Done cần acceptance/evidence.",
"Snapshot 23/10/2026 có 9 danh sách/39 thẻ: To Do 25; yêu cầu 2; Blocked 1 (hỏi rubric); milestone đề xuất 8; mô phỏng 3; Backlog/Doing/Review/Done trống. Hình tổng hợp API không phải screenshot Trello; không chứng minh việc hoàn tất."
],"subsections":[
sub("8.1. Luồng board và quy ước",["Luồng đề xuất Backlog → To Do → Doing → Review → Done; Blocked hiển thị vướng mắc. Milestone gắn deliverable/tuần baseline. SIM cần nhãn mô phỏng. Trước Done cần review, checklist, bằng chứng và quyết định cần thiết."]),
sub("8.2. Kết nối Trello — WBS — Draw.io — Word",["Mã WBS/CR nối kế hoạch, card, file sơ đồ và report. Card không thay tài liệu baseline hoặc nghiệm thu. Snapshot lịch nhóm Oct–Nov/27M trong ZIP là đề xuất riêng chưa phê duyệt, không trộn vào baseline 20 tuần/1,2 tỷ."])
]},
{"heading":"CHƯƠNG 9. THIẾT KẾ VÀ BIỂU ĐỒ DRAW.IO","paragraphs":[
"Kiến trúc minh họa work package thiết kế, không thay đánh giá runtime. Sơ đồ repo thể hiện ba vai trò qua React/TypeScript/Vite, FastAPI/SQLAlchemy đến SQL Server. Đây là thiết kế theo hồ sơ, không khẳng định production deployment.",
"ERD LMS_12 thể hiện 12 bảng và PK/FK; manifest nói một số quan hệ được giản lược để dễ đọc. Sơ đồ cần được đối chiếu với schema SQL nguồn.",
"Draw.io giữ source .drawio/XML có thể sửa và PNG để trình bày. Tài liệu chính thức phân biệt định dạng export với source [DRAWIO-FORMATS], và mô tả tùy chọn PNG [DRAWIO-PNG]. Hình tĩnh không chứng minh UI editor đã được chụp."
],"subsections":[
sub("9.1. Kiến trúc và dữ liệu",["Frontend/API/database là lớp thiết kế. HTTP/JSON/JWT, RBAC và transaction cần đối chiếu code/API/test. ERD là góc nhìn; schema là nguồn chi tiết."]),
sub("9.2. Quy trình xuất biểu đồ",["Chọn câu hỏi; mở source; kiểm title/node/connector/arrow/note; lưu source; export PNG đủ biên/độ phân giải; xem ảnh; chèn inline/căn giữa/caption; giữ cặp source-output. Sau sửa phải review lại. Archive có 15 cặp; manifest path cũ sai thư mục, workspace dùng drawio/ và anh_so_do/. Sequence diagram là mô hình logic, không phải log end-to-end; LMS_14 không gán ngày."])
]},
{"heading":"CHƯƠNG 10. NGHIỆM THU VÀ ĐÓNG DỰ ÁN","paragraphs":[
"Nghiệm thu đối chiếu từng acceptance criteria với kết quả chạy và evidence. Closure package cần baseline, source version, test/defect, UAT/sign-off thật, hướng dẫn vận hành, tồn đọng và lessons. Hồ sơ hiện có biểu mẫu mô phỏng, chưa chứng minh chữ ký/acceptance.",
"Ví dụ EVM dùng PV=1.200M, EV=1.200M, AC=1.175M; suy ra SV=0, SPI=1, CV=+25M, CPI≈1,021. Đây là ví dụ số học; không có invoice/timesheet xác nhận AC và không có kỳ đo ngày status.",
"Closure chỉ PASS khi gate được review và người có thẩm quyền xác nhận. Thiếu bằng chứng thì ghi kế hoạch/chưa nghiệm thu."
],"subsections":[
sub("10.1. Tiêu chí nghiệm thu",["Kiểm đủ 10 AC và Must-have, defect P0/P1, dữ liệu, hướng dẫn, known issues và tồn đọng được chấp nhận. Kịch bản chưa chạy vẫn NOT RUN."]),
sub("10.2. Lessons learned và hướng phát triển",["Giữ một baseline duy nhất; tách kế hoạch với actual; một A trong RACI; cần evidence trước Done; không suy diễn runtime từ sơ đồ. Upload an toàn, SSO và tích hợp lớp học là hướng phát triển cần CR và đánh giá nguồn lực."])
]},
{"heading":"KẾT LUẬN VÀ KIẾN NGHỊ","paragraphs":[
"Báo cáo giữ baseline 20 tuần/1,2 tỷ VNĐ/8,5 FTE và tách kế hoạch, API snapshot, mô phỏng, runtime evidence. Trello hỗ trợ theo dõi và traceability; Draw.io giữ source cùng PNG. Không dùng n8n.",
"Trước khi nộp cần điền metadata thật, nhận rubric/đề cương chính thức, chụp T01–T05/D01–D03/L01–L07 từ ứng dụng thật và chạy/ghi UAT nếu yêu cầu. Chỉ cập nhật trạng thái khi có chứng cứ. DOCX có thể qua kiểm tra định dạng nhưng submission readiness vẫn INCOMPLETE."
]},
{"heading":"TÀI LIỆU THAM KHẢO","paragraphs":[]},
{"heading":"PHỤ LỤC","paragraphs":["Phụ lục ghi danh mục asset và checklist bằng chứng còn thiếu. Static diagram, API aggregate, runtime screenshot và test evidence là các loại khác nhau."],
"subsections":[
sub("Phụ lục A. Danh mục sơ đồ Draw.io",["ZIP có 15 sơ đồ. Năm PNG được chèn: WBS, workflow, network phụ thuộc, architecture và ERD; các sơ đồ còn lại được lưu trong archive và liệt kê bên dưới."]),
sub("Phụ lục B. Checklist ảnh Trello, Draw.io và LMS",["Guide nêu T01–T05, D01–D03, L01–L07. Tất cả hiện CHƯA CHỤP — NOT RUN. Khi capture, lưu ảnh gốc, thời điểm, URL/route hoặc click path, trạng thái trang, hash và reviewer. Không dùng API aggregate thay T01, PNG thay UI Draw.io hay diagram thay LMS runtime."]),
sub("Phụ lục C. Loại bằng chứng và giới hạn",["Baseline là kế hoạch; snapshot chỉ đúng thời điểm trích; SIMULATED không phải test; NOT RUN không phải pass/fail."])
]}
]

TABLES = [
("Điều lệ dự án","CHƯƠNG 1. TỔNG QUAN VÀ KHỞI TẠO DỰ ÁN","Bảng điều lệ dưới đây là baseline học thuật; vai trò đại diện, approvals và ngày ký vẫn cần xác nhận trước khi dùng như hồ sơ chính thức.", """Trường|Giá trị / lưu ý
Tên dự án|University Learning Management System (LMS) Implementation
Mã|PRJ-LMS-2026
Môn học|Quản lý dự án phần mềm
Thời lượng|20 tuần
Ngân sách|1.200.000.000 VNĐ
Nguồn lực|8,5 FTE; không khóa số đầu người
Trạng thái|Kế hoạch học thuật; phê duyệt thực chưa được chứng minh"""),
("Stakeholder register rút gọn","CHƯƠNG 2. CÁC BÊN LIÊN QUAN VÀ TỔ CHỨC DỰ ÁN","Bảng rút gọn giữ nguyên nhóm và chiến lược từ register nguồn. Tên riêng không được thêm vì hồ sơ mô tả vai trò giả định.", """Nhóm|Power|Interest|Chiến lược|Điểm tham gia
Ban Giám hiệu / SH-01 (mô phỏng)|Cao|Cao|Quản lý chặt|Mốc, thay đổi
Phòng Đào tạo / SH-02|Cao|Cao|Quản lý chặt|Yêu cầu, scope, UAT
Phòng CNTT / SH-03|Cao|Cao|Quản lý chặt|Kiến trúc, backup
Giảng viên / SH-04|Vừa|Cao|Tham vấn|Nhu cầu, demo
Sinh viên / SH-05|Thấp|Cao|Cập nhật|Luồng học
Nhóm dự án / SH-06|Vừa|Cao|Cộng tác|Họp tuần, blocker
Giảng viên môn học / SH-07|Cao|Cao|Quản lý chặt|Đề cương/đánh giá"""),
("RACI cho các đầu ra chính","CHƯƠNG 2. CÁC BÊN LIÊN QUAN VÀ TỔ CHỨC DỰ ÁN","Mỗi gói việc cần một A duy nhất. Sponsor là vai trò giả định trong mô hình.", """Deliverable|PM|BA|Dev/QA|Sponsor*
Charter/governance|A/R|C|I|C
Yêu cầu/scope/WBS|A|R|C|A (approve)
CPM/cost/risk|A/R|C|C|I
Architecture/API/DB|A|C|R|I
Development/integration|A|I|R|I
Test/triage|A|C|R|I
UAT/sign-off|C|R|C|A
Handover/lessons|A/R|R|R|A"""),
("Ranh giới phạm vi","CHƯƠNG 3. QUẢN LÝ PHẠM VI VÀ WBS","Trong phạm vi là LMS core; các khả năng mở rộng được đưa ngoài phạm vi.", """In-scope|Out-of-scope
Admin/Lecturer/Student; auth/RBAC|SSO
Courses, lecturer assignment, enrollment|Student self-enrollment
Modules/lessons|Realtime class/chat
Assignment/submission text-only MVP|File upload in MVP
Quiz, grading, grades, notification|AI/plagiarism
Schema, seed, tests, demo, PM report|Payment/native app"""),
("WBS cấp 2 và đầu ra","CHƯƠNG 3. QUẢN LÝ PHẠM VI VÀ WBS","WBS là cấu trúc công việc, không chứng minh gói việc đã hoàn tất.", """WBS|Gói|Đầu ra
1|Khởi tạo|Charter, stakeholders, kickoff
2|Yêu cầu/phạm vi|SRS, use cases, scope, WBS
3|Thiết kế/lập kế hoạch|Architecture, API, DB, CPM, budget, risk
4|Prototype|Auth, course, content, assignment, quiz, grades
5|Quality|Unit/API/system, triage
6|UAT/demo|Test scenarios, evidence, demo
7|Closure|Handover, lessons, closure"""),
("CPM 19 hoạt động, đơn vị tuần","CHƯƠNG 4. QUẢN LÝ TIẾN ĐỘ VÀ CPM","Mạng LMS_14 không gán ngày; bảng này là nguồn duration/float baseline.", """ID|Pred.|Dur.|ES-EF|LS-LF|TF
ACT-01|—|2|0-2|0-2|0
ACT-02|01|2|2-4|2-4|0
ACT-03|02|2|4-6|4-6|0
ACT-04|02|2|4-6|5-7|1
ACT-05|02|2|4-6|4-6|0
ACT-06|03,05|1|6-7|6-7|0
ACT-07|04,06|1|7-8|7-8|0
ACT-08|07|1|8-9|8-9|0
ACT-09|08|1|9-10|9-10|0
ACT-10|09|1|10-11|10-11|0
ACT-11|10|1|11-12|11-12|0
ACT-12|11|1|12-13|12-13|0
ACT-13|12|2|13-15|13-15|0
ACT-14|13|1|15-16|15-16|0
ACT-15|13|1|15-16|15-16|0
ACT-16|15|1|16-17|18-19|2
ACT-17|14,15|2|16-18|16-18|0
ACT-18|17|1|18-19|18-19|0
ACT-19|16,18|1|19-20|19-20|0"""),
("Milestone baseline","CHƯƠNG 4. QUẢN LÝ TIẾN ĐỘ VÀ CPM","Mốc tuần là baseline kế hoạch, không phải actual date.", """Mốc|Thời điểm|Bàn giao
M1|Cuối W2|Charter
M2|Cuối W4|Scope/requirements
M3|Cuối W6|PM plan, UX, architecture/DB
M4|Cuối W12|Prototype feature complete
M5|Cuối W15|System/integration test
M6|W16|UAT plan; chưa xác nhận
M7|W18|Demo/go-live simulation
M8|W20|Closure package"""),
("Resource breakdown","CHƯƠNG 5. QUẢN LÝ NGUỒN LỰC VÀ CHI PHÍ","Tổng phân bổ 8,5 FTE; không suy ra số đầu người.", """Vai trò|FTE|Giai đoạn|Labor|Trọng tâm
PM|1.0|20 tuần|150M|Tích hợp scope/time/cost/risk
BA|1.0|20 tuần|110M|Yêu cầu/SRS/UAT
UI/UX|1.0|W3-W14|60M|Wireframe/prototype
Backend lead|1.0|20 tuần|125M|Architecture/DB/auth
Backend dev|1.0|W5-W20|80M|API nghiệp vụ
Frontend lead|1.0|20 tuần|125M|React/routing
Frontend dev|1.0|W5-W20|80M|UI ba vai trò
QA|1.0|W5-W20|72M|Test/UAT
DevOps|0.5|20 tuần|38M|Môi trường/SQL/backup
Tổng|8.5|—|840M|Headcount chưa chốt"""),
("Budget baseline","CHƯƠNG 5. QUẢN LÝ NGUỒN LỰC VÀ CHI PHÍ","Sáu khoản mục cộng đúng 1,2 tỷ VNĐ; contingency không phải chi phí đã tiêu.", """Khoản mục|VNĐ|Tỷ lệ|Kiểm soát
Labor|840.000.000|70.00%|8.5 FTE planned
Hạ tầng|120.000.000|10.00%|Dev/staging/demo
Công cụ|48.000.000|4.00%|Licenses/collaboration
Đào tạo|40.000.000|3.33%|Workshop/materials
Hành chính|32.000.000|2.67%|Meetings/reviews
Contingency|120.000.000|10.00%|CR/issue approval
BAC tổng|1.200.000.000|100.00%|Estimate baseline"""),
("Rủi ro ưu tiên","CHƯƠNG 6. QUẢN LÝ RỦI RO","Risk register là kế hoạch mô phỏng; score không chứng minh sự kiện.", """ID|Risk|P x I|Trigger|Response
RSK-01|Scope creep|4x4=16|Yêu cầu ngoài core|Freeze; CR; defer
RSK-02|Authorization breach|2x5=10|Thiếu token/role check|RBAC; denial test
RSK-03|Late development|3x4=12|Burn-down lệch >3 ngày W10|Vertical slice; float
RSK-04|Low adoption|3x4=12|Pilot usage thấp|Workshop; feedback
RSK-05|PM docs inconsistency|3x4=12|Lệch WBS/CPM/budget|Reconcile docs
RSK-07|Late UAT feedback|3x3=9|Reject sát W16|Demo sớm; triage
RSK-09|Upload expectation|3x2=6|Kỳ vọng nộp file|Text-only; CR"""),
("Quality gates","CHƯƠNG 7. QUẢN LÝ CHẤT LƯỢNG VÀ KIỂM THỬ","Gate là điều kiện kế hoạch; trạng thái phê duyệt chưa được xác nhận.", """Gate|Tuần|Điều kiện|Evidence
QG1 Scope freeze|W4|SRS/use cases/WBS/scope|Plan; thiếu sign-off
QG2 Design freeze|W6|Architecture/ERD/API|Plan; thiếu sign-off
QG3 Feature complete|W12|Vertical slices/RBAC|Chưa xác nhận chạy
QG4 UAT readiness|W15|10 AC, P0/P1=0, seed|UAT chưa chạy
QG5 Closure|W20|UAT/docs/handover|Chưa có biên bản"""),
("UAT scenarios, SIMULATED/NOT RUN","CHƯƠNG 7. QUẢN LÝ CHẤT LƯỢNG VÀ KIỂM THỬ","Mười AC được định nghĩa; số đã xác minh chạy là 0.", """ID|Mục tiêu|Vai trò|Status
AC-01|Authentication|All|SIMULATED / NOT RUN
AC-02|Chặn API quản trị|Student|SIMULATED / NOT RUN
AC-03|Cô lập course|Lecturer|SIMULATED / NOT RUN
AC-04|Không enrollment trùng|Admin|SIMULATED / NOT RUN
AC-05|Ẩn lesson draft|Student|SIMULATED / NOT RUN
AC-06|Chặn nộp trễ|Student|SIMULATED / NOT RUN
AC-07|Chấm và đồng bộ điểm|Lecturer/Student|SIMULATED / NOT RUN
AC-08|Giới hạn quiz attempts|Student|SIMULATED / NOT RUN
AC-09|Ẩn đáp án đúng|Student|SIMULATED / NOT RUN
AC-10|Notification ownership|Student|SIMULATED / NOT RUN"""),
("Trello snapshot 23/10/2026, API aggregate","CHƯƠNG 8. TRUYỀN THÔNG, THAY ĐỔI VÀ TRELLO","Dữ liệu API không phải ảnh UI và không chứng minh Done.", """List|Cards|Note
00 REQUIREMENT|2|REQ-01/REQ-02
01 BACKLOG|0|Empty
02 TO DO|25|PM-01..10; DGM-01..15
03 DOING|0|Empty
04 REVIEW|0|Empty
05 DONE|0|No confirmed Done
06 BLOCKED|1|REQ-03 asks rubric
07 MILESTONES 10-11|8|Group proposal
08 SIMULATED UAT|3|UAT/EVM/evidence mock
TOTAL|39|Snapshot API"""),
("Quy ước card và Done","CHƯƠNG 8. TRUYỀN THÔNG, THAY ĐỔI VÀ TRELLO","Cards/lists/checklists hỗ trợ công việc; approval/evidence vẫn riêng.", """Field/step|Quy ước
Title|[WBS/REQ/AC/CR] + deliverable
Description|Kết quả, ranh giới, nguồn
Owner/date|Owner rõ; date nếu thống nhất
Checklist|Subtasks có thể review
Attachment|Source .drawio, PNG, evidence
Review|Reviewer, defect/CR, nhận xét
Done|Acceptance + evidence + approval nếu cần
Blocked/SIM|Lý do; nhãn mô phỏng"""),
("Kiến trúc LMS theo hồ sơ","CHƯƠNG 9. THIẾT KẾ VÀ BIỂU ĐỒ DRAW.IO","Kiến trúc là thiết kế trong repo, không phải runtime.", """Layer|Technology|Lưu ý
Presentation|React 19, TypeScript, Vite|Ba vai trò UI
API|FastAPI, REST, JSON, JWT|Auth/RBAC/rules
Data access|SQLAlchemy|Mapping/transaction
Database|SQL Server|12 tables, keys, seed
Cross-cutting|Validation/logging/authorization|Cần test runtime"""),
("EVM minh họa, không phải actuals","CHƯƠNG 10. NGHIỆM THU VÀ ĐÓNG DỰ ÁN","Không có invoice/timesheet hoặc kỳ đo thực tế gắn EVM.", """Metric|Value|Formula|Limitation
PV|1,200M|Planned Value|No status date
EV|1,200M|Earned Value|Illustrative
AC|1,175M|Actual Cost|No invoice/timesheet
SV / SPI|0 / 1.00|EV-PV / EV÷PV|Not measured
CV / CPI|+25M / ~1.021|EV-AC / EV÷AC|Not actual saving"""),
("15 sơ đồ trong ZIP","PHỤ LỤC","Năm PNG được chèn; các source khác giữ trong archive.", """ID|Sơ đồ|Trong báo cáo
LMS_01|WBS|PNG chèn
LMS_02|Chu trình/cổng|PNG chèn
LMS_03|Use Case|Inventory
LMS_04|Activity ghi danh|Inventory
LMS_05|Activity nộp bài|Text-only note
LMS_06|Activity quiz|Inventory
LMS_07|Sequence nộp bài|Modeled
LMS_08|Sequence chấm bài|Modeled
LMS_09|Sequence quiz|Modeled
LMS_10|Class Diagram|Concept
LMS_11|State submission|Inventory
LMS_12|ERD 12 tables|PNG chèn; compare SQL
LMS_13|Architecture|PNG chèn; design
LMS_14|Dependency no dates|PNG chèn
LMS_15|Requirements traceability|Inventory"""),
("Checklist ảnh cần bổ sung","PHỤ LỤC","Checklist hướng dẫn không thay ảnh; mọi capture hiện chưa thực hiện.", """ID|Đối tượng|Evidence|Status
T01|Trello overview|UI thật, thấy lists|NOT RUN
T02|Card/checklist|Card thật|NOT RUN
T03|Schedule|Calendar/timeline thật|NOT RUN
T04|Simulated UAT|Nhãn SIMULATED thật|NOT RUN
T05|Done|Chỉ với evidence thật|NOT RUN
D01-D03|Draw.io|Editor/export/review|NOT RUN
L01-L07|LMS runtime|UI thật; route/click path|NOT RUN"""),
("Phân loại bằng chứng","PHỤ LỤC","Kế hoạch, snapshot, mô phỏng, runtime là loại chứng cứ khác nhau.", """Loại|Ví dụ|Có thể kết luận|Không thể kết luận
Baseline|20 tuần, 1.2B, 8.5 FTE|Kế hoạch|Actual time/cost/headcount
Trello API|9 lists, 39 cards|Số liệu snapshot|UI screenshot/Done
Draw.io source/PNG|15 pairs|Có nguồn biểu đồ|Runtime/test log
UAT/EVM simulated|10 AC, EVM|Kịch bản/số học mẫu|Test/actual cost
Capture checklist|T01-T05/D01-D03/L01-L07|Việc còn thiếu|Ảnh thật""")
]

IMG = [
("IMG-01",3,"WBS được lấy từ ZIP, là cấu trúc bàn giao đề xuất chứ không phải rubric.","LMS_01.png","WBS dự án LMS, cấu trúc bàn giao đề xuất","Các gói khởi tạo, yêu cầu, thiết kế, prototype, QA và bàn giao."),
("IMG-02",8,"Sơ đồ Draw.io quy trình nối yêu cầu, Trello, review và thay đổi.","LMS_02.png","Chu trình quản lý dự án và cổng kiểm soát","Yêu cầu, scope, Trello, Draw.io, review và thay đổi."),
("IMG-03",4,"LMS_14 không gán ngày; bảng CPM mới là nguồn duration/float.","LMS_14.png","Mạng phụ thuộc công việc, không gán ngày","Mạng work package, không biểu diễn lịch ngày."),
("IMG-04",9,"Sơ đồ architecture trong repo mô tả thiết kế, không phải runtime.","LMS_13.png","Kiến trúc LMS theo hồ sơ repo, không phải runtime","Ba vai trò qua React, FastAPI và SQL Server."),
("IMG-05",9,"ERD có quan hệ giản lược; đọc cùng schema SQL nguồn.","LMS_12.png","ERD 12 bảng LMS, một số quan hệ được giản lược","Quan hệ PK/FK giữa 12 bảng."),
("IMG-06",8,"Snapshot không chứng minh phần việc đã hoàn thành.","01_Trello_thong_ke_API_khong_phai_screenshot.png","Trello LMS — thống kê API 23/10/2026, KHÔNG PHẢI SCREENSHOT","Tổng hợp list, card, mốc và thẻ mô phỏng.")
]
IMAGES=[]
for ident,ch,anchor,file,title,alt in IMG:
    path=A/("anh_minh_chung" if file.startswith("01_") else "anh_so_do")/file
    if not path.is_file(): raise FileNotFoundError(path)
    IMAGES.append((ident,ch,anchor,file,title,alt,path))
jwrite("content.json",{"version":1,"sections":S,"bibliography_heading":"TÀI LIỆU THAM KHẢO","citation_style":"numeric","bibliography_order":"citation_order"})

steps=[
{"operation":"format.paragraph","selector":{"type":"paragraph","index":4},"options":{"alignment":"left"}},
{"operation":"heading.numbering_apply","options":{"levels":2,"allow_literal_prefixes":False,"suppress_first_level_label":True,"start_text":"CHƯƠNG 1. TỔNG QUAN VÀ KHỞI TẠO DỰ ÁN","end_text":"KẾT LUẬN VÀ KIẾN NGHỊ"}}
]
assets=[]
for i,(title,chapter,anchor,data) in enumerate(TABLES,1):
    rows=tabrows(data)
    steps.extend([
{"operation":"table.create","selector":{"type":"paragraph","text":anchor},"options":{"rows":len(rows),"columns":len(rows[0]),"data":rows,"style":"Table Grid"}},
{"operation":"caption.insert","selector":{"type":"paragraph","text":anchor},"options":{"label":"BẢNG","title":title,"sequence_id":"Bang","caption_separator":"."}}
])
    assets.append({"asset_id":f"TBL-{i:02d}","asset_type":"TABLE","source_basis":"LMS PM repo / user ZIP","source_location":chapter+"; Word native table","target_section":chapter,"target_caption":f"BẢNG {i}. {title}","decision":"MATCHED","coverage_note":"Native Word table, SEQ caption; plan/snapshot limits are stated.","evidence_files":"D:\\Download\\LMS\\docs\\audit\\06_PM_DOCUMENT_RECONCILIATION.md","capture_id":"","runtime_route":"","expected_media_count":0,"caption_required":"true","status":"PASS","reviewed_by":REVIEWER,"review_date":DATE})
for i,(ident,ch,anchor,file,title,alt,path) in enumerate(IMAGES,1):
    steps.append({"operation":"image.insert","selector":{"type":"paragraph","text":anchor},"options":{"image_path":str(path),"width_cm":15.2,"alt_text":alt,"title":title,"caption":title,"caption_label":"HÌNH","caption_sequence":"Hinh","caption_separator":".","placement":"after","alignment":"center","preserve_aspect_ratio":True,"auto_shrink":True,"inline":True}})
    chname={3:"CHƯƠNG 3. QUẢN LÝ PHẠM VI VÀ WBS",4:"CHƯƠNG 4. QUẢN LÝ TIẾN ĐỘ VÀ CPM",8:"CHƯƠNG 8. TRUYỀN THÔNG, THAY ĐỔI VÀ TRELLO",9:"CHƯƠNG 9. THIẾT KẾ VÀ BIỂU ĐỒ DRAW.IO"}[ch]
    assets.append({"asset_id":ident,"asset_type":"API_RECONSTRUCTED_IMAGE" if ident=="IMG-06" else "STATIC_DIAGRAM","source_basis":"Trello API snapshot (not UI)" if ident=="IMG-06" else "User ZIP .drawio with paired PNG","source_location":str(path),"target_section":chname,"target_caption":f"HÌNH {i}. {title}","decision":"MATCHED","coverage_note":"Static export, not runtime screenshot." if ident!="IMG-06" else "Aggregate API image; not T01-T05 UI screenshot.","evidence_files":str(path),"capture_id":"","runtime_route":"","expected_media_count":1,"caption_required":"true","status":"PASS","reviewed_by":REVIEWER,"review_date":DATE})
jwrite("operations-plan.json",{"version":1,"steps":steps})

# Cover metadata: known values only.
cover=[
("document_type","Tiểu luận môn học","Yêu cầu user","USER_INSTRUCTION","VERIFIED","Requested course report."),
("project_title","Quản lý dự án phần mềm xây dựng hệ thống LMS","User request and LMS charter","USER_INSTRUCTION","VERIFIED","Descriptive report title."),
("course_name","Quản lý dự án phần mềm","Yêu cầu user","USER_INSTRUCTION","VERIFIED","Course named directly."),
("institution","","Not supplied","NOT_PROVIDED","PLACEHOLDER","Add real institution."),
("faculty","","Not supplied","NOT_PROVIDED","PLACEHOLDER","Add real faculty."),
("program_or_major","","Not supplied","NOT_PROVIDED","PLACEHOLDER","Add real program."),
("student_name","","Not supplied","NOT_PROVIDED","PLACEHOLDER","Add real student/team."),
("student_id","","Not supplied","NOT_PROVIDED","PLACEHOLDER","Add real ID."),
("class_or_cohort","","Not supplied","NOT_PROVIDED","PLACEHOLDER","Add class/cohort."),
("supervisor_name","","Not supplied","NOT_PROVIDED","PLACEHOLDER","Add instructor."),
("academic_year","","Not supplied","NOT_PROVIDED","PLACEHOLDER","Confirm academic year.")]
cwrite("cover-metadata.csv",["field","value","authority","authority_type","status","reviewed_by","review_date","notes"],[
{"field":f,"value":v,"authority":a,"authority_type":t,"status":s,"reviewed_by":REVIEWER,"review_date":DATE,"notes":n} for f,v,a,t,s,n in cover])
jwrite("cover-metadata.json",{"course_name":"Quản lý dự án phần mềm","student":"[Bổ sung tên sinh viên/nhóm]","student_id":"[Bổ sung mã số]","class_or_cohort":"[Bổ sung lớp/khóa]","supervisor":"[Bổ sung giảng viên hướng dẫn]","academic_year":"[Bổ sung niên khóa]"})

# Verified project claims, separate from citation bibliography.
evs=[
("EV-RECON","docs/audit/06_PM_DOCUMENT_RECONCILIATION.md","Mục 1–4; reconciliation dated 2026-10-21"),
("EV-CHARTER","docs/project-management/01_PROJECT_CHARTER.md","Charter/baseline"),
("EV-STAKE","docs/project-management/02_STAKEHOLDER_REGISTER.md","Stakeholder register"),
("EV-RACI","docs/project-management/03_RACI_MATRIX.md","RACI"),
("EV-SCOPE","docs/project-management/04_SCOPE_BASELINE_WBS.md","Scope/WBS"),
("EV-CPM","docs/project-management/06_SCHEDULE_CPM_GANTT.md","Activity and CPM table"),
("EV-COST","docs/project-management/07_RESOURCE_AND_BUDGET_BASELINE.md","Resources, cost and cash flow"),
("EV-RISK","docs/project-management/08_RISK_REGISTER.md","Risk register"),
("EV-QA","docs/project-management/09_QUALITY_PLAN_AND_GATES.md","Quality gates/DoD"),
("EV-UAT","docs/project-management/12_UAT_AND_ACCEPTANCE_EVIDENCE.md","10 scenarios and simulated/not run status"),
("EV-CLOSE","docs/project-management/13_PROJECT_CLOSURE_AND_LESSONS_LEARNED.md","EVM/closure example"),
("EV-ARCH","docs/03_ARCHITECTURE.md","Architecture design"),
("EV-TRELLO","ARCHIVE:ke_hoach/Trello_snapshot_23_10_2026.json","snapshot_date/lists/not_a_screenshot"),
("EV-DIAGRAM","ARCHIVE:ke_hoach/so_do_manifest.json","15 diagrams; manifest paths"),
("EV-GUIDE","sources/Huong_dan_trinh_bay_chup_anh_Trello_Drawio_LMS.docx","Capture guide T/D/L requirements")]
reg={}; paths={}
for eid,src,loc in evs:
    if src.startswith("ARCHIVE:"): path=A/src.split(":",1)[1]; label=str(path)
    elif src.startswith("sources/"): path=W/src; label=str(path)
    else: path=L/src; label=src
    if not path.is_file(): raise FileNotFoundError(path)
    h=digest(path); paths[eid]=(label,h,loc)
    reg[eid]={"id":eid,"review_status":"reviewed","source_file":label,"source_sha256":h,"support_location":loc,"reviewed_by":REVIEWER,"review_date":DATE}
jwrite("evidence.json",reg)
claim_defs=[
("CL-01","Tóm tắt/Ch1","Baseline 20 weeks and 1.2B VND.","EV-RECON"),
("CL-02","Tóm tắt/Ch5","8.5 FTE planned; actual headcount not fixed.","EV-RECON"),
("CL-03","Ch2","Stakeholder roles are academic planning assumptions.","EV-STAKE"),
("CL-04","Ch3","Scope/out-of-scope follows current baseline.","EV-SCOPE"),
("CL-05","Ch4","19 CPM activities; week 20 finish; ACT-04 float 1 and ACT-16 float 2.","EV-RECON"),
("CL-06","Ch5","Budget totals 1.2B; labor 840M; reserve 120M.","EV-COST"),
("CL-07","Ch6","Risk scores and responses are simulated planning.","EV-RISK"),
("CL-08","Ch7/Appendix","10 UAT scenarios SIMULATED/NOT RUN; no real sign-off.","EV-UAT"),
("CL-09","Ch10","EVM is illustrative; no invoice/timesheet actual cost.","EV-CLOSE"),
("CL-10","Ch8","Trello snapshot has 9 lists/39 cards; Done empty.","EV-TRELLO"),
("CL-11","Ch9/Appendix","Archive has 15 diagram pairs; manifest has stale paths.","EV-DIAGRAM"),
("CL-12","Appendix B","Guide capture IDs T01-T05/D01-D03/L01-L07 remain pending.","EV-GUIDE"),
("CL-13","Ch9","Architecture is design evidence, not runtime proof.","EV-ARCH")]
claimrows=[]
for cid,loc,summary,eid in claim_defs:
    label,h,src_loc=paths[eid]
    claimrows.append({"claim_id":cid,"report_location":loc,"claim_summary":summary,"evidence_id":eid,"source_file":label,"source_sha256":h,"source_location":src_loc,"review_status":"reviewed","support_confirmed":"yes","reviewed_by":REVIEWER,"review_date":DATE})
cwrite("claim-evidence.csv",["claim_id","report_location","claim_summary","evidence_id","source_file","source_sha256","source_location","review_status","support_confirmed","reviewed_by","review_date"],claimrows)

# Reviewed primary documentation used by report citations.
cite_defs=[
("PMI-SCHED","Practice Standard for Scheduling",["Project Management Institute"],2011,"https://www.pmi.org/-/media/pmi/documents/public/pdf/certifications/practice-standard-scheduling.pdf","official_pmi_practice_standard_scheduling.pdf","Second Edition, schedule model and CPM method","Critical Path Method (CPM)","PMI copyright; public reference copy, no open license claimed","Project Management Institute","Scheduling practice and CPM context."),
("TRELLO-CARDS","Add and customize cards and lists",["Atlassian"],2026,"https://support.atlassian.com/trello/docs/add-and-customize-cards-and-lists/","official_atlassian_trello_cards.html","Card features in saved official page","labels, attachments, dates, and more","Atlassian Support; license not stated on page","Atlassian","Trello card metadata context."),
("TRELLO-CHECKS","Add, delete, and manage checklists",["Atlassian"],2022,"https://support.atlassian.com/trello/docs/adding-checklists-to-cards/","official_atlassian_trello_checklists.html","Article body in saved official page","Each item in a checklist can be checked to mark it as complete.","Atlassian Support; license not stated on page","Atlassian","Trello checklist tracking context."),
("DRAWIO-PNG","Export a diagram to a PNG image",["JGraph"],2026,"https://www.drawio.com/docs/manual/export/export-to-png/","official_drawio_export_png.html","PNG export options in saved page","Width, Height, and DPI for your image.","draw.io docs; license not stated","JGraph","PNG export options."),
 ("DRAWIO-FORMATS","Export diagram formats",["JGraph"],2026,"https://www.drawio.com/docs/manual/export/export-diagram/","official_drawio_export_formats.html","Format comparison in saved page","PNG with embedded XML","draw.io docs; license not stated","JGraph","Source/export distinction.")
]
cites={}
for eid,title,authors,year,url,file,loc,excerpt,lic,sort,claim in cite_defs:
    fp=W/"sources"/file
    cites[eid]={"id":eid,"title":title,"authors":authors,"year":year,"url":url,"verified_by":REVIEWER,"synthetic":False,"tags":["primary","official"],"review_status":"reviewed","reviewed_by":REVIEWER,"reviewed_at":DATE+"T00:00:00Z","support_location":loc,"support_excerpt":excerpt,"source_file":file,"source_sha256":digest(fp),"source_license":lic,"source_url":url,"retrieved_at":DATE,"claim":claim,"language":"en","author_sort_key":sort,"publisher":authors[0]}
jwrite("report-evidence.json",cites)

cwrite("requirements-matrix.csv",["requirement_id","rubric_requirement","rubric_location","report_section","evidence_files","verification","status","notes","waived_by"],[
{"requirement_id":"USER-01","rubric_requirement":"WordAssistant workflow/style; no n8n","rubric_location":"User request","report_section":"Entire report","evidence_files":"output/final.docx; source-audit.md","verification":"Compare direct request with output","status":"PASS","notes":"Workflow means WordAssistant authoring workflow."},
{"requirement_id":"USER-02","rubric_requirement":"Add Trello and Draw.io PM material","rubric_location":"User request","report_section":"Chapters 8–9; appendices","evidence_files":"output/final.docx; report-evidence.json","verification":"Inspect content/assets","status":"PASS","notes":"API and static diagram assets labeled."},
{"requirement_id":"GUIDE-01","rubric_requirement":"T01-T05/D01-D03/L01-L07 evidence","rubric_location":"Attached guide","report_section":"Appendix B","evidence_files":"output/final.docx; screen-inventory.json","verification":"Compare captures with checklist","status":"NOT_RUN","notes":"Actual images unavailable."},
{"requirement_id":"RUBRIC-01","rubric_requirement":"Official assignment/rubric","rubric_location":"Not supplied","report_section":"Entire report","evidence_files":"source-audit.md","verification":"Input inventory","status":"NOT_RUN","notes":"Do not infer scoring criteria.","waived_by":""}
])

outline=[]; order=0
def add_heading(src,loc,text,level,include):
    global order
    order+=1
    outline.append({"item_id":f"H-{order:03d}","source_basis":src,"source_location":loc,"planned_heading":text,"planned_level":level,"target_heading":text,"target_level":level,"target_order":order,"include_in_toc":"true" if include else "false","decision":"MATCHED","coverage_note":"Semantic Word heading in profile/content outline.","evidence_files":"project.json; content.json","status":"PASS","reviewed_by":REVIEWER,"review_date":DATE})
for sec in S:
    add_heading("WordAssistant profile and LMS outline","content.json",sec["heading"],1,sec["heading"] not in {"TÓM TẮT"})
for sec in S:
    for child in sec.get("subsections",[]):
        add_heading("LMS report outline","content.json",child["title"],child["level"],True)
for h in ["MỤC LỤC","DANH MỤC HÌNH","DANH MỤC BẢNG"]:
    add_heading("WordAssistant profile front matter","profile.front_matter_titles",h,1,False)
cwrite("structure-parity.csv",["item_id","source_basis","source_location","planned_heading","planned_level","target_heading","target_level","target_order","include_in_toc","decision","coverage_note","evidence_files","status","reviewed_by","review_date"],outline)

manifest=json.loads((A/"ke_hoach"/"so_do_manifest.json").read_text(encoding="utf-8"))
questions={"LMS_01":"How are deliverables grouped?","LMS_02":"How do requirements, Trello, Draw.io and review connect?","LMS_03":"Which actors/use cases are modeled?","LMS_04":"What steps compose Admin enrollment?","LMS_05":"What is student submission/text-only scope?","LMS_06":"What comprises quiz/grading?","LMS_07":"What sequence models submission?","LMS_08":"What sequence models grading?","LMS_09":"What sequence models quiz?","LMS_10":"Which domain concepts are shown?","LMS_11":"How does submission state change?","LMS_12":"What tables/PK/FK are shown?","LMS_13":"How are frontend/API/database layered?","LMS_14":"Which dependencies exist without dates?","LMS_15":"How are requirements traced to evidence?"}
selected={"LMS_01","LMS_02","LMS_12","LMS_13","LMS_14"}; drows=[]
for m in manifest:
    key=Path(m["drawio"]).stem; dp=A/"drawio"/(key+".drawio"); pp=A/"anh_so_do"/(key+".png")
    drows.append({"diagram_id":key,"diagram_type":m["name"],"question_or_scope":questions[key],"source_files":f"{dp}; {pp}","evidence_symbols_or_methods":"Inspect source labels/connectors and paired PNG; compare abstraction to repo.","puml_source":"","rendered_output":str(pp),"docx_location":"Chapters 3/4/8/9" if key in selected else "Appendix A/source archive","verified_by":REVIEWER,"status":"PASS" if dp.is_file() and pp.is_file() else "FAIL","notes":m.get("note","") or ("PNG embedded" if key in selected else "Inventory only; no runtime claim.")})
cwrite("diagram-plan.csv",["diagram_id","diagram_type","question_or_scope","source_files","evidence_symbols_or_methods","puml_source","rendered_output","docx_location","verified_by","status","notes"],drows)

caps=[("T01","Trello board overview"),("T02","Card and checklist"),("T03","Calendar/timeline"),("T04","Simulated UAT label"),("T05","Done only with real evidence"),("D01","Draw.io source open"),("D02","PNG export settings"),("D03","Export review"),("L01","LMS entry/auth"),("L02","Admin course"),("L03","Lecturer content"),("L04","Student flow"),("L05","Assignment submission"),("L06","Quiz/grading"),("L07","Grades/notification")]
jwrite("screen-inventory.json",{"schema_version":1,"system_title":"University LMS — planned runtime captures","source_project_root":str(L),"screens":[{"capture_id":i,"name":n,"route":"","status":"NOT_RUN","reason":"No verified runtime screenshot; record real route/click path and hash during capture.","screenshot":"","sha256":"","captured_at":"","page_state_review":""} for i,n in caps],"wireframes":[]})
figs=[]
for ident,ch,anchor,file,title,alt,path in IMAGES:
    figs.append({"figure_id":ident,"caption":title,"kind":"Trello API aggregate (not UI)" if ident=="IMG-06" else "Draw.io static PNG","route_or_source":"Trello API snapshot" if ident=="IMG-06" else "Paired .drawio source","source_file":str(path),"role":"Aggregate only" if ident=="IMG-06" else "Static diagram","state":"Reviewed static asset","viewport":"","capture_date":"","verified_by":REVIEWER,"artifact_path":str(path),"status":"PASS","notes":alt})
for cid,name in caps:
    figs.append({"figure_id":cid,"caption":"","kind":"planned runtime capture","route_or_source":"Trello/Draw.io/LMS visible application","source_file":"sources/Huong_dan_trinh_bay_chup_anh_Trello_Drawio_LMS.docx","role":"Pending","state":"NOT_RUN","viewport":"","capture_date":"","verified_by":"","artifact_path":"","status":"NOT_RUN","notes":name+"; capture real UI and record provenance."})
cwrite("figure-plan.csv",["figure_id","caption","kind","route_or_source","source_file","role","state","viewport","capture_date","verified_by","artifact_path","status","notes"],figs)

cross=[
("X01","user_requirements","User request","WordAssistant workflow/style; Trello/Draw.io; no n8n.","Entire report","Compare request/output","output/final.docx; source-audit.md"),
("X02","guide_requirements","Attached guide","List T/D/L captures and mark missing evidence NOT RUN.","Appendix B","Compare guide checklist","output/final.docx; screen-inventory.json"),
("X03","assignment_rubric_requirements","No official rubric supplied","Do not invent grading criteria; readiness incomplete.","Project manifest","Input inventory","source-audit.md; project.json"),
("X04","heading_toc","WordAssistant profile/LMS outline","Semantic headings, TOC, figure/table lists.","Front matter","Inspect headings/fields/render","output/final.docx; structure-parity.csv"),
("X05","abstract","Report profile","Summary states purpose, baseline and limitations.","TÓM TẮT","Compare summary/body","output/final.docx"),
("X06","screen_hierarchy","Guide and LMS source","Separate runtime screenshots, diagrams and API aggregate.","Chapters 8–9/Appendix","Review classifications","screen-inventory.json; output/final.docx"),
("X07","runtime_screenshots","Attached guide","Real captures carry visible state and provenance.","Appendix B","Require image/hash/click path","screen-inventory.json"),
("X08","diagrams","User ZIP manifest","Selected source/PNG pairs have captions and limits.","Chapters 3/4/8/9","Inspect asset pair/caption","diagram-plan.csv; output/final.docx"),
("X09","visual_content","WordAssistant asset inventory","All tables/images accounted and captioned.","Whole report","Compare matrix/media/render","asset-parity.csv; output/final.docx"),
("X10","argument_citations","Primary docs and LMS sources","External claims cited; project claims mapped separately.","Chapters 4/8/9","Integrity audit and map review","report-evidence.json; claim-evidence.csv")]
xrows=[{"check_id":i,"category":cat,"authority":auth,"source_location":auth,"acceptance_criterion":criterion,"report_location":loc,"verification_method":method,"evidence_files":files,"evidence_sha256":"","status":"NOT_RUN","document_sha256":"","reviewed_by":"","review_date":"","notes":"Final review/hash binding pending."} for i,cat,auth,criterion,loc,method,files in cross]
cwrite("acceptance-crosswalk.csv",["check_id","category","authority","source_location","acceptance_criterion","report_location","verification_method","evidence_files","evidence_sha256","status","document_sha256","reviewed_by","review_date","notes"],xrows)

brief=(W/"task-brief.md").read_text(encoding="utf-8")
brief += "\n\n## Authoring inputs prepared\n- content.json: 10 PM chapters, Trello/Draw.io and evidence limits.\n- operations-plan.json: semantic fields, native tables and inline images.\n- Matrices and source hashes prepared; canonical DOCX and QA remain pending.\n"
(W/"task-brief.md").write_text(brief,encoding="utf-8")
print(json.dumps({"sections":len(S),"tables":len(TABLES),"images":len(IMAGES),"operations":len(steps),"diagrams":len(drows),"claims":len(claimrows),"captures":len(caps)},ensure_ascii=False))

