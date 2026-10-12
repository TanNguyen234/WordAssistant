# Evidence and integrity fixes, 2026-10-12

Authority: parent task delegates the three confirmed evidence/integrity defects.

Exact write allowlist:
- `src/wordassistant/evidence/registry.py`
- `src/wordassistant/document/integrity.py`
- `tests/test_reviewed_evidence_regressions.py`
- `tests/test_evidence_lock_safety.py`
- `docs/plans/2026-10-12-evidence-review-fixes.md`

Invariants and done-when checks:
1. Vietnamese/English bibliography grouping headings never increase reference count or terminate the bibliography, whether styled as headings or ordinary paragraphs. Existing numeric and unnumbered entries remain supported.
2. A supplied audit cannot produce a stale provenance summary after linked reviewed source bytes change or disappear. Recheck current linked source bytes and raise EvidenceError on invalid source; unchanged sources and unrelated legacy records remain usable.
3. Every required reviewed field is a nonempty string; source URL must be HTTP(S), source digest remains SHA-256, and invalid types fail with EvidenceError. Candidate and legacy optional fields remain compatible. No PDF extraction in registry reads.

Procedure: focused regressions first; run them to demonstrate failures; implement within exact allowlist; run new regressions and existing academic source/integrity tests. Parent coordinates independent review and broader verification. No provider, live, network, commit, push, or full-suite calls. Graph tools were absent from the available tool inventory; inspect source and rg instead.

Assumptions: bibliography grouping labels are Tiếng Việt:/Tiếng Anh: and English equivalents; byte hashes establish identity, not claim support. Timestamp semantic verification remains outside this fix.

Verification evidence (local unit/integration fixtures only):
- Initial `python -m pytest tests/test_reviewed_evidence_regressions.py -q`: collection failed because this Python environment did not import `wordassistant`; this is environment evidence, not a defect reproduction.
- Corrected boundary for every following pytest command: `$env:PYTHONPATH='src'; $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'`. No dependency installation.
- Before source changes: `python -m pytest tests/test_reviewed_evidence_regressions.py -q --tb=no -o addopts=''`: **37 failed, 22 passed in 1.80s**. Failures covered missing/empty reviewed metadata, null causing wrong exception types, non-HTTP source URLs, bibliography grouping labels and changed/deleted reviewed source PDF bytes. Existing valid fixture cases passed.
- After source changes: `python -m pytest tests/test_reviewed_evidence_regressions.py tests/test_academic_sources.py tests/integration/test_integrity_audit.py -q -o addopts=''`: **74 passed in 4.73s**.
- After adding compatibility assertions without changing source: same focused command: **80 passed in 3.95s**. Includes candidate/legacy optional metadata, synthetic compatibility, registry retrieval without PDF extraction, unchanged linked source and missing unlinked source.
- Stable source diff inspected with `git diff -- src/wordassistant/evidence/registry.py src/wordassistant/document/integrity.py`. These files contain prior workspace changes; the current fix must be reviewed against intake source, not attributed the entire HEAD diff.

Implementation: language grouping labels are excluded while keeping bibliography entry counting; required reviewed strings are validated and source URLs are HTTP(S); the common evidence tag collector is shared by audit and supplied-manifest source freshness checking. Source SHA validation now rejects null with EvidenceError rather than TypeError. No source extraction is added to registry get/list.

NOT RUN: full suite (parent responsibility), live Word/render, network/provider, paid calls. UNKNOWN: timestamp semantic truth, source licenses' legal sufficiency, source claim support; byte identity does not establish those facts. Independent review is pending at parent; this artifact does not declare final PASS.

## Authorized follow-up scope

Parent requests additional confirmed fixes in existing source ownership: safe Windows lock-owner liveness (no Windows os.kill), fail-closed timeout preserving live/unknown owners regardless of lock age, dead-owner recovery, reviewed status type errors mapped to EvidenceError, and semantic outline heading bibliography boundaries using shared selectors helper. New exact test file is `tests/test_evidence_lock_safety.py`; selectors/structure are read-only dependencies. Native API tests mock kernel functions; no real process signaling occurs. Python documentation confirms os.kill(pid, 0) terminates on Windows: https://docs.python.org/3/library/os.html#os.kill. Native query contracts: https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocess and https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getexitcodeprocess. Unknown liveness must retain lock and raise EvidenceError at timeout. Only confirmed dead owners may be reclaimed.

Follow-up focused evidence:
- Same corrected local pytest boundary, before follow-up source edits: `python -m pytest tests/test_evidence_lock_safety.py tests/test_reviewed_evidence_regressions.py -q --tb=no -o addopts=''`: **13 failed, 65 passed in 6.53s**. Windows signals were replaced by a throwing test double throughout lock contention tests; no process was actually signaled. Missing native helper failures are new API test expectations; stale live lock theft, malformed ownership deletion, invalid-status TypeError, and Appendix counting were reproduced in existing code paths.
- After follow-up source edits: `python -m pytest tests/test_evidence_lock_safety.py tests/test_reviewed_evidence_regressions.py tests/test_academic_sources.py tests/integration/test_integrity_audit.py -q -o addopts=''`: **93 passed in 9.99s**.
- After adding three source-unchanged coverage cases (Windows dispatch without signaling, failed exit-code query closes handle and returns unknown, lock release preserves replacement owner), same command: **96 passed in 6.32s**.

Follow-up implementation: native Windows process query uses explicit ctypes signatures and releases its handle; invalid process IDs are treated as dead only on ERROR_INVALID_PARAMETER, permission/unknown failures remain unknown. POSIX signal zero is restricted to POSIX. Lock waiting uses monotonic deadline and raises EvidenceError at timeout, keeps uncertain ownership, reclaims a confirmed dead owner at most once, and guards release with its unique acquisition token. Semantic heading level is taken from shared `wordassistant.selectors._heading_level` and carried into bibliography records; direct/custom/inherited outline Appendix boundaries now count one source and continue citation auditing in appendix prose. Invalid review_status arrays/objects return EvidenceError and audit FAIL.

Follow-up limits: native kernel behavior is **mocked unit evidence**, not live process-management verification; no termination or paid/provider calls were performed. The shared selectors helper and other workers' files were not edited. Root owns fresh independent review and final full suite.

## Independent review repair scope

Parent authorizes only two confirmed medium findings in the same allowlist: remove acquired lock files after initialization write failure using acquired file identity and partial-byte ownership, handle short writes, preserve replacement-owner locks; convert reviewed-source filesystem read failures into EvidenceError so integrity audit fails rather than crashes and supplied provenance remains fail-closed. Focused regressions will mock write/read failures; no signals or native operations. Acceptance: write failure/zero write leaves no owned malformed lock, short writes produce complete owner JSON, replacement lock retained, PermissionError/OSError/FileNotFoundError at source read yield source FAIL and provenance EvidenceError. Other behaviors are out of scope.
