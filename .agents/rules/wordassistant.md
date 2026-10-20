# WordAssistant workspace rule

When a task involves `.docx`, use the `wordassistant` skill and CLI instead of manually unpacking OOXML unless recovery is required.
For long documents, start with `inspect FILE --summary --json`, then use `context FILE --query ... --max-tokens 4000 --json` and `--only-section ID` for the relevant section. Keep context at or below 8,000 estimated tokens per task turn; apply a heading selector to section edits.
Keep core operations deterministic; external AI providers are not required by the WordAssistant runtime.
Antigravity is an optional external-provider workflow. Do not invoke `agy` or `scripts/run_antigravity_workflow.py` automatically; use it only when the user explicitly asks for it. For normal repository work, inspect the relevant files, make a bounded change, run focused local checks, review the diff, and report any unavailable evidence.
