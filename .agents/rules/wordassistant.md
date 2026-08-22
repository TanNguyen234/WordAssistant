# WordAssistant workspace rule

When a task involves `.docx`, use the `wordassistant` skill and CLI instead of manually unpacking OOXML unless recovery is required.
For long documents, call `wordassistant context FILE --query ... --json` before reasoning about content.
Keep core operations deterministic; external AI providers are not required by the WordAssistant runtime.
