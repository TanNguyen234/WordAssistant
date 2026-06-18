---
name: docx-advanced-management
description: "Kỹ năng khai thác các tính năng quản lý tài liệu nâng cao: So sánh (diff), gộp chương (merge), bình luận phản biện (comments) và bảo mật file Word."
---

# Quản Lý Tài Liệu Word Nâng Cao (docx-advanced-management)

Hệ thống `docx-mcp` cung cấp các tính năng quản lý vòng đời tài liệu mạnh mẽ, giúp tự động hóa quy trình làm việc nhóm giữa nhiều Agent hoặc làm việc với giảng viên hướng dẫn.

---

## 1. So Sánh Hai Tài Liệu (Document Comparison & Diff)

Khi giảng viên hướng dẫn gửi lại một phiên bản tài liệu đã sửa đổi, hoặc khi muốn đối chiếu bản nháp cũ và mới, Agent có thể so sánh tự động để xuất ra file Word chứa các vết sửa đổi (tracked changes) và file text ghi nhận các thay đổi:

- **Công cụ sử dụng**: `compare_documents` hoặc `diff_to_text` (hoặc script helper `docx_diff.py`).
- **Ứng dụng**:
  - Tự động nhận diện những từ/đoạn nào bị xóa (strikethrough) hoặc thêm mới (underline).
  - Xuất ra file tóm tắt thay đổi để Agent phân tích và tự động chỉnh sửa.

---

## 2. Gộp Các Chương Độc Lập (Document Merge)

Khi phát triển đồ án lớn, mỗi chương có thể được viết độc lập bởi các Agent chuyên biệt nhằm tối ưu hóa hiệu suất và dung lượng ngữ cảnh (Context Window). Sau khi các chương hoàn thành, Agent sẽ tiến hành gộp chúng lại:

- **Công cụ sử dụng**: `merge_documents` (hoặc script helper `docx_merge.py`).
- **Quy trình gộp**:
  1. Mở file chương 1 (hoặc file bìa/mục lục làm gốc): `open_document("chuong1.docx")`.
  2. Lần lượt gộp các chương tiếp theo: `merge_documents("chuong2.docx")`, `merge_documents("chuong3.docx")`.
  3. Chạy `audit_document()` để làm sạch ID trùng lặp.
  4. Lưu thành file hoàn chỉnh: `save_document("do_an_hoan_chinh.docx")`.

---

## 3. Bình Luận & Phản Biện Nội Bộ (Document Comments)

Các Agent có thể làm việc chéo bằng cách chèn ý kiến nhận xét (comments) vào tài liệu để Agent khác vào sửa chữa, hoặc ghi nhận phản hồi từ giảng viên:

* **Xem danh sách comment**: `get_comments()`.
* **Thêm comment**: `add_comment(para_id, text)`.
* **Trả lời comment (Threaded reply)**: `reply_to_comment(parent_id, text)`.

---

## 4. Bảo Vệ & Khóa Tài Liệu (Document Protection)

Trước khi gửi tài liệu chính thức cho giảng viên duyệt hoặc nộp bài, Agent có thể bảo vệ cấu trúc tài liệu bằng cách khóa chỉnh sửa:

* **Chỉ cho phép sửa đổi dưới dạng Tracked Changes (Redlines)**:
  ```
  set_document_protection(edit_type="trackedChanges", password="your_password")
  ```
* **Chỉ cho phép thêm Bình luận (Comments-only)**:
  ```
  set_document_protection(edit_type="comments", password="your_password")
  ```
* **Khóa đọc duy nhất (Read-only)**:
  ```
  set_document_protection(edit_type="readOnly", password="your_password")
  ```
