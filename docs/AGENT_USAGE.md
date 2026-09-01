# Agent usage

Use `wordassistant-agent.json` for machine discovery and `.agents/skills/wordassistant/SKILL.md` for the short operating workflow.

1. Run `wordassistant doctor --json` once per environment.
2. Inspect unfamiliar documents.
3. Retrieve bounded context for long documents.
4. For a new long report, use `create`, write one bounded UTF-8 content JSON, and run `compose` once. Do not generate helper scripts.
5. Use a high-level command family and an output copy.
6. Use `apply` for a validated, atomic multi-operation plan rather than publishing a chain of temporary DOCX files.
7. Persist native field updates to a distinct final DOCX, then run `integrity audit` and bind that final file/evidence hash with `integrity provenance`. Any later mutation makes both stale.
8. Use dry-run before destructive changes.
9. Verify structural, semantic, dynamic-field, native, and visual statuses independently.
10. Render and inspect every page when layout matters.

`wordassistant capabilities --json` includes `selector_schema` with the allowed
keys, exact-match semantics, and copyable examples. Do not inspect source code
to guess selector fields.

Never infer automatic numbering from visible numeric text or a current TOC from the presence of a field instruction alone.

## Construction order for reliable Word semantics

For a new report, `compose` the substantive paragraphs, real Heading styles,
stable anchor text, evidence-linked citations, and existing bibliography section
first. Insert section breaks with selectors at the actual content
boundaries, then apply portrait/landscape layout to the resulting section
indexes. Finally insert/update TOC, REF, PAGEREF, PAGE, NUMPAGES, and SEQ fields
through a native backend when those features are requested.

Academic originality is provenance-first, not detector-evasion. Supply a verified evidence registry, use adjacent citations for borrowed claims/figures/tables, remove unresolved placeholders and invisible spoofing characters, include an honest AI-use disclosure, and preserve the generated provenance manifest. Repetition and punctuation findings are review prompts only; they are not evidence that AI authored the text.

## Non-negotiable delivery gates

- `validate.valid` must be `true`.
- `verify.delivery_status` must be `PASS`; `overall_status` alone is not a delivery verdict.
- Requested native fields must show an observed updated result after reopening
  in Word; placeholder or stale values fail.
- Review the visible content of every rendered page. Image count, dimensions,
  and file size do not detect blank or malformed pages.
- A negative test passes only if the exact requested invariant caused the
  rejection. Unknown arguments and harness exceptions are failed tests.
- Never invent evidence. Mark synthetic QA fixtures with `synthetic: true` and
  preserve their visible synthetic label in citations and the bibliography.
- If any artifact contradicts the narrative summary, the final verdict is
  `FAIL`.

Use a two-phase final verification. First run `verify` with `--native-fields
--render --engine word`; inspect every path returned in `render.page_images`.
Preserve `visual_review_challenge.token`, which binds the document hash to the
ordered page-image hashes. Then, and only then, rerun with `--visual-reviewed
--visual-review-token TOKEN`. The token is rejected if the document or any page
image changed, and it cannot override near-blank detection or another failed
gate.
