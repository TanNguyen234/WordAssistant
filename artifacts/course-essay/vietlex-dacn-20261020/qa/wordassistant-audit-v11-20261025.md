# WordAssistant review — VietLex HCMUNRE report v11

- Document: `../output/VietLex_DoAnChuyenNganh_RubricCriteria_FinalQA_20261025_v11-HCMUNRE-final.docx`
- DOCX SHA-256: `5bc0d4163e514a506056332b236e4605a60addd316990e04cec0e25a6c2322cb`
- Profile and variant: `hcmunre_dacn_2026_2027` / `report`
- Review date: 2026-10-25 (Asia/Bangkok)
- This records Codex inspection. It is not instructor approval, legal review, plagiarism assessment, or AI authorship detection.

## User-requested corrections

- Word outline has 107 semantic Heading 1–3 paragraphs. Chapter 1 has the Word-numbered 1.1 / 1.1.1 hierarchy. HCMUNRE report validation and the final Word delivery check pass. Twenty-three unnumbered headings belong to front matter and other unnumbered sections; chapter headings and numbered subsections have direct Word numbering assignments.
- The guide's “Mở đầu” section is present as `MỞ ĐẦU` with three substantive subheadings and a TOC entry; this follows the guide's label.
- The acknowledgement is a separate, full page with 380 words across five paragraphs. It thanks only ThS. Định Thị Hồng Loan. No unprovided recipient or specific contribution was added.
- The report prose has 1 cm first-line indentation in all 211 in-scope paragraphs (567 twips). The scope includes acknowledgement, schedule introduction, abstract, Chương 1–3 body, and academic-integrity disclosure. Cover/form fields, headings, keywords, the standalone `NỘI DUNG` divider, and references are intentionally excluded.
- `NỘI DUNG` remains an in-page divider and is not a heading or TOC entry.
- The F1–F7 functional prose was reduced to a short lead-in. The full CAP-01–CAP-12 requirements matrix remains. Remaining `F1` occurrences refer to the F1 score metric, not the removed functional list.
- The acknowledgement, declaration, supervisor-review and reviewer-review pages are distinct. The declaration and reviewer/signature fields remain editable because no truthful declaration, review text, dates, or signatures were supplied.
- The proposed six-phase schedule explicitly says dates/progress are unprovided and the plan awaits approval.

## Content kept, shortened, or left unresolved

- The former F1–F7 prose overlapped with the more detailed CAP-01–CAP-12 evidence and acceptance limits. That overlap was removed as requested; the CAP rows remain traceable to source and verification status.
- Repeated mentions of the official HCMUNRE criteria/no scoring scale remain in separate sections where they explain CAP derivation, evaluation planning, and submission limits. They distinguish official review criteria from a separate grading rubric and are not interchangeable statements. Repeated identities, report titles, named legal material, dates, and screenshot provenance are required in their respective covers, forms, captions, and evidence summaries. These heuristic repetitions were reviewed and dispositioned rather than deleted mechanically.
- The guide supplies review criteria but no scoring levels or weights. No course-specific assignment rubric was supplied. `RUBRIC-002` remains `NOT_RUN`; official-criteria human review remains `PENDING_HUMAN_REVIEW`.
- Current-law validity, protected/token/role routes, a newly deployed revision, and a new performance benchmark were not verified in this turn. The report labels those limits and does not present them as completed.

## Why the earlier omissions occurred

The available evidence points to an acceptance-model gap: the earlier inventory mirrored headings already present, and the delivery check established Word structure/rendering without checking Chapter 1 numbering semantics or acknowledgement completeness. The earlier completion statement was premature. Compact context may have contributed to loss of detail, but the evidence does not establish compaction as the sole cause.

## Bound verification evidence

- `validate-v11-hcmunre.json`: profile validation `valid: true`, no issues.
- `heading-numbering-v11.json`: 107 headings inspected; 84 numbered; Chương 1 numbering assignments are present.
- `indent-audit-v11.json`: all 211 in-scope paragraphs at 567 twips.
- `verify-v11-hcmunre-render.json`: Word-native fields and render passed; 79 pages.
- `visual-review-v11.json`: 79 pages covered by exact image hashes; eight changed pages reopened after v10 comparison, with 71 byte-identical images carried forward from the full v10 visual review.
- `verify-v11-hcmunre-delivery-pass.json`: delivery `PASS`, including structural, format, numbering, table geometry, native Word fields, render and visual gates.
- `integrity-audit-v11.json`: overall `WARN`, no `FAIL`; citation consistency, reviewed source evidence, and unresolved-placeholder gates pass. Warnings remain editorial/evidence-review prompts and are individually dispositioned in `integrity-warning-dispositions-v15.csv`.
