# VietLex official rubric source review

**Reviewed:** 2026-10-24 (Asia/Bangkok)  
**Purpose:** Determine whether the exact official rubric can be copied into the VietLex Word report without inventing, translating, repairing, or omitting criteria.  
**Current DOCX:** `output/VietLex_DoAnChuyenNganh_Clickthrough_FinalQA_20261023.docx`  
**Current DOCX SHA-256:** `38E897511263ECCBF6F9B0BF9173EA55E6CBE91FBA4E01B9F33345A3CFEEBE7E`

## Decision

The exact official assignment rubric was **not located in the sources checked**. This does not prove that no rubric exists elsewhere. No rubric text was created or added, and the canonical DOCX was left unchanged for this requirement. Keep the rubric and submission-readiness gates `INCOMPLETE` until the official file or an authoritative link is supplied and reviewed.

## Sources checked

1. **User-supplied presentation guide:** `C:\Users\VI TINH THANH AN\Documents\Huong dan trinh bay Báo cáo ĐACN_2026-2027.docx`  
   SHA-256: `0F3622DBCD74009FB0867E0D3FA4A1624A38983AF502E55D48868EDF33F74E78`.  
   WordAssistant inspection recorded 554 paragraphs, 2 tables, 14 images and 43 outline entries. The bounded content review found report-structure, formatting and instructor-comment instructions, but did not find a complete scoring rubric with criteria/levels/weights. This guide remains the formatting authority; it is not treated as a substitute scoring rubric.

2. **HCMUNRE public course list for cohorts 9 and 10:** [Công khai các môn học ngành CNTT, chuyên ngành Công nghệ phần mềm](https://hcmunre.edu.vn/cong-khai-cac-mon-hoc-nganh-cong-nghe-thong-tin-chuyen-nganh-cong-nghe-phan-mem-khoa-9-khoa-10), retrieved 2026-10-24. Entry 54 for “Đồ án Công nghệ phần mềm” gives a 30% progress / 70% final-report split, including 10% progress and 20% outline within the progress grade. This is an older-cohort course-weight summary, not a detailed rubric and not verified as the user's current assignment rubric.

3. **HCMUNRE 2022 program page:** [Ngành CNTT, chuyên ngành Công nghệ phần mềm (bản rà soát, cập nhật năm 2022)](https://daotao.hcmunre.edu.vn/node/211), retrieved 2026-10-24. It lists the course in the curriculum but the page material reviewed does not provide its grading criteria or performance levels.

4. **HCMUNRE 2021–2022 course announcement:** [Thông báo tổ chức chấm báo cáo Đồ án Công nghệ phần mềm](https://www.hcmunre.edu.vn/cong-tac-sinh-vien-thong-bao-thong-bao-to-chuc-cham-bao-cao-do-an-cong-nghe-phan-mem-hoc-ky-1-nam-hoc-2021-2022-thong-bao-to-chuc-cham-bao-cao-do-an-cong-nghe-phan-mem-hoc-ky-1-nam-hoc-2021-2022), retrieved 2026-10-24. It gives the 2021–2022 presentation schedule and logistics; it does not provide a scoring rubric.

The public web pages were reviewed at their official URLs and were not downloaded as source files; therefore no local content hashes are recorded for them. The guide is user-provided and its local file hash is recorded above.

## Search record and assumptions

Official-domain searches performed on 2026-10-24 included:

- `site:hcmunre.edu.vn "Rubric" "Đồ án" "Công nghệ thông tin"`
- `site:hcmunre.edu.vn "Đồ án chuyên ngành" rubric HCMUNRE`
- `site:hcmunre.edu.vn "Đồ án Công nghệ phần mềm" 30% 70%`
- `site:hcmunre.edu.vn filetype:pdf "Đồ án chuyên ngành" "tiêu chí chấm"`
- `site:hcmunre.edu.vn "phiếu chấm" "Đồ án" "Công nghệ phần mềm"`
- `site:daotao.hcmunre.edu.vn "Đồ án Công nghệ phần mềm" "đánh giá" rubric`

Assumption kept explicit: the older course-level percentage split may describe a related course but is not accepted as the user's official assignment rubric. StrongWine, the outline sample, and the format guide are not scoring authorities for VietLex.

## Outcome

- Rubric requested in Word: **YES**.
- Exact official source located: **NO / NOT_RUN**.
- Rubric appendix added: **NO** (no source to preserve or verify).
- Canonical DOCX changed for this requirement: **NO**; its SHA-256 remains `38E897511263ECCBF6F9B0BF9173EA55E6CBE91FBA4E01B9F33345A3CFEEBE7E`.
- Next action: provide the official rubric file or its authoritative course/instructor link. Then compare the complete rubric, append it unchanged, update the TOC if required, render and review the resulting DOCX, and bind both hashes to the review record.

