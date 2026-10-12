# WordAssistant repository review, 2026-10-12

The user authorized repository review, evidenced fixes, logical commits and a
push of `feat/wordassistant-v2-universal-core`. Existing pending academic-report,
writing-review and bounded-context work is included. No history was rewritten.

## Review scope and evidence

Fresh read-only reviewers covered evidence/research/citations, Word semantics,
core/context/CLI and release contracts. Follow-up reviews checked the resulting
fixes, including managed bibliography boundaries. CRG was unavailable in every
reviewer's tool inventory; this is source/diff review with regression evidence,
not a graph-backed review. The Antigravity runner was preflighted in dry-run
mode; its configured Gemini provider was not called. Local independent review
and deterministic tests supplied the available review evidence.

### Confirmed defects repaired

| Area | Trigger and corrected behavior | Regression evidence |
|---|---|---|
| Citation numbering | Author-sorted `[3], [2], [1]` labels were reconstructed by occurrence. Persist style/order/heading/review policy in Word `docVars`; insertion, regeneration, removal and repeated composition share the policy. | `test_citation_number_consistency.py`, core citation workflow |
| Source policy | A source-backed scaffold could accept legacy evidence when the profile option was omitted on first compose/insert. Persist policy when creating that scaffold and retain reviewed-source gates. Uncited prose can still be authored without a registry. | scaffold policy and uncited-content regressions |
| Citation anchors | Inserting or composing within the managed bibliography could report success while regeneration removed the requested content. Reject targets in the managed region, preserve following custom-outline sections, and permit creation of a new bibliography heading. | bibliography anchor, child-heading and proposed-heading regressions |
| Synthetic references | Rich HCMUNRE bibliography runs omitted the visible synthetic marker. Preserve the marker in that style too. | parameterized synthetic citation workflow |
| Reference count | Language headings and prose after a custom-outline Appendix inflated the reference minimum. Exclude language headings and use semantic heading boundaries. | eight-source and Appendix regressions |
| Audit freshness | Supplied audits bound the DOCX/registry but not current linked PDF bytes. Recheck linked reviewed sources before reusing an audit. | changed/missing/inaccessible source regressions |
| Reviewed metadata | Empty/null review fields and unhashable review statuses were accepted or raised the wrong exception. Validate required strings, source URL and status types; audit invalid registries as failures. | reviewed field/type and registry-audit regressions |
| Windows lock safety | `os.kill(pid, 0)` can terminate a process on Windows. Query process liveness using native read-only APIs; live/unknown owners time out without losing ownership. | mocked native liveness, timeout/dead-owner tests |
| Lock initialization | Failed/short owner writes left malformed lock files. Complete short writes and clean up only the acquired file with matching identity/content; preserve replacement owners. | lock initialization and ownership regressions |
| Source I/O | A source read error escaped the integrity audit. Convert source filesystem failures to `EvidenceError` and source FAIL findings. | mocked PermissionError/OSError/deletion tests |
| Word headings | Custom front titles lost outline semantics and section selectors rejected them. Store real outline levels and recognize direct/inherited heading boundaries. Retain conservative legacy-guide indexing for Bullet/body styles. | front-title/index/selector tests and authoritative guide regression |
| Supported library versions | The installed wheel under python-docx 1.1.2 failed because the 1.2.0 development runtime exposed an internal outline descriptor. Read the OOXML element directly; preserve the declared dependency range. | missing-descriptor tests and actual 1.1.2 CLI create/summary/context smoke |
| Captions | Localized image options were rejected and captions lacked chapter counters. Expose the options, verify an explicit chapter against the nearest literal built-in Heading 1, and use chapter-scoped Word `SEQ` fields. Reject cyclic style inheritance. | direct CLI/batch image and chapter-caption regressions |
| Context and cache | Empty strict section IDs expanded retrieval; missing IDs on empty indexes succeeded. Reject both, enforce the retrieval ceiling, and version cached indexes so old boundaries are rebuilt. | context and cache version regressions |
| Agent/release contract | Some entrypoints still recommended full inspection; machine discovery omitted research; release verification deleted existing `dist/`. Align agent guidance/discovery and build the verification wheel in a fresh temporary directory. | manifest/help/package gates and dist hash comparison |

Implementation scope and red/green evidence are recorded in the matching files
under `docs/plans/2026-10-12-*.md`. Regression failures are preserved as defect
evidence rather than described as successful negative tests.

## Verification

- Focused local unit/integration tests passed after corrections. The final
  citation/compose/real-guide/heading group exited 0. No live provider request
  or paid model call was used to verify academic source discovery.
- First release run: **542 passed, 1 failed, 10 warnings**. The real-guide
  `17.3` boundary regression was corrected. That run also preceded the final
  managed-region corrections and is not final verification evidence.
- Second release run: **555 passed, 10 warnings**, then installed-wheel
  inspection failed under python-docx 1.1.2. Corrected the missing-descriptor
  dependency and confirmed the academic scaffold, summary and strict context
  through the CLI in that actual 1.1.2 runtime. Development uses 1.2.0.
- Stable source/config/test snapshot: 209 files in
  `artifacts/repository-review-20261012/source-snapshot-verified.json`.
- Final full release verification: **PASS, exit 0; 558 tests passed, 10 existing
  style-ID deprecation warnings**. The authoritative command is
  `.venv\Scripts\python.exe -u -X utf8 scripts\release_check.py`, with output
  in `artifacts/repository-review-20261012/release-check-verified.log`.
- Offline wheel build and isolated installation passed, including both public
  help surfaces, the academic profile, scaffold/summary/strict context,
  packaged asset hashes, dependency metadata and PDFium page rendering.
- All 209 source/config/test hashes matched after the release gate. `pip check`
  reported no broken requirements. The pre-existing `dist/` wheel was preserved
  byte-for-byte (SHA-256 `410e389e01e5ed7ec248e6abf6b17f9e518391e95218885ec2d6b17c550f8fb1`).
- Package synchronization, feature-matrix synchronization and `git diff --check`
  passed at the stable-source gate. Git's LF-to-CRLF notices are informational.

## Limits

This review does not certify that every possible input or third-party Word
implementation is defect-free. Windows liveness failure cases use mocked APIs;
the final suite's native evidence is reported separately in its log. New chapter
caption counters are covered structurally; their explicit chapter prefix must be
reverified after a chapter rename or move. Page-by-page visual approval of a
finished academic report, a literal 200-page fixture, live Crossref/Unpaywall
requests, paid providers and similarity/plagiarism comparison were not run in
this repository review. Context budgets are estimated tokens; the per-turn
8,000-token rule is agent guidance rather than a cross-command runtime counter.
LibreOffice was unavailable locally; its direct-render branch reported
`SKIPPED_WITH_REASON`. The installed-wheel PDFium page renderer passed.

## Primary references

- [Python `os.kill` platform behavior](https://docs.python.org/3/library/os.html#os.kill).
- [Microsoft process query API](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocess) and [exit status API](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getexitcodeprocess).
- [Word document variables](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.documentvariables?view=openxml-3.0.1).
- The unchanged official guide under `use_cases/hcmunre_dacn_2026_2027/assets/` controls the institutional report profile. Its chapter-caption passages and fixture hash are recorded in the caption plan/release checker.
