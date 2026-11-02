---
name: wordassistant
description: Create, inspect, revise, validate and render editable Word DOCX files with the WordAssistant CLI and a selected profile. Use for DOCX workflows in this repository.
---

# WordAssistant

Use the CLI as the control plane. Discover normal operations through doctor, capabilities and command help; inspect source when implementing a helper, diagnosing a gap or recovering damaged content.

## Start or resume

- For an existing report, read task-brief.md, project.json and latest QA bound to the current DOCX hash. Update the brief and acceptance crosswalk when the user changes a requirement, before editing.
- Run doctor --json once per environment and capabilities --json before relying on native Word or a renderer. Save verbose capability JSON locally and retrieve only needed operations.
- For unknown or over-40-page DOCX files, use inspect FILE --summary --json. Retrieve one relevant section with context --query ... --max-tokens 4000 --only-section ID; discover the ID with one bounded query when needed. Keep retrieved document text below 8,000 tokens per task turn.
- Save changes to an output copy. Use unique heading/text selectors for scoped edits. An unscoped replacement can affect the whole document.

## Choose the workflow

- New report: select the controlling guide/profile, write content/evidence plans, then create, compose once and one compatible apply plan. Do not create a new script for each version.
- Existing report with structural/prose changes: reuse scripts/revise_course_report.py with an authored specification and exact input SHA-256. --prepare resolves a reviewable plan; apply it to a new output. It rejects stale/ambiguous targets, preserves citations/fields and protects paths/code identifiers from glossary edits. Inspect replacements for meaning; a glossary alone cannot improve an argument.
- Course/project report: follow [the canonical workflow](../../../docs/course-report-workflow.md). Reuse its initializer, asset renderer, revision helper, contact sheets and readiness checker. Keep course facts in workspace JSON and institution rules in the selected profile.
- Official rubric/criteria requested: follow [official-rubric workflow](../../../docs/official-rubric-workflow.md). Inspect profile source_assets and the user copy first. Preserve complete applicable criteria, distinguish them from scoring levels/weights and record missing scales honestly.
- Academic citations: follow [academic report workflow](../../../docs/academic-report-workflow.md). Discovery metadata is not claim support; citations require inspected passages and reviewed evidence.
- Prose editing: apply signs-of-ai-writing when relevant. Improve specificity, explanation, evidence and flow; do not infer authorship or optimize for detector evasion.

## Content before layout

Derive outline and illustrations from the assignment and actual project, not a sample's counts. Before drafting, record each applicable requirement, its planned location and verification method. Review against those requirements instead of merely inventorying existing headings.

For software analysis, explicitly decide whether use-case, data, class, activity, sequence, state, component and deployment views are required or inapplicable. Give a reason for every decision; this is not a quota of eight diagrams. Other subjects use their own appropriate models. A retrieval class diagram does not answer a domain-data question. For MongoDB, UML class notation may show logical records, multiplicities, embedded composition and identifier references; never invent ORM classes or SQL foreign keys.

Place each figure beside an explanation of what it shows, why relationships/branches matter and what consequence follows. A figure plus caption is not analysis. Write academic prose suited to the reader: explain technical terms and retain code identifiers where traceability needs them. Develop reasons and relationships instead of filling a word/page quota.

Record content_review_plan_file in project.json. This hash-bound plan records applicable model decisions and section reviews of argument, evidence, terminology and sufficiency. The readiness checker verifies records/assets; a reviewer must examine the content first, because software cannot infer prose quality or image meaning.

## Word semantics and final QA

Use real Heading styles, automatic multilevel numbering, section properties, PAGE/TOC/SEQ fields and table properties. Bold text is not a heading; visible numeric text is not automatic numbering. Preserve editable content, approved covers and factual/source limits.

Check the selected profile and current user choices for heading/caption alignment. Set persistent Heading style alignment with style.update and reconcile conflicting paragraph overrides; visual similarity is not enough. Figure captions follow captions.figure_alignment when configured. Keep caption titles concise; routes, IDs, capture status, source hashes and notation caveats belong in body/evidence unless explicitly required in a title. Conciseness and meaning still need editorial review.

Find chapter boundaries from actual Heading paragraphs, never cached TOC text. Captioned image insertion keeps the image with its following caption; repeating table headers keep with the first data row. Existing documents may need these paragraph properties repaired explicitly. Confirm the resulting pagination in Word.

Stabilize content/layout before final fields. Update fields through Word into a distinct final file, then render that saved file. Inspect every page for covers, heading hierarchy, captions/lists, images, tables, blank pages and clipping. Only then supply the observed visual-review token. A render, dimensions or image count cannot establish visual quality.

After the last DOCX mutation, save profile validation, Word/native/render/visual verification, integrity audit and integrity provenance bound to the final DOCX/evidence hashes. Disposition every integrity warning. Run python scripts/check_course_essay_readiness.py WORKSPACE and report Word delivery, content/source review and submission readiness separately. validate.valid=true plus verify.delivery_status=PASS establishes Word delivery; unresolved rubric/source/review checks keep submission readiness incomplete.

Keep one canonical output pointer and current evidence paths in project.json. Reuse evidence only while its hash matches. Clean obsolete generated files from an exact workspace-confined manifest after dependency checks; preserve source inputs, final QA and reproducibility plans.


## Academic Integrity, Similarity & Stylometry Audit

Integrate `viet-text-audit` into the document QA lifecycle to ensure verifiable attribution and transparent similarity reporting:
- **Comprehensive Audit**: Run `wordassistant integrity audit file.docx [--corpus-dir <dir>] [--output-html <path>] [--json]`. Automatically uses `.wordassistant/evidence.json` as a reference corpus to cross-check cited versus uncited material.
- **Dedicated Similarity & Attribution**: Run `wordassistant integrity similarity file.docx [--corpus-dir <dir>] [--output-html <path>]`. Evaluates:
  1. `external_corpus_similarity`: Non-overlapping lexical overlap ($S_{lex}$) and semantic paraphrase ($S_{sem}$) coverage against the corpus ($S_{total} \le 15\%$ PASS, $15\%-30\%$ WARN, $>30\%$ FAIL).
  2. `evidence_source_attribution_fidelity`: Verifies whether passages matching evidence sources have proper quotation or explicit citations.
  3. `stylometric_profile_review`: Evaluates sentence entropy, Root TTR, burstiness, and transition entropy for human review (never treated as proof of AI authorship).
- **Interactive Report**: Generate standalone 2-column interactive HTML audit reports via `--output-html report.html` for human inspection.
