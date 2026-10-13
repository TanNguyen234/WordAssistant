import json
from pathlib import Path

from docx import Document
from PIL import Image

from wordassistant.document.render import RenderResult
from wordassistant.document.verify import verify_document


def test_reuse_report_attests_without_rendering_and_rechecks_document(tmp_path, monkeypatch):
    source = tmp_path / "report.docx"
    doc = Document()
    doc.add_paragraph("A substantive report paragraph for verification.")
    doc.save(source)
    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(b"%PDF-stable")
    page = tmp_path / "page-1.png"
    image = Image.new("RGB", (20, 20), "white")
    image.save(page)
    image.close()

    monkeypatch.setattr("wordassistant.document.verify._pdf_page_count", lambda _: 1)
    monkeypatch.setattr("wordassistant.document.verify.render_pdf_pages", lambda *args, **kwargs: (page,))
    monkeypatch.setattr(
        "wordassistant.document.verify.audit_pdf_page_content",
        lambda *args, **kwargs: {"status": "PASS", "pages": [{"page": 1, "near_blank": False}], "near_blank_pages": []},
    )
    first = verify_document(
        source,
        render=True,
        renderer=lambda *args, **kwargs: RenderResult(pdf, pdf.stat().st_size, "libreoffice", 1),
    )
    report_path = tmp_path / "full-report.json"
    report_path.write_text(json.dumps(first), encoding="utf-8")
    reuse_token = first["visual_review_reuse"]["token"]

    def forbidden(*args, **kwargs):
        raise AssertionError("reuse must not call a renderer or rasterizer")
    monkeypatch.setattr("wordassistant.document.verify._render_via_execution_service", forbidden)
    monkeypatch.setattr("wordassistant.document.verify.render_pdf_pages", forbidden)
    reused = verify_document(
        source,
        visual_reviewed=True,
        visual_review_token=reuse_token,
        reuse_render_report=report_path,
    )
    assert reused["render_status"] == "PASS"
    assert reused["visual_status"] == "PASS"
    assert reused["visual_review_attestation"]["basis"] == "VERSIONED_RENDER_REPORT_REUSE"
    assert reused["native_word_status"] == "NOT_REQUESTED"

    monkeypatch.setattr(
        "wordassistant.document.verify.audit_pdf_page_content",
        lambda *args, **kwargs: {"status": "UNAVAILABLE", "reason": "extractor unavailable", "pages": [], "near_blank_pages": []},
    )
    unavailable = verify_document(
        source,
        visual_reviewed=True,
        visual_review_token=reuse_token,
        reuse_render_report=report_path,
    )
    assert unavailable["visual_status"] == "REVIEW_REQUIRED"
    assert unavailable["manual_review_required"] is True
    assert unavailable["overall_status"] == "INCOMPLETE"
    assert any(i["code"] == "page_content_audit_unavailable" for i in unavailable["issues"])
    assert not any(i["code"] == "near_blank_rendered_pages" for i in unavailable["issues"])
    assert "visual_review_attestation" not in unavailable
    monkeypatch.setattr(
        "wordassistant.document.verify.audit_pdf_page_content",
        lambda *args, **kwargs: {"status": "PASS", "pages": [{"page": 1, "near_blank": False}], "near_blank_pages": []},
    )

    wrong_count_report = json.loads(report_path.read_text(encoding="utf-8"))
    wrong_count_report["render"]["page_count"] = 2
    report_path.write_text(json.dumps(wrong_count_report), encoding="utf-8")
    wrong_count = verify_document(
        source,
        visual_reviewed=True,
        visual_review_token=reuse_token,
        reuse_render_report=report_path,
    )
    assert wrong_count["render_status"] == "FAIL"
    assert wrong_count["visual_status"] == "FAIL"
    report_path.write_text(json.dumps(first), encoding="utf-8")

    bad_token = verify_document(
        source,
        visual_reviewed=True,
        visual_review_token="wa-visual-reuse-v1:wrong",
        reuse_render_report=report_path,
    )
    assert bad_token["delivery_status"] == "FAIL"

    altered_report = json.loads(report_path.read_text(encoding="utf-8"))
    altered_report["render_reuse_manifest"]["version"] = 99
    report_path.write_text(json.dumps(altered_report), encoding="utf-8")
    bad_schema = verify_document(
        source,
        visual_reviewed=True,
        visual_review_token=reuse_token,
        reuse_render_report=report_path,
    )
    assert bad_schema["visual_status"] == "FAIL"
    report_path.write_text(json.dumps(first), encoding="utf-8")

    page.write_bytes(b"changed")
    changed = verify_document(
        source,
        visual_reviewed=True,
        visual_review_token=reuse_token,
        reuse_render_report=report_path,
    )
    assert changed["render_status"] == "FAIL"
    assert changed["visual_status"] == "FAIL"
