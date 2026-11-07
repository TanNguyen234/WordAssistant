# WordAssistant agent operating contract

These rules apply to WordAssistant and to agents using this repository as a DOCX workflow. A target repository's own `AGENTS.md`, project configuration, supplied source documents, and the user's current instructions determine project-specific content. Never carry an HCMUNRE requirement into another school or report unless that profile is selected.

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

5. **Anti-Carelessness & Framework Limitation Invariants (Chống làm ẩu & Khắc phục triệt để hạn chế WordAssistant)**:
   - **Zero-Residual Template Cleanup Gate (Dọn sạch 100% rác và bảng mẫu của template)**:
     * Cấm tuyệt đối việc để sót bảng mẫu rỗng (placeholder tables), đoạn văn mẫu giữ chỗ (placeholder paragraphs), hoặc ngắt trang tạo trang trắng (orphan breaks/blank pages) từ template gốc trong file đầu ra.
     * Khi dùng template ĐACN HCMUNRE cho Tiểu luận môn học (Course Essay), PHẢI xóa bỏ hoàn toàn: `doc.tables[0]` (bảng lịch làm việc 7x4 thừa) và `doc.tables[1]` (bảng viết tắt mẫu 7x3 thừa nếu chèn bảng mới).
     * Phải duyệt kiểm tra tự động trước khi lưu: không còn bất kỳ bảng rỗng, không còn trang trắng vô nghĩa (như lỗi Trang 8 và Trang 14).
   - **Dynamic Image Aspect Ratio Scaling & Anti-Ragged Pagination (Co giãn ảnh động theo tỷ lệ & Chống ngắt trang rác)**:
     * Cấm gán cứng một kích thước ảnh cố định (ví dụ ép rộng 14.5 cm đồng loạt).
     * Mọi hình ảnh chèn vào bắt buộc phải được đọc kích thước pixel thực tế bằng thư viện xử lý ảnh (`Pillow`) để tính tỷ lệ khung hình (Aspect Ratio R = width / height):
       - Ảnh khổ ngang rộng (R >= 1.3): Chiều rộng cho phép 12.5 cm - 13.5 cm, chiều cao tối đa không vượt quá 9.0 cm.
       - Ảnh khổ dọc, hình vuông, hoặc ảnh bảng giao diện cao (R < 1.3): Bắt buộc thu nhỏ chiều rộng về 9.5 cm - 11.0 cm, hoặc khống chế chiều cao tối đa h <= 8.5 cm để không bao giờ làm tràn trang đột ngột.
     * Bắt buộc bật thuộc tính `keep_with_next = True` cho: đoạn văn dẫn nhập ngay trước ảnh, đoạn văn chứa chính hình ảnh, và đoạn văn Caption ngay dưới ảnh để triệt tiêu hoàn toàn hiện tượng "nửa trang trắng" (trang chỉ có 3–6 dòng chữ rồi ngắt trang vì ảnh sau quá to).
   - **Academic Rigor & Anti-Summarization Protocol (Kỷ luật học thuật - Cấm tóm tắt sơ sài)**:
     * Cấm tự ý tóm tắt, cắt xén, rút gọn các kịch bản kiểm thử, cấu hình CLI, log terminal, hoặc bảng đối chiếu thành các gạch đầu dòng hời hợt.
     * Bắt buộc phục hồi và trình bày 100% đầy đủ: toàn bộ mã lệnh Cisco IOS (`configure terminal`, `ip route`, `router ospf`, `vlan`...), log Netmiko/Django terminal khi thực thi tự động, bảng đối chiếu thông số giữa Giao diện Web vs Terminal CLI, và phân tích chuyên môn quản trị mạng sâu từ tài liệu nguồn.
   - **Hybrid Static + Dynamic TOC/LOF/LOT Gate (Khắc phục hạn chế WordAssistant)**:
     * Khắc phục hạn chế `python-docx` không có layout engine và Word COM bị treo modal dialog khi cập nhật trường ngầm:
     * Mọi khối Mục lục (TOC), Danh mục hình (LOF), Danh mục bảng (LOT) PHẢI được xuất theo kiến trúc Lai (Hybrid):
       1. Tự động tính toán số trang thực tế và điền sẵn danh mục có chữ, dấu chấm dẫn tab leader (`w:tab w:leader="dot"`), và số trang tĩnh hiển thị ngay lập tức khi mở file ở bất kỳ môi trường nào (không bao giờ hiển thị chữ giữ chỗ thô `"Update field in Word"`).
       2. Bọc các mục đó bên trong mã trường Word dynamic (`w:fldSimple w:instr="TOC ..."` hoặc `w:r` tương thích) để khi người dùng mở trong Microsoft Word vẫn có thể bấm `F9` cập nhật tự động.
   - **Headless COM Automation Safety (An toàn tự động hóa Word COM)**:
     * Khi gọi Microsoft Word qua COM: Bắt buộc thiết lập `word.DisplayAlerts = 0` (wdAlertsNone) và `word.Visible = False`.
     * Tuyệt đối không gọi các hàm kích hoạt popup modal tương tác người dùng (như `tof.Update()`) trong môi trường headless.
     * Luôn bọc trong khối `try...finally` để đảm bảo `doc.Close(SaveChanges=False)` và `word.Quit()` giải phóng hoàn toàn tiến trình `WINWORD.EXE`.
   - **Mandatory Independent Visual Inspection Gate (Cổng kiểm tra trực quan từng trang)**:
     * Không bao giờ được phép tuyên bố hoàn thành hoặc bàn giao chỉ dựa vào kết quả lệnh script.
     * Bắt buộc phải render toàn bộ tài liệu sang PDF và xuất 100% các trang thành ảnh PNG độc lập (150 DPI).
     * Agent phải duyệt kiểm tra trực quan toàn bộ các trang để xác nhận: không có trang trắng thừa, không có bảng rác template, Mục lục hiển thị chữ và số trang đầy đủ, không có hình ảnh bị cắt hay ngắt trang dị dạng trước khi bàn giao.


