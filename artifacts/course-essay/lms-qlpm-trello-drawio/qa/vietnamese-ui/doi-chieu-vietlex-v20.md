# Đối chiếu báo cáo LMS với VietLex v20

Ngày rà soát: 26/10/2026. Phạm vi: nội dung, lập luận, nguồn dẫn, mô hình, bằng chứng giao diện và hình thức Word. Đây là đối chiếu chất lượng và mức phù hợp; không dùng số trang hoặc số chương của VietLex làm tiêu chuẩn cho LMS.

## Nguồn và thẩm quyền

- Báo cáo LMS đầu vào: `output/LMS_HCMUNRE_day_du.docx`, SHA-256 `8d8061ac370722f40b784746f1db336de3bd176a19875608a27ac684b9f52459`.
- Mẫu đối chiếu mới nhất đã xác định: `D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020/output/VietLex_DoAnChuyenNganh_20261025_v20-final.docx`, SHA-256 `aa6bae6a26b3d077d6d90d7282b0c724a09bec6ba0e5415ebff6f15082dd6c9b`. Đọc bản tóm tắt, cấu trúc, brief, QA và phần phân tích giao diện có liên quan. Không tuyên bố kiểm chứng mọi sự kiện pháp lý hoặc chạy lại dự án VietLex.
- Thẩm quyền hình thức: profile HCMUNRE được người dùng chọn và hướng dẫn chính thức đi kèm WordAssistant. Thẩm quyền nội dung: đề tài, học phần và chỉ dẫn trực tiếp của người dùng; tài liệu và mã nguồn LMS là bằng chứng dự án. Tài liệu đính kèm là nguồn tham khảo, không tự cấp quyền thao tác bên ngoài.
- Bản sửa mới: `output/LMS_HCMUNRE_Viet_hoa.docx`; xem dấu kiểm toàn vẹn và QA cuối trong `final-review.json` cùng thư mục. Giữ nguyên đầu vào và mẫu VietLex.

## Kết quả đối chiếu

| Hạng mục | Nhận xét có căn cứ | Xử lý trong LMS |
|---|---|---|
| Bìa và phần đầu | LMS đã có hai bìa, logo trường thật, khung bìa ngoài, tên trường, môn và đề tài; đủ phần đầu HCMUNRE. | Giữ toàn bộ; xác minh lại sau cập nhật trường và dàn trang. Không quay về bản cũ 38 trang. |
| Đề cương | VietLex là đồ án chuyên ngành, đi từ cơ sở đến thiết kế và thực nghiệm. LMS là tiểu luận quản lý dự án với 10 chương quản trị. | Giữ đề cương phù hợp học phần. Không ép thành ba chương hoặc sao chép nghiệp vụ pháp luật. |
| Độ sâu lập luận | VietLex giải thích được nguy cơ người dùng hiểu sai từ nhãn giao diện và giới hạn bằng chứng. LMS trước đó chủ yếu gom ảnh vào phụ lục. | Thêm mục khảo sát giao diện theo vai trò ở Chương 9: trách nhiệm, dữ liệu quan sát, ý nghĩa trạng thái, điểm tạm tính, giới hạn kiểm chứng và bước tiếp theo. |
| Nguồn kiến trúc | Đoạn kiến trúc LMS dẫn mã xử lý bài tập; tệp đó không đủ hỗ trợ toàn bộ kiến trúc giao diện, API và SQL Server. | Bổ sung nguồn kiến trúc được đọc trực tiếp; thay nguồn tại đúng nhận định và chú thích hình kiến trúc. |
| Nguồn mô hình dữ liệu | Mã xử lý bài tập không tự chứng minh đủ 12 bảng. Lược đồ SQL có 12 lệnh tạo bảng. | Bổ sung bản nguồn SQL có hash; dẫn tại đoạn 12 bảng và hình dữ liệu. Tách bằng chứng thiết kế khỏi bằng chứng vận hành. |
| Giao diện tiếng Việt | Còn Admin, raw PUBLISHED, Gradebook, Quiz trong nhãn, vai trò thô, thông báo API tiếng Anh. | Việt hóa nhãn, thông báo, trạng thái, tên truy cập và định dạng điểm. Giữ enum, tuyến API và nội dung mẫu. Tiêu đề mẫu như “Quiz 1 - AI” còn tiếng Anh là dữ liệu được giữ nguyên theo yêu cầu. |
| Tính đúng của thông tin hiển thị | Tổng quan từng ghi 100% bình thường khi không có phép đo; số khóa học gồm bản nháp; liên kết nhanh quản trị dẫn vào chức năng không cấp quyền. | Bỏ kết luận sức khỏe máy chủ thiếu dữ liệu, dùng nhãn đếm chính xác, sửa liên kết theo vai trò; có kiểm thử tập trung. |
| Điểm và kết quả học tập | Một điểm thành phần đã lưu không đủ suy ra xếp loại học lực hoặc đạt học phần. | Bỏ xếp loại Giỏi/Khá/Đạt suy từ trung bình đơn giản; ghi rõ trung bình tạm tính chưa áp dụng trọng số. Không thay thuật toán hoặc điểm đã lưu. |
| Bằng chứng kiểm thử | VietLex phân lớp kiểm chứng và nêu giới hạn; ảnh LMS không đủ xác nhận toàn bộ UAT. | Thêm mục kết quả rà soát và giới hạn ở Chương 7. Ghi 4 kiểm thử đơn vị, kiểm tra kiểu/build/lint và quan sát ba vai trò riêng. Giữ 10 UAT chưa thực hiện; không suy ra đã nghiệm thu. |
| Ảnh sản phẩm | Sáu ảnh LMS cũ có nhãn chưa Việt hóa; bốn ảnh Trello là chứng cứ thực tế cần giữ. | Thay sáu ảnh web bằng ảnh gốc mới; thêm tổng quan, hộp thư rỗng, danh sách bài kiểm tra và màn hình điện thoại. Giữ bốn ảnh Trello. Tên, thư điện tử và dữ liệu mẫu không che, không ghép; mật khẩu giữ hành vi che vốn có của ứng dụng. |
| Sơ đồ | LMS có các góc nhìn quản trị và nghiệp vụ riêng; không thể dùng mô hình truy xuất của VietLex thay mô hình LMS. | Giữ nguồn Draw.io và các hình phù hợp; chú thích không biến PNG thành ảnh thao tác trình biên tập. Các hình chưa sử dụng vẫn được liệt kê trong danh mục nguồn. |
| Trích dẫn | Nguồn dự án, tài liệu công cụ và PMI có vai trò khác nhau; số tài liệu không phải thước đo học thuật duy nhất. | Thêm 4 nguồn sơ cấp đã đọc, tổng 15 nguồn; đánh lại số theo chính sách HCMUNRE, giữ tác giả đậm, tên tài liệu nghiêng và ngày truy cập cho trang không ghi năm. Không tạo bài báo hoặc nguồn giả để tăng số lượng. |
| Thuật ngữ trong báo cáo | Một số tên bảng còn cụm tiếng Anh nén như Quality gates, Milestone baseline, actuals. | Đổi 10 tên bảng/hình sang tiếng Việt, giữ mã kỹ thuật ở nơi cần truy vết. Viết lại đoạn kiến trúc và dữ liệu thành lời giải thích liền mạch, giảm đường dẫn dài trong thân bài. |
| Thụt đầu dòng | VietLex v20 có yêu cầu riêng của người dùng về 1 cm; không tìm thấy điều đó như quy tắc bắt buộc trong hướng dẫn HCMUNRE đã chọn. | Không tự áp 1 cm hoặc xem toàn bộ LMS là sai vì khác mẫu. Xác minh theo profile được chọn. Thụt treo tài liệu tham khảo có mục đích riêng. |
| Danh tính và phê duyệt | Tên người hướng dẫn, lời cảm ơn, chữ ký, số trang và nội dung đánh giá của VietLex thuộc bối cảnh khác. | Không sao chép. Các trường chưa được cung cấp vẫn để trống có thể chỉnh sửa. Biểu mẫu nhận xét chính thức được giữ đầy đủ; không tạo trọng số chấm điểm còn thiếu. |

