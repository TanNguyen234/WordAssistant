---
name: wordassistant
description: Create, inspect, retrieve bounded context from, validate, and render Word DOCX files with profile-aware rules. Use for any DOCX workflow in this repository.
---

# WordAssistant skill

Use the CLI as the stable control plane. Never inspect repository source or raw OOXML to discover normal operations.

1. Run `wordassistant doctor --json` once per environment.
2. Inspect unfamiliar short DOCX files with `wordassistant inspect FILE --json`. For documents over 40 pages or of unknown length, use `wordassistant inspect FILE --summary --json`; full inspection includes every paragraph's text and should not be sent to an agent as context.
3. For a long document, retrieve one relevant section at a time. Start with `wordassistant context FILE --query "..." --max-tokens 4000 --json` if you need to discover the section ID, then use `--only-section SECTION_ID` for strict single-section retrieval. Keep total retrieved context at or below 8,000 tokens in one task turn and repeat only for another necessary section. A 200-page DOCX may be indexed locally; its full text must not be pasted into the LLM prompt. The older `--active-section-id` / `--section` option prioritizes a section but may include neighbors.
4. Edit only the selected section or exact text target using a stable selector/anchor and save an output copy. For section-wide text edits, use a heading selector; `edit replace` without a selector may change matching text throughout the document.
5. Check `wordassistant capabilities --json` before native or renderer-dependent work.
6. Mutate an output copy. Use `--dry-run` before destructive changes.
7. For a new long report, write one bounded UTF-8 content JSON and run `compose` once after `create`; do not generate helper scripts. Then use one `apply` version-1 plan for compatible formatting/layout mutations so validation and rollback cover the whole operation and no intermediate DOCX is published.
8. Persist native field updates to a distinct final DOCX before the final academic audit. Then run `integrity audit` with the exact profile variant and evidence registry and create `integrity provenance` bound to that final DOCX hash. Any later DOCX mutation invalidates both audit and provenance.
9. Run `wordassistant verify OUTPUT --json` after edits.
10. When formatting matters, render and inspect every page. A successful render does not prove fields or numbering are functional.
11. A final delivery PASS requires both `validate.valid == true` and `verify.delivery_status == "PASS"`; `overall_status` only summarizes the checks requested in that invocation.

## Course-essay gate (project-driven)

Before editing a course essay, turn the user's rubric and supplied references into a small requirement/evidence matrix. Select an institution profile only when the user or assignment names it. If the rubric or a required reference is missing, mark that check unresolved instead of borrowing rules from another school or inventing requirements.

Classify every figure before placing it in Word:

- **Runtime screenshot:** captured from the running application; record the route, role, UI state, capture date, and source.
- **Saved project capture:** an existing image from the project; label it as a saved capture and do not claim it was freshly verified at runtime.
- **Source-backed wireframe:** a proposed or simplified screen drawn from the real route/template and its visible controls. Follow the user's sample style. For a plain form/table sample, use simple black lines on white, accurate labels and empty fields/rows; do not add browser chrome, invented records, prices, metrics, or features.
- **Diagram:** derive routes, modules, classes, and process steps from current source code and identify its evidence source.

For a screen hierarchy, inventory controller routes that return HTML views and verify each route's template. Treat POST actions, JSON/API endpoints, and redirect-only handlers as actions or endpoints, not separate screens. A single view returned by several aliases remains one screen. Preserve exact paths in a machine-readable inventory when drawing them would make the reference-style diagram hard to read.

Build only the content the assignment requires. Do not require a complete database schema, synthetic sample rows, a screenshot for every feature/persona, or a fixed desktop viewport unless the rubric asks for it. Never expose real customer data in examples. Keep captions concise and distinguish screenshots from wireframes.

For Word, preserve real styles, caption/TOC fields, section properties, and page numbering. Update fields in Microsoft Word, save, render the saved copy, and visually review every page when layout matters. Check both covers when present, running headers/footers, text color, accidental numbering, image aspect ratio, clipping, and page breaks. Keep the source file unchanged and report any rubric, runtime, or visual check that could not be completed.

## Course-essay quality checks

1. Follow the supplied rubric and selected institution profile; do not infer school-specific requirements from another report.
2. Keep each illustration beside the analysis it supports when the assignment gives that structure.
3. Match wireframes and diagrams to the user's supplied examples. Do not impose browser-chrome mockups or one-box-per-page requirements unless requested.
4. Verify important routes and fields against current controllers/templates. Separate implemented screens, inline states, actions, API endpoints, and proposed designs.
5. Preserve dynamic Word fields and inspect the rendered output for stale numbering, clipping, color/style regressions, unexpected spacing, and missing page elements.
6. Include a database/schema inventory or sample data only when the assignment requires it and the source supports it.

