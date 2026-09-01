---
name: antigravity-orchestrator
description: Route non-trivial WordAssistant repository work through small fail-closed Antigravity phases with continuous scope checks and fresh independent review. Use for implementation, fixes, release work, or live black-box QA; do not use for a single simple read-only command.
---

# Antigravity orchestrator

Use `antigravity-workflow.json` as the state-machine contract and
`scripts/run_antigravity_workflow.py` as the execution control plane.

Examples:

```powershell
python scripts/run_antigravity_workflow.py --lane read_only --request "Inspect the public agent contract"
python scripts/run_antigravity_workflow.py --lane live_qa --request "Run the approved public-CLI black-box scenario" --run-dir artifacts/antigravity-live-test/run_TIMESTAMP
python scripts/run_antigravity_workflow.py --lane fix --request "Fix the reproduced selector defect" --allow-write src/wordassistant/ --allow-write tests/
```

For `change` and `fix`, each `--allow-write` value is only a ceiling. The plan
must still return exact file paths; subsequent writes are limited to that
smaller set. `read_only` and `live_qa` reject caller-supplied write paths.

## Routing

- `read_only`: answer or inspect without mutation.
- `change`: implement a requested capability.
- `fix`: reproduce and fix one root cause.
- `live_qa`: test the public product without source edits.

Do not combine lanes or feed the whole project into one invocation. Each phase
gets one objective, one immediate predecessor result, and the minimum files or
CLI evidence it needs. A phase cannot mark itself complete when a declared gate
is missing.

## Invariants

1. Freeze the user request, acceptance criteria, exclusions, and authority in
   `intake` before discovery.
2. Discovery is bounded. Prefer public manifests, CLI capability output, `rg`
   targets, and task-specific context; never read the repository wholesale.
   The `live_qa` lane folds discovery into `plan` to avoid a redundant model
   invocation.
3. `plan` declares an exact write allowlist and one focused test before any
   source edit.
4. `implement` makes one root-cause change. The deterministic repository
   monitor rejects tracked/non-ignored writes outside the allowlist; the
   Antigravity sandbox supplies process isolation. This guardrail is not an OS
   security boundary.
5. `focused_test` tests the declared invariant. An unrelated error is not a
   passing negative test.
6. `constraint_audit` compares the live Git delta and evidence with the frozen
   request. Contradiction, unsupported claims, or scope growth fail closed.
7. Reviewers start with fresh context, are read-only, have non-overlapping
   mandates, and report severity plus exact evidence. They do not trust the
   implementer's summary.
8. `final_gate` cannot waive failed evidence. It returns only `PASS`, `FAIL`, or
   `INCOMPLETE`.

For DOCX work, also use the `wordassistant` skill. The `live_qa` lane may write
only below `artifacts/antigravity-live-test/` and must operate through the
public WordAssistant CLI; it must not use direct OOXML, python-docx, or direct
Word COM as a substitute. The runner executes live QA from a generated
artifact workspace containing only public manifests, docs, and skills; source,
tests, and Git history are not copied into that workspace.

Live QA is deliberately split into four fresh sessions with one objective each:
author substantive content, apply Word features, verify/render/review delivery,
then run negative cases against disposable copies. Each session receives only
its immediate artifact/result handoff. Every predecessor artifact marked
`output` must reappear with the same path and SHA-256 as an `input`; command
logs and side evidence must use the `evidence` role.

Every phase returns one JSON object with `status`, `phase`, `scope`, `evidence`,
`next_phase`, and one `gate_results` entry for every declared gate. Phase
contracts add typed fields: `request_contract` (intake), `discovery`,
`write_allowlist` plus `focused_test` (plan), `implementation`, `test_result`,
`audit`, `findings` (reviewers), or `final_result`. Keep narrative details in
evidence files instead of inflating the handoff.
