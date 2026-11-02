# Workflow fix and VietLex status — 2026-10-24

## Cause

Over-context raised the chance of selecting a stale DOCX, guide, or instruction, but it was not the main cause. The main failure was process design: requirements were not frozen into a current-hash acceptance crosswalk, and the workflow allowed Word delivery PASS to stand in for content completeness. There were no hard checks for visible TOC parity, image-to-caption counts, distinct runtime/diagram evidence, per-claim source binding, ordinary UI click-through, and an official rubric appendix. Repeated corrections exposed these missing gates.

## WordAssistant-wide changes

- Added `docs/official-rubric-workflow.md` for any WordAssistant deliverable that requests an official rubric. It requires the exact authority, a complete source-language appendix, source/output hashes and a visual review; missing or unverified criteria remain incomplete.
- Added the rubric gate to `AGENTS.md`, the WordAssistant skill and the packaged `wordassistant-agent.json` manifest. The manifest copy was synchronized with the package data.
- The reusable course-essay starter defaults `include_official_rubric_in_docx` to true and records authority/hash/review metadata. Its readiness gate refuses absent, unsupported, unreadable, partial, changed, or stale rubric evidence.
- Tightened text parity: the rubric appendix text must exactly match all extractable source text, with no extra text after the appendix heading. A human visual check remains necessary for table structure and formatting. Scanned or image-bearing sources stay incomplete until a verified facsimile method exists.
- Preserved the visible-browser screenshot rule, per-page click path/status/hash review, error-state screenshots, and failure on non-2xx/console/visible errors in the shared course-essay workflow.
- Kept the active task brief as the handoff and refreshed source and QA pointers rather than reopening old report history.

## VietLex evidence and document state

- The supplied HCMUNRE guide is a presentation authority (local SHA-256 `0F3622DBCD74009FB0867E0D3FA4A1624A38983AF502E55D48868EDF33F74E78`); no complete scoring rubric was found in the bounded review.
- Official public-source review is preserved in `qa/rubric-source-review-20261024.md`. The public course page for cohorts 9 and 10 gives an older course-weight split, not detailed criteria/levels for this assignment. It was not used as a substitute.
- Refreshed the source snapshot on 2026-10-24 at `21:52:35+07:00`, dirty-status SHA-256 `1704bef16663ea98fc8560581ad97f2d3ad84c66d870545ff1f3d60189a70ba1`. Reviewed the current `app/services/rag_pipeline.py` claim against SHA-256 `4f0c9360adcf75217c0ad1f5a5e09e4cabf5aa6cafb6c874460225479fb32b1d`; the stale-hash blocker in v12 is reconciled.
- The preserved input remains `output/VietLex_DoAnChuyenNganh_Final.docx`, SHA-256 `D1E88C5C5A2BE681F6ED34F1E50BAE724A646E3C711D1B3B5CE2AB3069E378ED`.
- The canonical output remains `output/VietLex_DoAnChuyenNganh_Clickthrough_FinalQA_20261023.docx`, SHA-256 `38E897511263ECCBF6F9B0BF9173EA55E6CBE91FBA4E01B9F33345A3CFEEBE7E`. No DOCX bytes were changed for the rubric request because the exact source is unavailable.
- Existing hash-matched Word QA reports delivery PASS: 83 pages, 105 headings aligned with the TOC, 20 images (11 visible UI screenshots, 7 source-derived diagrams, 2 logos), and 15 tables. All 83 pages were visually reviewed after the last DOCX save.

## Current readiness

`python scripts/check_course_essay_readiness.py D:\Download\ProfessionalLegalRAG\artifacts\course-essay-vietlex-20261020` was run with stdout and stderr saved separately as `qa/readiness-final-clickthrough-v13.json` and `.stderr.txt`. Exit code **1** means incomplete.

| Gate | Result | Current reason |
|---|---|---|
| Word delivery | PASS | Current DOCX hash matches the saved verify/render/profile checks. |
| Content and sources | INCOMPLETE | Exact official rubric is not located; rubric and related human acceptance rows remain NOT_RUN. |
| Submission readiness | INCOMPLETE | Rubric and some content acceptance checks are unresolved; legal-currentness, deployment revision and protected/token routes remain NOT_RUN. |

The runtime click-through and visual/caption parity checks pass in v13. The old v12 stale `rag_pipeline.py` finding is no longer present. The DOCX must remain unchanged for the rubric requirement until the exact official file or authoritative instructor link is supplied.

## Verification and remaining work

- `.venv\Scripts\python.exe -m pytest tests\test_course_essay_readiness.py tests\agent\test_agent_manifest.py tests\test_package_data.py -q` — exit 0, including the PDF extraction/unreadable-page regression tests.
- `.venv\Scripts\python.exe -m pytest -q` — full repository suite, exit 0, reached 100%. It ran before the two PDF-specific tests were added; no implementation code changed afterward, and the updated focused suite passed. Existing deprecation warnings remain in `document/structure.py` style lookup.
- `python scripts/sync_package_data.py --check` — exit 0.
- `git diff --check` — exit 0; Git emitted only its LF-to-CRLF working-copy notices.
- Readiness checker — exit 1 (`INCOMPLETE`), with separate stdout/stderr saved as recorded above.
- CRG graph tools were unavailable in this session; review uses direct source, `rg`, tests and stable diffs, with no graph-backed claim.
- After the official rubric is supplied: preserve the source, append it without edits, add the appendix to the TOC if required, review its full contents and tables, render/review every page, rerun readiness, and bind both hashes.

