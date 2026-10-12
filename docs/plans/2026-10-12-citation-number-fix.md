# Citation number integrity fix

Authority: parent task delegates citation integrity fixes and focused regression tests.
Scope: `operations/citations.py`, `document/compose.py`, this plan, and
`tests/test_citation_number_consistency.py` only. Preserve concurrent edits.

Done when repeated insert, bibliography regeneration, removal (including the
last source), and subsequent composition share the document's numbering policy;
HCMUNRE rich bibliography runs and language groups persist; conflicting numeric
labels fail before saving; generic first-occurrence removal continues to work.

Persist style, order, bibliography heading and reviewed-source requirement in a
standard Word document variable. Share ordering, validation, renumbering and
bibliography construction helpers. Removal has no registry parameter, so preserve
the existing bibliography runs while relabeling and removing entries.

First add regressions and observe failures, then implement and run citation,
composition and profile focused tests. Root task owns independent review and
broader release checks. No commit, push, provider calls, installation or live Word.

Source: Microsoft Open XML `DocumentVariables` documentation, read 2026-10-12:
https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.documentvariables?view=openxml-3.0.1
`w:docVars` persists customer name/value data under document settings.

Evidence (unit/integration, source stable):

- Initial `python -m pytest tests/test_citation_number_consistency.py -q` could
  not import the package; rerun with `PYTHONPATH=src` reproduced all four intended
  failures: repeat citation [1] versus [3], incorrect removal order, existing
  sources omitted on recomposition, and conflicting numeric labels accepted.
- Final `PYTHONPATH=src python -m pytest tests/test_citation_number_consistency.py
  tests/core/test_citation_workflow.py tests/integration/test_compose_workflow.py
  tests/test_academic_report_profile.py -q`: 20 passed. Existing pytest-asyncio
  configuration warning and style-ID deprecation warning remain.
- `git diff --check` for the four owned paths: exit 0.

NOT RUN: broad suite, native Word, render/visual inspection, provider calls.
Root task owns independent review and release checks. Legacy DOCX created before
policy persistence cannot automatically identify a custom bibliography heading.
Implicit insert/remove/default regeneration rejects legacy numeric mappings
that differ from first occurrence. Adopt consistent legacy labels by composing
with explicit citation style and bibliography order/heading; repair conflicting
legacy labels by regenerating with explicit style and the existing bibliography
heading. Regeneration adopts first occurrence order and rewrites both citation
labels and bibliography entries. Two regression tests failed as expected before
adding this guard and explicit repair path, then passed in the final focused run.

Bounded expansion authorized by root: add `document/scaffold.py` to owned paths
to persist source-backed report policy when creating the scaffold, before first
compose/citation insertion. Two parameterized regressions reproduced acceptance
of legacy evidence when compose/insert omitted a redundant profile option.
The source-backed scaffold now stores its selected style, order, reference
heading and reviewed-source requirement. Official proposal cloning is unchanged.

Root completion after delegated runtime limit: verify the scaffold policy
regressions, then propagate shared semantic heading boundaries into reference
mutations. Exact additional scope: operations/citations.py and this existing
regression file. Regeneration/removal must preserve an Appendix using an
inherited custom outline style, matching the new index/selector semantics.

Root regression also covers composing uncited report text without a registry:
persist the source policy without forcing bibliography generation when there
are no citations and no explicit bibliography-generation request. Source-linked
content and explicit bibliography generation still require evidence.

Additional root invariant: hcmunre_numeric bibliography must visibly label
synthetic fixtures just like the generic styles. Extend allowlist to
tests/core/test_citation_workflow.py. Parameterized test first reproduced missing
synthetic marker for hcmunre_numeric; add the explicit marker to rich runs.

Fresh final independent review identified citation anchors inside a managed
bibliography being deleted by regeneration. Three regressions reproduced
acceptance of the bibliography heading, language heading, and entry as anchors.
Reject all managed bibliography anchors before inserting or saving. This
source correction invalidates the already-started release suite; root reruns
the complete release gate on stable source afterward.

Apply the same region guard to compose targets before content mutation. Six
regressions reproduced targets in bibliography/child headings being silently
deleted. Preserve the earlier ability to create a new bibliography heading:
proposed absent headings are permitted; duplicate or missing persisted managed
headings remain rejected. Two fresh/existing-content regressions first failed
under the new guard, then are included in the focused verification.
