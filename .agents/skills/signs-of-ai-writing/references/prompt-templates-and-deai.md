# De-AI Rewriting Protocols & Prompt Templates

This guide provides proven rewriting directives and automated prompts to transform AI-generated drafts into crisp, authentic, and objective prose (for both English and Vietnamese).

---

## 1. The 4-Stage De-AI Protocol

When tasked with cleaning or rewriting suspected or acknowledged AI-generated drafts:

```
[1. Triage & Strip] ───> [2. Source Verify] ───> [3. Restructure] ───> [4. Human Polish]
  - Remove engine tags      - Check URLs/DOIs       - Break bullet lists    - Restore direct "is/are"
  - Remove placeholders     - Strip UTM tags        - Merge chopped text    - Delete trailing participles
  - Delete chatbot banter   - Drop phantom claims   - Kill fake challenges  - Replace clichés with concrete verbs
```

### Stage 1: Triage & Strip
1. Run `python scripts/ai_writing_linter.py <file>` to locate hard leaks.
2. Delete all conversational intros ("Certainly!", "Dưới đây là..."), sign-offs, and meta-instructions.
3. Purge system tags (`oaicite`, `turn0search0`, `【...†L...】`, `[cite: ...]`, `[span_...]`).
4. Strip tracking parameters from references (`utm_source=chatgpt.com`, `referrer=grok.com`).

### Stage 2: Deep Source Verification
1. Verify that every external URL resolves and is archived.
2. Check DOI syntax and confirm that the cited paper actually matches the subject.
3. If a citation lacks page numbers or is clearly confabulated, flag or remove the claim.

### Stage 3: Structural De-Biasing
1. **Dissolve Inline-Header Vertical Lists:** Convert bulleted lists (`* **Title:** Description`) back into continuous, cohesive paragraphs.
2. **Remove Canned Sections:** Eliminate generic "Challenges and Future Outlook", "Awards and Recognition", or "Key Takeaways" sections unless strictly warranted by primary sources.
3. **Flatten Heading Depth:** Ensure heading hierarchy is logical (h2 -> h3 -> h4) and not decorated with emojis or bold tags.

### Stage 4: Prose Humanization
1. **Restore Direct Copulas:** Replace *serves as a*, *stands as a*, *đóng vai trò là*, *được xem như là* with direct *is*, *was*, *là*, *có*.
2. **Sever Trailing Participles:** Delete sentence-ending `, highlighting...`, `, underscoring...`, `, qua đó khẳng định...`, `, góp phần...`.
3. **Neutralize Puffery:** Replace *vibrant*, *pivotal*, *rich tapestry*, *then chốt*, *bức tranh toàn cảnh* with plain, measurable facts.
4. **Vary Sentence Length:** Mix 6-word direct sentences with longer compound sentences to break the monotonous 18-word LLM cadence.

---

## 2. Universal De-AI Prompt Template (English)

Use this system instruction or prompt when asking an AI assistant to rewrite or humanize a text:

```markdown
Rewrite the following text to strictly adhere to the Wikipedia:Signs of AI writing (WP:AISIGNS) quality standards:

1. OBJECTIVITY & FACTUALITY:
   - Remove all puffery, boosterism, and unearned claims of legacy, importance, or broad trends.
   - Do not claim the subject "stands as a testament", "plays a pivotal role", or "marks a crucial moment".
   - State specific events, dates, and actions directly.

2. SYNTACTIC CLARITY:
   - Use direct verbs: replace "serves as / stands as" with "is / was / has".
   - Eliminate trailing participial clauses (e.g. ", highlighting its role in...", ", fostering collaboration...").
   - Ban negative parallelisms ("not only X, but also Y", "not X, but Y", "Y rather than X").
   - Eliminate mechanical "rule of three" adjective/noun clusters.

3. VOCABULARY HYGIENE:
   - Ban the following AI cliché words: delve, tapestry, pivotal, crucial, vibrant, intricate, interplay, landscape (figurative), testament, multifaceted, leverage, bolster, meticulously.

4. FORMATTING & CITATIONS:
   - Do not convert running prose into bulleted lists with bold inline headers.
   - Avoid excessive boldface. Never use emojis.
   - Strip all AI tracking parameters (utm_source=chatgpt.com) and verify citation coherence.
   - Output clean, natural, encyclopedic prose without any conversational intro or outro.
```

---

## 3. Bản Mẫu Lệnh Chỉ Đạo "Khử Dấu Vết AI" (Tiếng Việt)

Sử dụng bản mẫu chỉ đạo này khi cần yêu cầu viết lại hoặc biên tập tài liệu tiếng Việt:

```markdown
Hãy biên tập và viết lại văn bản sau đây theo tiêu chuẩn chống văn phong AI (WP:AISIGNS Tiếng Việt):

1. TÍNH KHÁCH QUAN VÀ TRUNG HƯNG:
   - Gọt bỏ toàn bộ các tính từ tán dương, sáo rỗng, thổi phồng vai trò: "đóng vai trò then chốt", "là minh chứng rõ nét", "đánh dấu bước ngoặt", "đặt nền móng vững chắc", "khẳng định vị thế".
   - Không gán ghép triết lý hoặc ý nghĩa xã hội giả tạo. Chỉ giữ lại sự thật khách quan, số liệu, thời gian và hành động cụ thể.

2. CÚ PHÁP TỰ NHIÊN:
   - Dùng động từ trực diện: thay vì "được xem như là / đóng vai trò là / vận hành như", hãy dùng trực tiếp "là / có / làm".
   - Cắt bỏ hoàn toàn các vế phân từ đuôi câu sáo rỗng: ", qua đó khẳng định...", ", góp phần nâng cao...", ", từ đó mở ra tiền đề...".
   - Loại bỏ các phép tương phản đối nghịch giả tạo: "không chỉ... mà còn...", "không đơn thuần là... mà là...", "hành động thay vì khẩu hiệu".
   - Không máy móc ghép các bộ ba vần điệu ("đổi mới, sáng tạo và bứt phá").

3. LOẠI BỎ TỪ VỰNG AI ĐIỂN HÌNH:
   - Tuyệt đối không dùng: "bức tranh toàn cảnh", "bức tranh đa sắc màu", "nép mình bên", "tọa lạc tại vị trí đắc địa", "mang đậm dấu ấn", "bề dày lịch sử", "di sản phong phú", "đi sâu vào", "tăng cường gắn kết".

4. HÌNH THỨC VÀ TRÌNH BÀY:
   - Không tự ý chẻ văn xuôi thành danh sách gạch đầu dòng có tiêu đề in đậm kèm dấu hai chấm (* **Tiêu đề:** Nội dung).
   - Không in đậm cơ học khắp bài. Tuyệt đối không dùng icon / emoji (🚀, 💡, 📌).
   - Xóa bỏ hoàn toàn các lời thoại chào hỏi, bàn giao của trợ lý ("Chắc chắn rồi", "Dưới đây là", "Hy vọng thông tin này hữu ích").
   - Trình bày mạch lạc, giản dị, tự nhiên như văn phong của một chuyên gia biên tập thực thụ.
```
