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

Optional backends:

```bash
python -m pip install -e ".[word]"
python -m pip install -e ".[native-word]"  # Windows + Microsoft Word
```

## Stable agent-facing commands

`wordassistant-agent.json` defines the canonical command surface. The older
`scaffold` and `replace` commands remain compatibility aliases.

```bash
wordassistant doctor --json
wordassistant capabilities --json
wordassistant profiles --json
wordassistant init . --json
wordassistant inspect file.docx --summary --json
wordassistant context file.docx --query "revise evaluation and error analysis" --max-tokens 4000 --json
wordassistant create output.docx --profile generic --variant default --title "Report" --json
wordassistant compose output.docx --output authored.docx --content content.json --evidence evidence.json --min-visible-characters 8000 --max-visible-characters 14000 --json
wordassistant apply authored.docx --output formatted.docx --plan operations.json --json
wordassistant edit replace file.docx --output revised.docx --options '{"pattern":"old text","replacement":"new text"}' --json
wordassistant table create revised.docx --output tabled.docx --options '{"rows":3,"columns":4}' --json
wordassistant page-number apply tabled.docx --output numbered.docx --options '{"section_index":0,"number_format":"decimal","start":1}' --json
wordassistant validate file.docx --profile generic --variant default --json
wordassistant render file.docx --json
wordassistant evidence list .wordassistant/evidence.json --json
wordassistant integrity audit authored.docx --evidence .wordassistant/evidence.json --profile generic --variant default --json
wordassistant integrity provenance authored.docx --evidence .wordassistant/evidence.json --output authored.provenance.json --json
```

Run `wordassistant capabilities --json` before native comments, revisions,
compare/merge, dynamic field refresh, charts, mail merge, or Word PDF export.
Capability status is operation-granular and does not treat package presence as
proof. See `docs/CAPABILITIES.md` and `docs/WORD_FIDELITY_ASSESSMENT.md`.

For strict section retrieval, use a section ID returned by `context` with
`--only-section ID`. The older `--section` / `--active-section-id` options
prioritize a section and may include neighboring sections.

## Long-document safety

For documents over 40 pages or of unknown length, `inspect --summary` returns
counts and at most 100 heading entries without paragraph text. Full `inspect`
includes document text, so do not send its output to an agent for a long file.
The local index uses styles, outline levels, numbering, tables, typography and
conservative legacy-DOCX heuristics. `context` ranks sections against the query
and caps each response at 12,000 estimated tokens. Agent workflows use 4,000
tokens per retrieval and at most 8,000 combined per task turn; this combined
limit is an agent rule, not an aggregate runtime counter. The workflow avoids:

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

`wordassistant capabilities --json` reports support per operation. The optional
`docx-mcp-server` is currently unintegrated and enables no public operation by
package presence alone. Verified native comments, revisions, compare, field
refresh, and PDF export use the isolated Microsoft Word backend. Advanced
controls, notes, charts, mail merge, native protection, and other unverified
paths remain explicitly unsupported until a committed round-trip test exists.

## Evidence policy

The old mutable global `references.json` design is retired. A project workspace uses `.wordassistant/evidence.json`, and records require an ID, title, authors, year, absolute URL, `verified_by` provenance, and an explicit boolean `synthetic`. Tampered records are rejected on read. No unrelated fallback citation is allowed.

Academic integrity is provenance-first, not detector-evasion. The `integrity` command cross-checks citations, bibliography, evidence, placeholders, invisible Unicode, AI-use disclosure, and review-only prose heuristics, then binds the final DOCX and registry hashes in an atomic provenance manifest. It does not claim to detect AI authorship. See `docs/ACADEMIC_INTEGRITY.md`.

## Quality gates

Before delivery:

1. run `wordassistant integrity audit ...` and write the provenance manifest for academic work;
2. `wordassistant validate ...`;
3. update dynamic fields to a distinct output with the Word-native backend;
4. run `wordassistant verify ... --native-fields --render --engine word`;
5. inspect every returned page image;
6. rerun with `--visual-reviewed --delivery` and require `delivery_status: PASS`.

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
