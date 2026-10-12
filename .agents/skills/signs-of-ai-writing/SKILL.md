---
name: signs-of-ai-writing
description: Review English or Vietnamese writing for clarity, factual support, source and citation quality, accidental template residue, and unnecessary generic phrasing. Use when asked to edit or audit prose. Do not infer whether a person or model wrote it, estimate authorship probability, evade detectors, or replace a writer's voice.
---

# Writing and source review

Use this skill to improve the text the reader will see. It is an editorial and evidence workflow, not an authorship detector.

## Ground rules

- A phrase, sentence rhythm, punctuation mark, list, or formal register cannot establish who wrote a passage. The linter only points to text that may need human review.
- Do not give AI-authorship percentages or verdicts. Do not call text "humanized," "undetectable," or plagiarism-free based on style edits.
- Do not remove a phrase because it appears on a cliché list. Check whether it is accurate, specific, necessary, and natural in the author's field and language.
- Preserve the author's intended meaning, uncertainty, terminology, dialect, and level of formality. Ask before changing a substantive claim or deleting a meaningful qualification.
- Distinguish writing quality from provenance. A source issue needs a source check; a style issue needs an editorial decision.

## Review workflow

1. **Establish scope.** Identify the requested passage, language, audience, discipline, and requested edit depth. For DOCX files, use WordAssistant `inspect` and bounded `context`; do not extract a whole long document into a prompt by default.
2. **Check claims and sources.** Mark factual claims, numbers, quotations, and technical assertions. Verify them against the cited primary source or an authoritative source appropriate to the claim. Record title, authors, publication date, version, DOI or stable URL, and the page/section supporting the claim. Metadata search results are leads, not proof that a source supports a claim.
3. **Check citation integrity.** Confirm that each in-text citation points to a real reference; the source exists; author/title/date/DOI agree with the source; and the cited passage actually supports the sentence. Use quotation marks and page/section locations for direct quotation. Never invent or silently substitute a reference.
4. **Review the prose.** Look for vague attribution, unsupported praise, repeated setup, unnecessary throat-clearing, unclear referents, overloaded sentences, mechanical transitions, and formatting that hides the argument. Treat every flagged example as a question, not a rule.
5. **Edit conservatively.** Make the smallest change that improves clarity or accuracy. Keep useful lists, technical terms, repetition required for precision, and the writer's natural cadence. Do not introduce facts or citations during a copyedit.
6. **Report evidence and limits.** Separate confirmed errors from suggestions and unresolved checks. Explain which sources and passages were inspected. Never describe this review as a plagiarism check unless an actual comparison against a defined corpus was performed.

## Optional linter

The bundled `scripts/ai_writing_linter.py` filename is retained for compatibility. It reports possible document-hygiene and editorial review items; its findings do not identify AI use or authorship. It reads plain-text files or standard input, and does not inspect DOCX packages.

```powershell
python .agents/skills/signs-of-ai-writing/scripts/ai_writing_linter.py draft.md --json
python .agents/skills/signs-of-ai-writing/scripts/ai_writing_linter.py draft.txt --lang vi
```

Use WordAssistant's `integrity audit` and `validate` commands for DOCX structure, citations, placeholders, and profile rules. Use `render`, native Word field update, and a page-by-page visual review when layout matters. A linter with no findings does not certify accuracy, originality, or authorship.

## Reference notes

- [English editorial examples](references/rules-en.md)
- [Vietnamese editorial examples](references/rules-vi.md)
- [Limits and false positives](references/false-positives-and-human-signs.md)
- [Review prompts](references/prompt-templates-and-deai.md)
