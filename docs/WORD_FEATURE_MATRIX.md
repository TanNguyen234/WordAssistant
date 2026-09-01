# Word feature matrix

The machine-readable matrix is generated from the runtime registry:

```powershell
$env:PYTHONPATH = "src"
python scripts/generate_feature_matrix.py
```

See `word_feature_matrix.json` for every callable operation, mutation status,
backend preference, minimum fidelity, and evidence dimensions. Runtime health
and current environment states come from:

```powershell
wordassistant capabilities --json
```

Important limitations:

- Native paths absent from the committed live-test allowlist are `UNVERIFIED` and are not advertised as supported.
- OOXML fields can be structurally valid while their displayed cache is stale.
- Automatic heading numbering requires Heading-style linkage; literal prefixes are rejected by verification.
- Visual delivery requires rendering and page-by-page review. PDF creation alone is not a visual pass.
- Word may normalize valid OOXML during save; native round-trip tests therefore inspect the saved result again.
