# VietLex — active handoff
Updated 2026-10-25, Asia/Bangkok.

Canonical DOCX: output/VietLex_DoAnChuyenNganh_20261025_v20-final.docx
SHA-256: aa6bae6a26b3d077d6d90d7282b0c724a09bec6ba0e5415ebff6f15082dd6c9b.
Preserved inputs: v18 (prose/models), v19 (alignment/titles). Final v20 changes Caption size only; authored paragraph/table equality checked in qa/caption-font-preservation-v20.json.

## Authority and scope
User: headings left; figure captions centered and concise; audit workflow/style completeness. Earlier approved: 1 cm body indent, thanks to ThS. Định Thị Hồng Loan, semantic chapter hierarchy, NỘI DUNG outside TOC, CAP-01–12 retained, fuller prose and basic UML/data views grounded in VietLex. Reusable generic safeguards and HCMUNRE report profile both required. Actual project read-only; official HCMUNRE guide controls institution formatting. No invented results, source support or instructor approval. No commit/push/paid calls.

## Acceptance and evidence
- 111 headings left in styles/effective paragraphs; 14 figure captions centered with short names and SEQ retained; Caption effective Times New Roman 13 per general guide rule. qa/style-audit-v20.json; qa/validate-v20.json.
- 93 saved Word-rendered pages: 27 changed pages freshly viewed; other 66 exact PNG hashes reuse actual v19 visual review. qa/visual-review-v20.json; qa/page-review-map-v20.json.
- 31 asset rows, 16 media placements (2 logos, 11 diagrams, 3 runtime images), 15 tables. Matrices v18/current DOCX; qa/parity-matrices-v20.json.
- 214 substantive Normal paragraphs, 19,437 whitespace words, 1 cm indent; 445-word acknowledgement on page 3. Ten reviewed references and 12 citation placements; all optional integrity findings dispositioned. Semantic review reused only after text/table equality; content-review-plan-v20.json.
- Pipeline source: style.update alignment; profile alignment validation including inheritance/overrides; figure alignment scope; scaffold respects chosen front-heading style. HCMUNRE report adds Caption 13. Focused tests PASS; previous full suite PASS after scaffold fix; final suite with caption rule PASS, exit 0. qa/changed-files-v20.json; qa/workflow-style-coverage-v20.md.
- Earlier cleanup preserved in qa/cleanup-final-receipt.json and qa/history/pre-v18-revision-inputs-and-adapters.zip. Do not repeat broad deletion.

## Final verification
Full suite PASS exit 0; profile/native fields/render/visual delivery PASS in qa/verify-v20-delivery.json. Crosswalk current hashes reconciled. qa/readiness-v20-final.json: word_delivery PASS; content_and_sources/submission_readiness INCOMPLETE only for external rubric/instructor-review records. No FAIL. project.json is canonical; do not edit DOCX further without invalidating current QA. Next action: deliver final DOCX and concise coverage report.

## External limits
Missing course-specific scoring rubric RUBRIC-002 and pending official-criteria/instructor review keep submission readiness INCOMPLETE. Guide criteria included; no fabricated weights/signatures. Current-law validity, protected-route/deployment parity and fresh VietLex benchmarks NOT RUN. CRG unavailable; source/diff review used.

## User request 2026-10-27
Reassess all three reports to completion. Preserve VietLex v20 and previous explicit left-heading/center-caption choices unless a concrete defect is established; use StrongWine only as an adaptable presentation reference. Current v20 and hash above remain canonical pending fresh checks. No inferred supervisor approval or new benchmarks.
- Fresh readiness 2026-10-27: qa/readiness-recheck-20261027.json exit 2, word_delivery PASS, content/source and submission FAIL: multiple project source hashes changed since review; rubric human review and scoring rubric still incomplete. Re-review affected claims against current source and document snapshot; do not merely rebind hashes.
- New source-based correction 2026-10-27: POST /chat output persistence is conditional; app/database.py development mode is stateless. Adjust only the processing description; source review and crosswalk remain pending until final hash.
- Current candidate supersedes v20: output/VietLex_20261027_dang_kiem_tra.docx SHA-256 b8490a3766649c05ca5ac4d3de49d144376d8149bbb2862dc4871f380a68a7cf; one conditional-persistence correction and Word-native field update. All v20 DOCX QA is historical for this hash. Recheck source, visual pages, rubric parity and readiness.
- Static re-review of 8 stale source claims recorded in qa/current-source-review-20261027-partial.json with current SHA-256 and scope limitations. No automatic source-hash rebind; broader content-review dependencies and historical snapshot parity remain open.
- Candidate b8490a37 rendered 93 pages; contact sheets of all pages viewed, selected pages at larger size. Partial visual review records small diagram labels and sparse pages 31/81; not delivery PASS. See qa/visual-review-20261027-partial.json.
