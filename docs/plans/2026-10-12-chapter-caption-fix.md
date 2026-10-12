# Chapter caption fix

Goal: support the guide's chapter.sequence captions without breaking generic
global captions or the Hinh/SoDo/Bang list identifiers.

Authority: presentation guide paragraphs 413–414 and 428–429 (zero-based
python-docx indices): first digit identifies the chapter, second the sequence
within that chapter. Microsoft MS-OI29500
17.16.5.56 states Word SEQ `\s` restarts following the specified heading level:
https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oi29500/a591c060-2800-4699-b1f4-dbb0c4374557

Frozen scope: operations/fields.py, operations/images.py, cli_contracts.py,
both hcm-university-dacn-2026-2027.json copies, this plan,
tests/ooxml/test_chapter_captions.py, docs/academic-report-workflow.md.
Do not alter scaffold, heading numbering, TOC creation, integrity, or citations.

Contract: optional positive integer chapter_number on caption.insert and
caption_chapter_number on image.insert. Find the nearest preceding built-in
Heading 1 at the inserted caption and require a literal CHƯƠNG N prefix
matching the supplied chapter. Reject automatic numbering in that heading.
Emit explicit N. prefix followed by the existing SEQ identifier with `\s 1`.
This choice works with literal headings and resets even if captions are added
out of order. Automatic STYLEREF numbering is outside this bounded fix.
Explicit chapter prefixes require reverification if headings are renumbered
or captions move across chapters. Existing generic captions are unchanged.

Done when focused tests prove all three labels preserve sequence identities,
successive chapters carry reset fields, missing/mismatched/non-heading and
automatic-numbered prerequisites fail without output, image and standalone
paths share behavior, and generic fields are unchanged. Tests first:
`$env:PYTHONPATH='src'; python -m pytest tests/ooxml/test_chapter_captions.py`.

Evidence level: OOXML integration; native Word updates and rendering NOT RUN.
CRG tools unavailable in this session; bounded source inspection used.

Approved scope expansion: profiles/loader.py must validate the new bounded
captions.numbering configuration because its existing strict schema rejects
the profile metadata. Root approved this expansion; no other worker owns the
loader. Add focused schema tests in test_chapter_captions.py before schema
implementation. Only the exact supported mode/options/heading/separator are
accepted, with type checks; arbitrary nested configuration remains rejected.

Results: initial collection without PYTHONPATH failed (environment, not
regression evidence). With PYTHONPATH=src, the caption regression run failed
10 tests for absent chapter options and passed the generic case. After the
caption fix, 14 focused tests passed. Schema positive test then failed for
unknown numbering config before the loader implementation. Final focused
command above: 22 passed. `git diff --check` on the four changed source files
passed (only existing CRLF conversion notices). Native Word update/render
and broader suite NOT RUN in this delegated phase; root owns final review
and one broader run after all workers' source changes stabilize.

Review followup (P2): cyclic Heading 1 base_style traversal can hang chapter
validation. Frozen followup scope: operations/fields.py, the existing focused
test file, and this plan. Add regression tests for self-cycle and a two-style
cycle through both caption and image entry points before implementing a
visited-style-ID guard. Done when cyclic inheritance raises a clear ValueError
before output is saved and the focused suite passes. No source expansion.

Followup evidence: before the guard, `python -c` wrapping the focused cyclic
pytest selection with subprocess timeout=15 exited with TimeoutExpired,
reproducing the nontermination with a bounded subprocess. After the guard,
the full focused command passed 26 tests. Four new cases cover self-cycles
and two-style cycles through both caption and image entry points; they verify
the existing output bytes remain intact. Word/native/render still NOT RUN.
