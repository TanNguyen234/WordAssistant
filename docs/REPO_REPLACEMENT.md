# Apply this bundle to the old GitHub repository

Use a feature branch. Do not overlay V2 while leaving the V1 runtime active.

1. Back up/uncommitted work.
2. Delete every V1 path in `REPLACE_MANIFEST.json` that still exists.
3. Copy the V2 bundle contents into the repository root.
4. Run `python scripts/sync_package_data.py --check`.
5. Install with `python -m pip install -e ".[dev]"`.
6. Run `python scripts/release_check.py`.
7. Run a real workflow: `wordassistant doctor --json`, inspect/context a source DOCX, scaffold/validate/render a test DOCX.
8. Commit on a branch and open a PR. Merge only if CI is green.

The deliberate deletion step prevents the old Gemini/DeepAgents prototype and the new deterministic CLI from coexisting and confusing weak agents.
