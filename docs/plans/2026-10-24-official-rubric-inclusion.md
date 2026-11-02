# Official rubric inclusion in WordAssistant

## Problem and caller

WordAssistant can record assignment requirements and map criteria, but its shared authoring instructions do not consistently require the complete official rubric to appear in a Word document when the user requests it. This lets an otherwise polished report omit the controlling scoring source or replace it with inferred criteria.

## Desired behavior

- For projects that set `include_official_rubric_in_docx: true`, include the complete official rubric as a clearly labelled appendix in the final DOCX.
- Before declaring a rubric absent, inspect every source asset shipped with the selected institution profile and any byte-identical user-supplied copy. An official guide may contain authoritative assessment criteria even when it is not a scored rubric.
- If the only official material is an assessment-criteria section in a larger guide, include the exact complete section in its corresponding review page and say that scoring levels/weights are absent. Do not call it a scored rubric or invent a point scale.
- Preserve all source criteria, levels, weights, tables and wording. Add only a short provenance note identifying the authority, source file and source SHA-256.
- Bind inclusion review to both the official source SHA-256 and the exact output DOCX SHA-256.
- The readiness checker fails closed: absent source, unreadable/unsupported source, missing appendix, incomplete or changed rubric text, missing human review, or stale hashes cannot pass.
- When the official rubric is unavailable, do not generate substitute criteria. Keep the DOCX unchanged for that requirement and report `INCOMPLETE`/`BLOCKED`.

## Scope and constraints

- This is a shared WordAssistant policy and reusable workflow, not VietLex-specific rubric content. The course-essay readiness checker additionally enforces machine-readable inclusion metadata.
- Rubric inclusion is required when the user or assignment requests it; documents that do not request a rubric appendix are unaffected.
- Supported source formats for automated text-parity checks are DOCX and text-readable PDF. Marker-bounded sections of a larger DOCX are supported when the selected section has no embedded images and markers are unique. Scanned or unsupported criteria remain incomplete until a verified facsimile workflow exists.
- Do not use StrongWine examples, public course-weight summaries, or unrelated guides as substitutes for the selected assignment's official rubric or criteria.
- Preserve the original rubric file and all existing report inputs.

## Acceptance checks

1. With inclusion disabled, readiness does not require a rubric appendix.
2. With inclusion enabled and no official rubric source, readiness is `INCOMPLETE` and the report receives no synthesized rubric content.
3. A source DOCX/PDF with a complete, exact text appendix, or an image-free marker-bounded assessment section in its matching review page, plus provenance, reviewer/date and matching source/output hashes, passes the inclusion check.
4. Omitted/altered rubric text, missing review metadata, an unsupported/scanned source, or a stale source/output hash fails or remains incomplete.
5. The starter and workflow instructions state when to include the rubric and explicitly forbid reconstructing missing criteria.
6. Focused tests and the full repository suite pass; `git diff --check` is clean.

## Verification plan

- Add failing checker tests for missing source, exact inclusion, incomplete content and stale hashes.
- Implement the smallest checker seam in `scripts/check_course_essay_readiness.py`.
- Review source and stable diff; run focused tests, then the broader suite once after the final source edit.
- Run the read-only readiness checker for the VietLex artifact. It must remain incomplete if the exact official assessment criteria are missing or unresolved; a detailed scoring rubric may be separately absent.

## Original case assumption (corrected 2026-10-25)

The 2026-10-24 review correctly distinguished the HCMUNRE presentation guide from a scored rubric but incorrectly concluded that no official assessment criteria were present. The guide contains four explicit supervisor-review criteria and two reviewer-page instructions; it says not to assign points on those pages. Those criteria are official and must be included verbatim. The checked sources contain no scoring levels or weights. Do not treat the older course-level grading-weight summary as a substitute.

## Execution record — 2026-10-24

- Shared rule is now in `docs/official-rubric-workflow.md`, `AGENTS.md`, the WordAssistant skill, workspace rule, README, and packaged agent manifest. The course-essay starter defaults to rubric inclusion; its checker enforces exact full-text parity and source/output hashes.
- Focused readiness, agent-manifest, package-data, and PDF rubric tests passed (exit 0). The full repository suite passed (exit 0); the two later-added PDF regression tests were run in the focused suite, with no implementation code changed afterward.
- `python scripts/sync_package_data.py --check` and `git diff --check` passed.
- VietLex readiness v13 returned exit 1: Word delivery PASS; content/source and submission readiness INCOMPLETE because the exact official rubric and other required content checks are unresolved. The DOCX hash remains unchanged.

## Correction — 2026-10-25

- The user pointed out that the rubric/criteria are already among WordAssistant's bundled HCMUNRE materials. The bundled presentation guide is byte-identical to the user-supplied guide (SHA-256 `0F3622DBCD74009FB0867E0D3FA4A1624A38983AF502E55D48868EDF33F74E78`).
- The prior “no official rubric located” conclusion was too broad. The four supervisor-review criteria and reviewer instructions are official criteria; the guide does not provide a scored scale. Update the WordAssistant workflow to inspect profile assets first and support exact section parity in review pages.
- Current implementation scope: add marker-bounded DOCX section readiness support with fail-closed handling when selected criteria contain images, test the source/output hash binding and omission case, correct the VietLex source review and crosswalk, then update only the two review pages in a new output copy.
