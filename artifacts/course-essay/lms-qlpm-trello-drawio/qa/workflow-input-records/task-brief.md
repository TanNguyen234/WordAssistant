# Active brief — LMS course essay

## Goal and authority
- Continue the WordAssistant DOCX for the Software Project Management course: LMS project, Trello tracking and Draw.io diagrams.
- Direct user constraint: **no n8n**. Attached capture guide is followed where applicable; it does not supply identity or an official course rubric.
- HCMUNRE `course_essay_style` is borrowed for layout/typography only. Keep `document_type=Tiểu luận môn học`; do not apply ĐACN content rules or claim HCMUNRE affiliation.
- Treat `D:\Download\LMS` as the read-only project-facts source.

## Current artifact and QA
- Canonical input/output: `output/final.docx`, SHA-256 `81bd50274bb0e7ee19ee3b57a20967755b3a73189530324cefad23ea52963ff5`.
- Existing Word delivery QA for that hash: `qa/final-delivery.json` PASS; 33-page Word render and visual review PASS. Previous generic document is preserved at `qa/final-generic-backup.docx`.
- User updated WordAssistant profile/workflow. New controller: `docs/course-report-workflow.md` plus `docs/report-content-plan.md`; use the existing-workspace revision path and keep output separate until verified.
- Current workspace has no `content-review-plan.json` or `project.json.content_review_plan_file` pointer. The previous readiness JSON predates the updated content-review gate.

## Constraints and next steps
- Preserve current final until a revised candidate passes. Do not invent screenshots, results, rubric criteria, names or credentials. Keep project files read-only.
- Inspect the selected profile's source assets and user guide for any applicable rubric/criteria; record applicability without importing ĐACN-only criteria.
- Review report sections and software-model dimensions against the updated workflow; write a hash-bound `content-review-plan.json` and update the project pointer/crosswalk.
- Run the updated readiness checker; revise only confirmed content gaps in a separate candidate, then refresh fields/render/visually review and bind all QA to one final hash.

## Current state
- No DOCX or LMS application source has been changed during this continuation. CRG MCP tools are unavailable in this environment; source inspection is the fallback.
