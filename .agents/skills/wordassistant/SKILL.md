---
name: wordassistant
description: Create, inspect, retrieve bounded context from, validate, and render Word DOCX files with profile-aware rules. Use for any DOCX workflow in this repository.
---

# WordAssistant skill

Use the CLI as the stable control plane. This keeps weak agents from loading implementation details or hundreds of OOXML tools.

1. Run `wordassistant doctor --json` once per environment.
2. Inspect unfamiliar documents with `wordassistant inspect FILE --json`.
3. For documents longer than a few pages, retrieve only task-relevant content with `wordassistant context FILE --query "..." --max-tokens 8000 --json`.
4. Create a skeleton with `wordassistant scaffold OUTPUT --profile PROFILE --variant VARIANT --title "..." --json`.
5. Validate before delivery. For HCMUNRE report use `--profile hcmunre_dacn_2026_2027 --variant report`; for its proposal use `--variant proposal`.
6. Render to PDF with `wordassistant render FILE --json` and inspect the rendered result when layout matters.
7. Never fabricate evidence. Store only records with provenance in the project evidence registry.

Do not require the user or agent to supply internal section IDs; `--section` is an optional override only.
