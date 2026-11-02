# Official rubric and assessment criteria in Word

This workflow applies to any WordAssistant task that asks for an official assignment, evaluation, or scoring rubric in a Word deliverable. It is not limited to a particular school or project.

## Discover and classify the source

1. Read the assignment and current user instructions, select the applicable institution profile, then inspect the files listed in that profile's `source_assets` before searching externally or declaring the source missing. Inspect user-supplied copies too; record paths and SHA-256 values and reconcile duplicates.
2. Classify the source content precisely:
   - A **scoring rubric** defines criteria and may define performance levels, points, weights, or scoring notes.
   - **Official assessment criteria** are explicit evaluation prompts or aspects stated by an authority, even when the source does not assign points or weights.
   - A **format guide**, course outline, grade-weight summary, sample report, or unrelated rubric does not become a scoring rubric merely because it describes report content or grading percentages.
3. If the selected profile's official guide contains assessment criteria but no scored rubric, use those exact criteria for the corresponding review page when the user asks for the rubric/criteria. State that the guide has no scoring levels or weights. Do not report “no official criteria found,” and do not invent score bands, percentages, levels, or additional prompts.
4. Do not substitute a rubric from another assignment, an old cohort's grade-weight split, a sample report, or an unrelated course. If no applicable official rubric or assessment criteria are present in the inspected sources, keep the requirement `INCOMPLETE` and identify exactly which source was missing.

## Preserve and include

1. Preserve the original source unchanged. For a complete standalone scoring rubric, include the complete source in a clearly labelled appendix and preserve every criterion, level, weight, scoring note, table, ordering and source-language wording.
2. When the authority embeds assessment criteria in a larger profile guide, include the complete relevant source section in the matching report review page. Do not append the entire format guide as if it were a rubric. Keep the source file hash and exact section start/end markers in `rubric_inclusion.source_sections`.
3. Bind review metadata to the source and final DOCX hashes, the authority, source section or appendix heading, review method, reviewer and date. Include an appendix heading in the outline/TOC only when the controlling guide requires it.
4. Check exact text after saving. The course-essay readiness checker supports whole-source appendix parity and marker-bounded DOCX section parity. A DOCX with images outside the selected source section can pass text parity only when the selected section itself contains no embedded images; image-bearing criteria, scanned content, unreadable text, ambiguous markers, or incomplete sections stay `INCOMPLETE` pending a verified facsimile workflow. A human must visually compare the included section and its layout.
5. Text parity does not prove that a rubric is authoritative, that the right assignment/profile was selected, or that visual content is correct. Preserve a hash-bound human source and output review.

## Required handoff

Report separately whether the user requested a scoring rubric or official assessment criteria, which profile assets and external sources were inspected, what exact material was found, whether it was included in full, whether scoring levels/weights exist in that source, and whether the source/output hashes and visual review pass. Word formatting `PASS` does not establish rubric compliance or submission readiness.
