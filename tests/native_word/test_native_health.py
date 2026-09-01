from pathlib import Path
import subprocess

from wordassistant.backends.word_native.backend import WordNativeBackend
from wordassistant.operations.models import OperationRequest


class _Documents:
    def Open(self, path, **kwargs):
        raise AssertionError("health probe must not open a document")


class _App:
    def __init__(self):
        self.Documents = _Documents()
        self.quit_called = False
        self.Visible = None
        self.DisplayAlerts = None

    def Quit(self):
        self.quit_called = True


def test_native_health_launches_invisibly_and_quits():
    app = _App()
    backend = WordNativeBackend(
        com_factory=lambda: app,
        platform_name="Windows",
        word_executable=Path("C:/Program Files/Microsoft Office/WINWORD.EXE"),
    )

    health = backend.health()

    assert health.available is True and health.operational is True
    assert app.Visible is False
    assert app.DisplayAlerts == 0
    assert app.quit_called is True


def test_native_health_is_unavailable_off_windows():
    backend = WordNativeBackend(com_factory=lambda: _App(), platform_name="Linux")

    health = backend.health()

    assert health.available is False
    assert health.operational is False
    assert "Windows" in health.reason


def test_default_native_health_uses_isolated_worker_and_contains_com_disconnect(tmp_path):
    calls = []

    def worker(payload, timeout):
        calls.append((payload, timeout))
        return subprocess.CompletedProcess(
            args=["native-worker"],
            returncode=0,
            stdout='{"status":"SUCCESS","word_version":"15.0"}\n',
            stderr="Windows fatal exception: code 0x80010108\n",
        )

    backend = WordNativeBackend(
        worker_runner=worker,
        platform_name="Windows",
        word_executable=Path("C:/WINWORD.EXE"),
    )

    health = backend.health()

    assert calls[0][0] == {"action": "health"}
    assert health.operational is True
    assert health.details["isolated"] is True
    assert "0x80010108" in health.details["worker_warning"]


def test_isolated_execution_retries_one_transient_word_launch_failure(tmp_path, monkeypatch):
    calls = []

    def worker(payload, timeout):
        calls.append(payload)
        if len(calls) == 1:
            return subprocess.CompletedProcess(
                ["worker"], 1, '{"status":"ERROR","message":"Server execution failed"}\n', ""
            )
        return subprocess.CompletedProcess(
            ["worker"],
            0,
            '{"status":"SUCCESS","operation":"comment.list","backend_used":"word-native","fidelity":"native","output_path":null,"warnings":[],"manual_review_required":false,"data":{"comments":[]}}\n',
            "",
        )

    monkeypatch.setattr("wordassistant.backends.word_native.backend.time.sleep", lambda _: None)
    backend = WordNativeBackend(
        worker_runner=worker,
        platform_name="Windows",
        word_executable=Path("C:/WINWORD.EXE"),
    )

    result = backend.execute(
        OperationRequest("comment.list", input_path=tmp_path / "input.docx")
    )

    assert len(calls) == 2
    assert result.data["comments"] == []
