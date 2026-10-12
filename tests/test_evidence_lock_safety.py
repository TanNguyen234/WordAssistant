import ctypes
import json
from unittest.mock import Mock

import pytest

from wordassistant.evidence import registry


def _forbid_kill(monkeypatch):
    calls = []

    def forbidden(*args):
        calls.append(args)
        raise AssertionError("Process signaling is forbidden in Windows lock tests")

    monkeypatch.setattr(registry.os, "kill", forbidden)
    return calls


@pytest.mark.parametrize("exit_code, alive", [(259, True), (0, False)])
def test_windows_liveness_queries_kernel_without_signaling(monkeypatch, exit_code, alive):
    calls = _forbid_kill(monkeypatch)
    kernel = Mock()
    kernel.OpenProcess.return_value = 123

    def exit_status(handle, code_pointer):
        code_pointer._obj.value = exit_code
        return 1

    kernel.GetExitCodeProcess.side_effect = exit_status
    monkeypatch.setattr(ctypes, "WinDLL", Mock(return_value=kernel), raising=False)
    assert registry._windows_process_alive(321) is alive
    kernel.OpenProcess.assert_called_once_with(0x1000, False, 321)
    kernel.CloseHandle.assert_called_once_with(123)
    assert calls == []


@pytest.mark.parametrize("error, alive", [(87, False), (5, None)])
def test_windows_inaccessible_or_missing_process_is_conservative(monkeypatch, error, alive):
    calls = _forbid_kill(monkeypatch)
    kernel = Mock()
    kernel.OpenProcess.return_value = 0
    monkeypatch.setattr(ctypes, "WinDLL", Mock(return_value=kernel), raising=False)
    monkeypatch.setattr(ctypes, "get_last_error", lambda: error, raising=False)
    assert registry._windows_process_alive(321) is alive
    kernel.CloseHandle.assert_not_called()
    assert calls == []


def test_windows_dispatch_never_signals_process(monkeypatch):
    calls = _forbid_kill(monkeypatch)
    monkeypatch.setattr(registry.sys, "platform", "win32")
    query = Mock(return_value=True)
    monkeypatch.setattr(registry, "_windows_process_alive", query)
    assert registry._process_alive(321) is True
    query.assert_called_once_with(321)
    assert calls == []


def test_windows_exit_query_failure_keeps_unknown_state_and_closes_handle(monkeypatch):
    calls = _forbid_kill(monkeypatch)
    kernel = Mock()
    kernel.OpenProcess.return_value = 123
    kernel.GetExitCodeProcess.return_value = 0
    monkeypatch.setattr(ctypes, "WinDLL", Mock(return_value=kernel), raising=False)
    assert registry._windows_process_alive(321) is None
    kernel.CloseHandle.assert_called_once_with(123)
    assert calls == []


@pytest.mark.parametrize("alive", [True, None])
def test_timeout_preserves_old_live_or_unknown_owner_lock(tmp_path, monkeypatch, alive):
    calls = _forbid_kill(monkeypatch)
    monkeypatch.setattr(registry, "_process_alive", lambda pid: alive, raising=False)
    path = tmp_path / "evidence.json"
    lock = tmp_path / "evidence.json.lock"
    original = json.dumps({"pid": 321, "ts": 0})
    lock.write_text(original)
    with pytest.raises(registry.EvidenceError, match="lock|timed out"):
        with registry._file_lock(path, timeout=0):
            pytest.fail("A live or unknown owner lock must not be acquired")
    assert lock.read_text() == original
    assert calls == []


def test_dead_owner_lock_can_be_recovered(tmp_path, monkeypatch):
    calls = _forbid_kill(monkeypatch)
    monkeypatch.setattr(registry, "_process_alive", lambda pid: False, raising=False)
    path = tmp_path / "evidence.json"
    lock = tmp_path / "evidence.json.lock"
    lock.write_text(json.dumps({"pid": 321, "ts": 0}))
    with registry._file_lock(path, timeout=0):
        assert json.loads(lock.read_text())["pid"] == registry.os.getpid()
    assert not lock.exists()
    assert calls == []


def test_malformed_lock_owner_times_out_without_deleting(tmp_path, monkeypatch):
    calls = _forbid_kill(monkeypatch)
    path = tmp_path / "evidence.json"
    lock = tmp_path / "evidence.json.lock"
    lock.write_text("not a lock owner")
    with pytest.raises(registry.EvidenceError):
        with registry._file_lock(path, timeout=0):
            pytest.fail("Unknown ownership must fail closed")
    assert lock.read_text() == "not a lock owner"
    assert calls == []


def test_release_preserves_a_different_owner_lock(tmp_path):
    path = tmp_path / "evidence.json"
    lock = tmp_path / "evidence.json.lock"
    replacement = json.dumps({"pid": 123, "ts": 0, "token": "other-owner"})
    with registry._file_lock(path):
        lock.write_text(replacement)
    assert lock.read_text() == replacement


@pytest.mark.parametrize("failure", ["exception", "zero", "partial_exception"])
def test_initialization_write_failure_removes_owned_lock(tmp_path, monkeypatch, failure):
    calls = _forbid_kill(monkeypatch)
    original_write = registry.os.write
    writes = []

    def write(fd, payload):
        writes.append(payload)
        if failure == "partial_exception" and len(writes) == 1:
            return original_write(fd, payload[:5])
        if failure == "zero":
            return 0
        raise OSError("mock write failure")

    monkeypatch.setattr(registry.os, "write", write)
    path = tmp_path / "evidence.json"
    with pytest.raises(OSError):
        with registry._file_lock(path):
            pytest.fail("An incomplete lock must not be acquired")
    assert not (tmp_path / "evidence.json.lock").exists()
    assert calls == []


def test_short_writes_complete_lock_owner_payload(tmp_path, monkeypatch):
    calls = _forbid_kill(monkeypatch)
    original_write = registry.os.write
    monkeypatch.setattr(registry.os, "write", lambda fd, payload: original_write(fd, payload[:5]))
    path = tmp_path / "evidence.json"
    lock = tmp_path / "evidence.json.lock"
    with registry._file_lock(path):
        assert json.loads(lock.read_bytes())["pid"] == registry.os.getpid()
    assert not lock.exists()
    assert calls == []


def test_write_failure_preserves_replacement_owner(tmp_path, monkeypatch):
    calls = _forbid_kill(monkeypatch)
    path = tmp_path / "evidence.json"
    lock = tmp_path / "evidence.json.lock"
    replacement = json.dumps({"pid": 123, "ts": 0, "token": "replacement"})

    def write(fd, payload):
        lock.write_text(replacement)
        raise OSError("mock write failure")

    monkeypatch.setattr(registry.os, "write", write)
    with pytest.raises(OSError):
        with registry._file_lock(path):
            pytest.fail("Write must fail")
    assert lock.read_text() == replacement
    assert calls == []