| Need | Command |
|---|---|
| Read structure | `inspect` |
| Find relevant text | `context` |
| Create report | `create` |
| Populate long report | `compose` |
| Atomic multi-edit | `apply` |
| Edit text | `edit` |
| Formatting | `format` |
| Lists/headings | `list` |
| Table work | `table` |
| Image work | `image` |
| Sections/layout | `section` |
| Pagination | `page-number` |
| Fields/TOC | `field`, `toc`, `caption` |
| Citations/references | `reference` |
| Academic integrity/provenance | `integrity` |
| Comments/revisions | `comment`, `revision` |
| Final QA | `verify`, then `render` |

Examples:

```powershell
wordassistant create report.docx --profile generic --title "Report" --json
wordassistant compose report.docx --output authored.docx --content content.json --evidence evidence.json --min-visible-characters 8000 --max-visible-characters 14000 --json
wordassistant apply authored.docx --output formatted.docx --plan operations.json --json
wordassistant inspect thesis.docx --summary --json
wordassistant context thesis.docx --query "chapter 3 results" --max-tokens 4000 --only-section chapter-3-results --json
wordassistant edit replace thesis.docx --output revised.docx --selector '{"type":"heading","text":"Results"}' --options '{"pattern":"old","replacement":"new"}' --dry-run --json
wordassistant format paragraph revised.docx --output formatted.docx --selector '{"type":"heading","text":"Results"}' --options '{"keep_with_next":true}' --json
wordassistant page-number apply report.docx --output numbered.docx --options '{"section_index":1,"number_format":"decimal","start":1}' --json
wordassistant table create report.docx --output table.docx --options '{"rows":3,"columns":4}' --json
wordassistant image insert report.docx --output illustrated.docx --options '{"image_path":"figure.png","alt_text":"Measured results"}' --json
wordassistant reference citation-insert report.docx --output cited.docx --selector '{"type":"text","text":"Claim supported by evidence"}' --options '{"evidence_id":"src-1","evidence_registry":"evidence.json"}' --json
wordassistant comment create report.docx --output reviewed.docx --options '{"start":0,"end":5,"text":"Clarify this claim"}' --json
wordassistant revision enable reviewed.docx --output tracking.docx --json
wordassistant integrity audit tracking.docx --evidence evidence.json --profile generic --variant default --json
wordassistant integrity provenance tracking.docx --evidence evidence.json --output tracking.provenance.json --json
wordassistant verify tracking.docx --render --json
```

For a native final gate, first run `verify FILE --native-fields --render --engine word --json`. Inspect every returned `render.page_images` path. Only after that real page review, rerun with `--visual-reviewed`; the flag is an attestation, not an automatic image check.

Real Heading styles are not the same as bold text. Automatic heading numbering is not literal `1.1` text. TOC/REF/PAGE fields may be stale until a native update reports `UPDATED_NATIVE`. Never invent citations or silently substitute an unavailable backend.

Do not optimize prose to evade an AI detector. The integrity command does not perform AI detection. It fails deterministic source/provenance defects and reports repetition or unusual punctuation only as human-review style signals. Preserve legitimate Vietnamese diacritics and disclose permitted AI assistance truthfully.

For new reports, `compose` authors content first and binds citations to their claim paragraphs; anchor section breaks to real content boundaries before applying section layout. Inspect every rendered page's content; dimensions and file existence are insufficient. Unexpected blank pages, stale fields, an unavailable gate, or any conflict between the summary and artifacts force FAIL. Negative tests must reject the exact tested invariant, not merely raise an unrelated argument or harness error. Mark synthetic evidence with `synthetic=true`; it remains visibly labeled in the document.


## Existing course-essay project source check

When an essay is checked against a current application repository, preserve the input and make corrections in an output copy. Validate every figure/caption pair against the current route/template and inspect the image itself. A matching asset hash establishes snapshot provenance only; do not claim current runtime verification without a fresh route capture. For dynamic figure numbering, inspect SEQ field position and confirm the visible Word-rendered caption and list-of-figures entry. Rerender after any DOCX mutation. If no course rubric or runtime capture is supplied/performed, report that check as NOT_RUN.
For course-essay work, follow the ordered runbook in `docs/strongwine-course-essay-workflow.md`; it records the initializer, each script/CLI input and output, route inventory, wireframe/UML process, Word field update, and visual QA gates. Read `docs/strongwine-course-essay-lessons.md` before recurring StrongWine edits and update it only with verified mistakes, causes, and prevention steps. Do not use StrongWine-only scripts as generic project tools without adapting and verifying their source-specific configuration.
