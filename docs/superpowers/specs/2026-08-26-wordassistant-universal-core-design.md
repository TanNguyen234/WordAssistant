# WordAssistant Universal Core Design

## Objective

Transform WordAssistant into a near-complete, deterministic Microsoft Word automation platform that weak AI agents can operate through no more than 25 stable command families, while preserving all current profile, HCMUNRE, retrieval, workspace, evidence, scaffold, validation, verification, rendering, inspection, and safe-replacement behavior.

## Delivery strategy

Implementation proceeds as vertical capability slices after a shared foundation. Each slice adds a public operation contract, one or more backend implementations, truthful capability registration, CLI/API exposure, focused RED/GREEN tests, real DOCX round-trip tests, and validation/inspection support where deterministic.

Focused tests run throughout development. The broad suite is deferred until source and configuration are stable, then run once before the live-agent exercise. Before that live exercise, Codex launches multiple fresh, independent, read-only reviewer agents against the stable diff: architecture/change impact, Word/OOXML fidelity, and tests/security/release readiness. A fourth adversarial integrator reviews their evidence, deduplicates findings, and may reject unsupported conclusions. All high/medium findings must be fixed or explicitly dispositioned with evidence; fixes trigger focused re-review. Only then does Codex control the user's Windows desktop, open Antigravity, and submit a black-box usability prompt requiring Antigravity itself to discover and operate WordAssistant without source-code inspection. Antigravity must create a realistic approximately ten-page academic DOCX and exercise as many implemented workflows as practical. Codex observes the agent workflow, then independently inspects, renders where an engine is available, deeply verifies, and reviews the produced artifact and execution evidence. Codex does not substitute direct repository calls for Antigravity during the live generation step. Any fixes invalidate the relevant focused gates and affected reviewer conclusions. The complete final suite and release checks run after the live-agent exercise. Logical commits are created only after final verification and then pushed to the required feature branch.

## Architecture

```text
Agent / Human
    |
Stable CLI and Python facade
    |
Operation registry and selector resolver
    |
Transaction coordinator
    |
Deterministic backend router
    +-- python-docx core
    +-- direct OOXML
    +-- optional Microsoft Word native COM
    +-- optional docx-mcp adapter
    +-- LibreOffice renderer
```

The public layer describes intent, not implementation technology. Every operation returns a common envelope containing status, operation, input/output paths, backend used, fidelity, warnings, manual-review requirement, and structured result data. Errors add a stable code, required backend, and suggested action.

Fidelity is evidence-based rather than appearance-based. Structural OOXML, semantic Word behavior, refreshed dynamic results, and rendered appearance are independent dimensions. A feature that only writes plausible text or XML cannot inherit a stronger fidelity claim from another backend.

## Shared foundation

### Operation model

An operation specification defines its name, mutation/read-only classification, accepted selector kinds, required capability, backend preference, fidelity policy, dry-run behavior, and handler interface. Backend handlers return typed operation results rather than printing or exiting.

### Capability model

Capability status is computed from four facts:

1. The operation is registered.
2. At least one backend implements it.
3. That backend is available in the current environment.
4. Its health probe succeeds when required.

States are `SUPPORTED_CORE`, `SUPPORTED_OOXML`, `SUPPORTED_NATIVE`, `SUPPORTED_FALLBACK`, `READ_ONLY`, `UNAVAILABLE`, and `UNSUPPORTED`. Read, create, edit, delete, advanced-edit, and native-Word dimensions remain distinct.

Each operation row also reports evidence dimensions without changing those compatibility states: `structural`, `native_roundtrip`, `dynamic_result`, and `visual`. Values are `VERIFIED`, `AVAILABLE_NOT_RUN`, `UNAVAILABLE`, or `NOT_APPLICABLE`, with test/report identifiers when verified. Capability output must not collapse a structurally valid field into a fresh Word-rendered result.

### Selector model

