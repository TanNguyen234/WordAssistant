# Software course / capstone project starter

Use this folder for a software course report or capstone project. The StrongWine final report is the mandatory structural baseline in both cases: keep every baseline heading and its depth, and map it to an evidence-backed equivalent in the new project. Do not shorten the report because the assignment is called a course essay, project, or capstone. If an official assignment conflicts with a baseline section, record the conflict and stop for resolution; do not silently remove the section.

The baseline governs structure only. Never copy StrongWine's project claims, data, routes, screenshots, student details, course identity, supervisor, approvals, or signatures. Every cover value must come from the current user, assignment/rubric, or selected official profile. Otherwise leave an explicit blank placeholder.

Follow `docs/strongwine-course-essay-workflow.md` in order for the full runbook, exact commands, input/output contracts, UML evidence rules, and Word QA. Read `docs/course-essay-lessons.md` for verified failure causes and prevention steps. That document separates reusable project steps from StrongWine-only helpers. The base workflow does not call agy/Antigravity, n8n, or a model provider.

## Start

1. Copy the project folder using `scripts/init_course_essay_project.py`.
2. Record `document_type` separately from `course_name`; record the supervisor and its authority in `project.json`. Transcribe every cover identity field and its authority in `cover-metadata.csv`. A name read from StrongWine is never an authority.
3. Record the assignment file or a faithful `assignment_summary`, rubric, selected Word profile (if any), source project and revision in `project.json`; map every rubric requirement in `requirements-matrix.csv`.
4. Map all 204 StrongWine headings in `structure-parity.csv` and all 109 image/table slots (65 image instances and 44 tables) in `asset-parity.csv`, preserving every reference ID and reference field. Each heading row must keep the same target level and sequence order as StrongWine. Each row needs an evidence-backed target heading/section and caption, a `MATCHED` or `ADAPTED` decision, a coverage note, existing evidence file(s), reviewer, date, and `PASS` status. `OMIT`, `NOT_APPLICABLE`, `SKIP`, changed heading levels/order, missing rows, or blank rows do not pass.
5. Read only the relevant source files and document them in `screen-inventory.json` and `figure-plan.csv`.
6. Plan each UML diagram in `diagram-plan.csv`: record its question, source files/symbols, editable `.puml`, rendered image and verification status. A diagram renderer does not verify the facts in a diagram.
7. Separate current runtime screenshots from wireframes. A wireframe shows verified controls and blank data areas; a runtime screenshot shows the running application at a recorded route, role, state, viewport and date.
8. Build diagrams from source evidence. Include rendered GET views as screens; list POST actions and API endpoints as actions or interfaces, never as pages. Use `build` in `scripts/build_course_essay_assets.py` only for its Java Spring MVC route/template adapter. For another framework, manually verify route/handler/template first, then use its `render` subcommand; keep `source_verification=NOT_RUN_MANUAL_REVIEW_REQUIRED` until the person completes that source review.
9. Create or update the DOCX with the WordAssistant CLI. Select an institutional profile only when the assignment requires it.
10. Update Word fields, save a new output candidate, render that saved copy, and inspect every page. Compare all cover identity fields against `cover-metadata.csv`, then re-render after any document change.
11. Save the raw Word verify JSON and integrity audit JSON at the paths configured in `project.json`. If an institution profile is selected, run `wordassistant validate OUTPUT_DOCX --profile ID --variant VARIANT --json` and save its output to `qa/profile-validation.json`. Keep reports bound to the same `output_docx`.
12. Map each factual claim about the project, including labels such as `(S1)`–`(S8)`, in `claim-evidence.csv`; resolve its `evidence_id` through `evidence.json`. Record source path, source SHA-256, exact source location, review status, support confirmation, reviewer, and date.
13. Keep academic citations in `report-evidence.json`, separate from project evidence. Run `wordassistant integrity audit OUTPUT_DOCX --evidence report-evidence.json --profile PROFILE --variant VARIANT --json`; point `project.json.report_citation_registry_file` to that same file so readiness checks the correct registry hash.
14. Give every warning in the integrity audit a matching row in `integrity-warning-dispositions.csv` using its gate name and one-based finding index. A source-evidence failure cannot be waived into readiness; repair the mapping and rerun the audit.
15. Run `python scripts/check_course_essay_readiness.py PATH_TO_THIS_WORKSPACE` from the WordAssistant repository root. It reads the project, DOCX, QA reports, rubric matrix, identity manifest, all StrongWine parity rows, evidence maps, warning dispositions, and required acceptance checks without modifying them. Exit code `0` means every configured gate passed, `1` means incomplete, and `2` means a hard failure.
16. Report all three statuses separately. A WordAssistant PASS only covers Word delivery. If the rubric is absent, any StrongWine heading lacks an evidence-backed target section, cover identity is unresolved, project claims do not resolve to reviewed source records, or another required gate is incomplete, label the DOCX a draft and submission readiness `INCOMPLETE`.

