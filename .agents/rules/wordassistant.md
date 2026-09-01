# WordAssistant workspace rule

When a task involves `.docx`, use the `wordassistant` skill and CLI instead of manually unpacking OOXML unless recovery is required.
For long documents, call `wordassistant context FILE --query ... --json` before reasoning about content.
Keep core operations deterministic; external AI providers are not required by the WordAssistant runtime.
For non-trivial implementation, repair, release, or live QA, route through the `antigravity-orchestrator` skill and `antigravity-workflow.json`; execute one phase per fresh Antigravity session and stop when a machine gate fails.
