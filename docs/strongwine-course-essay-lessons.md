# Nhật ký lỗi và cách phòng tránh — tiểu luận học phần StrongWine

Ngày hoàn tất: 2026-10-19 (Asia/Bangkok)

## Phạm vi và tệp được kiểm tra

- Tệp gốc mới nhất trước khi sửa: `artifacts/strongwine_staged_m3.docx`
- SHA-256 tệp gốc: `56F150FE21920E91F3283AD5EAE576747EECC5D60E763EA59A0B655E6665F365`
- Bản đầu ra đã sửa: `artifacts/strongwine_course_essay_lists_rebuilt.docx`
- SHA-256 đầu ra: `d0626681d1ce2816cae31c224c12ba72bee1747f859f66aa8a1b8704ad7de0cf`
- Phân loại: tiểu luận học phần. Không áp quy cách luận văn ĐACN HCMUNRE hoặc profile generic làm rubric môn học khi chưa có hướng dẫn của giảng viên.
- Phạm vi sửa: số trang bắt đầu ở 0 và danh mục hình/bảng rỗng. Không sửa nội dung thân bài, số hiệu chú thích, hình ảnh hoặc câu chữ.

## Lỗi đã sửa

### 1. Số trang phần mở đầu bắt đầu ở 0

- **Biểu hiện:** trang “MỞ ĐẦU” in “Trang 0”; mục lục chính cũng ghi trang 0 cho MỞ ĐẦU và các đề mục đầu tiên.
- **Nguyên nhân:** section bắt đầu tại “MỞ ĐẦU” đặt trường PAGE bắt đầu từ 0.
- **Khắc phục:** đặt số bắt đầu của section thành 1; dùng Word làm mới các trường PAGE/PAGEREF và mục lục chính sau khi dàn trang.
- **Kết quả:** `page-number inspect` báo section “MỞ ĐẦU” bắt đầu ở 1. Render Word hiển thị “MỞ ĐẦU” là Trang 1 và trang kế là Trang 2; mục lục chính ghi số trang in tương ứng.

### 2. Danh mục hình và danh mục bảng rỗng

- **Biểu hiện ban đầu:** hai trang danh mục in “No table of figures entries found.”
- **Nguyên nhân:** trường danh mục cũ lọc theo nhãn `Hình`/`Bảng` (`TOC \c`), nhưng phần lớn chú thích hiển thị không có trường SEQ mang nhãn khớp. Kiểm tra trước sửa nhận diện 63 chú thích hình và 44 chú thích bảng; có 2 ảnh chưa có chú thích liền kề.
- **Khắc phục:** tạo hai kiểu đoạn Word riêng kế thừa cách trình bày Caption (`FigureCaptionList`, `TableCaptionList`), gán đúng kiểu cho các chú thích hiện có, rồi dùng hai trường TOC riêng lọc theo kiểu đoạn để Word dựng danh mục.
- **Kết quả:** render Word có 63 mục hình (55 ở trang vật lý 13, 8 ở trang 14) và 44 mục bảng (trang vật lý 15). So sánh tuần tự nội dung chú thích trong DOCX gốc và các đoạn đã phân loại ở bản đầu ra cho kết quả trùng khớp: 63/63 hình, 44/44 bảng. Không tự đặt tên cho 2 ảnh chưa có chú thích.
- **Số trang in:** trang vật lý 13–15 in lần lượt Trang 12–14; mục lục chính ghi trang in 12 cho danh mục hình và 14 cho danh mục bảng.

### 3. Chữ xanh, căn lề không thống nhất, dòng biểu mẫu bị giãn và sơ đồ bị cắt

