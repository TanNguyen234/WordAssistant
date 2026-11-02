# Rà trực quan — VietLex final

- DOCX SHA-256: `7ff79d15628a447fdfa0c4fc96705ab9858662f3634d45e450a3820a5e8a09d8`
- PDF SHA-256: `3537bf9e75aba76b35a9f908891ce584ec3667ca3aeee1afcaf4d024d21a4a16`
- Render do Microsoft Word xuất: 44 trang.
- Ảnh trang được raster hóa bằng PDFium. Visual reuse token ràng buộc hash DOCX và hash/kích thước của 44 ảnh trang; PDF hash chỉ là provenance. Chi tiết từng SHA nằm trong `page-manifest.json`.
- Đã mở và rà đủ 44 trang theo 5 contact sheet: `contact-01-09.png`, `contact-10-18.png`, `contact-19-27.png`, `contact-28-36.png`, `contact-37-44.png`.

## Kết quả xem

- Trang bìa chính có khung bốn cạnh; trang cận bìa căn giữa và giữ đủ nội dung. Header/footer và số trang không tràn lề.
- Form nhận xét, lịch trình, tóm tắt/abstract, bảng viết tắt, mục lục, danh mục hình/bảng hiển thị đúng. TOC/list tiếp tục tự nhiên qua trang, không có trang trắng gần rỗng.
- Hình cây màn hình, use case, class, retrieval, sequence và hai wireframe đều nằm trong lề, caption khớp danh mục; wireframe dùng nét đen trên nền trắng, không có browser chrome hoặc dữ liệu giả. Chúng được ghi là source-backed, không phải runtime capture.
- Bảng trong thân bài vừa bề rộng trang. Chú thích, mục lục và citation [1]–[3] không bị cắt hoặc mất.
- Không thấy chữ xanh bất thường, chữ bị giãn/cắt hoặc ảnh bị crop trong render cuối.

## Render sai do Poppler

Một lượt chẩn đoán Poppler từng làm ảnh trang 2 trông như bị crop và báo thiếu display font `Symbol`. Mình đối chiếu PDF Word gốc bằng PyMuPDF và xem lại đúng ảnh trang cuối từ PDFium; cả hai hiển thị đầy đủ nội dung căn giữa. Vì vậy lỗi nằm ở ảnh do Poppler tạo, không nằm trong DOCX/PDF bàn giao. Verify cuối dùng manifest Word/PDFium, có `visual_status=PASS` và `delivery_status=PASS`.
