# Academic report upgrade plan (2026-10-12)

## Goal

Complete the reusable HCMUNRE 2026–2027 report workflow in WordAssistant from
the user-provided presentation guide and its report-page samples. Improve the
agent contract and the bilingual writing-review skill so another repository's
agent can prepare an editable, source-grounded DOCX without fabricating
content or claiming detector evasion.

## Authority and evidence

- Primary layout authority: `Hướng dẫn trình bày Báo cáo ĐACN_2026-2027.docx`
  supplied by the user. The WordAssistant CLI inspected it: 554 paragraphs,
  2 tables, 3 sections, 14 images, 2 footnotes, and 2 endnotes.
- Repository copy: `src/wordassistant/data/use_cases/hcmunre_dacn_2026_2027/assets/huong_dan_trinh_bay_dacn_2026_2027.docx`, SHA-256
  `0f3622dbcd74009fb0867e0d3fa4a1624a38983af502e55d48868edf33f74e78`.
- WordprocessingML inspection of that repository copy found the sample cover
  frame in section 2: `w:pgBorders`, `offsetFrom=page`, `display=firstPage`,
  top/left `thinThickSmallGap`, bottom/right `thickThinSmallGap`, size and
  space 24. This is a structural check; the source's live Word render was not
  available because the user had it open and the isolated render did not
  complete.
- Current profile/schema/scaffolder and CLI were inspected through the public
  WordAssistant CLI and bounded source searches. CRG graph tools are not
  available in this session.
- Upgrade package V4 was inspected as an implementation reference, not copied
  wholesale. Its standalone scripts are not wired into the current CLI, and a
  supplied second-cover preview is blank, so package QA claims are not treated
  as current verification.

## Requirements

1. A selected HCMUNRE report profile is independent of generic profiles and
   follows the written guide: A4, Times New Roman 13 pt, 1.5 spacing, margins
   top/bottom/left/right 2/2/3/2 cm, required front matter, three exact chapter
   titles, appendix before references, and references last.
2. The two covers, review/schedule/abstract pages, table of contents, figure
   and table lists, abbreviations, body headers/footers, page numbering,
   captions, and citations use real Word styles, sections, fields, and
   numbering semantics where the feature calls for them. Cover layout stays
   editable and does not use hidden layout tables.
3. No front-matter page number is displayed; Arabic page 1 starts at MỞ ĐẦU.
   TOC, figure/table lists, and PAGE values are reported stale until Word has
   updated and persisted them.
4. Source discovery is opt-in. Search results are candidates; DOI metadata
   must be resolved and checked. A full-text file is downloaded only when an
   explicit reuse license is recorded, via HTTPS with safe redirect, size,
   MIME, and PDF-signature checks. Save source URL, license, retrieval time,
   version when known, and SHA-256 with the evidence record. Citation insertion
   uses a reviewed evidence ID; finding/downloading a source does not by itself
   prove relevance or originality.
   HCMUNRE bibliography entries use unique bracketed numbers, language-specific
   alphabetic grouping/sorting, bold author names, italic titles, and only the
   publication details present in the source record.
5. The writing-review skill reports concrete editorial/citation issues as
   review signals. It must not infer authorship from style, assert a numerical
   AI probability, promise to bypass detection, or rewrite text merely to
   manipulate a detector.
6. The root `AGENTS.md` explains source precedence, profile selection, bounded
   context, metadata honesty, citation provenance, real Word semantics, and
   the verify/render/reopen gate in a repository-neutral way.

## Scope boundaries

- Do not use the separate proposal/outline document as a source for this report
  profile.
- Do not invent a student's project topic, results, names, supervisor,
  signatures, source relevance, or AI-use declaration.
- This task creates and verifies the reusable workflow/template; it cannot
  deliver a completed thesis without those inputs.
- No commit, push, migration, paid API call, or provider-backed Antigravity
  phase is authorized. The Antigravity runner was inspected with `--dry-run`
  only; it would call an external Gemini model during execution.
