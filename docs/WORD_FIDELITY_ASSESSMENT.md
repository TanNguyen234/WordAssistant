# Word fidelity assessment

## Decision

WordAssistant should keep its compact, deterministic agent-facing control plane and adopt the Codex documents plugin's artifact-quality discipline. A feature is not considered complete merely because its OOXML exists or its rendered text looks plausible. Verification must distinguish structural creation, Microsoft Word round-trip behavior, dynamic-field freshness, and visual quality.

## Comparison

| Area | WordAssistant plan | Codex documents plugin | Optimized direction |
|---|---|---|---|
| Agent usability | Stable CLI/facade, bounded context, profiles, selectors, transactions, capability routing | Task-oriented document scripts and detailed authoring guidance | Keep WordAssistant as the public control plane; expose plugin-grade checks through `verify` |
| Semantic Word behavior | Strong OOXML and backend architecture, but many tests currently prove structure only | Requires real styles, numbering, fields, exact table geometry, native field refresh, and render review | Add semantic contracts and native round-trip gates per feature |
| Visual quality | Render routing and heuristic verification planned | Render every page to images and inspect at 100% before delivery | Produce page images plus a machine-readable visual report; never infer visual correctness from XML alone |
| Dynamic fields | Real field-code construction and optional native update | Treat TOC, REF, PAGEREF, PAGE, SEQ, LOF, and LOT as stale until updated by Word | Record field freshness and update engine; separate `field_structure_status` from `field_result_status` |
| Tables | CRUD/layout operations | Exact `tblW`/`tblGrid`/`tcW`/indent/layout/margin consistency | Add a geometry normalizer and fail verification on contradictory widths |
| Styles/fonts | Style CRUD and profile formatting | Explicit design tokens and complete font mappings | Add style contracts, inheritance checks, and `ascii`/`hAnsi`/`eastAsia`/`cs` font mapping |
| Platform reach | API-key-free core with optional Word/LibreOffice backends | Strong artifact workflow but not a persistent cross-platform product API | Preserve fallback behavior while labeling native-dependent fidelity honestly |

## Historical probe evidence

The bullets in this section describe the defect-finding probe run before the
remediations below. They are retained as historical evidence, not as the
current capability statement.

A focused DOCX was created through the current operation layer, opened by desktop Microsoft Word, repaginated, updated, saved, exported to PDF, and inspected.

- `Heading 1` and `Heading 2` persisted as built-in semantic Word styles with outline levels. Word included them in a real TOC.
- The visible `1` and `1.1` heading prefixes were literal paragraph text. Word reported `ListType=0` and an empty `ListString`; inserting or moving headings would not renumber them.
- `SEQ`, `REF`, `PAGEREF`, and `TOC` field instructions were real. Before Word opened the file, cached results were placeholders; after native update, Word materialized the caption number, reference text, page references, and TOC entries.
- Roman front-matter numbering and Arabic section restart were real section/page-field semantics. Word rendered the first section as `i` and the second section footer as `Page 1 of 2`. This proves the mechanism, not every pagination configuration.
- The table rendered, but the geometry audit found `tblW=auto`, no explicit table indent, a grid sum of 8640 twips, and row cell-width sums of 8505 twips. Word can normalize this differently across edits or renderers.
- Style font records contained `ascii` and `hAnsi` mappings but no explicit `eastAsia` mapping, so Vietnamese/mixed-script portability is not yet fully controlled.

## Meaning of current support

### Styles and headings

The style survives save/reopen and is recognized by Word when an actual Heading style is applied. That is materially different from bolding a normal paragraph. It is not a promise of pixel-identical appearance under every template or Word installation unless all relevant style properties, inheritance, theme behavior, and fonts are fixed and rendered.

### Heading numbering

Heading numbering is now a genuine multilevel Word numbering definition linked
to `Heading 1` through `Heading 9`. Native Word round-trip tests prove Word
reports list semantics and recomputes the visible list strings. Literal `1.1`
text remains rejected by verification when no numbering properties exist.

### Pagination

Section numbering elements and PAGE fields are functional Word objects. Reliable pagination additionally requires Word repagination, story-range field updates, section/link audits, and PDF/page-image review. Layout-dependent page counts cannot be certified from OOXML alone.

### TOC, LOF, LOT, and references

Field codes are functional, but their displayed results may be stale until an appropriate engine updates and saves them. Verification must report whether fields are merely structurally valid, freshly updated by Word, or frozen/static. A placeholder cache must never be described as an up-to-date TOC.

Native verification now reports two separate facts: `field_evaluation_status`
shows whether an isolated Microsoft Word session successfully evaluated the
fields, while `field_freshness_status` certifies persisted freshness only when
Word reports that the opened artifact needs no changes after evaluation. A
dynamic PAGE/NUMPAGES value evaluated correctly in memory does not, by itself,
turn stale OOXML cache text into a persisted-fresh PASS.

### Citations

The citation workflow is a deterministic, evidence-registry-linked static
workflow. Numeric citations are renumbered after deletion, but they are not
Microsoft Word Source Manager citations and must not be advertised as such.

## Required release gates

Each advertised mutation feature must have the applicable evidence below:

1. Structural: save, reopen, inspect OOXML/relationships, and assert semantic invariants.
2. Native round-trip: when behavior is Word-dependent, open with Word, repaginate/update as needed, save, reopen, and re-inspect.
3. Dynamic result: compare field codes and cached results after update; record update engine and freshness.
4. Visual: export/render, inspect every page image, and report overflow, clipping, blank-page, font, spacing, table, and pagination findings.
5. Capability truth: publish the available backend and evidence dimensions separately; unavailable native/visual evidence remains a limitation, not a pass.

## Implementation priorities

1. Keep operation-level evidence and capability status synchronized with tests.
2. Require native verification for freshness claims about dynamic fields.
3. Render every page and complete visual review before delivery claims.
4. Use those gates in the Antigravity black-box test before final capability
   claims, commits, and push.

## Remediation evidence from this review

The first three fidelity defects were corrected before broader implementation resumed:

- Heading numbering now links the generated multilevel definition to Heading 1-9 and the corresponding style numbering properties. Microsoft Word native round-trip reported `ListType=4` with `ListString` values `1`, `1.1`, and `1.1.1`; paragraph text remained free of literal prefixes.
- Fixed tables now synchronize DXA table width, zero table indent, fixed layout,
  grid columns, cell widths, and explicit cell margins. Width is checked against
  the section containing each table. The geometry audit passes before and after
  a Microsoft Word save/reopen.
- Fixed fonts now populate `ascii`, `hAnsi`, `eastAsia`, and `cs` slots and remove conflicting theme mappings.
- Native field refresh now repaginates twice, updates main/story/header/footer fields, TOCs and tables of figures, records bounded cached results, and labels freshness `UPDATED_NATIVE`.
- Native PDF export no longer calls `SaveAs2` on the PDF destination. A live isolated-worker check produced a non-empty file with `%PDF-` signature.
