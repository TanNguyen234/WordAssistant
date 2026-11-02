"""Prepare the bounded, hash-checked LMS revision; preserve the input."""
import csv, hashlib, json
from pathlib import Path
R=Path(__file__).resolve().parent
def save(p,x):(R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
src=R/'output/LMS_HCMUNRE_day_du.docx'
digest=hashlib.sha256(src.read_bytes()).hexdigest()
assert digest=='8d8061ac370722f40b784746f1db336de3bd176a19875608a27ac684b9f52459'
with (R/'acceptance-crosswalk.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
for ident,category,criterion,location in [
 ('X09','user_requirements','Vietnamese UI on real LMS; raw enum, routes and demo records preserved.','Chương 9; Phụ lục E'),
 ('X10','runtime_screenshots','Replace six old web screenshots with fresh, unredacted actual demo UI; retain real Trello images.','Phụ lục E'),
 ('X11','argument_citations','Deep applicability review against VietLex v20; repair source attribution and explain role observations and verification limits.','Chương 7; Chương 9; comparison audit')]:
 if not any(x['check_id']==ident for x in rows):
  row={k:'' for k in rows[0]};row.update(check_id=ident,category=category,authority='User request 2026-10-26',source_location='User request; VietLex v20 read-only comparison',acceptance_criterion=criterion,report_location=location,verification_method='Source, UI and native Word review',status='PENDING',notes='New output requires fresh verification; old output evidence is historical.')
  rows.append(row)
with (R/'acceptance-crosswalk.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
captions={
 'Stakeholder register rút gọn':'Các bên liên quan chính',
 'Milestone baseline':'Các mốc của đường cơ sở tiến độ',
 'Resource breakdown':'Phân bổ nguồn lực theo vai trò',
 'Budget baseline':'Đường cơ sở ngân sách',
 'Quality gates':'Các cổng kiểm soát chất lượng',
 'UAT scenarios, SIMULATED/NOT RUN':'Kịch bản kiểm thử chấp nhận chưa thực hiện',
 'Trello snapshot 23/10/2026, API aggregate':'Số liệu tổng hợp Trello ngày 23/10/2026',
 'Quy ước card và Done':'Quy ước thẻ và điều kiện hoàn tất',
 'EVM minh họa, không phải actuals':'Minh họa phương pháp giá trị đạt được',
 'Use Case LMS theo vai trò':'Ca sử dụng LMS theo vai trò'}
quality=[
 'Lần rà soát giao diện ngày 26/10/2026 bổ sung hai loại bằng chứng: kiểm thử tự động cho quy tắc trình bày và quan sát trực tiếp trên hệ thống đang chạy. Bốn kiểm thử tập trung kiểm tra nhãn trạng thái, định dạng điểm, thông báo lỗi và đường dẫn thao tác nhanh theo vai trò. Kiểm tra kiểu dữ liệu, tạo bản phân phối và kiểm tra mã tĩnh đều kết thúc thành công. Các cảnh báo về hiệu ứng React còn được lưu trong nhật ký; kết quả này không có nghĩa toàn bộ ứng dụng không còn lỗi.',
 'Quan sát trực tiếp sử dụng ba tài khoản dùng thử trên cơ sở dữ liệu kiểm thử có sẵn. Quản trị viên mở danh sách người dùng và trang tổng quan; giảng viên xem bài tập WEB220 cùng một bài nộp đã lưu; sinh viên xem bài tập và bảng điểm AI310. Người quan sát chỉ đọc, không tạo tài khoản, gửi bài, làm bài kiểm tra hoặc chấm điểm để tạo hình minh chứng. Phụ lục E giữ nguyên tên, thư điện tử và nội dung mẫu đang hiển thị theo yêu cầu của người dùng.',
 'Phạm vi kiểm chứng vì vậy cần được đọc theo từng lớp. Kiểm thử đơn vị xác nhận các hàm chuyển đổi nhãn và đường dẫn với dữ liệu đầu vào đã chọn. Quan sát giao diện xác nhận các màn hình thực tế đã tải và hiển thị dữ liệu theo ba vai trò. Các trường hợp truy cập trái phép, thao tác đồng thời, giới hạn tải, mất kết nối và giao dịch cập nhật dữ liệu vẫn cần kịch bản chạy riêng. Mười kịch bản UAT trong kế hoạch chưa được nâng trạng thái đạt chỉ từ ảnh chụp.',
 'Đối với nghiệm thu, mỗi lỗi cần gắn với bước tái hiện, kết quả mong đợi, kết quả quan sát và bằng chứng sau sửa. Chẳng hạn, liên kết nhanh của quản trị viên phải đi đến chức năng được cấp quyền; nhãn điểm phải giải thích được cách tính. Hai yêu cầu này có thể kiểm tra cụ thể hơn nhận định chung rằng giao diện thân thiện. Nhóm cần bổ sung người thực hiện, môi trường chạy và xác nhận của bên chấp nhận trước khi sử dụng hồ sơ này như biên bản nghiệm thu.'
]
ui=[
 'Giao diện được khảo sát theo trách nhiệm của từng vai trò để kiểm tra sự thống nhất giữa phân quyền, dữ liệu và cách diễn đạt. Mục đích của việc Việt hóa là giúp người dùng hiểu hành động và trạng thái; các mã API như ADMIN, LECTURER, STUDENT và PUBLISHED vẫn giữ nguyên khi trao đổi với máy chủ. Tên học phần, tên tài khoản, tiêu đề bài tập và nội dung bài nộp là dữ liệu đã lưu, nên không được sửa để làm đẹp ảnh. Vì vậy, một số tiêu đề mẫu còn chứa thuật ngữ tiếng Anh dù nhãn điều khiển đã dùng tiếng Việt.',
 'Ở vai trò quản trị, danh sách người dùng hiển thị mã tài khoản, họ tên, thư điện tử, vai trò và trạng thái. Các trường này hỗ trợ phân biệt đối tượng trước thao tác sửa hoặc khóa. Trang tổng quan được sửa để ghi số khóa học đã được ghi nhận, thay cho kết luận tất cả đang vận hành. Ô theo dõi hệ thống ghi rõ chưa có dữ liệu giám sát; số tài khoản hoặc việc mở được trang không đủ để kết luận máy chủ hoạt động bình thường. Ba liên kết nhanh của quản trị viên dẫn tới người dùng, khóa học và thông báo phù hợp với quyền hiện có.',
 'Ở vai trò giảng viên, bài tập WEB220 hiển thị nhãn Đã giao, điểm tối đa và hạn nộp. Từ danh sách bài tập, thao tác Xem và Chấm bài mở một bài nộp văn bản có sẵn của sinh viên Trần Bình. Quan sát này nối ca sử dụng chấm bài với dữ liệu cụ thể mà không tạo thêm điểm. Danh sách bài kiểm tra phân biệt Đã xuất bản với Bản nháp hoặc đã ẩn; tên bài mẫu được giữ nguyên. Khi triển khai kiểm thử tiếp theo, cần kiểm tra thêm quyền sở hữu học phần và các điều kiện từ chối sửa, xuất bản hoặc chấm bài ngoài phạm vi phụ trách.',
 'Ở vai trò sinh viên, khóa AI310 hiển thị bài tập và hành động Cập nhật bài nộp. Bảng điểm có một điểm thành phần 10/10 với trọng số 10%, là dữ liệu đã tồn tại trước lần chụp. Giá trị trung bình trên đầu trang hiện chỉ là trung bình tạm tính từ những điểm được ghi nhận, chưa áp dụng trọng số học phần. Do đó, giao diện bỏ xếp loại Giỏi hoặc Đạt và bổ sung lời giải thích ngay cạnh kết quả. Cách trình bày này tránh biến một điểm thành phần thành kết luận hoàn thành học phần.',
 'Kiểm tra trên khung màn hình 390 × 844 cho thấy các thẻ điểm chuyển thành một cột và phần đầu trang thu gọn. Chiều rộng nội dung trang bằng chiều rộng vùng xem quan sát được; bảng điểm có vùng cuộn riêng để giữ các cột. Đây là kiểm tra một kích thước màn hình và một trạng thái dữ liệu, chưa thay được đánh giá khả năng tiếp cận bằng bàn phím, trình đọc màn hình hoặc nhiều thiết bị. Hướng tiếp tục là kiểm tra nhãn trường nhập, thứ tự lấy tiêu điểm, thông báo lỗi và xác nhận trước thao tác có ảnh hưởng đến người dùng.',
 'Các ảnh chụp gốc, tuyến truy cập, thời điểm và dấu kiểm toàn vẹn được lưu trong hồ sơ minh chứng. Ảnh xác nhận nội dung đã quan sát, còn trạng thái HTTP của tài liệu gốc chưa được công cụ trình duyệt cung cấp nên vẫn được ghi là chưa xác định. Khi dùng báo cáo để đánh giá sản phẩm, cần đọc đồng thời ảnh giao diện, quy tắc trong mã nguồn và kết quả chạy của từng kịch bản. Phần hạn chế này giúp phân biệt kết quả đã kiểm tra với công việc còn phải thực hiện.'
]
spec={'input_sha256':digest,'scope_start':'MỞ ĐẦU','scope_end':'TÀI LIỆU THAM KHẢO','first_line_indent_cm':0,
 'caption_titles':[{'old':k,'new':v} for k,v in captions.items()],
 'insertions':[
  {'before_heading':'CHƯƠNG 8. TRUYỀN THÔNG, THAY ĐỔI VÀ TRELLO','blocks':[{'kind':'heading','text':'Kết quả rà soát giao diện và giới hạn kiểm chứng','level':2,'numbering_from':'Kiểm thử chấp nhận và phân loại lỗi'}]+[{'kind':'paragraph','text':t} for t in quality]},
  {'before_heading':'CHƯƠNG 10. NGHIỆM THU VÀ ĐÓNG DỰ ÁN','blocks':[{'kind':'heading','text':'Khảo sát giao diện theo vai trò','level':2,'numbering_from':'Kiến trúc và dữ liệu'}]+[{'kind':'paragraph','text':t} for t in ui]}]}
save('qa/vietnamese-ui/revision-spec.json',spec)
print('Prepared specification and pending acceptance criteria.')
