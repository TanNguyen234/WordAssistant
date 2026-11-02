# Kế hoạch và nhật ký hoàn tất — đồ án chuyên ngành VietLex

**Điểm vào khi tiếp tục:** đọc `task-brief.md` trước. File này giữ yêu cầu đang có hiệu lực, output/hash hiện tại, QA mới nhất và blocker. Nhật ký phía dưới lưu lịch sử các vòng; khi có khác biệt, không dùng mô tả lịch sử hoặc QA hash cũ để ghi đè trạng thái trong brief/`project.json`/bằng chứng mới nhất.

## Mục tiêu, phạm vi, authority

- Loại báo cáo: **Đồ án chuyên ngành**; GVHD: **ThS. Đinh Thị Hồng Loan**, theo chỉ dẫn trực tiếp của người dùng.
- Độ sâu và style được rà theo StrongWine; outline, sơ đồ, hình/bảng VietLex lấy từ yêu cầu và source riêng, không lấy quota của bài mẫu.
- `D:\Download\ProfessionalLegalRAG` chỉ đọc. Chỉ ghi artifact trong workspace `artifacts/course-essay-vietlex-20261020`.
- Không khởi chạy app cục bộ, DB, provider, benchmark hoặc test suite mới. Theo yêu cầu ảnh thật, đã mở deployment công khai bằng Chrome ẩn danh và chỉ GET 11 route; không gửi form/POST/AI request hay truy cập dữ liệu riêng tư. Không tuyên bố kiểm chứng luật hiện hành.
- Không có đề cương/rubric chính thức; yêu cầu tương ứng giữ `NOT_RUN`, submission readiness là `INCOMPLETE`.

## Bản chuẩn trước vòng sửa theo hướng dẫn 2026–2027 (lịch sử)

- DOCX: `output/VietLex_DoAnChuyenNganh_Final.docx`
- PDF Word: `output/VietLex_DoAnChuyenNganh_Final.pdf`
- SHA-256 DOCX: `d1e88c5c5a2be681f6ed34f1e50bae724a646e3c711d1b3b5ce2ab3069e378ed`
- Render Word: 67 trang; outline 106 heading; ma trận ghi 9 hình/sơ đồ, 13 bảng thân bài và 2 bảng phần đầu. Đây là inventory của VietLex hiện tại, không phải quota cho bài sau.
- Source snapshot: `source/source_manifest.json`, chụp 22/10/2026 trên dirty worktree; source không bị sửa.

## Các bước đã hoàn tất

1. Đối chiếu bài trước, StrongWine, project source và evidence; cập nhật phân loại thành đồ án chuyên ngành và authority của GVHD; không mang tên học phần cũ sang bìa.
2. Lập outline/project inventory theo bài; bổ sung phần đầu/độ sâu và evidence để bài không dừng ở bản 44 trang. Trình bày cơ sở, yêu cầu, nghiệp vụ, OOAD, kiến trúc/database, web/UI, kiểm thử/đánh giá, giới hạn, hướng phát triển, citation và phụ lục.
3. Cập nhật hai source claim có hash đổi sau snapshot cũ, bổ sung record vận hành còn thiếu; capture lại manifest chỉ đọc ngày 22/10. Các claim được đối chiếu với source hiện tại.
4. Dựng lại ma trận: 106 heading; 9 hình/sơ đồ; 13 bảng nội dung; 2 bảng phần đầu. Số lượng phát sinh từ bài VietLex, không cài đặt như mức bắt buộc.
5. Bổ sung hai bài ACL đã có review nhưng thiếu trong registry, thành năm nguồn ACL. Audit citation dùng registry học thuật riêng với claim-to-source của project.
6. Cập nhật thống nhất ngày snapshot trong tóm tắt, abstract, Chương 2 và Phụ lục A. `field update-all` bằng Word trả `SUCCESS`, `updated=true`, `repaginated=true`, 1 TOC và 2 danh mục hình/bảng.
7. Profile validation v10 trả `valid=true`. Render Word có 67 trang; 63 trang trùng byte/hash với bản đã duyệt trước, 4 trang thay đổi (8, 9, 21, 61) được mở ở độ phân giải gốc và không thấy crop/overflow. `verify-delivery-final-v10.json` trả `overall_status=PASS`, `delivery_status=PASS`, render/visual/native fields PASS.
8. Readiness hiện chỉ còn thiếu rubric/đề cương chính thức và yêu cầu rubric chưa chạy. Vì vậy Word delivery PASS nhưng content/submission readiness INCOMPLETE.

