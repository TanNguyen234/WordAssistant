"""Text Audit Adapter for WordAssistant.

Bridges WordAssistant document integrity validation with viet-text-audit for
lexical overlap, semantic paraphrase similarity, and stylometric profile analysis.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any


def is_text_audit_available() -> bool:
    """Checks whether the viet_text_audit engine is installed and importable."""
    try:
        import viet_text_audit.pipeline  # noqa: F401
        return True
    except (ImportError, Exception):
        import sys
        candidate_paths = [
            Path(__file__).resolve().parents[4] / "viet-text-audit" / "src",
            Path(r"D:/Download/viet-text-audit/src"),
            Path(r"D:/Projects/AI_Paper/pythonProject/.venv/Lib/site-packages"),
        ]
        for p in candidate_paths:
            if p.exists() and str(p) not in sys.path:
                sys.path.insert(0, str(p))
        try:
            import viet_text_audit.pipeline  # noqa: F401
            return True
        except (ImportError, Exception):
            return False


def _extract_text_from_file(file_path: Path) -> str:
    """Extracts raw text from a file (.docx, .pdf, .txt, .md)."""
    if not file_path.is_file():
        return ""

    if is_text_audit_available():
        try:
            from viet_text_audit.ingestion.parser import UnifiedDocumentParser
            parser = UnifiedDocumentParser()
            return parser.parse(file_path).raw_text
        except Exception:
            pass

    # Fallback readers
    ext = file_path.suffix.lower()
    if ext in {".txt", ".md", ".json"}:
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
    elif ext in {".html", ".htm"}:
        try:
            from html.parser import HTMLParser
            class _HClean(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.fed = []
                    self._ignore = False
                def handle_starttag(self, tag, attrs):
                    if tag.lower() in ("script", "style", "noscript"):
                        self._ignore = True
                def handle_endtag(self, tag):
                    if tag.lower() in ("script", "style", "noscript"):
                        self._ignore = False
                def handle_data(self, d):
                    if not self._ignore:
                        self.fed.append(d)
                def get_text(self):
                    return "".join(self.fed)
            p_obj = _HClean()
            p_obj.feed(file_path.read_text(encoding="utf-8", errors="ignore"))
            lines = [line.strip() for line in p_obj.get_text().splitlines() if line.strip()]
            return "\n".join(lines)
        except Exception:
            return ""
    elif ext == ".docx":
        try:
            from docx import Document
            doc = Document(file_path)
            lines = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    lines.extend([c.text for c in row.cells if c.text.strip()])
            return "\n".join(lines)
        except Exception:
            return ""

    return ""


def build_evidence_corpus(registry_path: Path | str | None = None) -> list[dict[str, str]]:
    """Extracts documents from an evidence registry JSON to serve as reference corpus.

    Supports reading full text from `source_file` or falling back to `support_excerpt` / `quote` / `claim`.
    """
    if registry_path is None:
        default_paths = [
            Path(".wordassistant/evidence.json"),
            Path("evidence.json"),
        ]
        reg_file = next((p for p in default_paths if p.is_file()), None)
    else:
        reg_file = Path(registry_path).expanduser().resolve()

    if reg_file is None or not reg_file.is_file():
        return []

    try:
        data = json.loads(reg_file.read_text(encoding="utf-8"))
    except Exception:
        return []

    records: list[dict[str, Any]] = []
    if isinstance(data, dict):
        records = list(data.values())
    elif isinstance(data, list):
        records = data
    else:
        return []

    corpus_docs: list[dict[str, str]] = []

    for item in records:
        if not isinstance(item, dict):
            continue
        doc_id = str(item.get("id") or "").strip()
        if not doc_id:
            continue

        title = str(item.get("title") or doc_id).strip()
        url = str(item.get("url") or f"evidence://{doc_id}").strip()
        extracted_text = ""

        # 1. Attempt reading from source_file
        source_file = item.get("source_file")
        if source_file and isinstance(source_file, str):
            candidates = [
                Path(source_file),
                reg_file.parent / source_file,
                reg_file.parent / "sources" / source_file,
                reg_file.parent / ".wordassistant" / "sources" / source_file,
            ]
            for candidate in candidates:
                if candidate.is_file():
                    extracted_text = _extract_text_from_file(candidate)
                    if extracted_text.strip():
                        break

        # 2. Fall back to excerpts/quotes if source file was missing or empty
        if not extracted_text.strip():
            excerpt_parts = []
            for field in ("support_excerpt", "quote", "claim"):
                val = item.get(field)
                if val and isinstance(val, str) and val.strip():
                    excerpt_parts.append(val.strip())
            extracted_text = "\n".join(excerpt_parts)

        if extracted_text.strip():
            corpus_docs.append({
                "doc_id": doc_id,
                "title": title,
                "url": url,
                "text": extracted_text,
            })

    return corpus_docs


def load_external_corpus(corpus_dir: Path | str | None = None) -> list[dict[str, str]]:
    """Loads text from .txt, .docx, .pdf, and .md files in a designated corpus directory."""
    if corpus_dir is None:
        return []

    c_dir = Path(corpus_dir).expanduser().resolve()
    if not c_dir.is_dir():
        return []

    supported_exts = {".txt", ".docx", ".pdf", ".md", ".html", ".htm"}
    corpus_docs: list[dict[str, str]] = []

    for file_path in sorted(c_dir.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in supported_exts:
            continue

        raw_text = _extract_text_from_file(file_path)
        if raw_text.strip():
            corpus_docs.append({
                "doc_id": file_path.stem,
                "title": file_path.name,
                "url": str(file_path.resolve()),
                "text": raw_text,
            })

    return corpus_docs


def run_document_text_audit(
    docx_path: str | Path,
    corpus_dir: str | Path | None = None,
    evidence_registry_path: str | Path | None = None,
    output_html: str | Path | None = None,
    auto_evidence_corpus: bool = True,
    exclude_quotes: bool = True,
    exclude_bib: bool = True,
    include_semantic: bool = True,
    include_ai_assessment: bool = True,
) -> dict[str, Any]:
    """Runs lexical, semantic, and stylometric audit on a DOCX document."""
    if not is_text_audit_available():
        return {
            "available": False,
            "error": "viet_text_audit is not installed",
            "corpus_size": 0,
            "lexical_overlap_score": 0.0,
            "semantic_paraphrase_score": 0.0,
            "total_attributed_score": 0.0,
            "matched_intervals": [],
            "source_attributions": [],
            "ai_assessment": None,
            "metadata": {"corpus_status": "MODULE_NOT_FOUND"},
        }

    from viet_text_audit.pipeline import DocumentAnalysisOrchestrator
    from viet_text_audit.reporting.html_generator import HTMLReportGenerator

    orchestrator = DocumentAnalysisOrchestrator()
    d_path = Path(docx_path).expanduser().resolve()

    # Load corpus documents
    if corpus_dir:
        for doc in load_external_corpus(corpus_dir):
            orchestrator.add_to_corpus(doc["doc_id"], doc["text"], title=doc["title"], url=doc["url"])

    if auto_evidence_corpus:
        for doc in build_evidence_corpus(evidence_registry_path):
            orchestrator.add_to_corpus(doc["doc_id"], doc["text"], title=doc["title"], url=doc["url"])

    # Run analysis
    try:
        report = orchestrator.analyze_file(
            d_path,
            include_semantic=include_semantic,
            include_ai_assessment=include_ai_assessment,
            exclude_quotes=exclude_quotes,
            exclude_bib=exclude_bib,
        )
        raw_text = orchestrator.parser.parse(d_path).raw_text
    except Exception as exc:
        return {
            "available": True,
            "document_id": d_path.name,
            "total_raw_characters": 0,
            "total_eval_characters": 0,
            "excluded_characters_count": 0,
            "lexical_overlap_score": 0.0,
            "semantic_paraphrase_score": 0.0,
            "total_attributed_score": 0.0,
            "corpus_size": len(orchestrator.corpus),
            "matched_intervals": [],
            "source_attributions": [],
            "ai_assessment": None,
            "metadata": {"error": str(exc), "corpus_status": "EMPTY_OR_UNREADABLE_DOCUMENT"},
            "html_report_path": None,
        }

    # Generate HTML report if requested
    html_report_path: str | None = None
    if output_html:
        out_p = Path(output_html).expanduser().resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        html_content = HTMLReportGenerator.generate_html(report, raw_text)
        out_p.write_text(html_content, encoding="utf-8")
        html_report_path = str(out_p)

    ai_dict = None
    if report.ai_assessment:
        ai_data = asdict(report.ai_assessment)
        st = ai_data.get("status", "INSUFFICIENT_TEXT")
        sty = ai_data.get("stylometry", {})
        existing_metrics = ai_data.get("metrics") if isinstance(ai_data.get("metrics"), dict) else {}

        decision_val = ai_data.get("decision")
        if not decision_val:
            decision_val = "INSUFFICIENT_TEXT" if st == "INSUFFICIENT_TEXT" else ("AI_FLAGGED" if st in ("AI_FLAGGED", "CLASSIFIED") else "HUMAN_ADVISORY")

        metrics_dict = {
            "transition_entropy": existing_metrics.get("transition_entropy", ai_data.get("transition_entropy", 0.0)),
            "ngram_uniformity_score": existing_metrics.get("ngram_uniformity_score", ai_data.get("ngram_uniformity_score", 0.0)),
            "sentence_length_variance": existing_metrics.get("sentence_length_variance", sty.get("sentence_length_variance", 0.0) if isinstance(sty, dict) else 0.0),
            "burstiness": existing_metrics.get("burstiness", sty.get("burstiness", 0.0) if isinstance(sty, dict) else 0.0),
            "repetition_ratio": existing_metrics.get("repetition_ratio", sty.get("repetition_ratio", 0.0) if isinstance(sty, dict) else 0.0),
            "ttr": existing_metrics.get("ttr", sty.get("ttr", 0.0) if isinstance(sty, dict) else 0.0),
            "root_ttr": existing_metrics.get("root_ttr", 0.0),
            "entropy": existing_metrics.get("entropy", 0.0),
            "avg_sentence_len": existing_metrics.get("avg_sentence_len", sty.get("avg_sentence_len", 0.0) if isinstance(sty, dict) else 0.0),
            **existing_metrics,
        }
        word_count = (
            existing_metrics.get("word_count")
            or (sty.get("word_count") if isinstance(sty, dict) else 0)
            or ai_data.get("word_count", 0)
        )
        ai_dict = {
            **ai_data,
            "decision": decision_val,
            "metrics": metrics_dict,
            "word_count": word_count,
        }

    return {
        "available": True,
        "document_id": report.document_id,
        "total_raw_characters": report.total_raw_characters,
        "total_eval_characters": report.total_eval_characters,
        "excluded_characters_count": report.excluded_characters_count,
        "lexical_overlap_score": report.lexical_overlap_score,
        "semantic_paraphrase_score": report.semantic_paraphrase_score,
        "total_attributed_score": report.total_attributed_score,
        "corpus_size": len(orchestrator.corpus),
        "matched_intervals": [asdict(m) for m in report.matched_intervals],
        "source_attributions": [asdict(s) for s in report.source_attributions],
        "ai_assessment": ai_dict,
        "metadata": report.metadata,
        "html_report_path": html_report_path,
    }
