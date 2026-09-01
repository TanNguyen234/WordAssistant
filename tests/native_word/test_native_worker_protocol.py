from __future__ import annotations

import io
import json

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