Selectors support document, section, heading, paragraph index, table index, bookmark, caption, text match, style, and stable internal ID. CLI flags compile to the same selector object accepted by the Python facade. Ambiguous or stale selectors fail before mutation and report candidate matches.

### Transactions and checkpoints

Mutations follow preflight → optional checkpoint → mutate output copy → structural validation → optional render/verify → commit output. Failure restores the checkpoint or leaves the original untouched. Checkpoints live under `.wordassistant/checkpoints`, include file hash and operation metadata, and support create/list/restore commands.

## Backend responsibilities

### Python-docx backend

Handles ordinary paragraphs, runs, styles, basic lists, tables, inline images, sections, headers/footers, core properties, and deterministic package saving.

Style creation uses explicit design tokens and validates built-in identity, `basedOn`, `next`, outline level, quick-style status, and complete font mappings (`ascii`, `hAnsi`, `eastAsia`, and `cs`) where formatting is fixed by a profile.

### OOXML backend

Handles numbering definitions, structurally valid fields, bookmarks, hyperlinks, captions, references, section/page-number elements, custom properties, notes where safe, content controls where safe, and package-level inspection. It preserves unknown parts and relationships.

Heading numbering is a distinct semantic operation: levels link to Heading styles through `w:pStyle`, use real multilevel formats and restart rules, and never prepend literal numbers as a substitute. Table operations maintain an exact geometry contract: table width, grid-column sum, every row's effective cell-width sum, indent, layout mode, and margins agree.

### Microsoft Word native backend

Uses optional `pywin32` on Windows. Health checks prove Word installation, COM dispatch, application launch, document open/save, and cleanup. Word runs invisibly with alerts disabled. Context managers and `finally` blocks close documents and quit Word on every path. Native handlers cover field updates, comments, tracked changes, compare/combine revisions, strong protection, mail merge, charts, pagination-sensitive operations, and PDF export.

Native field refresh repaginates first, updates body and applicable story ranges, TOCs and tables of figures, saves, reopens, and records refreshed cached results. Native automation runs in an isolated worker so COM teardown warnings or crashes cannot corrupt the caller process.

### docx-mcp backend

Remains optional. It registers only explicitly mapped, probeable operations. Raw MCP tools never become public CLI commands.

### LibreOffice backend

Provides fallback rendering and only those field-update behaviors proven by automated tests. Auto rendering prefers Word native, then LibreOffice, else returns `UNAVAILABLE`.

## Capability slices

1. Foundation: operation registry, result/error schema, selectors, transactions, router, capability matrix, Python facade, and agent manifest.
2. Fundamentals: text editing, regex/scoped replacement, run formatting, paragraph formatting, style CRUD, and profile/runtime mismatch fixes.
3. Lists: bullet, numbered, multilevel, restart/continue, indentation, and custom formats.
4. Tables: CRUD, row/column/cell operations, merge/split, dimensions, layout, styles, captions, nesting, and stable selection.
5. Images: inventory, insert/replace/remove/resize, aspect ratio, alt text, captions, and safe drawing-relationship preservation.
6. Sections: page sizes, orientation, margins, gutter, mirrored margins, section breaks, columns, first/odd/even behavior, and link state.
7. Pagination and headers/footers: complete section-aware numbering and declarative header/footer contents.
8. Fields and references: field abstraction, TOC, captions, LOF/LOT, hyperlinks, bookmarks, and cross-references.
9. Academic references and notes: evidence-linked citations, bibliography generation, footnotes, and endnotes.
10. Native review workflows: comments, revisions, compare/merge, content controls, protection, properties, equations, charts, and mail merge.
11. Product surface: compact CLI families, facade completion, expanded inspect/context, validators, final verify model, docs, matrices, CI, and release gates.

## CLI compatibility

Existing commands remain available. `scaffold` aliases the improved `create` workflow, and `replace` aliases the relevant `edit` operation. New functionality is grouped under the command families specified by the product contract. Every mutator supports `--output`, `--dry-run`, and `--json` when meaningful. Every family supports `--help`.

