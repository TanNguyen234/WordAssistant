# Migration from WordAssistant V1 / universal-foundation bundle

V2 is a clean replacement, not another patch layer.

## Remove/retire from the old repository

- `src/main.py` provider-bound generation demo.
- `src/agents.py` eager Gemini/DeepAgents initialization.
- old `src/context_manager.py`, `src/document_profile.py`, `src/docx_indexer.py` modules.
- `scripts/markdown_to_docx.py` as the canonical Word engine.
- `scripts/format_checker.py` as the only QA gate.
- old eager `docx_diff.py` / `docx_merge.py` wrappers.
- root mutable `references.json` as a trusted citation store.
- the six competing academic-only `.agents/skills/docx-*` skills.
- generated root artifacts such as `final_essay.docx`.

## Replace with

- installable `src/wordassistant/` package and `wordassistant` CLI.
- strict profiles with separate HCMUNRE `report` and `proposal` variants.
- query-driven bounded context.
- project-local evidence registry.
- one agent skill plus provider-neutral rules.
- optional `docx-mcp-server` advanced backend.
- deterministic tests using the two real HCMUNRE source DOCX files.

When applying V2 to the GitHub repository, use a clean branch and delete retired V1 files in the same PR rather than leaving both architectures active.
