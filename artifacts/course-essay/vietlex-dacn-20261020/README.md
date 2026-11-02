# VietLex — Đồ án chuyên ngành

## Bản bàn giao chuẩn

- DOCX: `output/VietLex_DoAnChuyenNganh_Final.docx`
- PDF Word: `output/VietLex_DoAnChuyenNganh_Final.pdf`
- Loại báo cáo: **Đồ án chuyên ngành**.
- GVHD: **ThS. Đinh Thị Hồng Loan**, theo chỉ dẫn trực tiếp của người dùng.
- Profile v9 là profile thị giác tùy chỉnh theo ví dụ, không chứng nhận tuân thủ quy định chính thức của trường.
- Source snapshot được cập nhật ngày 22/10/2026; source project vẫn dirty và được giữ chỉ đọc. StrongWine chỉ làm ví dụ về chiều sâu/trình bày, không cung cấp dữ kiện hoặc quota cho VietLex.

Bản DOCX có **67 trang** sau cập nhật field trong Microsoft Word. Kiểm kê riêng bài này gồm **106 heading**, **9 hình/sơ đồ**, **13 bảng nội dung** và **2 bảng phần đầu**, tổng cộng 24 artifact được ghi trong ma trận asset. Đây là số đo của snapshot và outline VietLex này; không phải mục tiêu cố định cho bài khác.

## Nội dung và bằng chứng

Bài có bìa/biểu mẫu, abstract tiếng Việt và tiếng Anh, danh mục, bảy chương nội dung, kết luận, tài liệu tham khảo và phụ lục. Năm bài nghiên cứu ACL Anthology được đưa vào registry citation; PDF đã lưu khớp hash. Claim về code, route, template, kiến trúc và số liệu dự án được truy vết riêng qua `claim-evidence.csv` và `evidence.json`.

Sơ đồ và wireframe là mô hình được kiểm tra theo source/template; chúng không phải ảnh chụp runtime. Wireframe không thêm control hoặc dữ liệu mẫu. Runtime, benchmark mới và hiệu lực pháp luật hiện hành chưa được chạy/kiểm chứng.

## QA của đúng DOCX cuối

- `qa/profile-validation-final-v10.json`: profile `capstone`, `valid=true`, không có issue.
- `qa/verify-delivery-final-v10.json`: Word delivery `PASS`; Word-native, field freshness, render và visual đều `PASS`; render Word có 67 trang. DOCX SHA-256 `d1e88c5c5a2be681f6ed34f1e50bae724a646e3c711d1b3b5ce2ab3069e378ed`.
- `qa/visual-review-final-v10.json`: đã tính đủ 67 trang; 63 trang có hash trùng bản đã duyệt trước, còn trang 8, 9, 21 và 61 đã mở ở độ phân giải gốc, không thấy cắt xén hay tràn trang.
- Integrity audit hiện hành nằm ở `qa/integrity-audit-final-v10.stdout.json`: `WARN`, 7 cổng `PASS`, 3 `WARN`, 0 `FAIL`. Có 53 phát hiện biên tập/heuristic (5 typography, 27 quantitative, 21 repetition), được ghi disposition trong `integrity-warning-dispositions.csv`; citation/bibliography và source-evidence gates `PASS`.
- `qa/readiness-final-v10.json`: Word delivery `PASS`; content/sources và submission readiness `INCOMPLETE` vì chưa có đề cương/rubric chính thức. Runtime và rà hiệu lực luật hiện hành cũng `NOT_RUN`. Không gọi đây là bản xác nhận sẵn sàng nộp.

## Pipeline tái lập cho bài VietLex này

1. Giữ `D:\Download\ProfessionalLegalRAG` chỉ đọc; hash các file nguồn và ghi revision/dirty status vào `source/source_manifest.json`.
2. Lập requirement/outline động từ đề, profile, project và StrongWine như checklist chiều sâu; đánh dấu từng nhóm áp dụng, điều chỉnh hoặc không áp dụng có lý do. Không dùng số heading/hình/bảng của bài mẫu làm quota.
3. Đối chiếu route GET, handler, template và role; POST/API là hành động, không phải trang. Ghi source trong `screen-inventory.json`, claim trong `claim-evidence.csv`/`evidence.json`.
4. Chọn sơ đồ theo câu hỏi của bài. Với UML, `.puml` là input có thể sửa và được viết từ class/method/schema đã kiểm; PlantUML render PNG là output, không xác nhận sự thật của sơ đồ. Với wireframe, dùng GET view và control thật từ template; ảnh runtime chỉ được gắn nhãn khi app thực sự chạy và đã chụp.
5. Ghi mọi heading cuối cùng và mọi hình/bảng dự kiến vào ma trận riêng; dựng danh mục Word từ caption. Chạy `scripts/build_vietlex_parity_matrices.py` sau khi DOCX/caption đã chốt, rồi đối chiếu kết quả với ma trận.
6. Soạn/format bản DOCX riêng bằng WordAssistant; citation học thuật dùng `report-evidence.json`, claim project dùng `evidence.json`.
7. Cập nhật field một lần bằng Word trong bản output mới; render bản đã lưu, xem mọi trang và ảnh ở kích thước gốc khi cần. Sau sửa DOCX, chạy lại render/review.
8. Chạy validation, verify, integrity audit và readiness; giữ stdout JSON và stderr riêng. Báo riêng Word delivery, content/sources và submission readiness.

Runbook theo từng bước, schema input/output và giới hạn script nằm tại `D:\Download\WordAssistant\docs\strongwine-course-essay-workflow.md`. Starter cho project mới tại `D:\Download\WordAssistant\templates\course-essay-starter\README.md`.
