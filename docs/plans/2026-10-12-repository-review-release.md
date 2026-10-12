# Repository review and release (2026-10-12)

## Authority and acceptance

The user explicitly authorized repository-wide review, fixing evidenced defects,
separate logical commits, and pushing the existing branch. Preserve the pending
academic-report, source-review, writing-skill, and bounded-context changes.
No history rewriting, deletions of user data, paid-provider calls, or deployment.

Done when independent bounded reviews cover source/citation safety, Word fidelity,
core/agent/release contracts; confirmed defects have regression coverage; the
stable source passes the full suite and release/package checks; commits are
logically separated and pushed to origin without force; residual limits are stated.

## Baseline and procedure

- Branch: feat/wordassistant-v2-universal-core; HEAD: 2f5cf1b.
- Origin branch matched HEAD after fetch (0 ahead / 0 behind).
- Existing uncommitted changes are from the user's preceding requests.
- CRG unavailable in this session; source/diff review is the fallback.
- Antigravity runner preflight/dry-run only: configured Gemini calls are not
  authorized. Fresh read-only local reviewers cover non-overlapping mandates.
- Package sync check and pip check passed at intake.
- Freeze exact source/test write sets per confirmed defect before editing.
- Run focused regressions during fixes, then full pytest and release checks
  once source is stable. Record results after verification, not assumptions.
- Stage explicit paths/hunks by theme, inspect staged diffs, commit, push the
  existing branch, then confirm remote hash and clean tracked working tree.

## Review results and final verification

Confirmed documentation mismatch: README and a skill example still advertised
unbounded inspection or unscoped edits. Allowlist: README.md and
.agents/skills/wordassistant/SKILL.md. Align examples with the implemented CLI;
documentation-only review (no redundant behavioral test).

Confirmed image-caption CLI schema omission: image.insert implements
caption_sequence but public override rejects it. Exact fix allowlist:
src/wordassistant/cli_contracts.py and tests/agent/test_cli_image_caption.py.
Focused invariant: both direct CLI and atomic apply accept HÌNH/Hinh and emit
a SEQ Hinh field in the saved DOCX. Test before implementation.

Further review and verification pending.

Strict context error-path fix allowlist: src/wordassistant/context/retrieve.py,
tests/test_context.py. Explicit empty/non-string targets must fail rather than
expand retrieval; missing IDs must fail even when no sections exist.

Release checker source review found unconditional deletion of existing dist/.
Allowlist: scripts/release_check.py. Build verification now uses a fresh
temporary output directory and preserves existing release wheels. Verify via
the actual offline release run and compare pre/post dist artifact hashes.
Extend installed-wheel smoke to the new academic profile and strict context.

Heading-index upgrades exposed stale cached indexes: cache identity previously
depended only on DOCX bytes, so old custom-heading boundaries survived an
indexer upgrade. Allowlist: src/wordassistant/workspace.py and
tests/test_workspace_index_version.py. Version cached index payloads; legacy
or future schemas must be misses and current indexes must round-trip.

Agent contract consistency allowlist: GEMINI.md, .agents/rules/wordassistant.md,
wordassistant-agent.json and packaged copy. Apply bounded-context guidance to
remaining entrypoints and expose evidence/research in machine discovery.
The release help gate checks every advertised command in source and wheel.

Stable review outcome: independent reviewers reproduced the root causes and
reviewed final managed-bibliography and library-compatibility corrections with
no remaining actionable HIGH/MEDIUM issue in the bounded correction. Source
and focused regression inspection are review evidence; full release evidence
is tracked separately, not inferred from that review.

Release attempts: first suite 542 passed/1 failed (real-guide 17.3 boundary),
fixed without weakening fixture assertions; second suite 555 passed, then
installed 1.1.2 python-docx rejected the 1.2-only outline descriptor. Three
regressions reproduced that mismatch; direct OOXML lookup now passes the
heading/selector/real-guide/citation focused group and actual 1.1.2 CLI smoke.
Both earlier attempts are superseded for final verification. Third attempt is
running on 209 snapshotted source/config/test files. Logs preserve all attempts.

Final stable verification: release_check.py exited 0 and reported PASS;
558 pytest cases passed with 10 existing style-ID deprecation warnings. Offline
build/isolated install, public help, installed academic scaffold/summary/strict
context, official asset hashes, dependency metadata and PDFium fallback passed.
LibreOffice direct render was SKIPPED_WITH_REASON (not installed). All 209
snapshot hashes remained unchanged; pip check passed. Existing dist wheel hash
remained 410e389e01e5ed7ec248e6abf6b17f9e518391e95218885ec2d6b17c550f8fb1.

Commit partition: editorial skill; academic source/Word semantics;
bounded-context/agent contracts; registry lock safety; release checks/report.
Push only the current branch without force after reviewing each staged diff.