## Repository and CLI workflow

1. Use the WordAssistant CLI as the control plane. In a new environment, run `wordassistant doctor --json` once, then use `capabilities --json` before selecting optional Word-native operations.
2. Inspect an unfamiliar DOCX before editing it. For documents over 40 pages or of unknown length, start with `wordassistant inspect FILE --summary --json`; full `inspect --json` includes every paragraph's text and can flood agent context.
3. For long documents, retrieve one task-relevant section at a time with `wordassistant context FILE --query "..." --max-tokens 4000 --only-section SECTION_ID --json`. If the ID is unknown, run one bounded query without `--only-section`, then use an ID returned by context. Keep retrieved text at or below 8,000 tokens in one task turn; ask for another section only when needed. `--active-section-id` prioritizes a section but may include neighbors; `--only-section` is the strict boundary. A 200-page file may be indexed locally, but its full text must not be copied into LLM context.
4. Edit only the selected section or exact target. For section-wide text edits, pass `--selector '{"type":"heading","text":"EXACT HEADING"}'`; for one unique paragraph, use an exact text or paragraph selector. Without `--selector`, text replacement can apply across the document. Save to an output copy.
5. Prefer JSON output for automation. Preserve source paths, hashes, commands, and whether a result is unit, integration, sandbox, live, or not run.
6. For behavior changes, record scope and acceptance checks, write focused tests, implement the change, review the stable diff, and run the broader suite once. A later source change invalidates earlier verification evidence.
7. Do not read or copy unrelated proposal, outline, or sample files as authorities for a report. Keep source precedence explicit when guidance and examples differ.

## Academic source and citation workflow

