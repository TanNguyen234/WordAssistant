# WordAssistant 2.0

WordAssistant is a deterministic, profile-driven control plane for Microsoft Word (`.docx`) automation. It is designed so that **weak AI agents can use it without reading the whole repository, loading a 100–200 page document into context, or understanding OOXML internals**.

HCMUNRE specialized-project reports/proposals are included as the first real use case. They are not hard-coded as the product boundary.

## 60-second setup

Windows PowerShell:

```powershell
./scripts/bootstrap.ps1
```

Linux/macOS:

```bash
./scripts/bootstrap.sh
```

Or manually:

```bash
python -m pip install -e .
wordassistant doctor --json
```

Optional advanced Word/OOXML backend:

```bash
python -m pip install -e ".[word]"
```

## Stable agent-facing commands

```bash
wordassistant doctor --json
wordassistant capabilities --json
wordassistant profiles --json
wordassistant init . --json
wordassistant inspect file.docx --json
wordassistant context file.docx --query "revise evaluation and error analysis" --max-tokens 8000 --json
wordassistant scaffold output.docx --profile generic --variant default --title "Report" --json
wordassistant replace file.docx --old "old text" --new "new text" --output revised.docx --json
wordassistant validate file.docx --profile generic --variant default --json
wordassistant render file.docx --json
wordassistant evidence list .wordassistant/evidence.json --json
```

`--section` exists as an optional precision override for `context`; agents do not need to discover or supply section IDs for normal use.

## Long-document safety

`inspect` builds a structural index from styles, outline levels, numbering, tables, typography and conservative legacy-DOCX heuristics. `context` ranks sections against the user's query and enforces a hard input budget. It therefore avoids the anti-pattern:

```text
200-page DOCX -> entire text -> LLM
```

and instead uses:

```text
DOCX -> structural sections -> query ranking -> bounded context -> AI agent
```

The real HCMUNRE guidance file is a regression fixture: it uses legacy/custom styles rather than Word Heading styles, so the detector explicitly handles that case. The included 200-section stress tests verify budgeted retrieval behavior.

## Profiles and use cases

Human-editable profiles live in `profiles/`. Package copies are synchronized by:

```bash
python scripts/sync_package_data.py
python scripts/sync_package_data.py --check
python scripts/release_check.py
```

HCMUNRE examples:

```bash
wordassistant scaffold report.docx \
  --profile hcmunre_dacn_2026_2027 --variant report \
  --title "TÊN ĐỀ TÀI" --student "..." --supervisor "..." --json

wordassistant scaffold proposal.docx \
  --profile hcmunre_dacn_2026_2027 --variant proposal --json
```

The report variant uses the written report guidance as normative. The proposal variant preserves the supplied official proposal template.

## Advanced Word surface

The base CLI deliberately exposes a small stable command set. This is intentional: weak agents should not preload 200+ low-level OOXML tools.

`wordassistant capabilities --json` reports whether the optional `docx-mcp-server` backend is installed. That backend is the route for Word-native operations such as tracked changes, comments, footnotes/endnotes, bookmarks, fields/cross-references, charts, equations, content controls, protection and deep OOXML audit. Load it only when a task requires those capabilities.

## Evidence policy

The old mutable global `references.json` design is retired. A project workspace uses `.wordassistant/evidence.json`, and records require an ID, title, authors, year, absolute URL, and `verified_by` provenance. No unrelated fallback citation is allowed.

## Quality gates

Before delivery:

1. `wordassistant validate ...`
2. `wordassistant render ...`
3. inspect the rendered PDF when layout matters.

Repository verification:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m compileall -q src
python scripts/sync_package_data.py --check
python scripts/release_check.py
```

## Agent integrations

- `GEMINI.md`: compact Antigravity entrypoint.
- `.agents/rules/wordassistant.md`: workspace rule.
- `.agents/skills/wordassistant/SKILL.md`: one discoverable skill rather than many competing academic-only skills.
- `AGENTS.md`: provider-neutral operating rules.

See `docs/ARCHITECTURE.md`, `docs/MIGRATION_V1_TO_V2.md`, and `use_cases/hcmunre_dacn_2026_2027/README.md`.
