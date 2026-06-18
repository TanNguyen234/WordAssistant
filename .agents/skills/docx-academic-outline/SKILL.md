---
name: docx-academic-outline
description: "Guidelines for creating and managing academic document outlines (Heading 1, 2, 3 structure) for Vietnamese university essays, project reports, and theses."
---

# Lập Đề Cương Đồ Án / Tiểu Luận Học Thuật (docx-academic-outline)

## 1. Cấu trúc Khung Sườn Đồ Án / Tiểu Luận Tiêu Chuẩn

Một đồ án tốt nghiệp hoặc tiểu luận đại học tiêu chuẩn tại Việt Nam bắt buộc phải có cấu trúc các phần như sau:

| Phần tài liệu | Loại Heading | Cấu trúc trang | Ghi chú |
|---|---|---|---|
| **Trang Bìa Chính & Bìa Phụ** | Không dùng Heading thông thường | Trang riêng | Thông tin Trường, Khoa, Lớp, Đề tài, GVHD, SVTH, Năm |
| **Lời Cam Đoan / Lời Cảm Ơn** | Heading 1 (Không số) | Trang riêng | Tự nguyện, chân thành |
| **Mục Lục (Table of Contents)** | Heading 1 (Không số) | Trang riêng | Tự động sinh từ Word |
| **Danh Mục Hình Vẽ / Bảng Biểu** | Heading 1 (Không số) | Trang riêng | Tự động sinh |
| **Danh Mục Từ Viết Tắt** | Heading 1 (Không số) | Trang riêng (nếu có) | Bảng gồm: Từ viết tắt - Nghĩa tiếng Việt - Nghĩa tiếng Anh |
| **MỞ ĐẦU (Introduction)** | Heading 1 (Không số) | Bắt đầu đánh số trang từ đây | Nêu tính cấp thiết, mục tiêu, đối tượng, phạm vi nghiên cứu |
| **CHƯƠNG 1, 2, 3... (Nội dung chính)** | Heading 1 (Chương 1., Chương 2.) | Mỗi chương nằm ở 1 trang mới | Cấu trúc nội dung chi tiết (xem phần dưới) |
| **KẾT LUẬN & HƯỚNG PHÁT TRIỂN** | Heading 1 (Không số) | Trang riêng | Tóm tắt kết quả đạt được và các hạn chế, hướng đi tiếp theo |
| **TÀI LIỆU THAM KHẢO** | Heading 1 (Không số) | Trang riêng | Định dạng theo chuẩn IEEE hoặc APA |
| **PHỤ LỤC (Appendices)** | Heading 1 (Không số / Phụ lục A) | Trang riêng (nếu có) | Code mẫu, bảng số liệu thô |

---

## 2. Thiết Kế Nội Dung Các Chương Chính

### A. Đối với Tiểu luận (Essay - 15-30 trang)
Thường gồm 3 chương chính:
- **Chương 1**: Cơ sở lý thuyết / Tổng quan tài liệu về đề tài.
- **Chương 2**: Phân tích thực trạng / Mô tả giải pháp đề xuất.
- **Chương 3**: Đánh giá kết quả / Thảo luận giải pháp.

### B. Đối với Đồ án môn học / Chuyên ngành (Project - 30-50 trang)
- **Chương 1**: Phân tích yêu cầu bài toán & Cơ sở lý thuyết liên quan.
- **Chương 2**: Thiết kế hệ thống (Kiến trúc, Cơ sở dữ liệu, Sơ đồ hoạt động).
- **Chương 3**: Triển khai cài đặt & Kiểm thử kết quả.

### C. Đối với Đồ án tốt nghiệp / Khóa luận tốt nghiệp (Thesis - 60-100 trang)
Thường có 4-5 chương:
- **Chương 1**: Tổng quan về đề tài (Bối cảnh, bài toán, khảo sát các nghiên cứu liên quan hiện có).
- **Chương 2**: Cơ sở lý thuyết nền tảng (Các thuật toán, mô hình AI, công nghệ cốt lõi).
- **Chương 3**: Thiết kế & Đề xuất giải pháp (Đóng góp chính của đồ án: mô hình cải tiến, kiến trúc hệ thống chi tiết).
- **Chương 4**: Triển khai, Thực nghiệm & Đánh giá kết quả (So sánh hiệu năng với các phương pháp khác, phân tích biểu đồ).

---

## 3. Quy Tắc Định Danh & Lập Trình Heading trong Word

1. **Liên kết Styles**:
   - Sử dụng `get_styles` để xem các style Heading 1, Heading 2, Heading 3 có sẵn trong file template.
   - Gán đoạn văn tiêu đề với style thích hợp thông qua ID paragraph.
2. **Không viết cứng số thứ tự**:
   - Ví dụ: Không ghi `"Chương 1. Giới thiệu"` vào text của paragraph. Chỉ ghi `"Giới thiệu"`, số chương `"Chương 1."` hoặc `"1.1"` sẽ được Word tự động sinh thông qua Style Heading đã liên kết Multilevel List.
3. **Phân tách chương**:
   - Luôn chèn một **Page Break** hoặc **Section Break (Next Page)** trước mỗi Heading 1 của Chương để đảm bảo mỗi chương luôn bắt đầu ở đầu trang mới.
