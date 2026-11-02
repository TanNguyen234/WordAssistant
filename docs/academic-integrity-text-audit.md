# Academic Integrity & Text Audit Architecture in WordAssistant

## 1. Overview & Purpose

WordAssistant's academic integrity suite provides deterministic, transparent, and reproducible verification of academic documents (`.docx`). By integrating the `viet-text-audit` engine, WordAssistant extends its static document checks (invisible Unicode characters, unlinked placeholders, quotation-citation adjacency, and citation numbering consistency) with deep lexical and semantic text similarity analysis, evidence source attribution fidelity cross-checking, and descriptive stylometric profiling.

---

## 2. Core Architecture & Verification Gates

The text audit workflow is exposed through `audit_integrity()` and CLI actions (`integrity audit`, `integrity similarity`).

```
                    ┌────────────────────────────────────────┐
                    │            DOCX Document               │
                    └───────────────────┬────────────────────┘
                                        │
                         UnifiedDocumentParser / OOXML
                                        │
                                        ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │                        Integrity Audit Engine                          │
    ├─────────────────────────────┬──────────────────────────────────────────┤
    │  Deterministic Gates (WA)   │      Text Audit Engine (viet-text-audit) │
    │  - invisible_unicode        │  - external_corpus_similarity            │
    │  - typography_punctuation   │  - evidence_source_attribution_fidelity  │
    │  - long_verbatim_quotes     │  - stylometric_profile_review            │
    │  - numeric_citation_consist │                                          │
    │  - source_evidence          │                                          │
    │  - repetitive_prose         │                                          │
    │  - unresolved_placeholders  │                                          │
    │  - ai_use_disclosure        │                                          │
    └─────────────────────────────┴──────────────────────────────────────────┘
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
    JSON Integrity Report                               2-Column HTML Visual Report
   (Gates, Scores, Citations)                          (Color-coded Interactive Spans)
```

### The 3 Text Audit Gates

| Gate Name | Classification | Scoring & Conditions | Default Threshold |
| :--- | :--- | :--- | :--- |
| `external_corpus_similarity` | `EXTERNAL_CORPUS_SIMILARITY_CHECK` | Non-overlapping coverage combining Winnowing lexical overlap ($S_{lex}$) and MiniLM semantic paraphrase ($S_{sem}$). | **PASS**: $S_{total} \le 15\%$<br>**WARN**: $15\% < S_{total} \le 30\%$<br>**FAIL**: $S_{total} > 30\%$ |
| `evidence_source_attribution_fidelity` | `EVIDENCE_SOURCE_FIDELITY_CHECK` | Verifies whether text matching registered evidence entries in `.wordassistant/evidence.json` has explicit adjacent citations or quotation tags. | **PASS**: All evidence matches cited<br>**WARN**: High-overlap match lacking citation |
| `stylometric_profile_review` | `STYLE_REVIEW_NOT_AI_EVIDENCE` | Evaluates descriptive stylometry: Root TTR, sentence entropy, burstiness, transition entropy. | **PASS**: Normal variation or $< 150$ words (`INSUFFICIENT_TEXT`)<br>**WARN**: Stylometric flags (human review only) |

---

## 3. Evidence Registry Cross-Auditing

When `auto_evidence_corpus=True` (the default), WordAssistant automatically indexes documents from `.wordassistant/evidence.json` into the comparison corpus:
1. If an evidence record contains a valid `source_file`, the entire file (`.docx`, `.pdf`, `.txt`) is parsed and indexed.
2. If `source_file` is absent, text from `support_excerpt`, `quote`, and `claim` is extracted and indexed.
3. This allows the system to verify whether the author has accurately attributed passages drawn from their cited background literature.

---

## 4. CLI Usage & Operations

### 4.1 Running Comprehensive Integrity Audit

```bash
# Basic audit with automatic evidence registry cross-checking
wordassistant integrity audit thesis_draft.docx --json

# Audit with external corpus directory and 2-column HTML report output
wordassistant integrity audit thesis_draft.docx \
  --corpus-dir ./reference_papers/ \
  --evidence .wordassistant/evidence.json \
  --output-html ./build/integrity_report.html \
  --json
```

### 4.2 Running Dedicated Similarity & Attribution Audit

```bash
wordassistant integrity similarity thesis_draft.docx \
  --corpus-dir ./reference_papers/ \
  --output-html ./build/similarity_report.html
```

### 4.3 Key Arguments

- `--corpus-dir`, `--corpus`: Path to a directory containing reference `.docx`, `.pdf`, `.txt`, or `.md` documents.
- `--output-html`: Output path for the standalone, interactive 2-column HTML similarity report.
- `--no-auto-evidence-corpus`: Disable automatic inclusion of `.wordassistant/evidence.json` in the comparison corpus.
- `--evidence`: Path to custom evidence registry JSON.
- `--fail-on-warn`: Exit with return code `2` if any gate yields `WARN` (in addition to `FAIL`).

---

## 5. Ethical Guidelines & Scientific Transparency

1. **Similarity $\neq$ Misconduct**: High similarity scores indicate character overlap with existing documents, not academic dishonesty. Properly quoted and attributed text must not be penalized.
2. **Stylometry $\neq$ AI Authorship Proof**: Machine learning classifiers and stylometric heuristics exhibit high false-positive rates on non-native writing and structured academic discourse. Stylometric findings are strictly classified as `STYLE_REVIEW_NOT_AI_EVIDENCE` and must be evaluated by human reviewers.
3. **Transparent Character Offsets**: All match intervals record absolute start and end offsets mapped back to raw document characters, preventing hallucinated overlap claims.
