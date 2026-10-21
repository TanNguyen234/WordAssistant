# Software course report / capstone starter

Use this starter for a course essay, software project report, or đồ án chuyên ngành. The required depth is the same regardless of the document label: follow the assignment, rubric, selected institutional profile, and verified project evidence. Use StrongWine as a full-report example and depth checklist. Its headings, figures, tables, and page count are specific to that report; they are never quotas for another project.

Follow `docs/strongwine-course-essay-workflow.md` in order. Read `docs/course-essay-lessons.md` for verified failure causes and prevention. The base workflow does not call agy/Antigravity, n8n, or model providers.

## Start each project

1. Create a new workspace with `python scripts/init_course_essay_project.py PATH --title 'Verified title'`. The destination must not already exist.
2. Record `document_type`, `course_name`, title, supervisor and each authority separately in `project.json` and `cover-metadata.csv`. A reference sample is never an authority for identity, approvals, signatures, project claims or results.
3. Record the assignment or a faithful summary, rubric, selected profile, read-only source root and revision. Map each rubric requirement in `requirements-matrix.csv`. Missing assignment or rubric stays `NOT_RUN` and blocks a submission-ready claim.
4. Before writing, draft the complete outline from the assignment, rubric, profile and verified project scope. Compare its depth with StrongWine's report groups: front matter/forms where applicable; abstract and lists; background/related work; current system and requirements; business/function models; OO analysis/design; architecture/data/components; implementation/UI; testing/evaluation/limitations; conclusion/future work; references and appendices. Include every applicable required area or record a reviewer-approved reason why a reference-only area does not apply. Do not shorten because the work is called a course essay.
5. Put one row per planned Word heading in `structure-parity.csv`. Its row count is project-specific. The final DOCX outline must match the matrix in heading text, level and order. The reviewer must confirm the outline covers the entire assignment/rubric/profile and uses StrongWine to check depth; the checker cannot discover a requirement that was never entered in the matrix.
6. Put one row per actual planned figure, diagram, wireframe, screenshot or table in `asset-parity.csv`. Its row count is project-specific. Record source, exact location, evidence, target section and final caption. The checker confirms evidence paths and that each caption appears in the final DOCX; it does not certify the visual itself. If no visuals are required, record `visual_inventory_review` in `project.json` with `decision: NONE_REQUIRED`, a reason, reviewer and date.
7. Read only source files needed for the report. Record routes/templates in `screen-inventory.json`, visuals in `figure-plan.csv`, and UML/ERD questions and source symbols in `diagram-plan.csv`. Keep project source read-only.
8. For UML, write editable `.puml` from verified source symbols, then render with `python -m wordassistant.cli plantuml render INPUT.puml --output OUTPUT.png --format png --json`. Keep source and rendered image. A successful render proves syntax/rendering only; the reviewer compares every node and relation with source.
9. For screen hierarchy, enumerate actual GET views in `screen-inventory.json`; represent POST/API actions as actions/interfaces, never as pages. Use `python scripts/build_course_essay_assets.py render --inventory PATH --wireframe-dir PATH --diagram-dir PATH --report PATH` after manually verifying routes/templates. Use its `build` mode only for its supported Java Spring MVC adapter. The render-only report explicitly does not verify source routes.
10. Draw wireframes with the controls and labels found in the actual templates, simple black lines on white, empty data, and no invented controls. Keep wireframes distinct from runtime captures. A runtime screenshot records real route, role, state, viewport and date; do not claim one when the app was not run.
11. Compose/edit a new DOCX copy with WordAssistant. Use real Word styles, fields, captions, TOC/list fields and page numbers. Cite checked academic sources via `report-evidence.json`; track project facts separately in `claim-evidence.csv` and `evidence.json`.
12. Update fields in Word, save, render the saved DOCX and inspect every page. After any DOCX change, rerender and review the final file again. Correct clipping, unexpected color, spacing, crop or missing caption before final QA.
13. Save the raw verify, profile-validation and integrity-audit JSON. Disposition every integrity warning in `integrity-warning-dispositions.csv`. Keep all reports bound to the same output path and hash.
14. Run `python scripts/check_course_essay_readiness.py PATH_TO_WORKSPACE`. It is read-only. Report Word delivery, content/sources, and submission readiness separately. A Word delivery `PASS` does not imply rubric compliance or submission readiness.

## Project files

- `project.json`: identity/authority, assignment/profile/source, output path, QA paths and manual acceptance records.
- `cover-metadata.csv`: authority and review status for visible identity fields.
- `requirements-matrix.csv`: variable set of rubric requirements mapped to report sections/evidence.
- `structure-parity.csv`: blank project-specific heading plan; no sample headings are preseeded.
- `asset-parity.csv`: blank project-specific visual plan; no sample images/tables are preseeded.
- `screen-inventory.json`, `figure-plan.csv`, `diagram-plan.csv`: route/template, capture and editable diagram provenance.
- `claim-evidence.csv` and `evidence.json`: reviewed claims about the project and their source evidence.
- `report-evidence.json`: reviewed academic source registry used by WordAssistant citations.
- `integrity-warning-dispositions.csv`: one human disposition per current audit warning.
- `output/` and `qa/`: final DOCX and its matching delivery/content evidence.

Set a manual acceptance check to `true` only after a person completes and records that review. Do not infer missing facts. Keep the report `INCOMPLETE` where a required source, rubric, or review is missing.