- **Biểu hiện:** liên kết và một số tiêu đề vẫn xanh; Heading 1 căn giữa/lệch trái tùy đoạn; khối ký tên, câu hỏi và đánh giá bị giãn; trường `Lớp` rớt riêng sang dòng mới. Sơ đồ Hình 3.1 mất một phần bên phải dù OOXML báo không crop.
- **Nguyên nhân:** màu nằm trong style `Hyperlink` và ghi đè màu trực tiếp ở run; style `Heading 1` chưa đặt căn giữa; các paragraph biểu mẫu dùng căn đều với ngắt dòng/tab; ảnh PNG Hình 3.1 đã bị cắt ngay lúc dựng PlantUML (`class_architecture_layered.png`, 4096 px chiều rộng). Kiểm tra crop metadata và tỉ lệ thôi không phát hiện được nội dung đã bị cắt bên trong ảnh raster.
- **Khắc phục:** đặt màu style/run chữ thành đen; căn giữa Heading 1 bằng style; tạo style `SignatureBlock`, `FormPrompt`, `FormInfo`; đổi thông tin sinh viên sang hai hàng ổn định; dựng lại Hình 3.1 từ `.puml` ở 180 DPI, cập nhật PNG nguồn và khung Word theo tỉ lệ ảnh mới.
- **Kết quả:** `artifacts/strongwine_course_essay_visual_corrected.docx`, SHA-256 `b4a803ae984856a40acb45f927d02de147813fd3002cc0d0793385d70993d124`; render Word 176 trang. Đã xem trực tiếp các trang 5–6, 17, 19, 44–46; hình hiện đủ ô `HomeController` và phương thức, không còn cắt ở mép phải.
- **Kiểm tra ảnh:** 65 ảnh inline, 64 tệp media, 0 crop metadata, 0 lệch tỉ lệ trên 1%, 0 vượt vùng nội dung A4. Ảnh giao diện còn màu vì màu đó thuộc screenshot, không phải màu chữ Word.
- **Caption audit:** `REVIEW_REQUIRED` (55/65 hình, 3/44 bảng có caption ngay sát đối tượng, 0 mơ hồ), giống hệt bản trước lần chỉnh này. Không tự di chuyển/đặt lại caption vì chưa xác định quan hệ đúng cho từng bảng; giữ cảnh báo để đối chiếu với rubric.

## Bằng chứng kiểm tra bản cuối

- Render bằng Microsoft Word: 176 trang, không có trang trắng trong PDF.
- Đã xem contact sheet của toàn bộ 176 trang; xem riêng độ phân giải cao các trang danh mục hình, danh mục bảng và trang nối giữa hai phần. Không còn thông báo danh mục rỗng; các trang danh mục và phần nội dung sau đó không bị tràn hoặc mất trang.
- PDF render: `artifacts/strongwine_course_essay_rebuilt_render/strongwine_course_essay_lists_rebuilt.pdf`
- Contact sheet: `artifacts/strongwine_course_essay_rebuilt_render/contact_sheets/`
- Ảnh xem riêng danh mục: `artifacts/strongwine_course_essay_rebuilt_render/review_page_13.png`, `review_page_14.png`, `review_page_15.png`.
- `page-number inspect`: `SUCCESS`; section “MỞ ĐẦU” bắt đầu ở 1 và có trường PAGE ở chân trang.
- `verify ... --json` chạy theo profile `generic`: `overall_status FAIL`; `structural_status PASS`, `numbering_status PASS`, `field_structure_status PASS`. Profile này báo lỗi định dạng vì áp lề 2,54 cm, cỡ chữ 12 pt và giãn dòng 1,15; các giá trị đó chưa được xác nhận là yêu cầu của môn học. Vì vậy không tự ý đổi định dạng theo kết quả generic. `field_freshness_status` là `STALE_OR_UNKNOWN`; Word render mới là bằng chứng trực quan cho nội dung danh mục và số trang được hiển thị.
- Chưa đối chiếu tính đúng học thuật của mọi luận điểm/trích dẫn với tài liệu nguồn hoặc hướng dẫn chấm của giảng viên; các nguồn và rubric đó không có trong bộ đầu vào của lần sửa này.

## Lỗi/bất định còn cần lưu ý

- Có 2 ảnh chưa có chú thích liền kề. Không thêm chú thích đoán nội dung. Nếu giảng viên yêu cầu mọi ảnh đều phải có chú thích, cần xác định tên/mô tả đúng từ tác giả trước khi bổ sung.
- Chưa có hướng dẫn môn học để kết luận lề, font, giãn dòng, cấu trúc phụ lục hoặc cách lập tài liệu tham khảo có đúng rubric hay không.
- Báo cáo cũ `artifacts/PAGE_BY_PAGE_AUDIT_REPORT.md` không ghi hash DOCX đã kiểm tra và thống kê 64 hình, trong khi caption audit hiện tại ghi nhận 65 ảnh. Không dùng báo cáo cũ để chứng nhận bản cuối; mọi kiểm tra phải gắn với hash của đúng tệp.

## Checklist để không tái phạm