1. Search for sources that support the actual research question. Prefer primary research, official standards, and authoritative institutional material where appropriate; use reviews for context and label their role.
2. Treat search results and DOI metadata as discovery leads only. Open or download the source, confirm its identity and version, and inspect the relevant page, section, table, or figure before citing a claim.
3. Record stable identifiers, authors, title, date/version, publisher or repository, source URL, retrieval date, applicable reuse license when downloading, and a content hash for a saved source.
4. A downloaded file or a valid DOI does not prove relevance, claim support, permission to redistribute, originality, or absence of plagiarism. Do not bypass paywalls or download a full text without an allowed access basis.
5. Cite only source material that has been reviewed for the claim. Keep direct quotations exact, clearly marked, and tied to a page or section. Paraphrase from the checked source, cite it, and preserve uncertainty; do not copy source phrasing without quotation marks. For the HCMUNRE profile, bibliography numbers use brackets, author names are bold, titles are italic, and publication details appear only when supported by the evidence record.
6. Never invent a source, page, quotation, author, result, source-review state, or similarity result. If a source or passage cannot be checked, say so and leave the claim unresolved.
7. The writing review skill is editorial guidance, not authorship detection. Do not assign AI probabilities, promise detector evasion, or infer plagiarism from style. See `.agents/skills/signs-of-ai-writing/SKILL.md`.

### WordAssistant source commands

- `wordassistant research search --query ...` returns Crossref discovery leads. `research import-doi` stores a non-citable candidate.
- `research open-access` reads the required Unpaywall email from an environment variable; do not pass or print the value. `research download` stores only a PDF with an explicit supported license and records its hash.
- `research excerpt` returns bounded passages from the saved source. `research review` requires an exact excerpt, location, claim, reviewer identity, and explicit support confirmation before changing the record to `reviewed`.
- Citation and composition operations reject `candidate` evidence and recheck saved source hashes for `reviewed` evidence. The HCMUNRE report profile also rejects legacy or manually entered records until their downloaded source passage has been reviewed. Do not bypass these gates by copying DOI metadata into prose.
- See `docs/academic-report-workflow.md` for the reusable scaffold, caption, research, compose, and Word validation sequence.

## DOCX content and Word semantics

1. Select a profile explicitly for institution-specific rules. The HCMUNRE ĐACN 2026–2027 profile is one selectable use case, not a universal report format.
2. Put persistent behavior in real Word styles, section properties, page-number fields, caption `SEQ` fields, TOC/list fields, and table properties. Direct visual formatting alone does not satisfy a Word-template requirement.
3. Keep documents editable and standards-compatible. Do not use layout tables for covers unless the controlling guide requires them. Avoid macros and unsupported package parts.
4. Do not fabricate a topic, results, names, signatures, approvals, supervisor details, source support, or declarations. When those inputs are unavailable, create an honest editable template and identify the remaining fields.
5. Base operations must not require Gemini, OpenAI, Anthropic, or other model-provider keys. Use an optional advanced Word backend only when a requested Word-native feature needs it; check its availability before relying on it.
6. Validate against the selected profile. When appearance matters, update and save fields through Microsoft Word, render the saved file, inspect every page, reopen it, and confirm the styles and layout persist. Report when native Word or visual review was not available.

## Scope and side effects

- Do not commit, push, migrate, delete user data, force an operation, or make a paid-provider call without the user's explicit authorization for that action.
- For networked research, verify the configured provider boundary and response schema before a full run. Do not log credentials or store an email used only for a provider request.
- Do not activate Claude-, Cursor-, Kiro-, or OpenCode-only hooks as Codex lifecycle hooks.

## Official rubrics in Word reports

For any WordAssistant task that requests an official rubric or assessment criteria in a Word deliverable, follow `docs/official-rubric-workflow.md`. Inspect the selected profile's bundled `source_assets` and user-supplied copies before declaring the source missing. Preserve the original and include either the complete standalone rubric appendix or the complete applicable assessment-criteria section in its review page. Distinguish explicit review criteria from scoring levels/weights; never invent missing criteria or substitute a course-weight summary, sample, or another assignment's rubric. For course essays, populate `rubric_inclusion` metadata and run the readiness gate described in `docs/course-report-workflow.md`.

## Skills

- Load only skills that match the current work. UI tasks use the relevant UI skill; API and module-boundary work uses the matching design skill; current framework behavior uses official documentation or Context7.
- For DOCX work, follow `.agents/skills/wordassistant/SKILL.md`.
- For English or Vietnamese prose review, follow `.agents/skills/signs-of-ai-writing/SKILL.md`; use its linter findings as optional review prompts only.
- Skills guide workflow. They do not install tools, plugins, credentials, dependencies, or authorize external calls.


