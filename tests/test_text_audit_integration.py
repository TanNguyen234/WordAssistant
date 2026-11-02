"""Integration tests for WordAssistant and viet-text-audit."""

import json
from pathlib import Path
import pytest
from docx import Document

from wordassistant.document.text_audit_adapter import (
    is_text_audit_available,
    build_evidence_corpus,
    load_external_corpus,
    run_document_text_audit,
)


@pytest.fixture
def temp_workspace(tmp_path: Path):
    """Creates a temporary workspace with sample documents and evidence registry."""
    # 1. Reference document in corpus dir
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    ref_file = corpus_dir / "ref_1.txt"
    ref_file.write_text(
        "Trí tuệ nhân tạo đang làm thay đổi toàn diện phương pháp nghiên cứu và đào tạo học thuật tại các trường đại học.",
        encoding="utf-8",
    )

    # 2. Evidence registry JSON with a source file and an excerpt
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    evidence_source_file = evidence_dir / "paper_source.txt"
    evidence_source_file.write_text(
        "Chuyển đổi số trong giáo dục đại học đòi hỏi sự đồng bộ giữa hạ tầng công nghệ và năng lực số của giảng viên.",
        encoding="utf-8",
    )

    registry_path = tmp_path / "evidence.json"
    registry_data = {
        "ev-01": {
            "id": "ev-01",
            "title": "Chuyển đổi số giáo dục đại học",
            "authors": ["Nguyễn Văn A"],
            "year": 2024,
            "url": "https://example.edu.vn/cds",
            "verified_by": "system",
            "synthetic": False,
            "source_file": str(evidence_source_file),
            "support_excerpt": "Chuyển đổi số trong giáo dục đại học đòi hỏi sự đồng bộ.",
        },
        "ev-02": {
            "id": "ev-02",
            "title": "Văn hóa số học đường",
            "authors": ["Trần Thị B"],
            "year": 2023,
            "url": "https://example.edu.vn/vhs",
            "verified_by": "system",
            "synthetic": False,
            "support_excerpt": "Xây dựng môi trường văn hóa số lành mạnh là nền tảng cốt lõi.",
        },
    }
    registry_path.write_text(json.dumps(registry_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3. Query DOCX document copying text from ref_1 without quote
    query_docx = tmp_path / "thesis_draft.docx"
    doc = Document()
    doc.add_heading("Chương 1: Tổng quan nghiên cứu", level=1)
    doc.add_paragraph(
        "Trí tuệ nhân tạo đang làm thay đổi toàn diện phương pháp nghiên cứu và đào tạo học thuật tại các trường đại học. "
        "Đây là xu hướng tất yếu của thời đại công nghệ số hiện nay."
    )
    doc.add_paragraph(
        "Đồng thời, theo tài liệu [ev-01], nghiên cứu tiếp tục phân tích sự phát triển của hệ thống thông tin."
    )
    doc.save(query_docx)

    return {
        "tmp_path": tmp_path,
        "corpus_dir": corpus_dir,
        "evidence_registry": registry_path,
        "query_docx": query_docx,
    }


def test_adapter_availability():
    """Verify that viet-text-audit is detected and available in the environment."""
    assert is_text_audit_available() is True


def test_build_evidence_corpus(temp_workspace):
    """Verify that evidence registry entries with source_file or support_excerpt are converted to corpus docs."""
    corpus = build_evidence_corpus(temp_workspace["evidence_registry"])
    assert len(corpus) == 2
    ids = [d["doc_id"] for d in corpus]
    assert "ev-01" in ids
    assert "ev-02" in ids
    # ev-01 read from source_file
    ev1 = next(d for d in corpus if d["doc_id"] == "ev-01")
    assert "Chuyển đổi số" in ev1["text"]
    # ev-02 extracted from support_excerpt
    ev2 = next(d for d in corpus if d["doc_id"] == "ev-02")
    assert "văn hóa số" in ev2["text"].lower()


def test_load_external_corpus(temp_workspace):
    """Verify loading text/docx/pdf files from an external corpus directory."""
    corpus = load_external_corpus(temp_workspace["corpus_dir"])
    assert len(corpus) == 1
    assert "Trí tuệ nhân tạo" in corpus[0]["text"]


def test_run_document_text_audit(temp_workspace):
    """Verify end-to-end audit execution on DOCX with similarity detection and HTML report generation."""
    html_output = temp_workspace["tmp_path"] / "similarity_report.html"
    result = run_document_text_audit(
        docx_path=temp_workspace["query_docx"],
        corpus_dir=temp_workspace["corpus_dir"],
        evidence_registry_path=temp_workspace["evidence_registry"],
        output_html=html_output,
    )

    assert result["available"] is True
    assert result["corpus_size"] >= 3  # 1 from corpus_dir + 2 from evidence registry
    assert result["lexical_overlap_score"] > 0.0  # Copied sentence from ref_1
    assert "ref_1" in [attr["source_id"] for attr in result["source_attributions"]]
    assert html_output.is_file()
    assert html_output.stat().st_size > 500
    assert "Trí tuệ nhân tạo" in html_output.read_text(encoding="utf-8")
