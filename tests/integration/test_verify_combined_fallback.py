import json
from pathlib import Path

from docx import Document

from wordassistant.document.render import RenderResult
from wordassistant.document.verify import verify_document
from wordassistant.operations.fields import append_field


def _field_payload():
    return {
        "fields": [{"type": 1, "instruction": "PAGE", "result": "1", "locked": False}],
        "source_results_were_current": True,
    }


def _run_with_render_failure(
    tmp_path, monkeypatch, *, worker_failure=False, fallback_failure=False,
    field_failure=False,
):
    source = tmp_path / "report.docx"
    doc = Document()
    append_field(doc.add_paragraph("Page "), "PAGE", "1")
    doc.save(source)
    page = tmp_path / "page-1.png"
    page.write_bytes(b"png")
    fallback_pdf = tmp_path / "fallback.pdf"
    fallback_pdf.write_bytes(b"%PDF-fallback")

    if worker_failure:
        completed = type("Completed", (), {
            "returncode": 1,
            "stdout": json.dumps({"status": "ERROR", "message": "worker launch failed"}),
            "stderr": "",
        })()
    else:
        def fake_worker(payload, timeout):
            Path(payload["output_path"]).write_bytes(b"%PDF-private")
            fields = (
                {"status": "ERROR", "message": "Word field update failed"}
                if field_failure
                else {"status": "SUCCESS", "data": _field_payload()}
            )
            return type("Completed", (), {
                "returncode": 0,
                "stdout": json.dumps({"status": "SUCCESS", "data": {
                    "render": {"status": "ERROR", "message": "Word export failed"},
                    "fields": fields,
                }}),
                "stderr": "",
            })()

        completed = None
        monkeypatch.setattr(
            "wordassistant.backends.word_native.backend._run_native_worker", fake_worker
        )

    if worker_failure:
        monkeypatch.setattr(
            "wordassistant.backends.word_native.backend._run_native_worker",
            lambda *args, **kwargs: completed,
        )

    def fallback(*args, **kwargs):
        if fallback_failure:
            raise RuntimeError("LibreOffice fallback failed")
        return RenderResult(fallback_pdf, fallback_pdf.stat().st_size, "libreoffice", 1)

    monkeypatch.setattr(
        "wordassistant.document.verify._render_via_execution_service", fallback
    )
    monkeypatch.setattr(
        "wordassistant.document.verify.render_pdf_pages", lambda *args, **kwargs: (page,)
    )
    monkeypatch.setattr(
        "wordassistant.document.verify._pdf_page_count", lambda _: 1
    )
    monkeypatch.setattr(
        "wordassistant.document.verify.audit_pdf_page_content",
        lambda *args, **kwargs: {
            "status": "PASS",
            "pages": [{"page": 1, "near_blank": False}],
            "near_blank_pages": [],
        },
    )
    return verify_document(source, render=True, native_fields=True)


def test_combined_render_stage_error_is_reported_when_fallback_succeeds(
    tmp_path, monkeypatch
):
    report = _run_with_render_failure(tmp_path, monkeypatch)

    assert report["render_status"] == "PASS"
    assert report["render"]["engine"] == "libreoffice"
    assert report["field_evaluation_status"] == "PASS"
    warning = next(issue for issue in report["issues"] if issue["code"] == "native_render_fallback")
    assert "Word export failed" in warning["message"]


def test_combined_worker_failure_and_fallback_failure_are_both_reported(
    tmp_path, monkeypatch
):
    report = _run_with_render_failure(
        tmp_path, monkeypatch, worker_failure=True, fallback_failure=True
    )

    assert report["render_status"] == "FAIL"
    assert report["field_evaluation_status"] == "FAIL"
    warning = next(issue for issue in report["issues"] if issue["code"] == "native_render_fallback")
    fallback_error = next(issue for issue in report["issues"] if issue["code"] == "render_failed")
    assert "worker launch failed" in warning["message"]
    assert "LibreOffice fallback failed" in fallback_error["message"]


def test_combined_render_reason_survives_simultaneous_field_failure(
    tmp_path, monkeypatch
):
    report = _run_with_render_failure(tmp_path, monkeypatch, field_failure=True)

    assert report["render_status"] == "PASS"
    assert report["field_evaluation_status"] == "FAIL"
    warning = next(issue for issue in report["issues"] if issue["code"] == "native_render_fallback")
    assert "Word export failed" in warning["message"]
    assert "Word field update failed" not in warning["message"]
