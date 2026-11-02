# VietLex adapters

The report now uses the reusable WordAssistant CLI and helpers in `D:/Download/WordAssistant/scripts/`:

- `init_course_essay_project.py`: blank project initialization.
- `build_course_essay_assets.py`: planned subject assets.
- `revise_course_report.py`: hash-bound scoped edits preserving citations/fields.
- `make_course_essay_contact_sheets.py`: final page review sheets.
- `check_course_essay_readiness.py`: separate Word, content and submission gates.
- `clean_course_report_workspace.py`: exact-hash manifest cleanup; dry-run default.

Canonical workflow: `D:/Download/WordAssistant/docs/course-report-workflow.md`. School rules belong to the explicitly selected profile. Course facts and prose are data in this workspace; never reuse VietLex paths or HCMUNRE requirements as defaults for another subject.

`render_screen_hierarchy.py` is retained only as the adapter for VietLex's source-grounded screen map. The obsolete version adapters and intermediate inputs are preserved byte-for-byte in `../qa/history/pre-v18-revision-inputs-and-adapters.zip`; `../qa/cleanup-final-manifest.json` records original paths and hashes. Restore one exact input from that archive only when reproducing its authored revision plan. Do not copy an old adapter to create another version.
