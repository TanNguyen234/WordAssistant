---
name: docx-academic-format
description: "Rules and guides for applying Vietnamese academic styling (fonts, spacing, margins, header/footer) to Word documents using templates or python-docx script styling."
---

# Định Dạng Chuẩn Học Thuật Việt Nam (docx-academic-format)

## 1. Page Margins & Sizes (Kích thước & Căn lề)

Khi định dạng trang A4, Agent phải thiết lập các thuộc tính section chính xác:

- Khổ giấy: **21.0 cm x 29.7 cm** (A4)
- Margins:
  - Top: `2.0 cm` (1.134 inch / 1134 DXA)
  - Bottom: `2.0 cm` (1.134 inch / 1134 DXA)
  - Left (đóng gáy): `3.0 cm` (1.701 inch / 1701 DXA)
  - Right: `2.0 cm` (1.134 inch / 1134 DXA)

```python
# Ví dụ python-docx áp dụng căn lề
section = doc.sections[0]
section.page_width = Inches(8.27)  # A4 width
section.page_height = Inches(11.69) # A4 height
section.top_margin = Inches(0.79)   # 2.0 cm
section.bottom_margin = Inches(0.79) # 2.0 cm
section.left_margin = Inches(1.18)   # 3.0 cm
section.right_margin = Inches(0.79)  # 2.0 cm
```

---

## 2. Paragraph & Typography Formatting (Đoạn văn & Cỡ chữ)

Mọi văn bản chính (Normal Text) phải tuân thủ:
- **Font**: `Times New Roman`
- **Size**: `13 pt` (Word size 26)
- **Căn lề**: `Justify` (Căn đều hai bên)
- **Giãn dòng**: `1.5 lines` (Line spacing factor: 1.5)
- **Giãn cách đoạn**: `Spacing After = 6 pt`, `Spacing Before = 0 pt`
- **Thụt đầu dòng**: `First line indent = 1.27 cm` (0.5 inch / 720 DXA) cho dòng đầu tiên của mỗi đoạn. Không thụt đầu dòng đối với các tiêu đề (Heading) hoặc đoạn chứa hình ảnh/bảng biểu.

```python
# Ví dụ cấu hình Paragraph Format bằng python-docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

p_format = paragraph.paragraph_format
p_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
p_format.line_spacing = 1.5
p_format.space_after = Pt(6)
p_format.space_before = Pt(0)
p_format.first_line_indent = Pt(36) # 0.5 inches = 36 pt (720 DXA)
```

---

## 3. Định Dạng Caption Cho Hình Ảnh & Bảng Biểu

### A. Hình ảnh
- Căn giữa cả hình ảnh và đoạn chú thích.
- Chú thích đặt **DƯỚI** hình ảnh.
- Cỡ chữ chú thích: `11 pt` hoặc `12 pt`, **in nghiêng (Italic)**, Times New Roman.
- Ví dụ: *Hình 1.1: Quy trình xử lý ngôn ngữ tự nhiên*

### B. Bảng biểu
- Bảng biểu căn giữa trang.
- Chú thích đặt **TRÊN** bảng.
- Cỡ chữ chú thích: `11 pt` hoặc `12 pt`, **in nghiêng (Italic)**, Times New Roman.
- Ví dụ: *Bảng 3.2: Kết quả thực nghiệm độ chính xác của các mô hình*

---

## 4. Header & Footer (Đánh số trang)

1. **Trang bìa & Mục lục**: Không đánh số trang (hoặc đánh số La Mã i, ii, iii... cho các trang phụ lục/mục lục trước phần Mở đầu).
2. **Nội dung chính**: Số trang được đánh bằng số Ả Rập (1, 2, 3...) đặt ở góc dưới bên phải hoặc ở giữa footer. Bắt đầu đánh số 1 từ trang đầu tiên của phần **MỞ ĐẦU**.
3. Để thực hiện điều này, cần chia tài liệu thành nhiều Section. Section 1 (Trang bìa, mục lục) và Section 2 (Nội dung chính). Tắt thuộc tính `Link to Previous` ở footer của Section 2 để bắt đầu đánh số trang độc lập.
