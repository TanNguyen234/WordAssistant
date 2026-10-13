# Long-document verification optimization

## Goal

Reduce repeated work when verifying and visually reviewing long Word documents while preserving the existing delivery checks and default CLI output.

## Authority and assumptions

- The user authorized planning, implementation, and independent review of the WordAssistant speed improvements discussed in this task.
- The current task covers verification/render efficiency and a read-only caption audit. Caption insertion/reconciliation and in-memory batch mutation remain out of scope because they need separate backend and evidence design.
- Existing workspace changes from earlier work are pre-existing task state and must be preserved.
- CRG tools are unavailable in this session; source inspection and focused tests provide the implementation evidence.

## Scope

1. Reuse a prior full render report for visual-review attestation without exporting the DOCX or rasterizing pages again.
2. Audit a PDF's page text with one Poppler process when available, preserving page-by-page blank-page detection and PDFium fallback.
3. Validate each successful PNG page set once while preserving fallback when Poppler emits invalid images.
4. Add a compact verify output that writes the complete report to a separate artifact and summarizes results on stdout.
5. Add a report-only caption audit for immediately adjacent captions on body images and top-level tables.

## Required behavior

- Keep existing `verify --render` and full JSON behavior compatible.
- A reusable report must bind the current DOCX SHA-256, exact PDF SHA-256, renderer identity/options, page count, and ordered PNG hashes/sizes. The reuse attestation must use a distinct versioned token; legacy render challenges retain their current semantics.
- Reuse must revalidate the report schema, all files, hashes, page ordering/count, PDF page count, current DOCX structure/profile/numbering/fields, and current native-field check if requested. It must rerun the PDF page-content audit. It must never copy prior PASS statuses into a new result.
- Reuse must make zero renderer and zero page-rasterizer calls. Any changed/missing DOCX, PDF, PNG, page order/count, or token fails closed.
- The full report file is written atomically. `--summary` requires `--report-output`; default stdout remains the existing full JSON.
- Summary stdout includes status/gates, issues, inventory counts, renderer/page count, review token, and full-report path/hash, but omits native field results and per-page manifests.
- Poppler extraction uses UTF-8 and form-feed page boundaries. It must preserve empty leading/interior/trailing pages and reject a page-count mismatch; a failed extraction falls back to PDFium.
- Poppler-produced PNGs remain validated inside the fallback decision. A successful page set is not revalidated a second time.

## Acceptance checks

- Focused tests prove valid reuse calls neither renderer, page rasterizer, nor Word export and preserves source bytes.
- Mutating any bound artifact, ordering, count, schema, or token prevents a delivery PASS.
- Old report statuses cannot override a fresh structural/profile/native-field failure.
- Legacy visual-review challenges and full JSON remain compatible.
- N-page Poppler audit performs one extraction subprocess and returns the same per-page blank-page findings as the previous implementation; failure/mismatch exercises the PDFium fallback.
- PNG tests cover one validation on successful Poppler and PDFium paths and retain fallback for invalid Poppler output.
- Summary output preserves all issues/gates and the saved full report hash matches the file.
- Caption audit distinguishes figure and table labels, reassembles split complex SEQ fields, and reports mismatched types without modifying the DOCX.
- Run focused tests, then the full suite once after the final source edit; run an integration smoke on a small synthetic DOCX/PDF if the required local renderer is available.

## Out of scope

- Caption insert/replace/remove or automatic reconciliation/mutation APIs; only
  the read-only audit described below is included.
- Changes to `apply` transaction/evidence semantics or in-memory OOXML batching.
- Any project database, live site, provider, or Word document mutation.

## Phase: combined isolated Word field check and render

The bounded native-worker optimization combines `field.update_all` and `render.pdf`
only when `verify_document` is asked for both render and native field checks, the
source contains fields, no custom renderer is supplied, and no render-reuse report
is being consumed. The host makes a private DOCX/PDF workspace. In one Word session,
the worker snapshots cached field results, exports the PDF first, then updates and
saves fields only in the private DOCX. The host validates both stage envelopes and
artifacts, publishes the PDF atomically, and sends it through the existing page,
content, and visual gates.

Render and field stage outcomes remain independent: a failed PDF export does not
discard a successful field evaluation, and a successful render cannot clear a
field failure. Malformed combined-worker results fail the affected gate; rendering
falls back through the existing renderer. Custom-renderer and render-reuse paths
retain their existing worker/session behavior. Native `render.pdf` and
`field.update_all` must remain in the verified operation allowlist before the
combined action starts.

## Phase: report-only caption audit

The `wordassistant caption audit FILE --json` command reports visible caption
evidence without editing the document. It checks images in direct body
paragraphs (grouped by paragraph) and top-level body tables. A caption is
associated only when an immediately adjacent body paragraph is marked with the
Caption style, contains a recognized caption SEQ field, or starts with a common
Vietnamese/English figure or table label. Table metadata is reported separately
from a visible caption. Multiple matches, shared matches, empty captions,
metadata-only tables, and missing matches remain explicit review findings; the
tool never writes inferred caption text.

Explicit figure/table labels and SEQ identifiers must match the audited object
kind; generic Caption-style paragraphs may apply to either kind. Split complex
field instructions are reassembled before identifying SEQ captions. The audit
excludes headers/footers, images inside tables, nested tables, and objects inside
content controls or custom XML wrappers.
These limits are returned in the report's `scope` object so consumers do not
mistake the result for full-document semantic coverage. A completed report uses
`PASS` when no review findings exist and `REVIEW_REQUIRED` otherwise; content
findings do not turn a completed read-only audit into a CLI execution error.
