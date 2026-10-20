# Course essay project starter

Use this folder for a new course essay based on a software project. Fill in the assignment-specific facts before drafting. The assignment and supplied rubric control the paper; a sample paper is only a visual reference unless the instructor says otherwise. Never copy a school profile, project facts, routes, data, or screenshots from another project.

Follow `docs/strongwine-course-essay-workflow.md` in order for the full runbook, exact commands, input/output contracts, UML evidence rules, and Word QA. Read `docs/course-essay-lessons.md` for verified failure causes and prevention steps. That document separates reusable project steps from StrongWine-only helpers. The base workflow does not call agy/Antigravity, n8n, or a model provider.

## Start

1. Copy the project folder using `scripts/init_course_essay_project.py`.
2. Record the assignment file or a faithful `assignment_summary`, rubric, selected Word profile (if any), source project and revision in `project.json`; map every rubric requirement in `requirements-matrix.csv`.
3. Read only the relevant source files and document them in `screen-inventory.json` and `figure-plan.csv`.
4. Plan each UML diagram in `diagram-plan.csv`: record its question, source files/symbols, editable `.puml`, rendered image and verification status. A diagram renderer does not verify the facts in a diagram.
5. Separate current runtime screenshots from wireframes. A wireframe shows verified controls and blank data areas; a runtime screenshot shows the running application at a recorded route, role, state, viewport and date.
6. Build diagrams from source evidence. Include rendered GET views as screens; list POST actions and API endpoints as actions or interfaces, never as pages. Use `build` in `scripts/build_course_essay_assets.py` only for its Java Spring MVC route/template adapter. For another framework, manually verify route/handler/template first, then use its `render` subcommand; keep `source_verification=NOT_RUN_MANUAL_REVIEW_REQUIRED` until the person completes that source review.
7. Create or update the DOCX with the WordAssistant CLI. Select an institutional profile only when the assignment requires it.
8. Update Word fields, save a new output candidate, render that saved copy, and inspect every page. Re-render after any document change.
9. Save the raw Word verify JSON and integrity audit JSON at the paths configured in `project.json`. If an institution profile is selected, run `wordassistant validate OUTPUT_DOCX --profile ID --variant VARIANT --json` and save its output to `qa/profile-validation.json`. Keep reports bound to the same `output_docx`.
10. Map each factual claim about the project, including labels such as `(S1)`–`(S8)`, in `claim-evidence.csv`; resolve its `evidence_id` through `evidence.json`. Record source path, source SHA-256, exact source location, review status, support confirmation, reviewer, and date.
11. Keep academic citations in `report-evidence.json`, separate from project evidence. Run `wordassistant integrity audit OUTPUT_DOCX --evidence report-evidence.json --profile PROFILE --variant VARIANT --json`; point `project.json.report_citation_registry_file` to that same file so readiness checks the correct registry hash.
12. Give every warning in the integrity audit a matching row in `integrity-warning-dispositions.csv` using its gate name and one-based finding index. A source-evidence failure cannot be waived into readiness; repair the mapping and rerun the audit.
13. Run `python scripts/check_course_essay_readiness.py PATH_TO_THIS_WORKSPACE` from the WordAssistant repository root. It reads the project, DOCX, QA reports, matrix, both evidence maps, warning dispositions, and required acceptance checks without modifying them. Exit code `0` means every configured gate passed, `1` means incomplete, and `2` means a hard failure.
14. Report all three statuses separately. A WordAssistant PASS only covers Word delivery. If the rubric is absent, project claims do not resolve to reviewed source records, or another required gate is incomplete, label the DOCX a draft and submission readiness `INCOMPLETE`.

All eight checks listed in `required_acceptance_checks` are mandatory. Set one to `true` only after a person completes the review and records its evidence in the relevant plan or QA report. If a check does not apply, record why in the plan/report before marking it complete; the checker does not infer completion from missing files.

Example handoff when a DOCX renders but assignment requirements or evidence are unresolved:

> Word delivery: PASS. Content and sources: INCOMPLETE — rubric not supplied; S1–S8 are not mapped to reviewed evidence records. Submission readiness: INCOMPLETE. This file is a draft, not confirmed ready to submit.

## Keep the evidence small and clear

- Keep the supplied source project read-only.
- Do not make up sample records, totals, dates, people, signatures, approvals or test results.
- Do not include every database table or every possible route unless the assignment asks for them. Record required coverage in the acceptance list.
- Keep a figure beside the section it explains. Give each figure a short caption and describe whether it is a wireframe, source image or runtime capture.
- Use the user's supplied diagram style. For simple academic wireframes, use black lines on white, real labels, empty controls and readable table headings. Do not add browser chrome or dashboard figures unless the source and assignment call for them.
- Remove only scratch material that is unreferenced and proven obsolete. Keep source files, evidence and the previous deliverable.

## Files

- `project.json`: project identity, authority and acceptance checks.
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
