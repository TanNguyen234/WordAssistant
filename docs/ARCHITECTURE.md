# WordAssistant 2.0 architecture

## Goal

Provide a small deterministic interface that an AI agent can reliably drive while routing each operation to a proven python-docx, OOXML, Microsoft Word, or rendering backend.

```text
AI agent / human
      |
      v
stable CLI / WordDocument facade
      |
ExecutionService + operation registry + selector resolver
      |
fidelity/evidence policy + deterministic backend router
      |
transaction coordinator for document mutations
 +----+-----------+---------------+----------------+
 |                |               |                |
python-docx   direct OOXML   Word native COM   LibreOffice
      |
optional mapped docx-mcp backend
```

## Boundary decisions

- `python-docx` handles deterministic everyday document objects and formatting.
- Direct OOXML handles numbering, fields, bookmarks, references, properties, and plain-text controls when package semantics are proven. Notes and advanced controls are not public until their Word semantics are proven.
- Microsoft Word runs in an isolated worker only for operations on the committed live-test allowlist. Other native implementations remain unreachable and `UNSUPPORTED`.
- `docx-mcp-server` registers no public operation until a real mapped adapter and health probe exist.
- The CLI surface stays small even if the backend has hundreds of functions.
- Profiles contain formatting/use-case rules. Core code contains no HCMUNRE-specific branching except presentation conveniences in scaffold output.
- Large-document context is query-driven and budgeted. Internal section IDs are optional implementation details, not required user inputs.
- Source conflicts are recorded rather than silently reconciled.
- Structural, native-roundtrip, dynamic-result, and visual evidence are independent. No dimension inherits a pass from another.

## Long-document index

The detector considers Word Heading styles and outline levels first, then conservative numbering/typography/legacy-document heuristics. Sample-page markers are isolated so they do not pollute nearby normative sections. This behavior is regression-tested against the actual HCMUNRE DOCX files.

## Packaging

Root `profiles/`, use-case assets, the agent manifest, and generated feature
matrix are human-visible. `scripts/sync_package_data.py` mirrors them into
package data so wheel installs retain the same discovery contract.