## Lỗi đã xác nhận và cách khắc phục

- Parity matrix ban đầu bỏ các heading front matter do generator chỉ thêm một số heading ngầm khi gặp một title cụ thể; content-depth plan lại không liệt kê chúng. Đã chuyển sang khai báo tường minh mọi heading trong plan và bỏ logic chèn heading ẩn. Phòng ngừa: mọi heading thực tế, kể cả TOC/danh mục/reference, phải có hàng trong structure matrix trước khi compose.
- Hai citation có trong bibliography nhưng thiếu evidence registry; registry cũ có ba nguồn trong khi bài dùng năm. Đã khôi phục hai record đã review, đối chiếu PDF/hash và chạy lại audit. Phòng ngừa: đối chiếu citation-number set giữa DOCX, registry và bibliography ngay trước audit.
- Readiness từng fail vì source hash của hai file đổi sau source snapshot. Đã đọc lại đúng vị trí source, cập nhật review/hash, bổ sung ops record còn thiếu và chụp lại manifest. Phòng ngừa: khóa timestamp/hash source snapshot cùng lần rà claim; nếu source đổi phải review lại, không sao chép hash cũ.
- Tham chiếu disposition trỏ tới `qa/visual-review-v9.md` không tồn tại. Đã tạo `qa/visual-review-final-v10.json` gắn render/hash thật và cập nhật evidence.

## QA và giới hạn của bản lịch sử trước vòng sửa 2026–2027

- Profile: `qa/profile-validation-final-v10.json`.
- Render/challenge: `qa/verify-challenge-final-v10.json`.
- Bàn giao Word: `qa/verify-delivery-final-v10.json`.
- Rà trực quan trang: `qa/visual-review-final-v10.json`.
- Integrity audit và readiness: `qa/integrity-audit-final-v10.stdout.json`, `qa/readiness-final-v10.json`.
- Integrity audit: `WARN` (7 `PASS`, 3 `WARN`, 0 `FAIL`); 53 phát hiện biên tập/heuristic có disposition trong `integrity-warning-dispositions.csv`. Citation/bibliography và source-evidence gates `PASS`.
- Không có rubric chính thức; không chạy app/runtime, DB/provider, benchmark mới hoặc kiểm luật hiện hành. Bản Word đã đạt delivery gates nhưng chưa có cơ sở xác nhận submission readiness.

## Phiên sửa theo hướng dẫn trình bày 2026–2027 — 2026-10-22

