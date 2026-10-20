# WordAssistant agent operating contract

These rules apply to WordAssistant and to agents using this repository as a DOCX workflow. A target repository's own `AGENTS.md`, project configuration, supplied source documents, and the user's current instructions determine project-specific content. Never carry an HCMUNRE requirement into another school or report unless that profile is selected.

## Repository and CLI workflow

1. Use the WordAssistant CLI as the control plane. In a new environment, run `wordassistant doctor --json` once, then use `capabilities --json` before selecting optional Word-native operations.
2. Inspect an unfamiliar DOCX before editing it. For documents over 40 pages or of unknown length, start with `wordassistant inspect FILE --summary --json`; full `inspect --json` includes every paragraph's text and can flood agent context.
3. For long documents, retrieve one task-relevant section at a time with `wordassistant context FILE --query "..." --max-tokens 4000 --only-section SECTION_ID --json`. If the ID is unknown, run one bounded query without `--only-section`, then use an ID returned by context. Keep retrieved text at or below 8,000 tokens in one task turn; ask for another section only when needed. `--active-section-id` prioritizes a section but may include neighbors; `--only-section` is the strict boundary. A 200-page file may be indexed locally, but its full text must not be copied into LLM context.
4. Edit only the selected section or exact target. For section-wide text edits, pass `--selector '{"type":"heading","text":"EXACT HEADING"}'`; for one unique paragraph, use an exact text or paragraph selector. Without `--selector`, text replacement can apply across the document. Save to an output copy.
5. Prefer JSON output for automation. Preserve source paths, hashes, commands, and whether a result is unit, integration, sandbox, live, or not run.
6. For behavior changes, record scope and acceptance checks, write focused tests, implement the change, review the stable diff, and run the broader suite once. A later source change invalidates earlier verification evidence.
7. Do not read or copy unrelated proposal, outline, or sample files as authorities for a report. Keep source precedence explicit when guidance and examples differ.

## Academic source and citation workflow

1. Search for sources that support the actual research question. Prefer primary research, official standards, and authoritative institutional material where appropriate; use reviews for context and label their role.
2. Treat search results and DOI metadata as discovery leads only. Open or download the source, confirm its identity and version, and inspect the relevant page, section, table, or figure before citing a claim.
3. Record stable identifiers, authors, title, date/version, publisher or repository, source URL, retrieval date, applicable reuse license when downloading, and a content hash for a saved source.
4. A downloaded file or a valid DOI does not prove relevance, claim support, permission to redistribute, originality, or absence of plagiarism. Do not bypass paywalls or download a full text without an allowed access basis.
5. Cite only source material that has been reviewed for the claim. Keep direct quotations exact, clearly marked, and tied to a page or section. Paraphrase from the checked source, cite it, and preserve uncertainty; do not copy source phrasing without quotation marks. For the HCMUNRE profile, bibliography numbers use brackets, author names are bold, titles are italic, and publication details appear only when supported by the evidence record.
6. Never invent a source, page, quotation, author, result, source-review state, or similarity result. If a source or passage cannot be checked, say so and leave the claim unresolved.
7. The writing review skill is editorial guidance, not authorship detection. Do not assign AI probabilities, promise detector evasion, or infer plagiarism from style. See `.agents/skills/signs-of-ai-writing/SKILL.md`.

### WordAssistant source commands

- `wordassistant research search --query ...` returns Crossref discovery leads. `research import-doi` stores a non-citable candidate.
- `research open-access` reads the required Unpaywall email from an environment variable; do not pass or print the value. `research download` stores only a PDF with an explicit supported license and records its hash.
- `research excerpt` returns bounded passages from the saved source. `research review` requires an exact excerpt, location, claim, reviewer identity, and explicit support confirmation before changing the record to `reviewed`.
- Citation and composition operations reject `candidate` evidence and recheck saved source hashes for `reviewed` evidence. The HCMUNRE report profile also rejects legacy or manually entered records until their downloaded source passage has been reviewed. Do not bypass these gates by copying DOI metadata into prose.
- See `docs/academic-report-workflow.md` for the reusable scaffold, caption, research, compose, and Word validation sequence.

## DOCX content and Word semantics

1. Select a profile explicitly for institution-specific rules. The HCMUNRE ĐACN 2026–2027 profile is one selectable use case, not a universal report format.
2. Put persistent behavior in real Word styles, section properties, page-number fields, caption `SEQ` fields, TOC/list fields, and table properties. Direct visual formatting alone does not satisfy a Word-template requirement.
3. Keep documents editable and standards-compatible. Do not use layout tables for covers unless the controlling guide requires them. Avoid macros and unsupported package parts.
4. Do not fabricate a topic, results, names, signatures, approvals, supervisor details, source support, or declarations. When those inputs are unavailable, create an honest editable template and identify the remaining fields.
5. Base operations must not require Gemini, OpenAI, Anthropic, or other model-provider keys. Use an optional advanced Word backend only when a requested Word-native feature needs it; check its availability before relying on it.
6. Validate against the selected profile. When appearance matters, update and save fields through Microsoft Word, render the saved file, inspect every page, reopen it, and confirm the styles and layout persist. Report when native Word or visual review was not available.

## Scope and side effects

- Do not commit, push, migrate, delete user data, force an operation, or make a paid-provider call without the user's explicit authorization for that action.
- For networked research, verify the configured provider boundary and response schema before a full run. Do not log credentials or store an email used only for a provider request.
- Do not activate Claude-, Cursor-, Kiro-, or OpenCode-only hooks as Codex lifecycle hooks.

## Skills

- Load only skills that match the current work. UI tasks use the relevant UI skill; API and module-boundary work uses the matching design skill; current framework behavior uses official documentation or Context7.
- For DOCX work, follow `.agents/skills/wordassistant/SKILL.md`.
- For English or Vietnamese prose review, follow `.agents/skills/signs-of-ai-writing/SKILL.md`; use its linter findings as optional review prompts only.
- Skills guide workflow. They do not install tools, plugins, credentials, dependencies, or authorize external calls.


## Course-essay project asset and caption gate

When checking an existing course essay against a current application project, preserve the input DOCX and work on a distinct output copy. Tie each screenshot/diagram to current route/template, actual image contents, and (when available) source asset hash. Hash-only evidence is snapshot provenance, not runtime verification. Mark mockups as proposals. Inspect dynamic SEQ field placement and the visible Word-rendered caption/list. Keep stdout JSON and stderr separate. Record missing rubric/runtime evidence as NOT_RUN, not PASS. Read `docs/strongwine-course-essay-lessons.md` and follow `docs/strongwine-course-essay-workflow.md`.
