# WordAssistant — Antigravity entrypoint

Use WordAssistant through its CLI. Do **not** read the entire repository or DOCX into model context.

## Fast path

```powershell
wordassistant doctor --json
wordassistant inspect <file.docx> --json
wordassistant context <file.docx> --query "what you need" --max-tokens 8000 --json
wordassistant validate <file.docx> --profile generic --variant default --json
```

For the HCMUNRE 2026–2027 specialized-project use case:

```powershell
wordassistant scaffold report.docx --profile hcmunre_dacn_2026_2027 --variant report --title "..." --json
wordassistant validate report.docx --profile hcmunre_dacn_2026_2027 --variant report --json
```

Rules: prefer JSON output, request bounded context before editing long files, never invent citations, and run validate + render before delivery.
