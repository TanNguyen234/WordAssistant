import subprocess

import pytest

from wordassistant.backends.word_native import backend as native_backend


def test_timeout_cleanup_has_a_bounded_fallback(monkeypatch):
    class Process:
        pid = 123
        returncode = None

        def __init__(self):
            self.calls = 0
            self.killed = False

        def communicate(self, *args, **kwargs):
            self.calls += 1
            if self.calls <= 2:
                raise subprocess.TimeoutExpired("worker", kwargs.get("timeout", 1))
            return "", ""

        def kill(self):
            self.killed = True

    process = Process()
    monkeypatch.setattr(native_backend.subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(native_backend.subprocess, "run", lambda *args, **kwargs: None)
    monkeypatch.setattr(native_backend.platform, "system", lambda: "Windows")

    with pytest.raises(TimeoutError, match="exceeded"):
        native_backend._run_native_worker({}, 1)

    assert process.killed is True
    assert process.calls == 3


def test_timeout_is_normalized_when_cleanup_confirmation_never_returns(monkeypatch):
    class Process:
        pid = 12345
        returncode = None

        def __init__(self):
            self.kill_calls = 0

        def communicate(self, *args, **kwargs):
            raise subprocess.TimeoutExpired("worker", kwargs.get("timeout", 1))

        def kill(self):
            self.kill_calls += 1

    process = Process()
    monkeypatch.setattr(native_backend.subprocess, "Popen", lambda *a, **k: process)
    monkeypatch.setattr(
        native_backend.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(
            subprocess.TimeoutExpired("taskkill", 5)
        ),
    )
    monkeypatch.setattr(native_backend.platform, "system", lambda: "Windows")

    with pytest.raises(TimeoutError, match="exceeded"):
        native_backend._run_native_worker({"action": "health"}, 1)

    assert process.kill_calls >= 1