## HCMUNRE behavior

HCMUNRE remains a profile, not a hard-coded global mode. Report generation applies A4, Times New Roman 13, 1.5 line spacing, exact margins, cover/inner cover, front matter, real TOC/LOF/LOT fields, semantic header/footer values, numeric page one at `MỞ ĐẦU`, and numeric citations with at least ten references. Validation proves the relevant section identity and page-number semantics. Official source assets are never rewritten.

## Validation and inspection

Inspection exposes paragraphs, runs, styles, lists, tables, images, sections, headers/footers, fields, bookmarks, hyperlinks, captions, citations, notes, comments, revisions, content controls, protection, properties, equations, and chart inventories when detectable.

Validation emits `ERROR`, `WARNING`, `INFO`, or `MANUAL_REVIEW`. It verifies deterministic package semantics and explicitly labels pagination or layout facts that require a render/native Word review. Final verification independently reports structural, style/format, numbering, table geometry, field structure, field freshness, native round-trip, render, and manual-review statuses. Render success alone does not prove semantic behavior, and structural success alone does not prove current pagination or field results.

## Testing

- Every new behavior begins with a focused failing test and minimal passing implementation.
- Every mutating subsystem has save → reopen → inspect → semantic assertion coverage.
- Heading tests prove Word-recognized styles and linked automatic numbering; visible numeric prefixes alone fail the gate.
- Table tests enforce exact width/grid/cell invariants after save/reopen and after native Word round-trip when available.
- Dynamic-field tests inspect cached results before and after native update and never treat placeholder text as fresh.
- Pagination-sensitive tests repaginate in Word, export to PDF, render every page to images, and audit section starts, formats, footer/header links, blank pages, overflow, and clipping.
- Backend routing tests cover availability, fidelity, refusal, fallback, and cleanup behavior.
- Native tests skip with an explicit reason when Word or `pywin32` is unavailable.
- Core tests stay platform-independent.
- Documentation and machine-readable feature matrices are checked against the implementation registry.
- The first broad suite runs only after the implementation diff is stable.
- After the first broad suite, at least three fresh independent reviewer agents inspect the same stable diff from non-overlapping perspectives. They receive repository instructions, branch/status, diff, focused/full-test evidence, and explicit authority to report findings only—not to edit. A separate adversarial integrator reconciles their reports. Reviewers must validate claims against source and tests; CRG graph evidence is used when callable, with `rg` and direct source inspection as the required fallback.
- Live testing cannot begin while a reviewer has an unresolved high/medium finding, a capability claim lacks matching evidence, or reviewer coverage does not include every changed source/configuration file.
- The live-agent test is executed through the Antigravity Windows application under Codex UI control. Antigravity receives a black-box prompt, discovers WordAssistant from its skill/manifest/CLI, and creates an approximately ten-page academic report while exercising creation, formatting, lists, tables, images, mixed sections, page numbering, headers/footers, fields, TOC/LOF/LOT, bookmarks, cross-references, citations, comments/revisions when native support is available, inspection, context retrieval, verification, and rendering. Direct repository calls by Codex may be used afterward for independent forensic verification, but not as a substitute for Antigravity performing the requested workflow.
- After product inspection and fixes, the final quality gate runs pytest, compileall, package-data sync, release check, CLI help smoke tests, usability simulations, asset hashes, and clean Git checks.

## Commit and remote strategy

No implementation checkpoint commits are created during unstable development. After final verification, changes are divided into logical commits by explicit paths without rewriting history. The commit sequence reflects architecture, core editing engines, document object engines, references/native workflows, agent interface, tests, and documentation. The verified branch is then pushed normally to `origin/feat/wordassistant-v2-universal-core`; force push is forbidden.

## Completion rule

WordAssistant is complete only when implementation, tests, capability discovery, documentation, HCMUNRE verification, live-product evidence, and backend availability agree. Any unimplemented or environment-unavailable feature remains explicitly limited and cannot be advertised as supported.
