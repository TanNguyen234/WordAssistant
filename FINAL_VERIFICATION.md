# Final verification snapshot

Release: WordAssistant 2.0.0

Required deterministic gates:

- full unit/regression suite;
- Python compile check;
- package-data synchronization check;
- real HCMUNRE guidance/proposal structural indexing;
- bounded retrieval on the real guidance file;
- bounded retrieval on a 200-section stress DOCX;
- HCMUNRE report scaffold -> validate -> LibreOffice PDF render;
- HCMUNRE proposal source-template preservation -> validate;
- exact SHA-256 equality for both user-supplied source DOCX assets;
- normal wheel build/install and packaged-profile/template resolution.

Run `python scripts/release_check.py` for the deterministic repository subset. Rendering additionally requires LibreOffice/soffice.