## Giới hạn còn phải tách bạch

- Lần chụp dùng cơ sở dữ liệu kiểm thử `UniversityLms_Test_Repeat_20261021_1027`, không tạo hoặc thay đổi bản ghi để chuẩn bị ảnh. Tên “After Edit”, “Other User” và dữ liệu tiếng Anh là dữ liệu có sẵn; giữ nguyên theo chỉ dẫn người dùng.
- Nhật ký trình duyệt có lỗi AuthProvider trong lần cập nhật nóng lúc 03:45:17 UTC. Giữ nguyên nhật ký này. Sau tải lại, các ảnh cuối bắt đầu 03:57 UTC cho thấy trang đã tải; không ghi nhận lỗi console mới trong chuỗi ảnh cuối. Không gọi toàn bộ phiên trình duyệt là không lỗi.
- Trạng thái HTTP của tài liệu gốc trong trình duyệt chưa được cung cấp: UNKNOWN. Không thay bằng mã HTTP từ một phép thăm dò ngoài phiên chụp.
- Calendar/Timeline Trello, thao tác trình biên tập Draw.io, API từ chối truy cập và ảnh terminal theo hướng dẫn ban đầu vẫn còn thiếu. Cột Done trống và thẻ nghiệm thu mô phỏng không được đổi thành kết quả hoàn thành.
- Chưa có rubric chấm điểm riêng của môn, thông tin sinh viên/lớp/người hướng dẫn và xác nhận nghiệm thu. Những mục này cần đầu vào thực; không phải lỗi có thể sửa bằng sao chép mẫu.
- Kiểm thử backend toàn bộ, tải, truy cập trái phép, ghi dữ liệu và khả năng tiếp cận đa thiết bị: NOT RUN trong lần sửa giao diện này. Không triển khai lên môi trường công khai.

## Cách tái lập và mức kiểm chứng

Kế hoạch sửa có hash: `revision-spec.json`, `revision-plan.json`. Thay hình và dẫn nguồn: `../../finish_vi_revision.py`. Nguồn dẫn: `../../report-evidence-vietnamese-reviewed.json`, các bản chụp nguồn trong `../../sources/`. Ảnh và nhật ký: `../../captures/2026-10-26-vi/`. Nhật ký mã nguồn và lệnh: `D:/Download/LMS/docs/audit/2026-10-26-vietnamese-ui/`.

Mức kiểm chứng mã: kiểm thử đơn vị và phân tích tĩnh; mức giao diện: tích hợp cục bộ bằng trình duyệt thật với dữ liệu thử có sẵn; mức tài liệu: Word native, trường tự động và hình render từng trang. Kết quả giao Word không đồng nghĩa đã đủ điều kiện nộp hoặc nghiệm thu sản phẩm.
