# Global Word document completeness review

Date: 2026-10-25

## Problem

VietLex v6 passed Word delivery checks while its Chapter 1 had no numbered subsection hierarchy and its acknowledgement still contained drafting placeholders. The validator checked profile-listed numbering and a small fixed set of placeholder strings; the report's acceptance matrix was also derived from the existing heading inventory. Those checks did not catch the user's stated content requirements.

## Approved scope

- Run a read-only completeness review for every selected profile, including `generic/default`.
- Detect high-confidence unresolved square-bracket draft placeholders in body paragraphs and table cells, including Vietnamese drafting instructions and common English tokens. Keep numbered bracket citations such as `[1]` valid.
- For a heading styled `Heading 1` whose text explicitly names a numbered chapter (`Chapter 1`, `Chương 1`, etc.), inspect descendant `Heading 2` and `Heading 3` paragraphs until the next `Heading 1`. Report children with neither automatic Word numbering nor a visible matching numeric prefix.
- Do not mutate documents or auto-apply numbering. The generic profile uses a review-level numbering warning; a selected profile can require chapter numbering and make it an error in final verification. Unresolved placeholders retain warning/draft and error/final-verify behavior by default; profiles may explicitly select review-only behavior.
- Set the generic profile defaults explicitly, and set the selected HCMUNRE `report` variant to require numbered chapter hierarchy plus strict unresolved-placeholder verification. The HCMUNRE `proposal` variant does not inherit that report-only requirement.
- Do not add universal grading criteria, score scales, rubric weights, acknowledgement word counts, or institution-specific requirements to the generic profile.

## Acceptance checks

1. A chapter with unnumbered Heading 2/3 descendants produces a numbering review finding; a chapter with automatic numbering or matching visible numbering does not.
2. An unnumbered document that has no explicitly numbered chapter heading does not receive a numbering finding.
3. Vietnamese/English draft instructions in square brackets are detected in paragraphs and tables; ordinary citation numbers are not.
4. The generic profile reports global findings; the HCMUNRE `report` variant fails final verification for unnumbered child headings under numbered chapters and unresolved placeholders; the HCMUNRE `proposal` variant remains independently configured.
5. VietLex v7 uses real Heading 1/2/3 styles, visible multi-level numbering in Chapters 1–3 and TOC levels 1–3; acknowledgement is one rendered page and contains only user-supported thanks; `NỘI DUNG` is absent from TOC; F1–F7 is condensed while CAP-01–12 remains.
6. v5 and v6 remain unchanged. Final DOCX QA and project readiness artifacts bind the v7 SHA-256.

## Failure states and limits

- A warning is a review prompt, not a claim that every generic document must use numbered headings.
- Placeholder matching is heuristic and intentionally high-confidence; report template-specific unknown tokens for review rather than inventing values.
- A Word delivery PASS does not imply academic or submission readiness. Official rubric human review, course scoring-rubric availability, current-law review, deployed-revision equivalence, and protected-route checks retain their existing states.
- The student's reply spells the supervisor name `ThS. Định Thị Hồng Loan`, while v6 cover metadata says `ThS. Đinh Thị Hồng Loan`. Use the latest user-provided spelling consistently in v7 and record the discrepancy; no other acknowledgement recipients or specific acts were supplied.

## Evidence and source of authority

- User's original VietLex task and 2026-10-25 follow-up, including the explicit choice to apply the numbering/placeholder review at global-default scope.
- Selected HCMUNRE report profile and its byte-identical user-supplied guide, SHA-256 `0f3622dbcd74009fb0867e0d3fa4a1624a38983af502e55d48868edf33f74e78`.
- The HCMUNRE guide has review criteria but no score scale or weights.