- No live DOI/OA lookup or source download is included in verification; provider
  behavior will be tested with deterministic fixtures and described as NOT RUN.

## Acceptance checks

- Profile schema validates and the selected report profile contains only the
  presentation-guide authority.
- Focused tests prove the scaffold's Word styles, page setup, cover-only page
  border, section/page-number semantics, front-matter fields, and exact
  required chapter titles after save/reopen.
- Focused tests prove source metadata cannot silently become a citation,
  unknown/unlicensed URLs are refused, downloads record a SHA-256, and unsafe
  redirects/hosts/content are rejected.
- The writing skill and agent contract contain no unsupported authorship
  certainty or detector-evasion instructions.
- A generated DOCX passes profile and structural validation. Native Word
  close/reopen and page-by-page rendering are separate delivery checks; they
  are reported as NOT RUN when the source guide is still open in the user's
  Word session or no safe renderer is available.
- Run focused tests for each implementation slice, then the broad suite once
  on the stable diff. Review the final Git diff and report changed files,
  commands, results, and remaining limitations.

## Implementation and verification log

- Implemented a standalone HCMUNRE report profile in both the repository
  profile directory and packaged profile data, with the guide's first-page
  border and a strict reviewed-source requirement for every evidence-linked
  citation.
- The scaffold persists named Word styles, section/page-number settings,
  caption sequence fields, editable lists/tables, border properties, and
  update-fields settings. Composition sorts bibliography entries per the
  selected profile and refuses source records without a downloaded/reviewed
  passage; it formats author names in bold and titles in italics using only
  publication metadata present in the evidence record. The integrity audit
  rechecks each linked evidence ID and source hash.
- Added an opt-in Crossref/Unpaywall research path, safe licensed PDF download,
  bounded excerpt search, explicit human support confirmation, and source
  provenance storage. No live provider or download call has been made.
- Rewrote the writing-review skill and linter as editorial prompts. They do not
  estimate authorship or offer detector-evasion advice.
- Focused implementation tests: 55 passed after the strict reviewed-source
  and bibliography-formatting changes. The later focused regression/sync run
  (`tests/test_draft_placeholders_rejected.py`,
  `tests/test_package_data_sync.py`, and
  `tests/test_academic_report_profile.py`) passed all 11 tests.
- The first broad run exposed two failures: final verification accepted an
  unfilled scaffold, and the logo lacked its source-side package mirror. The
  scaffold now includes explicit editable content prompts, and the logo is
  mirrored under `use_cases/`; the final `python -m pytest -q` run reached
  100% with no failure report. It emitted 8 style-lookup deprecation warnings
  from `document/structure.py:160`.
- `wordassistant profile validate` passed. A freshly generated report template
  passed structural validation with expected warnings for its 10 empty
  references and unfilled draft prompts. `wordassistant inspect` confirmed
  three sections, two fixed-width tables with PASS geometry, two packaged
  logo images, four TOC/list fields, and a PAGE field in the body footer. The
  page/TOC/list field caches remain placeholders until Microsoft Word updates
  and saves them.
- CRG graph tools were unavailable, so the final code review used the stable
  Git diff and direct source inspection. `git diff --check` passed.
- Native Word close/reopen, source-guide rendering, and page-by-page visual
  review remain NOT RUN because the user had the source guide open in Word and
  LibreOffice was unavailable. No live Crossref/Unpaywall request or source
  download was made. A filled thesis also remains out of scope until the user
  supplies its topic, verified project content, metadata, and sources.

## Technical documentation checked

- Crossref REST API: <https://api.crossref.org/swagger-ui/index.html>
- OpenAlex API and OA locations: <https://help.openalex.org/api/> and
  <https://help.openalex.org/data/locations/>
- Unpaywall API: <https://data.unpaywall.org/products/api>
- Creative Commons license deed: <https://creativecommons.org/cc-licenses/>
