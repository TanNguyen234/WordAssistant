# Long DOCX context guard (2026-10-12)

## Problem and authority

WordAssistant already indexes DOCX headings locally and `context` returns a
query-ranked, token-budgeted bundle. However, `inspect --json` includes every
paragraph's text, and the existing `--section` alias only prioritizes a section
before continuing to add other sections. Those interfaces make it too easy for
an agent handling a 200-page report to expose a large amount of text to its
conversation context when the task only concerns one section.

Authority: the user's request to keep agent input bounded and edit only the
relevant report part; repository CLI behavior and tests; the existing
WordAssistant agent contract.

## Desired behavior

- Keep the existing `inspect` and context-selection behaviors backward
  compatible.
- Add `wordassistant inspect FILE --summary --json`, which returns counts,
  fields, section setup, and a bounded outline preview without paragraph text
  or detailed object inventories.
- Add `wordassistant context FILE --only-section ID`, which returns text from
  exactly that indexed section and errors on an unknown ID. Existing
  `--active-section-id` / `--section` keep their priority behavior.
- Enforce a 12,000-token hard maximum at the retrieval API. Agent guidance for
  long documents uses 4,000 tokens per section and no more than 8,000 tokens
  accumulated in one task turn.
- Document that indexing happens locally but full DOCX text must not be sent to
  an LLM. Use a summary to discover headings, then query the relevant section.

## Scope boundaries

- Do not change existing full `inspect` output or the meaning of its JSON
  fields.
- Do not alter DOCX contents, citation behavior, rendering, or profile rules.
- Do not read a 200-page document into the model merely to discover its
  headings; use the bounded summary and targeted context command.

## Acceptance checks

- Tests prove summary output omits all paragraph text and detailed tables,
  while preserving counts and a bounded outline.
- Tests prove `--only-section` returns exactly one section, including for a
  document with multiple highly relevant sections, and rejects an unknown ID.
- Tests prove requests above 12,000 tokens fail with a clear error and existing
  context retrieval remains within budget.
- Agent workflows use a heading selector for section-wide edits; an unscoped
  replacement is reserved for explicitly document-wide changes.
- WordAssistant skill, root AGENTS, and agent-facing workflow docs instruct
  agents to use these bounded paths for long DOCX files.
- Focused tests, full test suite, CLI help, and a stable diff review pass.

## Verification log

- Added `inspect --summary`, which returns counts, section setup, fields, and
  no more than 100 outline entries; it omits paragraph text and detailed
  object inventories. Full `inspect --json` remains unchanged.
- Added `context --only-section SECTION_ID` as a strict single-section
  boundary. Existing `--active-section-id` and `--section` keep their prior
  behavior and may return neighboring sections. Requests above 12,000 tokens
  now fail closed.
- Section edits use the existing heading selector, which resolves the heading
  and its bounded body up to the next peer/superior heading. Agent examples now
  pass that selector to both dry-run and final replacement commands.
- Updated root AGENTS, the WordAssistant skill, agent usage docs, academic
  workflow, and the machine-readable agent manifest. Its package copy matches
  the root manifest.
- Focused tests passed for `tests/test_context.py`,
  `tests/test_context_budget_strict.py`, `tests/test_context_budget_hard.py`,
  `tests/test_cli.py`, `tests/test_cli_section_alias.py`,
  `tests/agent/test_antigravity_workflows.py`, and
  `tests/agent/test_agent_manifest.py`. The only output warnings were the
  existing style lookup deprecation in `document/structure.py:160`.
- Full `python -m pytest -q` reached 100% with no failure report. It emitted
  10 existing style lookup deprecation warnings from
  `document/structure.py:160`.
- `wordassistant inspect TEMPLATE --summary --json` returned only the compact
  outline and structural counts; a follow-up `context --only-section mo-au`
  returned exactly `MỞ ĐẦU`, without adjacent chapter text. CLI help shows the
  new flags. `scripts/sync_package_data.py --check` and `git diff --check`
  passed.
- Final fresh verification after documentation and manifest changes:
  `.venv\\Scripts\\python.exe -m pytest -q` reached 100% with exit code 0;
  it reported 10 existing style lookup deprecation warnings.
  `.venv\\Scripts\\python.exe scripts\\sync_package_data.py --check` and
  `git diff --check` both exited 0. Git printed only LF-to-CRLF notices.
- CRG tools were unavailable. The stable diff and direct source review were
  used instead. No DOCX source content was edited by this change.
