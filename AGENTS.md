# WordAssistant agent operating contract

1. Use the CLI as the control plane; do not read all source files before acting.
2. Run `wordassistant doctor --json` once in a new environment.
3. Inspect an unfamiliar DOCX before modifying it.
4. For long documents, retrieve bounded context with a task-specific query; never inject the whole DOCX into an LLM by default.
5. Prefer JSON output for machine use.
6. Do not invent citations or silently substitute unrelated sources.
7. HCMUNRE is a selectable profile/use case, not a universal rule.
8. Base operations must not require Gemini/OpenAI/Anthropic keys.
9. Use the optional advanced Word backend only when Word-native features require it; do not preload its full tool surface.
10. Validate and render before final delivery when formatting matters.
