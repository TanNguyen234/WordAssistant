---
name: docx-citation-verification
description: "Guidelines and workflows for verifying references online via Tavily and Gemini APIs, ensuring that AI Agents do not hallucinate or fabricate citations in academic writing."
---

# Xác Thực Trích Dẫn Học Thuật (docx-citation-verification)

## 1. Vấn Đề Bịa Trích Dẫn (AI Hallucination in Citations)

Trong viết lách học thuật, AI thường có xu hướng tự "bịa" ra tên tác giả, tên bài báo, năm xuất bản hoặc đường dẫn để khớp với luận điểm. Đây là hành vi **nghiêm cấm tuyệt đối** trong nghiên cứu khoa học. 

Mọi trích dẫn khoa học trong WordAssistant bắt buộc phải:
- Là tài liệu nghiên cứu **có thật**.
- Có tác giả, năm xuất bản, tên tạp chí/đại hội và URL nguồn **chính xác**.
- Được đăng ký chính thức trong cơ sở dữ liệu `references.json`.

---

## 2. Quy Trình Xác Thực Trích Dẫn Tự Động

Mỗi khi Agent muốn đưa một nhận định học thuật vào tài liệu và cần trích dẫn, Agent bắt buộc phải tuân theo quy trình sau:

```mermaid
graph TD
    A[Nhận định cần trích dẫn] --> B[Tra cứu trực tuyến bằng citation_helper.py]
    B --> C{Tìm thấy bài báo thật?}
    C -- Có --> D[Gemini trích xuất metadata chuẩn]
    D --> E[Tự động thêm vào references.json]
    D --> F[Viết mã [@cite_key] vào văn bản]
    C -- Không --> G[Tìm kiếm từ khóa khác hoặc bỏ trích dẫn]
```

---

## 3. Cách Sử Dụng Script Bổ Trợ `citation_helper.py`

Agent có thể chạy lệnh trực tiếp từ terminal để tìm kiếm và thêm nguồn tham khảo thật vào cơ sở dữ liệu:

```bash
# Định dạng: python scripts/citation_helper.py "<Từ khóa tìm kiếm hoặc tên bài báo>"
python scripts/citation_helper.py "Attention Is All You Need Vaswani 2017"
```

### Cách thức hoạt động:
1. Script sẽ gọi **Tavily Search API** để tìm kiếm trên các nguồn học thuật uy tín như Google Scholar, arXiv, ResearchGate, IEEE.
2. Dữ liệu thô từ Tavily sẽ được chuyển cho **Gemini API** để làm sạch và chuyển đổi thành cấu trúc JSON chuẩn (tác giả, tên bài, tạp chí, năm, volume, trang, link).
3. Kết quả được lưu tự động vào `references.json` dưới dạng khóa duy nhất (ví dụ: `vaswani2017attention`).
4. Agent chỉ cần sử dụng cú pháp `[@vaswani2017attention]` trong file markdown hoặc chèn thủ công qua MCP tools.
