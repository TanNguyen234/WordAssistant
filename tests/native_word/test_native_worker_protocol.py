from __future__ import annotations

import io
import json
from contextlib import contextmanager
from pathlib import Path

from wordassistant.backends.word_native import worker


class _SavedDocument:
    def __init__(self):
        self.Saved = False
        self.save_calls = 0

    def Save(self):
        self.save_calls += 1
        self.Saved = True


def test_owned_word_pid_handoff_is_utf8_safe_and_atomic(tmp_path):
    destination = tmp_path / "owned-word.pid"

    worker._write_owned_word_pid_handoff(destination, 5200)

    assert destination.read_text(encoding="utf-8") == "5200"
    assert not list(tmp_path.glob("*.tmp"))


def test_verify_fields_save_reports_persisted_state():
    document = _SavedDocument()
    data = {"field_results_freshness": "UPDATED_NATIVE"}

    result = worker._persist_verified_fields(document, data)

    assert document.save_calls == 1
    assert result["document_saved_after_evaluation"] is True


def test_worker_json_output_preserves_vietnamese(monkeypatch):
    output = io.StringIO()
    monkeypatch.setattr(worker.sys, "stdout", output)

    worker._emit_json({"status": "ERROR", "message": "Lỗi tiếng Việt"})

    assert json.loads(output.getvalue())["message"] == "Lỗi tiếng Việt"
    assert "Lỗi tiếng Việt" in output.getvalue()


def _run_combined_worker(monkeypatch, tmp_path, *, fail_stage=None):
    events = []
    output = io.StringIO()
    source = tmp_path / "private.docx"
    source.write_bytes(b"private-source")
    destination = tmp_path / "private.pdf"

    class Document(_SavedDocument):
        pass

    document = Document()

    class Backend:
        verified_operations = {"render.pdf", "field.update_all"}

        def __init__(self, **kwargs):
            pass

        @contextmanager
        def _session(self, path):
            events.append("open")
            try:
                yield object(), document
            finally:
                events.append("close")

        def _field_snapshot(self, doc):
            events.append("snapshot")
            return [{"type": 1, "instruction": "PAGE", "result": "1", "locked": False}]

        def _execute_document_operation(self, app, doc, request):
            events.append(request.name)
            if request.name == "render.pdf":
                if fail_stage == "render":
                    raise RuntimeError("render stage error")
                Path(request.output_path).write_bytes(b"%PDF-test")
                return {"page_count": 1}
            if fail_stage == "fields":
                raise RuntimeError("field stage error")
            return {"fields": [{"type": 1, "instruction": "PAGE", "result": "1", "locked": False}]}

    monkeypatch.setattr(worker, "WordNativeBackend", Backend)
    monkeypatch.setattr(worker.sys, "stdin", io.StringIO(json.dumps({
        "action": "verify_fields_and_render",
        "input_path": str(source),
        "output_path": str(destination),
    })))
    monkeypatch.setattr(worker.sys, "stdout", output)
    assert worker.main() == 0
    return json.loads(output.getvalue()), events, document, destination


def test_combined_worker_uses_one_session_and_exports_before_update(monkeypatch, tmp_path):
    payload, events, document, pdf = _run_combined_worker(monkeypatch, tmp_path)

    assert payload["status"] == "SUCCESS"
    assert payload["data"]["render"]["status"] == "SUCCESS"
    assert payload["data"]["fields"]["status"] == "SUCCESS"
    assert events == ["open", "snapshot", "render.pdf", "field.update_all", "close"]
    assert document.save_calls == 1
    assert pdf.read_bytes().startswith(b"%PDF")


def test_combined_worker_keeps_independent_stage_failures(monkeypatch, tmp_path):
    payload, events, document, pdf = _run_combined_worker(
        monkeypatch, tmp_path, fail_stage="render"
    )
    assert payload["data"]["render"]["status"] == "ERROR"
    assert payload["data"]["fields"]["status"] == "SUCCESS"
    assert "field.update_all" in events
    assert document.save_calls == 1
    assert not pdf.exists()

    payload, events, document, pdf = _run_combined_worker(
        monkeypatch, tmp_path, fail_stage="fields"
    )
    assert payload["data"]["render"]["status"] == "SUCCESS"
    assert payload["data"]["fields"]["status"] == "ERROR"
    assert pdf.exists()
    assert document.save_calls == 0
