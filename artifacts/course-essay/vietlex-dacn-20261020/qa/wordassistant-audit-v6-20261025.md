# WordAssistant audit of VietLex v6

Date: 2026-10-25 (Asia/Bangkok)

## Scope and file binding

- Audited DOCX: `output/VietLex_DoAnChuyenNganh_RubricCriteria_FinalQA_20261025_v6.docx`
- SHA-256: `b750f252d9b1955d896f905e1045d7d80654d5432273d447b8dc0bbedf892c39`
- Guide: `C:\Users\VI TINH THANH AN\Documents\Huong dan trinh bay Báo cáo ĐACN_2026-2027.docx`; the guide and bundled profile asset are recorded byte-identical at SHA-256 `0f3622dbcd74009fb0867e0d3fa4a1624a38983af502e55d48868edf33f74e78`.
- This is a read-only analysis. No DOCX, WordAssistant config, profile or rubric was changed in this review.

## WordAssistant findings

Commands used included `wordassistant inspect ... --summary --json`, bounded `wordassistant context ... --only-section ... --json`, `wordassistant list heading-numbering-inspect ... --json`, `wordassistant config show --json`, and `wordassistant profile show hcmunre_dacn_2026_2027 --json`.

- `heading.numbering_inspect` reports 105 heading paragraphs, `linked_levels=[]`, and no heading-numbering prefixes. Direct Word paragraph numbering is absent on the Chapter 1 title and its seven Heading 2 subsections. No Heading 3 appears within Chapter 1. The section headings therefore do not form the guide's illustrated `1.1` / `1.1.1` hierarchy.
- Current Chapter 1 headings are: “Retrieval và truy xuất trong tiếng Việt”; “RAG, evidence và giới hạn của câu trả lời sinh”; “Đánh giá theo tầng và nguyên tắc hướng đối tượng”; “Khung phân tích dùng trong bài”; “Sai lệch cấp văn bản trong retrieval pháp lý”; “Đánh giá groundedness trong hỏi đáp pháp lý”; “Tổng hợp nghiên cứu và khung phân tích riêng cho VietLex”. They use Heading 2, but have no numeric labels.
- The supplied guide says chapter/section numbering follows its rule and its TOC sample demonstrates `Chương 1`, `1.1`, and `1.1.1`. For Chapter 1 the guide calls for related prior work plus theoretical foundations (theory and technique). The current headings cover related concepts and studies, but the required multilevel numbering is absent.
- “MỞ ĐẦU” is present as the report's actual Heading 1, with three substantive subheadings: objectives/questions/scope; scope/method/evidence; contributions/report structure. The supplied guide uses “Mở đầu”; a separate “Lời mở đầu” page is not listed as a required front-matter item. The WordAssistant context index shows TOC entries as well as actual headings; this explains repeated index results and is not proof of duplicate body text.
- “LỜI CẢM ƠN” occupies a separate rendered page, but it contains drafting instructions and placeholders (`[sinh viên tự điền]`, `[mô tả đóng góp thực tế]`), not an author-written acknowledgement. The page is mostly empty. The declaration page likewise contains template instructions/placeholders. These are not finished report prose.
- `NỘI DUNG` is a standalone Heading 1 immediately before Chapter 1 and has no body text. It does not appear in the guide's sample TOC; it is a candidate to remove from the outline/TOC or demote to a non-heading label.
- “Yêu cầu chức năng rút ra từ source” presents F1–F7, while the later “Yêu cầu chức năng tái dựng từ source” presents CAP-01–CAP-12 for many of the same capabilities. The latter table carries more source and verification limits. This is a candidate to condense to a short lead-in plus the detailed table, after confirming the disposition.
- In the Word render contact sheet `qa/visual-review-v6-final-left-align/contact-sheets/pages-01-04.jpg`, PDF page 3 is the acknowledgement page and PDF page 4 is the declaration page; both are clearly sparse/template-like.

## Configuration and rubric scope

- `wordassistant status --json` identifies the workspace at `D:\Download\WordAssistant\.wordassistant`; `config show` reports the default `profile=generic`, `variant=default`, `context_budget=12000`. The workspace directory currently contains cache/checkpoint folders and no saved config file. This is not a machine-wide HCMUNRE configuration.
- v6 was validated with the HCMUNRE profile explicitly selected as `hcmunre_dacn_2026_2027`, variant `report`. That profile is institution-specific and has separate report/proposal variants. Its report `section_blueprint` lists top-level sections only; it does not define a 1.1/1.1.1 numbering scheme or a check for substantive acknowledgement text. The HCMUNRE guide has review criteria/instructions but no score scale or weights.
- No global rubric/config change is recommended. Keep the default generic. If the user approves reusable HCMUNRE behavior, implement it only in the HCMUNRE `report` profile: linked Word numbering for chapter/section/subsection levels, TOC levels 1–3, and validation that catches missing numbering and unresolved front-matter placeholders. Do not add a numeric grading scale or universal acknowledgement word count.

## Why v6 missed the requested items

The previous completion claim relied on a heading parity matrix built from headings already present and a Word delivery gate. Those checks confirmed Word styles, page rendering, fields and that the existing outline matched its matrix; they did not compare numbering against the guide's `1.1` / `1.1.1` example or judge whether the acknowledgement page contained real prose. The profile blueprint also listed only top-level sections. The crosswalk was marked PASS despite those gaps, and the final claim that the document was fully reviewed was premature. Compact context may have contributed to lost emphasis during handoff, but it is not a sufficient explanation: the original request had already stated the relevant requirements. The demonstrated failure was an incomplete acceptance model and an incorrect PASS interpretation.

## Decisions needed before the next DOCX

1. Acknowledgement facts: identify the people/units the student actually wants to thank and their real contribution. Do not pad the page or invent support. The supervisor name appears on the cover, but no specific contribution details were supplied.
2. Removal/condensing: confirm whether to remove the `NỘI DUNG` Heading 1 and reduce F1–F7 to a brief summary while keeping the CAP table.
3. Reuse scope: proposed approach is to keep the global/default WordAssistant config generic and, only after approval, add numbering and placeholder checks to the HCMUNRE report profile rather than to the global config.
4. Numbering: proposed hierarchy groups existing Chapter 1 material into numbered `1.1`, `1.2`, `1.3` parents and `1.1.1`-level children without adding unsupported claims; confirm whether to apply this structure to v7.
