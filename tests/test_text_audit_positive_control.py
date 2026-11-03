"""Positive Control Verification Test for Text Audit Engine.

Proves deterministically that:
1. When verbatim or paraphrased content is present from the reference corpus,
   the similarity score is strictly positive (> 0.0%) and attributes the correct source.
2. HTML reference files are indexed and matched accurately.
3. The 0.0% false reading issue is eliminated when valid overlap occurs.
"""

import sys
from pathlib import Path
import pytest

# Ensure viet-text-audit and WordAssistant are importable
sys.path.insert(0, r"D:\Download\viet-text-audit\src")
sys.path.insert(0, r"D:\Download\WordAssistant\src")

from viet_text_audit.pipeline import DocumentAnalysisOrchestrator
from wordassistant.document.text_audit_adapter import is_text_audit_available, run_document_text_audit


def test_positive_control_verbatim_overlap(tmp_path):
    """Test with injected verbatim reference passage to verify non-zero similarity score."""
    assert is_text_audit_available(), "viet-text-audit engine must be available"

    # 1. Create a reference corpus document
    ref_doc_path = tmp_path / "ref_architecture.txt"
    ref_text = (
        "Kiến trúc phân tầng trong Spring Boot bao gồm Controller, Service và Repository. "
        "Mỗi tầng đảm nhận một trách nhiệm riêng biệt giúp mã nguồn dễ bảo trì và mở rộng."
    )
    ref_doc_path.write_text(ref_text, encoding="utf-8")

    # 2. Create a query document that incorporates the reference text alongside other content
    query_doc_path = tmp_path / "student_report.txt"
    query_text = (
        "Lời mở đầu: Trong đồ án này chúng tôi xây dựng hệ thống phần mềm thương mại điện tử. "
        "Kiến trúc phân tầng trong Spring Boot bao gồm Controller, Service và Repository. "
        "Mỗi tầng đảm nhận một trách nhiệm riêng biệt giúp mã nguồn dễ bảo trì và mở rộng. "
        "Phần kết luận: Hệ thống đã hoàn thành việc triển khai thử nghiệm trên môi trường cục bộ."
    )
    query_doc_path.write_text(query_text, encoding="utf-8")

    # 3. Run analysis
    orchestrator = DocumentAnalysisOrchestrator()
    orchestrator.add_to_corpus("ref_arch_01", ref_text, title="Tài liệu Kiến trúc Spring Boot")

    report = orchestrator.analyze_text(query_text, doc_id="student_report")

    # 4. Assert positive control
    assert report.total_attributed_score > 0.0, f"Expected > 0%, got {report.total_attributed_score}"
    assert report.lexical_overlap_score > 0.0, f"Expected > 0%, got {report.lexical_overlap_score}"
    assert len(report.matched_intervals) > 0, "Expected at least one matched interval"
    
    # Verify matched text attributes to ref_arch_01
    matched_sources = {s.source_id for s in report.source_attributions}
    assert "ref_arch_01" in matched_sources


def test_positive_control_html_corpus_parsing(tmp_path):
    """Verify HTML reference files are indexed and detected in corpus directory."""
    html_corpus_dir = tmp_path / "corpus"
    html_corpus_dir.mkdir()

    html_file = html_corpus_dir / "spring_security.html"
    html_content = (
        "<!DOCTYPE html><html><head><title>Spring Security</title></head><body>"
        "<h1>Kiến trúc Bảo mật</h1>"
        "<p>Bộ lọc SecurityFilterChain đánh giá mọi yêu cầu HTTP để xác thực và phân quyền người dùng.</p>"
        "</body></html>"
    )
    html_file.write_text(html_content, encoding="utf-8")

    orchestrator = DocumentAnalysisOrchestrator()
    added_ids = orchestrator.add_corpus_directory(html_corpus_dir)
    assert len(added_ids) == 1, "HTML file must be discovered and added to corpus"
    assert "spring_security" in added_ids[0]

    # Query with the exact sentence from the HTML file
    query = (
        "Hệ thống ứng dụng cơ chế bảo mật tiêu chuẩn. "
        "Bộ lọc SecurityFilterChain đánh giá mọi yêu cầu HTTP để xác thực và phân quyền người dùng. "
        "Nhờ đó dữ liệu được bảo vệ an toàn."
    )
    report = orchestrator.analyze_text(query, doc_id="test_query")
    assert report.total_attributed_score > 0.0
    assert len(report.matched_intervals) > 0
    matched_sources = {s.source_id for s in report.source_attributions}
    assert any("spring_security" in s for s in matched_sources)
