# VietLex official assessment-criteria source review

Reviewed: 2026-10-25 (Asia/Bangkok)
Purpose: Correct the earlier conclusion that no official assessment material existed, verify the bundled authority, and record the exact criteria included in the VietLex DOCX.

## Controlling source

The exact source already exists in the selected WordAssistant profile's bundled source_assets:

- User-provided copy: C:\Users\VI TINH THANH AN\Documents\Huong dan trinh bay Báo cáo ĐACN_2026-2027.docx
- Bundled copy: D:\Download\WordAssistant\src\wordassistant\data\use_cases\hcmunre_dacn_2026_2027\assets\huong_dan_trinh_bay_dacn_2026_2027.docx
- SHA-256 for both copies: 0F3622DBCD74009FB0867E0D3FA4A1624A38983AF502E55D48868EDF33F74E78

The byte-identical file is also registered in profiles/hcmunre_dacn_2026_2027.json. The source was retrieved in bounded sections with WordAssistant context.

## What the guide contains

The guide provides official review criteria and page instructions. It does not provide numeric scoring levels, weights, or a separate scored matrix.

### Supervisor review page

Source heading: Trang “Nhận xét của giảng viên hướng dẫn” (không đánh số trang, xem mẫu kèm theo). Giảng viên hướng dẫn nhận xét các vấn đề:

1. Kết cấu, phương pháp trình bày.
2. Cơ sở lý luận.
3. Tính thực tiễn và khả năng ứng dụng của Đồ án tốt nghiệp
4. Kết quả: Đạt ở mức nào? (hoặc không đạt), không cho điểm vào trang nhận xét này.

### Reviewer page

Source heading: Trang “Nhận xét của người phản biện” (không đánh số trang, xem mẫu kèm theo)

- Cần thể hiện rõ quan điểm của người phản biện
- Không cho điểm vào trang nhận xét này.

The guide explicitly prohibits points on these pages. No grade bands or weights were inferred.

## Previous discrepancy and correction

The earlier source review looked for a separate scored matrix and did not inspect the selected profile's bundled source_assets. It therefore misreported the official criteria as missing. The prior VietLex review pages also contained locally drafted prompts that were not in the guide.

The WordAssistant workflow now checks selected-profile bundled sources and user-supplied sources first, distinguishes assessment criteria from a scored rubric, stores the exact source sections and markers in profile metadata, and supports hash-bound section comparison for the matching Word review pages.

## VietLex output

Current output: output/VietLex_DoAnChuyenNganh_RubricCriteria_FinalQA_20261025_v5.docx
Current output SHA-256: 382CF9351599DB29B010BE89DACCE7103A2D0F0C2BCA2CA436B61619460A8C30

The supervisor page contains all four criteria above and the reviewer page contains both official instructions. A marker-bounded source/output comparison returned PASS: each complete official section matches its corresponding Word page. The previous local prompts about urgency, scientific value, model accuracy, and defense questions were removed. The report abstract now distinguishes the guide's criteria from the absence of a numeric scoring rubric.

## Current verification

- WordAssistant validate: PASS for profile hcmunre_dacn_2026_2027, variant report; no issues.
- WordAssistant verify: overall PASS and delivery_status PASS; structural, format, field freshness/evaluation, native Word, render, and visual gates PASS; no issues.
- Microsoft Word render: 83 pages; embedded image inventory: 20 images.
- Every rendered page was reviewed. At 1.5x, all 83 current page images are pixel-identical to the previously reviewed v2 Word render. The v2 review-page edit changed pages 5, 6, 7, 8, 10, 11, and 13 from the earlier canonical document; those pages were inspected.
- Exact section comparison: PASS.
- Final verification report: qa/verify-vietlex-rubriccriteria-final-20261025.json
- Visual comparison: qa/render-rubriccriteria-finalqa-20261025-v5/visual-diff.json

Word delivery PASS does not establish submission readiness. The official-criteria inclusion record remains PENDING_HUMAN_REVIEW. The readiness checker reports word_delivery=PASS, content_and_sources=FAIL, and submission_readiness=FAIL (exit code 2). Additional blockers are requirement row 2 NOT_RUN; stale source hashes in claim rows 8 and 13; unreviewed official-criteria metadata; current law not independently checked; protected/token routes and deployed-revision confirmation NOT_RUN; and integrity record src-vietlex-home missing authors, synthetic, url, and year. No missing evidence was filled by inference.

## Outcome

- Official HCMUNRE assessment criteria found in WordAssistant's existing profile assets: YES.
- Separate numeric scoring matrix found in the checked guide: NO.
- Exact guide criteria/instructions included in the current VietLex review pages: YES.
- Automated submission readiness: FAIL for the independent blockers listed above.
