---
name: wordassistant
description: Create, inspect, retrieve bounded context from, validate, and render Word DOCX files with profile-aware rules. Use for any DOCX workflow in this repository.
---

# WordAssistant skill

Use the CLI as the stable control plane. This keeps agents from loading raw implementation details or complex OOXML trees into prompt context.

1. Run `wordassistant doctor --json` once per environment.
2. Inspect unfamiliar documents with `wordassistant inspect FILE --json`.
3. For documents longer than a few pages, retrieve bounded context with `wordassistant context FILE --query "..." --max-tokens 8000 --json`.
4. Create document skeletons with `wordassistant scaffold OUTPUT --profile PROFILE --variant VARIANT --title "..." --json`.
5. Perform safe text replacements with `wordassistant replace FILE --old "..." --new "..." --json`.
6. Verify and validate complete documents with `wordassistant verify FILE --profile PROFILE --variant VARIANT --json`.
7. Render to PDF with `wordassistant render FILE --json` and inspect the rendered result when layout matters.
8. Store only verified claims and references with `wordassistant evidence add ...`. Never fabricate citations.

Do not require the user or agent to supply internal section IDs; `--section` is an optional override only.
