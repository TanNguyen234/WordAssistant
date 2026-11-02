# Content review plan

Use this alongside the assignment, acceptance crosswalk and outline. It records actual editorial/model review; it does not generate requirements or evaluate prose automatically. New course-report workspaces point `project.json.content_review_plan_file` at this JSON.

## Root

`schema_version` is `1`. `document_sha256` binds all records to the saved final DOCX. `domain` is the subject, such as `software` or `literature`. For subjects other than software, `model_scope_reason` explains which representations the assignment needs; no UML checklist is imposed.

`model_decisions` and `section_reviews` are arrays. A software plan must consider these dimensions once each: `use_case`, `data`, `class`, `activity`, `sequence`, `state`, `component`, `deployment`. Each may be REQUIRED or NOT_APPLICABLE with a reviewed reason. A small functional application can reasonably omit a class or deployment view when the controlling task and source justify that decision. A user-requested data model cannot be omitted merely because a service class diagram exists.

## Model decision

Each item has `dimension`, `disposition`, `reason`, `authority`, `status`, `reviewer`, `review_date` and, when REQUIRED, `assets`. Use `status: REVIEWED` only after checking implementation/assignment, image meaning and notation. Dates use `YYYY-MM-DD`; reviewer identity describes the actual reviewer, including an agent when appropriate. This is separate from instructor approval.

Each asset contains:

| Field | Meaning |
|---|---|
| `editable_file`, `editable_sha256` | Editable diagram source and current hash |
| `rendered_file`, `rendered_sha256` | Reviewed image and current hash; the same bytes must be embedded in the DOCX |
| `caption_title` | Exact caption title after its dynamic label/number |
| `sources` | Objects with `file` and `sha256` for inspected implementation/requirement sources |
| `semantic_review` | Relationships/branches checked and what the image claims |
| `notation_review` | Meaning of arrows, multiplicities, composition, conditions and simplifications |

Paths may be absolute or relative to the report workspace. Keep implementation files read-only. An image hash proves identity, not semantic correctness; notes must describe the actual comparison.

## Section review

Each main reasoning unit has a unique actual `heading`, `status: REVIEWED`, `reviewer`, `review_date` and four review notes:

- `argument`: question answered, reasoning and consequences of the choice.
- `evidence`: source/claim or observation used, including limits.
- `terminology`: reader suitability, definitions and code identifiers.
- `sufficiency`: how the section answers the requirement; no universal length quota.

Review the section itself. Repeating “PASS” in four fields is not meaningful review. The checker validates records, headings, hashes, files, embedding and captions; it cannot infer whether notes are true. Update the review whenever content changes.

## Gate

`python scripts/check_course_essay_readiness.py WORKSPACE` includes `project_content_review` when configured. New templates include the pointer. Legacy workspaces without it retain their earlier behavior and must be upgraded before claiming this review coverage. Content-plan PASS does not approve a rubric or certify legal/academic claims.