## Course-essay project asset and caption gate

When checking an existing course essay against a current application project, preserve the input DOCX and work on a distinct output copy. Tie each screenshot/diagram to current route/template, actual image contents, and (when available) source asset hash. Hash-only evidence is snapshot provenance, not runtime verification. Mark mockups as proposals. Inspect dynamic SEQ field placement and the visible Word-rendered caption/list. Keep stdout JSON and stderr separate. `verify.delivery_status == PASS` means the Word delivery checks passed; it does not establish academic content or submission readiness. If rubric, required source review, or required project evidence is missing, record `NOT_RUN`/`BLOCKED` and set submission readiness to `INCOMPLETE`; do not describe the work as ready to submit. Review and disposition every integrity-audit warning. Internal labels such as `S1`–`S8` are traceable citations only when they resolve to reviewed evidence records and a visible source list. Read `docs/strongwine-course-essay-lessons.md` and follow `docs/course-report-workflow.md`.

Course-essay rubric inclusions also require a `project.json` record with the source/output hashes and human review. The readiness checker verifies exact text parity for DOCX and text-readable PDF sources; scanned, image-bearing, unreadable, missing, partial, or stale rubric evidence stays `INCOMPLETE`/`BLOCKED`.

For any multi-turn course-essay job, keep a concise `task-brief.md` at the workspace root as the active handoff: current request, controlling sources, frozen acceptance checks, do-not-change constraints, canonical input/output path and hash, latest QA bound to that hash, blockers, and next action. Create it before editing an existing report; update it immediately when the user adds or corrects a requirement. On resume, read the brief, `project.json`, and only the latest QA reports that match the current DOCX hash; retrieve other history or document sections only to answer a specific unresolved question. If the brief, matrices, project pointers, and latest artifact disagree, reconcile those records before editing. Keep the brief short and link detailed evidence instead of copying it.

Before editing a course essay, complete `acceptance-crosswalk.csv` with one row per applicable user/guide/assignment-rubric/content criterion. The readiness checker requires user, guide, assignment/rubric, heading/TOC, abstract, screen hierarchy, runtime screenshots, diagrams, visual content, and argument/citation coverage, evidence files and hashes, reviewer/date, and the current output DOCX SHA-256. `structure-parity.csv` must state `include_in_toc` for every heading; `asset-parity.csv` must state expected embedded media count and `caption_required` per asset. Captioned assets need their exact caption. Uncaptioned assets (such as cover logos) need a blank caption, exact location, evidence, and an explicit false value; the checker accounts for these separately from caption-bound figures. For every runtime screenshot, also record `capture_id` and exact `runtime_route`, and point `project.json` at a manifest whose capture context confirms a visible, non-headless browser tab, whose final HTTP(S) URL matches the route, and whose per-page arrival history records visible UI steps, confirms no local UI/file or direct-route load, and binds the image by SHA-256. Wait for each real page to load and record a timezone-aware timestamp, HTTP/document status, console errors/warnings, and a hash-bound human `page_state_review` before marking it successful. Screenshot every attempted page state, including visible error pages; record the observed error and keep its image instead of dropping the failed capture. Any non-2xx response, console error, or reviewed visible error must fail runtime readiness. Direct-route, local-file, and headless screenshots are not accepted when user-style navigation is required. The checker compares outline and TOC separately, verifies image totals/caption sequence, and rejects runtime captures with missing or mismatched click-through evidence. These automated checks do not prove image meaning, requirement discovery, abstract quality, or claim support; preserve a hash-bound human review record for those.

Before a course-essay handoff, run `python scripts/check_course_essay_readiness.py <workspace>` from the repository root. It is read-only and emits separate `word_delivery`, `content_and_sources`, and `submission_readiness` gates. Report its result and blocking reasons; never turn a Word delivery PASS into submission readiness PASS.
