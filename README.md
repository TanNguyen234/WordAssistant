# WordAssistant - Academic Document System for Agents

Hệ thống **WordAssistant** cung cấp các kỹ năng (Skills) chuyên sâu và công cụ bổ trợ cho AI Agent trong việc khởi tạo, viết nội dung, quản lý trích dẫn và định dạng tự động tài liệu Microsoft Word (.docx) ở cấp độ học thuật (Tiểu luận, Đồ án chuyên ngành, Đồ án tốt nghiệp, Báo cáo thực tập) theo đúng quy chuẩn đại học Việt Nam.

---

## 📁 Cấu trúc Thư mục Dự án

```
WordAssistant/
├── .agents/
│   └── skills/                  # Thư mục kỹ năng chuyên sâu cho Agent
│       ├── docx-mcp-core/       # Skill cốt lõi tương tác với docx-mcp (OOXML rules)
│       ├── docx-academic-outline/ # Skill cấu trúc đề cương đồ án Việt Nam
│       ├── docx-academic-format/  # Skill căn lề, font, giãn dòng học thuật
│       ├── docx-academic-citations/ # Skill quản lý trích dẫn IEEE/APA
│       └── docx-citation-verification/ # Skill tìm kiếm & xác thực trích dẫn thật qua Tavily + Gemini
├── templates/                   # Các file tài liệu Word mẫu đã được định hình
│   ├── tieu_luan_template.docx
│   ├── do_an_chuyen_nganh_template.docx
│   └── do_an_tot_nghiep_template.docx
├── scripts/                     # Các Python script tự động hóa bổ trợ
│   ├── format_checker.py        # Kiểm định định dạng file DOCX có chuẩn học thuật không
│   ├── markdown_to_docx.py      # Build tài liệu từ Markdown + Citations + Footnotes
│   ├── templates_generator.py   # Script tự động tạo lại các file templates
│   ├── citation_helper.py       # Tra cứu & xác thực trích dẫn thật qua Tavily và Gemini
│   ├── docx_diff.py             # So sánh 2 tài liệu Word, xuất file so sánh
│   └── docx_merge.py            # Gộp nhiều tệp tin Word chương thành một file
├── references.json              # Cơ sở dữ liệu trích dẫn của tài liệu (IEEE / APA)
├── requirements.txt             # Thư viện Python cần thiết
├── AGENTS.md                    # Luật lệ và tiêu chuẩn bắt buộc cho AI Agent
└── README.md                    # Tài liệu hướng dẫn sử dụng
```

---

## 🛠️ Hướng dẫn Cài đặt & Tích hợp

### 1. Cài đặt Dependencies Python
```bash
pip install -r requirements.txt
```

### 2. Tích hợp docx-mcp server vào AI Agent
WordAssistant hoạt động cực kỳ hiệu quả khi kết hợp với MCP Server `docx-mcp` (được cung cấp tại https://github.com/TanNguyen234/docx-mcp).

**Đối với Claude Code**:
Thêm MCP server trực tiếp bằng lệnh:
```bash
claude mcp add docx-mcp -- uvx docx-mcp-server
```

**Đối với Claude Desktop / Cursor / VS Code**:
Cấu hình file MCP settings của bạn:
```json
{
  "mcpServers": {
    "docx-mcp": {
      "command": "uvx",
      "args": ["docx-mcp-server"]
    }
  }
}
```

---

## 🚀 Hướng dẫn Sử dụng

### 1. Build Tài liệu từ Markdown và Citations
Bạn viết nội dung báo cáo bằng Markdown (ví dụ: `sample_essay.md`) và khai báo nguồn tài liệu tham khảo trong `references.json`. Sau đó, chạy script:
```bash
python scripts/markdown_to_docx.py sample_essay.md references.json output.docx
```
Script sẽ tự động:
- Căn lề chuẩn A4 (Trái 3cm, Phải 2cm, Trên 2cm, Dưới 2cm).
- Thiết lập font Times New Roman, cỡ chữ 13pt, line-spacing 1.5, space after 6pt.
- Phân tích và tạo Heading 1, 2, 3 tự động bắt đầu trang mới cho mỗi Heading 1.
- Định dạng bảng biểu, căn giữa, thiết lập viền và padding ô.
- Đổi các thẻ trích dẫn dạng `[@cite_key]` thành số thứ tự `[1]`, `[2]` (nếu là chuẩn IEEE) hoặc `(Tác giả, Năm)` (nếu là chuẩn APA).
- Tự động sinh danh mục **TÀI LIỆU THAM KHẢO** được định dạng chuẩn ở cuối trang.

### 2. Kiểm định định dạng (Format Auditing)
Để kiểm tra xem file Word có đạt chuẩn định dạng học thuật của Việt Nam hay không:
```bash
python scripts/format_checker.py output.docx
```
Công cụ sẽ quét toàn bộ tài liệu và đưa ra cảnh báo chi tiết nếu phát hiện lỗi về lề trang, font chữ không phải Times New Roman, cỡ chữ không chuẩn, giãn dòng sai hoặc căn lề không đều (Justify).

### 3. Tìm kiếm & Xác thực Trích dẫn Thật (Citation Verification)
Để tránh hiện tượng AI "bịa" trích dẫn, trước khi viết mã trích dẫn, hãy cho Agent chạy script tìm kiếm trực tuyến qua Tavily API và làm sạch metadata bằng Gemini API:
```bash
python scripts/citation_helper.py "Attention Is All You Need Vaswani 2017"
```
Script sẽ tự động tìm thông tin chính xác của bài viết trên internet và ghi thông tin chuẩn vào `references.json`. Agent chỉ cần sử dụng mã trích dẫn tương ứng (ví dụ: `[@vaswani2017attention]`) trong văn bản.

### 4. So sánh Hai Tài Liệu (Diff)
So sánh bản nháp của sinh viên với bản sửa của giảng viên hướng dẫn để xuất ra file docx chứa các tracked changes và file tóm tắt thay đổi:
```bash
python scripts/docx_diff.py draft.docx revised.docx compared_output
```

### 5. Gộp Nhiều Tài Liệu (Merge)
Gộp nhiều file Word chương thành một file đồ án hoàn chỉnh thống nhất (tự động điều chỉnh các `paraId` để tránh xung đột cấu trúc):
```bash
python scripts/docx_merge.py full_report.docx chuong1.docx chuong2.docx chuong3.docx
```