All checks listed in `required_acceptance_checks` are mandatory. Set a check to `true` only after a person completes the review and records its evidence in the relevant plan or QA report. `cover_metadata_fields_verified` means every non-placeholder cover value matches its declared authority and the final rendered cover. `strongwine_structure_parity_reviewed` means every one of the 204 canonical heading rows is present at the same depth or has an evidence-backed equivalent. `strongwine_asset_parity_reviewed` means every one of the 65 image instances and 44 tables has an evidence-backed target equivalent, visually checked in the final render. If a check does not apply, record why and resolve it before marking complete; the parity gates do not accept omission or `NOT_APPLICABLE`.

Example handoff when a DOCX renders but assignment requirements or evidence are unresolved:

> Word delivery: PASS. Content and sources: INCOMPLETE — rubric not supplied; S1–S8 are not mapped to reviewed evidence records. Submission readiness: INCOMPLETE. This file is a draft, not confirmed ready to submit.

## Keep the evidence small and clear

- Keep the supplied source project read-only.
- Do not make up sample records, totals, dates, people, signatures, approvals or test results.
- Do not copy StrongWine's database tables or routes. Preserve every StrongWine structural heading, but adapt its coverage to the new system's verified domain model and route inventory; add equivalent evidence-backed analysis instead of dropping a heading.
- Keep a figure beside the section it explains. Give each figure a short caption and describe whether it is a wireframe, source image or runtime capture.
- Use the user's supplied diagram style. For simple academic wireframes, use black lines on white, real labels, empty controls and readable table headings. Do not add browser chrome or dashboard figures unless the source and assignment call for them.
- Remove only scratch material that is unreferenced and proven obsolete. Keep source files, evidence and the previous deliverable.

## Files

- `project.json`: project identity, authority and acceptance checks.
- `cover-metadata.csv`: source authority and verification state for every cover identity field; reference samples are forbidden authorities.
- `structure-parity.csv`: one seeded row for every heading in the canonical StrongWine structure baseline; all 204 rows must be completed.
- `asset-parity.csv`: one seeded row for every StrongWine image instance/table; all 109 rows must map to a verified equivalent without copying sample media or data.
- `requirements-matrix.csv`: rubric-to-section/evidence map, initially blank.
- `claim-evidence.csv`: claim-to-source map with checked source hashes and reviewer confirmation.
- `evidence.json`: reviewed project-source evidence records referenced by `claim-evidence.csv`; this is not the Word bibliography registry.
- `report-evidence.json`: WordAssistant bibliography registry for academic citations inserted into the DOCX. The starter is empty; add only source records that meet WordAssistant's reviewed-source schema.
- `integrity-warning-dispositions.csv`: one-based per-finding review record for integrity warnings.
- `output/`: final DOCX location after Word fields, render, and review are complete.
- `qa/`: saved, unmodified Word verify, integrity audit, and readiness JSON reports.
- `screen-inventory.json`: blank starter for source-backed view routes and templates.
- `figure-plan.csv`: figure evidence plan; it does not claim that a capture has been made.
- `diagram-plan.csv`: UML/ERD question and evidence plan; it does not claim that a diagram has been verified.
