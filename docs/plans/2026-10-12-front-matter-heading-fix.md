# Front matter heading semantics fix

Authority: assigned bounded repair under the current WordAssistant request; no commit, network, live Word, provider call, or full suite in this worker.

Goal: generated front matter titles remain editable custom-styled Word headings and appear as distinct level-one index sections. Heading selectors must expand through descendants and stop at the next peer heading.

Exact write scope:
- `src/wordassistant/document/scaffold.py`
- `src/wordassistant/selectors.py`
- `src/wordassistant/document/structure.py`
- `tests/test_front_matter_heading_semantics.py`
- this plan

Assumption: custom styles may define or inherit OOXML outline levels. Body outline level 9 is not a heading. Display-only bold paragraphs remain ineligible for semantic heading selectors.

Acceptance: focused tests first reproduce the scaffold index and selector mutation defects; implementation preserves custom typography, shares semantic level resolution between selector and index, and focused tests pass. Root owns fresh independent review and release verification.

Graph coverage unavailable: no graph or semantic-search tools exposed. Bounded source and rg inspection used.

TOC self-inclusion is evaluated separately: preserving outline headings must not be traded for unreliable style-name recognition. Native TOC update is NOT RUN here.

Implementation: custom front title retains its existing Normal base and typography, receives explicit outline level 0. Selector and document index share effective outline resolution (paragraph, style, ancestor style); Body level 9 suppresses heading recognition and index heuristics. Style inheritance traversal guards against cycles.

Stable-source evidence (unit/local integration, no native Word):
- Initial `python -m pytest tests/test_front_matter_heading_semantics.py` could not import the source package. Corrected command uses session `PYTHONPATH=src`; no dependency installation.
- `$env:PYTHONPATH='src'; python -m pytest tests/test_front_matter_heading_semantics.py --tb=short` before source edits: 5 failed for the intended invariants (10 titles missing from index, scoped mutation rejected, explicit/inherited style headings ignored, Body override ignored).
- Same focused command after first implementation: 5 passed.
- Final `$env:PYTHONPATH='src'; python -m pytest tests/test_front_matter_heading_semantics.py tests/core/test_selectors.py tests/test_scaffold_validate.py tests/test_scaffold_structure_ooxml.py --tb=short`: 21 passed in 31.40s. Includes extra direct outline and inherited Body override protection.
- `git diff --check -- src/wordassistant/document/scaffold.py src/wordassistant/selectors.py src/wordassistant/document/structure.py tests/test_front_matter_heading_semantics.py docs/plans/2026-10-12-front-matter-heading-fix.md`: exit 0; CRLF notices only.

Existing edits in scaffold.py were preserved; this worker adds only the custom-title outline property block there. Root owns independent review and full release verification. Native rendering, live Word field update, TOC self-inclusion/exclusion, and visual formatting are NOT RUN in this worker. TOC range changes excluded by root instruction because no guide evidence establishes an alternative range.

Root release regression: full suite failed the real-guide 17.3 boundary because
the guide uses a bold numbered Bullet paragraph whose style has Body outline 9.
Allow conservative legacy heuristics for non-heading body/list styles, while
retaining direct Body overrides and inherited real-heading suppression. Exact
additional scope: structure.py and the existing heading regression file; the
existing real-guide regression already reproduces the defect.

Installed-wheel smoke exposed a supported-library compatibility defect:
python-docx 1.1.x CT_PPr does not expose the 1.2-only outlineLvl descriptor.
Exact correction scope: selectors.py and this existing regression file. Three
tests removing the descriptor reproduce AttributeError; read the standard OOXML
element directly instead, preserving paragraph/style/inherited semantics.