- **Mục tiêu:** tạo DOCX đầu ra mới theo tài liệu hướng dẫn người dùng cung cấp; sửa cấu trúc ba chương và các lỗi định dạng; thay hai wireframe bằng ảnh chụp runtime thật, đồng thời bổ sung ảnh cho các route công khai khác đã mở được.
- **Nguồn chuẩn:** `C:\Users\VI TINH THANH AN\Documents\Huong dan trinh bay Báo cáo ĐACN_2026-2027.docx` là tiêu chí định dạng/cấu trúc. `Final.docx` là đầu vào cần giữ nguyên; StrongWine chỉ là ví dụ độ sâu.
- **Giới hạn runtime:** chỉ dùng phiên Chrome ẩn danh và GET/read-only. Không chụp lịch sử hội thoại, tài khoản, dữ liệu người dùng hoặc route quản trị; route trả 401 được ghi là không truy cập được, không dựng ảnh thay thế.
- **Bằng chứng ảnh hiện có:** manifest `assets/runtime-captures/capture-manifest.json` ghi 11 route công khai, ảnh 1440×1000, ngày 2026-10-22, title/H1/status; trang văn bản `/documents/333670` được mở từ kết quả thật của truy vấn `45/2019/QH14`.
- **Đầu ra dự kiến:** `output/VietLex_DoAnChuyenNganh_Final_RuntimeScreens_20261022.docx`; bản nguồn và source project giữ nguyên.
- **Done-when:** tiêu đề chương khớp chính xác ba mục bắt buộc; không còn mô tả wireframe như ảnh thật; 11 ảnh route được chèn, caption/SEQ và danh mục được cập nhật; A4/lề/font/giãn dòng/page number được kiểm tra bằng profile hướng dẫn; render Word được xem hết trang; readiness checker báo riêng Word delivery, content/sources và submission readiness.
- **Trạng thái ban đầu:** chưa chỉnh DOCX; ảnh route đã chụp và đang chờ chèn. Các route quản trị/phiên cá nhân bị giới hạn quyền hoặc privacy. Rubric/đề cương môn học chính thức chưa có.


## Kết quả chốt — theo hướng dẫn 2026–2027 (2026-10-22)

- **Đầu ra:** `output/VietLex_DoAnChuyenNganh_Final_RuntimeScreens_20261022.docx`; bản DOCX đầu vào được giữ nguyên. SHA-256: `76091A0C2CB0DFAD4B987373ACD559331C82419E7906A9305961FCD11F1A507D`.
- **Cấu trúc/hình:** 106/106 heading được ánh xạ vào ma trận mới; chương thân bài theo 3 chương của hướng dẫn. Có 18 caption hình (7 sơ đồ từ source, 11 ảnh chụp runtime web công khai), 15 bảng và 20 ảnh nhúng tổng cộng. Ma trận: `structure-parity-runtime-v11.csv`, `asset-parity-runtime-v11.csv`; capture manifest: `assets/runtime-captures/capture-manifest.json`.
- **Rà hình:** đã xem 81/81 trang render Word. Ảnh runtime và caption không bị crop; có một trang ảnh (trang render 58, HÌNH 3.10–3.11) không hiện running header, đã ghi lại trong visual inventory để không che lỗi này.
- **Lệnh xác nhận:** `python -m wordassistant.cli verify <output.docx> --profile hcmunre_dacn_2026_2027 --variant report --reuse-render-report qa/verify-runtime-final-v8.json --native-fields --visual-reviewed --visual-review-token <token> --delivery --json`; profile validation v11 trả `valid=true` với cảnh báo 5/10 nguồn; integrity audit v11 trả `FAIL` duy nhất ở ngưỡng tối thiểu 10 nguồn; readiness: `python scripts/check_course_essay_readiness.py <workspace>`.
- **Readiness:** readiness checker raw status `FAIL`; `word_delivery=FAIL`, `content_and_sources=FAIL`. Hồ sơ nộp được phân loại `INCOMPLETE`: 5/10 nguồn đã review, rubric/đề cương chính thức chưa có và kiểm tra luật hiện hành `NOT_RUN`. Không thêm nguồn hoặc kết luận chưa có bằng chứng.
- **Cảnh báo integrity:** 45/45 cảnh báo heuristic đã có disposition trong `integrity-warning-dispositions-runtime-v11.csv`; `source_evidence` là blocker thật, không phải cảnh báo được miễn.
- **Artefact QA:** `qa/verify-runtime-final-v11.json`, `qa/integrity-audit-runtime-final-v11.stdout.json`, `qa/readiness-final-runtime-v11.stdout.json`, `qa/document-inventory-runtime-final-v12.json`, `qa/parity-matrices-runtime-v11.json`. Không sửa source project và không chạy test suite.
