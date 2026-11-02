# Agent entry points

Use wordassistant-agent.json for machine discovery and [.agents/skills/wordassistant/SKILL.md](../.agents/skills/wordassistant/SKILL.md) for the operating skill.

- [Course/project report workflow](course-report-workflow.md): authority, source inventory, content/model planning, helpers, figures, native Word and final review.
- [Content review schema](report-content-plan.md): subject-specific models and argument/evidence/terminology/sufficiency review.
- [Academic report workflow](academic-report-workflow.md): reviewed sources, citations and composition.
- [Official criteria workflow](official-rubric-workflow.md): complete source inclusion, parity, scoring limits and review state.

Discover selector/operation schemas through capabilities and command help. Save verbose JSON locally and retrieve relevant contracts. Use inspect --summary for long DOCX files and bounded section context. Preserve sources and edit output copies with unique selectors.

For a new long report, author the content plan once, compose once and apply compatible operations atomically. Reuse runbook helpers instead of a new script per version. Subject facts and institution rules belong in project inputs and selected profiles.

For delivery, preserve semantic Word styles/fields, update and save fields through Word, render the saved file and inspect every page before attesting visual review. Profile validation and verify.delivery_status must both pass for Word delivery. Final integrity audit/provenance and content review bind the exact DOCX/evidence hashes; later mutations make them stale.

Run python scripts/check_course_essay_readiness.py WORKSPACE and report its Word delivery, content/source and submission gates separately. Exit 0 is PASS, 1 is INCOMPLETE and 2 is FAIL. Layout PASS, source hashes and review strings do not prove academic accuracy, image meaning or rubric approval. State unresolved evidence honestly.
