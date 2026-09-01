# Capabilities

`wordassistant capabilities --json` is the authoritative environment-specific view. It combines the operation registry, callable backend handlers, backend health, and committed verification allowlists.

The generated `docs/word_feature_matrix.json` is the environment-independent contract. Every row records mutation status, backend preference, minimum fidelity, and separate structural/native/dynamic/visual evidence. `UNVERIFIED` is never equivalent to support.

Core operations require no API key. Microsoft Word workflows require Windows, Word, and `pywin32`. LibreOffice is a render fallback only when its executable is discovered. The optional docx-mcp package exposes no capability until WordAssistant has a mapped handler and a successful probe.
