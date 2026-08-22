# WordAssistant 2.0 architecture

## Goal

Provide a small deterministic interface that an AI agent can reliably drive while retaining an escape hatch to a full OOXML backend.

```text
AI agent / human
      |
      v
wordassistant CLI
      |
 +----+--------------------+
 |                         |
Core DOCX             Profile engine
 |                         |
 +---- context/index ------+
 |                         |
 +---- evidence/workspace -+
 |                         |
 +---- validate/render ----+
      |
optional docx-mcp backend for advanced Word-native features
```

## Boundary decisions

- `python-docx` handles deterministic everyday creation, inspection, common replacement and profile validation.
- `docx-mcp-server` is optional and reserved for tracked revisions/comments/notes/fields/cross-references and other deep OOXML features.
- The CLI surface stays small even if the backend has hundreds of functions.
- Profiles contain formatting/use-case rules. Core code contains no HCMUNRE-specific branching except presentation conveniences in scaffold output.
- Large-document context is query-driven and budgeted. Internal section IDs are optional implementation details, not required user inputs.
- Source conflicts are recorded rather than silently reconciled.

## Long-document index

The detector considers Word Heading styles and outline levels first, then conservative numbering/typography/legacy-document heuristics. Sample-page markers are isolated so they do not pollute nearby normative sections. This behavior is regression-tested against the actual HCMUNRE DOCX files.

## Packaging

Root `profiles/` and use-case source assets are human-visible. `scripts/sync_package_data.py` mirrors them into package data so normal wheel installs keep named profiles and the official proposal template available.