1. Xác định tài liệu là tiểu luận học phần hay luận văn; chỉ chọn quy cách/profile có hướng dẫn tương ứng.
2. Trước khi sửa số trang, chạy `page-number inspect`; xác nhận section nội dung bắt đầu ở 1 nếu rubric yêu cầu.
3. Trước khi cập nhật danh mục, đối chiếu trường TOC với cách đánh dấu chú thích thực tế. Không giả định nhãn SEQ khớp chỉ vì chữ hiển thị giống nhau.
4. Khi chú thích hiện có không dùng SEQ phù hợp, có thể phân loại bằng kiểu đoạn Word và lọc danh mục theo kiểu đó; giữ nguyên chữ/số thứ tự và không tự đoán chú thích còn thiếu.
5. Sau mỗi lần thay DOCX, cập nhật lại mục lục và trường trang trong Word, render lại toàn bộ tệp cuối, rồi rà trang mục lục, danh mục, đầu phần nội dung và các trang bị dịch chuyển.
6. Ghi đường dẫn, SHA-256, số trang và thời điểm render vào nhật ký. Bất kỳ lần sửa nào sau đó đều làm bằng chứng QA cũ hết hiệu lực.
7. Không coi `verify` theo profile generic là kết luận đạt/không đạt rubric học phần nếu chưa chọn đúng profile hoặc chưa có yêu cầu của giảng viên.
8. Không chỉ tìm màu xanh ở văn bản hiển thị; kiểm tra cả màu trong style `Hyperlink` và ghi đè `w:rPr/w:color` ở từng run/story.
9. Không căn đều các dòng biểu mẫu có tab hoặc ngắt dòng thủ công. Dùng style trái/giữa theo mục đích; xem PDF để bắt trường bị rớt riêng sang hàng mới.
10. Với ảnh, ngoài kiểm tra `a:srcRect`, khung Word và tỉ lệ pixel, phải nhìn sát mép ảnh. Raster có thể bị cắt từ trước khi nhúng nên không có dấu crop trong DOCX. Với PlantUML, kiểm tra nhãn/lớp ở mép phải trước khi chèn; nếu output chạm giới hạn pixel, giảm DPI rồi dựng lại cả `.puml` lẫn PNG nguồn.
11. Sau khi đổi ảnh hoặc kích thước khung ảnh, render lại DOCX cuối; bằng chứng render trước thay đổi không còn áp dụng. Soát trang bị ảnh hưởng và các trang ngay trước/sau để phát hiện xô trang.

## Lệnh và kết quả chính

- `wordassistant page-number inspect artifacts/strongwine_course_essay_lists_rebuilt.docx --json` — `SUCCESS`; section MỞ ĐẦU bắt đầu ở 1.
- `wordassistant verify artifacts/strongwine_course_essay_lists_rebuilt.docx --json` — `FAIL` theo profile generic; cấu trúc và đánh số `PASS`; các cảnh báo định dạng generic không được dùng làm rubric môn học.
- `wordassistant render artifacts/strongwine_course_essay_lists_rebuilt.docx --engine word --outdir artifacts/strongwine_course_essay_rebuilt_render --timeout 240 --json` — PDF 176 trang.
- So sánh văn bản chú thích giữa gốc và bản cuối theo kiểu đoạn: 63/63 caption hình và 44/44 caption bảng khớp đúng thứ tự.
- Kiểm tra PDF: trang danh mục hình có 63 dòng mục (55 + 8), trang danh mục bảng có 44 dòng; 0 trang trắng.
- Bản chỉnh kiểu/ảnh cuối: `artifacts/strongwine_course_essay_visual_corrected.docx`; SHA-256 `b4a803ae984856a40acb45f927d02de147813fd3002cc0d0793385d70993d124`.
- Render cuối: `artifacts/strongwine_course_essay_visual_delivery_render/strongwine_course_essay_visual_corrected.pdf` — Word, 176 trang; các trang cuối bị tác động đã xem riêng ở độ phân giải cao.
- Kiểm tra ảnh cuối: 65 inline, 64 media, 0 crop rectangles, 0 lệch tỉ lệ >1%; Hình 3.1 dựng lại từ PlantUML ở 180 DPI và cập nhật cả PNG nguồn.


## Lessons learned and prevention (2026-10-20)

