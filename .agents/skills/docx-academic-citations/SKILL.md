---
name: docx-academic-citations
description: "Guidelines and rules for inserting academic citations (IEEE, APA) and generating bibliography/references sections in Vietnamese university theses and reports."
---

# Quản Lý Trích Dẫn & Tài Liệu Tham Khảo (docx-academic-citations)

## 1. Cấu Trúc Cơ Sở Dữ Liệu Trích Dẫn (`references.json`)

Để quản lý trích dẫn một cách khoa học, tất cả tài liệu tham khảo phải được lưu trữ trong file `references.json` ở thư mục gốc của dự án dưới định dạng sau:

```json
{
  "citation_style": "IEEE", // Hoặc "APA"
  "sources": {
    "devlin2018bert": {
      "author": "Devlin, Jacob and Chang, Ming-Wei and Lee, Kenton and Toutanova, Kristina",
      "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
      "journal": "arXiv preprint arXiv:1810.04805",
      "year": "2018",
      "url": "https://arxiv.org/abs/1810.04805"
    },
    "nguyen2023rag": {
      "author": "Nguyen, Tan",
      "title": "Nghiên cứu xây dựng hệ thống hỏi đáp thông minh dựa trên kiến trúc RAG",
      "journal": "Tạp chí Khoa học và Công nghệ",
      "year": "2023",
      "volume": "15",
      "number": "2",
      "pages": "45-52"
    }
  }
}
```

---

## 2. Quy Tắc Trích Dẫn Trong Văn Bản (In-text Citation Rules)

### Chuẩn IEEE (Kỹ thuật, Công nghệ thông tin)
- Trích dẫn được đánh số theo thứ tự xuất hiện đầu tiên trong văn bản: `[1]`, `[2]`.
- Nếu trích dẫn nhiều tài liệu đồng thời: `[1, 2]` hoặc `[1-3]`.
- Định dạng danh mục Tài liệu tham khảo ở cuối bài: Sắp xếp theo số thứ tự tăng dần từ `[1]`.
- Ví dụ: *"Mô hình BERT [1] đã giải quyết được vấn đề học ngữ cảnh hai chiều."*

### Chuẩn APA (Kinh tế, Xã hội)
- Trích dẫn bằng Tên tác giả và Năm xuất bản: `(Nguyen, 2023)` hoặc `(Devlin et al., 2018)`.
- Định dạng danh mục Tài liệu tham khảo ở cuối bài: Sắp xếp theo thứ tự bảng chữ cái (ABC) của tên tác giả đầu tiên.
- Ví dụ: *"Mô hình BERT (Devlin et al., 2018) đã giải quyết vấn đề học ngữ cảnh."*

---

## 3. Quy Trình Chèn Trích Dẫn Của Agent

Khi phát hiện thẻ trích dẫn dạng `[@cite_key]` trong nội dung văn bản (ví dụ: `[@devlin2018bert]`), Agent phải:
1. Đối chiếu `cite_key` với danh sách `sources` trong `references.json`.
2. Thay thế `[@cite_key]` bằng mã trích dẫn tương ứng theo cấu hình `citation_style`:
   - Nếu `IEEE`: Sinh số thứ tự `[1]`, `[2]` dựa trên danh sách đã đăng ký từ đầu tài liệu.
   - Nếu `APA`: Sinh chuỗi `(Tác giả, Năm)`.
3. Tự động sinh hoặc cập nhật phần **TÀI LIỆU THAM KHẢO** ở cuối tài liệu.

### Quy định định dạng dòng tài liệu tham khảo:
- Font chữ: `Times New Roman`, cỡ `13 pt` (hoặc `12 pt` tùy yêu cầu).
- Không thụt đầu dòng dòng đầu, thụt lề treo (Hanging indent) **1.0 cm** cho các dòng tiếp theo của mỗi tài liệu.
- Định dạng chi tiết từng nguồn:
  - **IEEE**: `[Số_thứ_tự] Tên_Tác_giả, "Tên_Bài_Báo", Tên_Tạp_Chí, Tập, Số, trang, Năm.`
  - **APA**: `Tên_Tác_giả (Năm). Tên_Bài_Báo. Tên_Tạp_Chí, Tập(Số), trang. URL`
