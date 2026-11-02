# Heading number separator correction

## Goal

Render automatic multilevel heading numbers with a consistent visible space between the number and heading title. Keep real Word numbering, the existing `1.1` / `1.1.1` hierarchy, the chapter heading text, and TOC behavior.

## Authority and constraints

- User requirement: add missing Chapter 1 multilevel headings and correct the VietLex report under the HCMUNRE report profile.
- The final render showed labels such as `1.1Cơ` and `2.3Yêu` touching the heading text; longer labels sometimes received a wider tab gap.
- Preserve the existing chapter text (`CHƯƠNG N:`), suppress its automatic level-one label, and number only chapter content before the conclusion.
- Do not replace Word numbering with literal text.

## Acceptance checks

- A focused regression test requires `w:suff` to use a space for generated heading levels.
- Reapply numbering to the report's Chapter 1–3 scope and confirm the numbering inspector sees all expected headings.
- HCMUNRE `report` validation has no issues.
- Word-native render shows a visible, consistent separator and no new pagination or clipping defect.
- Recheck field freshness, visual review, and delivery on the final DOCX hash.