| Mistake found | Cause | Prevention |
|---|---|---|
| H5.10 showed an extra trailing 10 in Word/PDF although its paragraph looked correct. | The SEQ Hinh field followed the complete caption, so Word rendered its result after the title. | Keep the field within the visible Hinh 5.x label; audit field placement, repair an output copy, update Word fields, and inspect both PDF caption and figure list. Regression test: test_misplaced_caption_sequence_field_is_repaired_and_audited. |
| Empty /cart was labeled checkout; shipper sitemap was labeled profile-edit UI. | Figure/caption relation was assumed from numbering rather than checked against image contents and route/template. | Verify each image-caption pair against the current project route/template and actual image. Remove unsupported pairs instead of guessing. Mark mockups as proposals. |
| Old route/payment statements could remain in prose. | Earlier draft assumptions were not reconciled against current controllers/services. | Verify against current source. In this snapshot checkout is /cart/checkout and Stripe is the supported payment path. H6.2/H6.3 are proposed states. |
| Prepare was run on an already-prepared four-section DOCX and failed. | Prepare expects the three-section source master; it is not the repair mode for the prepared deliverable. | Use Prepare only on the source master. Use RepairCaptionSequence for the known field-placement defect, supply a new OutputDocx, then run the full QA. |
| stderr warnings were merged into JSON output. | PowerShell redirected 2>&1, making stdout JSON unparsable. | Save stdout JSON and stderr logs separately; parse the saved JSON. |

A matching image hash proves saved-snapshot provenance, not current runtime behavior. Generic validation is not a course rubric. Do not mark an uninspected render as a visual pass. Preserve original inputs and failed-run logs.

## Lessons learned and prevention: VietLex capstone (2026-10-22)

These entries describe verified defects from the VietLex rebuild. They add checks to the reusable runbook; the 67-page result and its counts are evidence for this project only, not a future-project target.

| Mistake found | Cause | Correction and prevention |
|---|---|---|
| The first VietLex deliverable was a short, generic report (44 pages) and omitted the full analysis depth expected from the StrongWine comparator. | The workflow treated “capstone” as a document label and did not require a complete rubric/source-based outline plus a qualitative parity review against the accepted full-report example before drafting. | Build the project-specific structure and asset matrices before composition. Review each applicable report group against StrongWine for depth, then record `MATCHED`, `ADAPTED`, or a reasoned exclusion. Never copy StrongWine headings/counts as a quota. Run the readiness checker against the final outline and captions. |
| The generic distinct-inner-cover check rejected the correct two-cover layout. | It anchored the page-break check to the second occurrence of the document-type text, which appears midway through the inner cover, instead of the start of that cover block. | Check the second repeated institution line as the cover-block anchor when available; retain the document-type fallback. A regression test covers two distinct cover blocks. Keep `require_distinct_inner_cover=true` when the selected sample/profile has two covers. |
| Replacing an empty “KẾT LUẬN” heading left a dangling Word `PAGEREF`/TOC bookmark. | The text-normalization edit removed the bookmark nodes attached to the empty heading instead of transferring them to the canonical heading. | Before changing a heading that owns bookmarks, move bookmark start/end nodes to its replacement. After Word saves fields, audit that every internal `PAGEREF` target resolves and that the rendered TOC points to the canonical heading. |
| Figure/table asset F09 was stranded on a page by itself after repagination. | The figure-list caption and the following asset table were allowed to split across a page boundary. | Add a page break before the caption when the list/table must remain a single block. Inspect the affected page at full size and compare all changed pages after field update. |
| The delivery verify failed although the correct 67-page render and visual review existed. | The reuse step was passed `visual_review_challenge.token`; `--reuse-render-report` requires `visual_review_reuse.token` (`wa-visual-reuse-v1:...`). | Keep both token types distinct in the procedure. For a reuse run, copy the versioned reuse token from the exact input report and confirm the DOCX hash, PDF, page count, page-image manifest, and render report are unchanged. |
| The profile disabled distinct-cover validation to work around the false positive. | The project profile was weakened instead of correcting the generic validator’s anchor selection. | Fix the shared validator and add a regression test, then restore the profile requirement and run profile validation on the final DOCX. Do not leave a project-level waiver for a generic checker defect. |
| Earlier notes described the visual review as complete while the final field-updated DOCX had not yet received a delivery attestation. | A successful render and manual viewing were treated as equivalent to the separate delivery gate. | Report visual review, Word delivery, content/source review, and submission readiness as separate states. Run the final delivery verification on the exact saved DOCX hash; readiness remains `INCOMPLETE` when rubric or required human source review is missing. |

For future reports, open `docs/strongwine-course-essay-workflow.md` and complete its project-specific matrices before drafting. Do not copy the 44-page failure or the 67-page correction as fixed dimensions; let the requirements and source evidence determine the outline and asset inventory.
