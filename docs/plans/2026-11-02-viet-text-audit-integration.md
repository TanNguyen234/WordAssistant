# Implementation Plan: Full Integration of `viet-text-audit` into `WordAssistant`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate `viet-text-audit` into `WordAssistant` to provide automated external corpus similarity checking, cross-lingual paraphrase detection, evidence registry content verification, and responsible stylometric assessment within `wordassistant integrity audit`.

**Architecture:** A loosely-coupled adapter (`src/wordassistant/document/text_audit_adapter.py`) bridges `WordAssistant` and `viet-text-audit`. It automatically indexes evidence files from `.wordassistant/evidence.json` and external corpora into `viet-text-audit`'s `DocumentAnalysisOrchestrator`, adding 3 new deterministic gates to `wordassistant integrity audit` and generating 2-column interactive HTML reports.

**Tech Stack:** Python 3.12, `wordassistant`, `viet-text-audit`, `python-docx`, `fastembed` (384-dim ONNX), MinHash LSH, Winnowing, Waterman-Eggert alignment.

---

## Global Constraints

- **Loose Coupling**: If `viet-text-audit` is not installed or available, `WordAssistant` must gracefully skip similarity gates with status `SKIPPED` without breaking core functions.
- **Visual Body Order**: Preserve true document visual order (paragraphs + table cells) as already implemented by `_collect_paragraphs`.
- **Zero Accusatory Language**: Findings must remain objective and descriptive (`S_lex`, `S_sem`, `S_total`). Never accuse authors or classify AI authorship definitively.
- **Strict Abstention**: Stylometric assessment must abstain (`INSUFFICIENT_TEXT`) on texts under 150 words.
- **Offline Capable**: All execution must run on CPU without requiring external network connections.
- **Backward Compatibility**: Existing `wordassistant integrity audit` behavior without `--corpus` must remain 100% backward-compatible.

---

## File Structure & Responsibilities

| File Path | Responsibility |
| :--- | :--- |
| `src/wordassistant/document/text_audit_adapter.py` | **New File**: Bridge between WordAssistant and `viet-text-audit`. Loads evidence files/excerpts from `EvidenceRegistry`, builds temporary corpus, and invokes `DocumentAnalysisOrchestrator`. |
| `src/wordassistant/document/integrity.py` | **Modified File**: Adds `corpus_dir`, `output_html`, and `auto_evidence_corpus` parameters to `audit_integrity()`. Evaluates 3 new gates: `external_corpus_similarity`, `evidence_source_attribution_fidelity`, `stylometric_profile_review`. |
| `src/wordassistant/cli.py` | **Modified File**: Adds `--corpus-dir`, `--output-html`, `--no-auto-evidence-corpus` CLI arguments to `wordassistant integrity audit`, and adds sub-action `wordassistant integrity similarity`. |
| `tests/test_text_audit_integration.py` | **New File**: Comprehensive test suite covering adapter, gate evaluation, evidence corpus auto-indexing, CLI execution, and HTML report export. |
| `.agents/skills/wordassistant/SKILL.md` | **Modified File**: Documents the similarity auditing and evidence cross-check capabilities for AI agents. |
| `docs/academic-integrity-text-audit.md` | **New File**: User and agent documentation explaining how to audit theses against reference corpora and evidence files. |

---

## Task Decomposition

### Task 1: Create the `TextAuditAdapter` Bridge Module

**Files:**
- Create: `D:/Download/WordAssistant/src/wordassistant/document/text_audit_adapter.py`
- Test: `D:/Download/WordAssistant/tests/test_text_audit_integration.py`

**Interfaces:**
- Consumes: `EvidenceRegistry` from `wordassistant.evidence.registry`, `DocumentAnalysisOrchestrator` from `viet_text_audit.pipeline`.
- Produces: `is_text_audit_available() -> bool`, `build_evidence_corpus(registry_path: Path) -> dict[str, str]`, `run_document_text_audit(docx_path: Path, corpus_dir: Path | None, evidence_registry_path: Path | None, output_html: Path | None) -> dict[str, Any]`.

- [ ] **Step 1: Write unit tests for TextAuditAdapter**
- [ ] **Step 2: Run test to observe failure**
- [ ] **Step 3: Implement `src/wordassistant/document/text_audit_adapter.py`**
- [ ] **Step 4: Run test to observe pass**
- [ ] **Step 5: Commit**

### Task 2: Extend `audit_integrity()` with Similarity & Stylometry Gates

**Files:**
- Modify: `D:/Download/WordAssistant/src/wordassistant/document/integrity.py`
- Test: `D:/Download/WordAssistant/tests/test_text_audit_integration.py`

- [ ] **Step 1: Write test for new integrity gates**
- [ ] **Step 2: Run test to observe failure**
- [ ] **Step 3: Update `audit_integrity()` in `src/wordassistant/document/integrity.py`**
- [ ] **Step 4: Run test to observe pass**
- [ ] **Step 5: Commit**

### Task 3: CLI Integration & Sub-action

**Files:**
- Modify: `D:/Download/WordAssistant/src/wordassistant/cli.py`
- Test: `D:/Download/WordAssistant/tests/test_text_audit_integration.py`

- [ ] **Step 1: Write CLI execution tests**
- [ ] **Step 2: Run test to observe failure**
- [ ] **Step 3: Update `src/wordassistant/cli.py`**
- [ ] **Step 4: Run test to observe pass**
- [ ] **Step 5: Commit**

### Task 4: Agent Skill, Documentation & End-to-End Regression

**Files:**
- Modify: `D:/Download/WordAssistant/.agents/skills/wordassistant/SKILL.md`
- Create: `D:/Download/WordAssistant/docs/academic-integrity-text-audit.md`
- Test: Full existing test suite (`pytest tests/`)

- [ ] **Step 1: Update `.agents/skills/wordassistant/SKILL.md`**
- [ ] **Step 2: Create `docs/academic-integrity-text-audit.md`**
- [ ] **Step 3: Run full regression test suite**
- [ ] **Step 4: Commit**
