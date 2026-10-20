# Course essay project starter

Use this folder for a new course essay based on a software project. Fill in the assignment-specific facts before drafting. The assignment and supplied rubric control the paper; a sample paper is only a visual reference unless the instructor says otherwise. Never copy a school profile, project facts, routes, data, or screenshots from another project.

Follow `docs/strongwine-course-essay-workflow.md` in order for the full runbook, exact commands, input/output contracts, UML evidence rules, and Word QA. That document separates reusable project steps from StrongWine-only helpers.

## Start

1. Copy the project folder using `scripts/init_course_essay_project.py`.
2. Record the assignment, rubric, selected Word profile (if any), source project and revision in `project.json`; map every rubric requirement in `requirements-matrix.csv`.
3. Read only the relevant source files and document them in `screen-inventory.json` and `figure-plan.csv`.
4. Plan each UML diagram in `diagram-plan.csv`: record its question, source files/symbols, editable `.puml`, rendered image and verification status. A diagram renderer does not verify the facts in a diagram.
5. Separate current runtime screenshots from wireframes. A wireframe shows verified controls and blank data areas; a runtime screenshot shows the running application at a recorded route, role, state, viewport and date.
6. Build diagrams from source evidence. Include rendered GET views as screens; list POST actions and API endpoints as actions or interfaces, never as pages.
7. Create or update the DOCX with the WordAssistant CLI. Select an institutional profile only when the assignment requires it.
8. Update Word fields, save a new final copy, render that saved copy, and inspect every page. Re-render after any document change.

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
- `screen-inventory.json`: blank starter for source-backed view routes and templates.
- `figure-plan.csv`: figure evidence plan; it does not claim that a capture has been made.
- `diagram-plan.csv`: UML/ERD question and evidence plan; it does not claim that a diagram has been verified.
