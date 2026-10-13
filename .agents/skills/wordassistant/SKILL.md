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

## User-specific course-essay gate

Before composing or changing a course essay, turn the user's instructions into a checked acceptance matrix. Do not begin DOCX mutations while any required row lacks an owner, source, or planned evidence. A profile from another school is not a substitute for the user's rules.

For a report based on an older reference document:

- Keep the reference read-only. Record which facts and assets may be reused; do not inherit its chapter order, page layout, or stale product screenshots when the user has excluded them.
- Build a database inventory from the current project/database. Cover every table and record its purpose, columns, SQL types, primary/foreign keys, nullability, defaults, unique constraints, indexes, relationships, and representative sample rows. Mark missing evidence instead of guessing. Redact passwords, tokens, and unnecessary personal data.
- Build a screenshot matrix from the complete feature/route inventory, with a row for each distinct function and each applicable persona (for example customer, administrator, and shipper). Capture fresh desktop screenshots at a viewport at least 1366 px wide. Show the complete browser tab content at web size; do not use mobile emulation, cropped cards, or stale reference images. Embed every required screenshot in the DOCX at readable size and record its route, persona, state, and resolution. A link to an image file does not count as an embedded figure.
- Prefer records explicitly designated as demo data or synthetic fixtures for screenshots. Show those values in context without forced masking when the values explain the workflow. For a shipper delivery, the screenshot should make the recipient, full delivery destination, order items and quantities, shipment status, and useful call/map actions readable. If the available live record is not confirmed as demo data, switch to a synthetic fixture; do not silently present real customer details as examples. If authentication prevents a live route capture, render the same project template with a verified fixture and record that capture source/state in the matrix.
- Use a two-cover plan when requested. Keep the cover frame visibly inset from the page edge (target at least 12 mm), and check the rendered cover. Use real Word heading styles with tidy, consistent level indentation and true multilevel numbering when required. Apply the requested body size; set headings and captions to black when required.
- Give every major section its required page boundary and verify the rendered start page. Keep each declaration or front-matter item to its requested page. Respect a stated minimum page count without imposing an arbitrary maximum or adding filler.
- Keep figure captions to the requested title form only. When the requested form is `Hình x.x: Tên hình`, do not append a source note, route, persona, or explanatory sentence to that caption.
- For that colon form, pass `caption_separator: ":"` to WordAssistant and verify the visible chapter.sequence number against the nearest real `Heading 1` before insertion. Preserve the selected institution profile's label casing unless the user gives a different label.

The acceptance matrix must map every required database table to its specification and sample data, and every requested function/persona to an embedded desktop screenshot. Before delivery, check those rows against the DOCX itself, then validate and render the saved output and visually review every page. If a row is missing, delivery is incomplete even when generic profile validation passes.

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
