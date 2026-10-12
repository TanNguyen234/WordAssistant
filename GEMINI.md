# WordAssistant — Antigravity entrypoint

For every non-trivial implementation, fix, release, or live-QA request, first
use `.agents/skills/antigravity-orchestrator/SKILL.md` and execute
`antigravity-workflow.json` one phase per fresh session. Do not collapse the
phases into one large prompt. The deterministic runner is
`scripts/run_antigravity_workflow.py`; its constraint monitor is authoritative.
For example: `python scripts/run_antigravity_workflow.py --lane live_qa
--request "Run the approved public-CLI black-box scenario" --run-dir
artifacts/antigravity-live-test/run_TIMESTAMP`. The monitor is authoritative
for the repository files it hashes; sandboxing remains the process boundary.

Use WordAssistant through its CLI. Do **not** read the entire repository or DOCX into model context.

## Fast path

```powershell
wordassistant doctor --json
wordassistant capabilities --json
wordassistant inspect <file.docx> --summary --json
wordassistant context <file.docx> --query "what you need" --max-tokens 4000 --json
wordassistant verify <file.docx> --profile generic --variant default --render --json
```

For the HCMUNRE 2026–2027 specialized-project use case:

```powershell
wordassistant create report.docx --profile hcmunre_dacn_2026_2027 --variant report --title "..." --json
wordassistant apply report.docx --output revised.docx --plan operations.json --json
wordassistant integrity audit revised.docx --evidence evidence.json --profile hcmunre_dacn_2026_2027 --variant report --json
wordassistant integrity provenance revised.docx --evidence evidence.json --profile hcmunre_dacn_2026_2027 --variant report --output revised.provenance.json --json
wordassistant verify revised.docx --profile hcmunre_dacn_2026_2027 --variant report --render --json
```

Rules: inspect `operation_statuses` before choosing native-only operations; prefer
JSON output; request bounded context before editing long files; write every
mutation to a distinct output copy; dry-run first; never invent citations; and
require final `verify` plus render review before delivery. Never treat an
unavailable native or visual gate as PASS.

For strict section edits, take an ID returned by `context` and retrieve it with
`--only-section ID`. `--section` only prioritizes a section and may add neighbors.
Keep retrieved context at or below 8,000 estimated tokens per task turn, then
edit with a heading selector and an output copy. For source-backed reports,
follow `docs/academic-report-workflow.md`; `research` candidates must be
downloaded and reviewed before citation.

For academic work, do not optimize text to evade AI detectors. Require real source evidence, citation/bibliography consistency, an honest AI-use disclosure, and hash-bound provenance. Treat repetition and punctuation findings only as prompts for human review, never proof of AI authorship.

## Fail-closed delivery contract

A final delivery PASS requires `validate.valid == true` and
`verify.delivery_status == "PASS"`. `overall_status` is not a delivery verdict.
Inspect the visible content of every
rendered page; PNG/PDF existence, byte size, and dimensions are not a visual
audit. A requested dynamic field must be observed after a native Word update,
not merely present as OOXML or placeholder text. Any contradiction between the
summary and JSON, Word reopen evidence, screenshots, or logs makes the run
FAIL.

Build substantive content before creating layout boundaries. Insert citations
with `--selector`; insert section breaks with `--selector` at actual content
boundaries and only then set section layout. A negative test passes only when
the exact requested invariant rejects the input—an unknown option or test
harness exception is a failed test. Synthetic sources must use
`"synthetic": true`; WordAssistant labels them visibly and they must never be
reported as verified real-world evidence.

The final native sequence is two-phase: run `verify FILE --native-fields
--render --engine word --json`, inspect every returned page image, then rerun
with `--visual-reviewed`. Never set `--visual-reviewed` before the page review;
it is an explicit attestation, not a renderer success flag.
