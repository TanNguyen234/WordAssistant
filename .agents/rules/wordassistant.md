# WordAssistant workspace rule

When a task involves `.docx`, use the `wordassistant` skill and CLI instead of manually unpacking OOXML unless recovery is required.

## IMMUTABLE FORMATTING & STRUCTURAL INVARIANTS (NEVER DEVIATE ACROSS TURNS)

Regardless of context compaction, multi-turn conversational history, or fallback profile defaults, every academic report, course essay, and Word deliverable MUST strictly comply with these canonical invariants:

1. **Paper Geometry**:
   - Paper Size: **A4** (`width: 21.0 cm`, `height: 29.7 cm`)
   - Margins: **Top: 2.0 cm | Bottom: 2.0 cm | Left: 3.0 cm | Right: 2.0 cm**
   - Printing: **1 mặt** (`one_sided: true`)

2. **Typography & Spacing**:
   - Primary Font: **Times New Roman** uniformly throughout all headings, body, tables, and captions.
   - Body Text: **13 pt**, line spacing: **1.5 lines**, spacing before: **0 pt**, spacing after: **0 pt** (or `6 pt` where specified), first line indent: **1.0 - 1.27 cm**.
   - Document Title (Bìa / Title): **18 pt Bold, CENTER, UPPERCASE**.
   - Heading 1 (CHƯƠNG... / MỞ ĐẦU / KẾT LUẬN / PHỤ LỤC / TÀI LIỆU THAM KHẢO): **16 pt Bold, CENTER, UPPERCASE**.
   - Heading 2: **14 pt Bold, LEFT**.
   - Heading 3: **13 pt Bold (hoặc Bold Italic), LEFT**.
   - Captions: **13 pt**, Figure Captions **CENTER** below media (`Hình X.Y. Tên hình`), Table Captions **LEFT/CENTER** above table (`Bảng X.Y. Tên bảng`).

3. **Canonical Section Blueprint**:
   - **Front Matter** (Bìa chính, Bìa phụ, Nhiệm vụ ĐA, Nhận xét GVHD, Nhận xét GVPB, Lời cảm ơn, Mục lục, Danh mục bảng, Danh mục hình, Danh mục từ viết tắt): KHÔNG đánh số trang (hoặc đánh số La Mã thường `i, ii, iii...`).
   - **University Logo Invariants**: Logo trường (university_logo.png) bắt buộc có mặt trên cả **Trang Bìa Chính (Cover)** và **Trang Bìa Phụ (Inner Cover)**. Kích thước hình vuông chuẩn **3.59 cm x 3.59 cm** (1293495 x 1293495 EMUs, ~3.6 cm x 3.6 cm, 101.8 pt), căn giữa (**CENTER**), nằm ngay dưới dòng KHOA CÔNG NGHỆ THÔNG TIN và phía trên khối Tên Đề Tài / Loại Văn Bản.
   - **Page 1 Start**: Trang 1 chính thức bắt đầu từ **`MỞ ĐẦU`** (Đánh số Ả Rập 1, 2, 3... đặt tại chân trang bên phải: `Trang {PAGE}`).
   - **Canonical Chapters**:
     * `CHƯƠNG 1: TỔNG QUAN TÀI LIỆU`
     * `CHƯƠNG 2: PHƯƠNG PHÁP THỰC HIỆN`
     * `CHƯƠNG 3: CÀI ĐẶT THỬ NGHIỆM, KẾT QUẢ VÀ ĐÁNH GIÁ`
     *(Course essay projects with specific structures, such as StrongWine 7 chapters or LMS 10 chapters, are marked as `ADAPTED` in `structure-parity.csv` but must strictly follow Heading 1-3 font sizes, alignments, and caption SEQ conventions).*
   - **Back Matter**:
     * `KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN`
     * `PHỤ LỤC` (Đánh số Phụ lục 1, Phụ lục 2... hoặc A, B...)
     * `DANH MỤC TÀI LIỆU THAM KHẢO` (Định dạng IEEE số trong ngoặc vuông `[1], [2]...`, tác giả in đậm, tên tài liệu in nghiêng, bắt buộc có evidence hash).

4. **Non-Automatable Quality Gates & Anti-Drift Invariants**:
   - **Diagram Canvas Scale**: PlantUML/DrawIO diagrams must be rendered with canvas width <= 1800 px at 180 DPI (`skinparam dpi 180`) to eliminate internal image clipping in Word.
   - **Semantic Alignment**: Every figure/table caption must match its actual visual content and surrounding analytical prose (no generic placeholder screenshots).
   - **AI Fluff Elimination**: Strictly ban generic filler intros ("Trong bối cảnh bùng nổ công nghệ 4.0...", "Như chúng ta đã biết...", "Chèn nội dung tại đây...").
   - **Readiness Verification**: Never claim completion or deliver a DOCX without running `python scripts/check_course_essay_readiness.py <workspace>` and confirming `delivery_status: PASS`, `content_and_sources: PASS`, and `submission_readiness: PASS`.

For long documents, start with `inspect FILE --summary --json`, then use `context FILE --query ... --max-tokens 4000 --json` and `--only-section ID` for the relevant section. Keep context at or below 8,000 estimated tokens per task turn; apply a heading selector to section edits.
Keep core operations deterministic; external AI providers are not required by the WordAssistant runtime. For repository work, inspect relevant files, make a bounded change, run focused local checks, review the diff, and report unavailable evidence.
When a user or assignment requests an official rubric or evaluation criteria in Word, inspect the selected profile's bundled assets and user-supplied copies first. Follow `docs/official-rubric-workflow.md`; preserve the exact source, distinguish review criteria from score levels/weights, and never invent, infer, repair, or fill missing criteria.
