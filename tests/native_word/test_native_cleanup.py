from pathlib import Path
import csv
import io
import json
import platform
import subprocess
import time

import pytest

from wordassistant.backends.word_native.backend import (
    WordNativeBackend,
    _run_native_worker,
    _word_process_id,
)
from wordassistant.operations.models import OperationRequest


class _Fields:
    def __init__(self, fail=False):
        self.fail = fail
        self.updated = False

    def Update(self):
        if self.fail:
            raise RuntimeError("field update failed")
        self.updated = True

    @property
    def Count(self):
        return 0


class _Updatable:
    def __init__(self):
        self.updated = False

    def Update(self):
        self.updated = True


class _Collection:
    def __init__(self, *items):
        self.items = list(items)

    @property
    def Count(self):
        return len(self.items)

    def __call__(self, index):
        return self.items[index - 1]


class _Document:
    def __init__(self, fail=False):
        self.Fields = _Fields(fail)
        self.closed = False
        self.saved_as = None
        self.repaginated = False
        self.toc = _Updatable()
        self.tof = _Updatable()
        self.TablesOfContents = _Collection(self.toc)
        self.TablesOfFigures = _Collection(self.tof)
        self.exported = None

    def Repaginate(self):
        self.repaginated = True

    def SaveAs2(self, path):
        self.saved_as = path

    def Close(self, **kwargs):
        self.closed = True

    def ExportAsFixedFormat(self, path, format_code):
        self.exported = (path, format_code)

    def ComputeStatistics(self, statistic):
        assert statistic == 2
        return 1


class _Documents:
    def __init__(self, document):
        self.document = document

    def Open(self, path, **kwargs):
        return self.document


class _App:
    def __init__(self, document):
        self.Documents = _Documents(document)
        self.quit_called = False
        self.Visible = None
        self.DisplayAlerts = None

    def Quit(self):
        self.quit_called = True


def _backend(document):
    app = _App(document)
    return WordNativeBackend(
        com_factory=lambda: app,
        platform_name="Windows",
        word_executable=Path("C:/WINWORD.EXE"),
    ), app


def test_native_field_update_saves_output_and_releases_word(tmp_path):
    document = _Document()
    backend, app = _backend(document)
    request = OperationRequest(
        "field.update_all",
        input_path=tmp_path / "source.docx",
        output_path=tmp_path / "output.docx",
    )

    result = backend.execute(request)

    assert document.Fields.updated is True
    assert document.repaginated is True
    assert document.toc.updated is True
    assert document.tof.updated is True
    assert document.saved_as == str((tmp_path / "output.docx").resolve())
    assert document.closed is True
    assert app.quit_called is True


def test_native_pdf_export_does_not_save_docx_over_pdf(tmp_path):
    document = _Document()
    backend, app = _backend(document)
    output = tmp_path / "output.pdf"

    result = backend.execute(
        OperationRequest(
            "render.pdf",
            input_path=tmp_path / "source.docx",
            output_path=output,
        )
    )

    assert document.exported == (str(output.resolve()), 17)
    assert document.saved_as is None
    assert result.output_path == output.resolve()
    assert document.closed is True
    assert app.quit_called is True
    assert result.backend_used == "word-native"


def test_native_backend_quits_word_when_document_operation_raises(tmp_path):
    document = _Document(fail=True)
    backend, app = _backend(document)

    with pytest.raises(RuntimeError, match="field update failed"):
        backend.execute(
            OperationRequest(
                "field.update_all",
                input_path=tmp_path / "source.docx",
                output_path=tmp_path / "output.docx",
            )
        )

    assert document.closed is True
    assert app.quit_called is True


def test_native_dry_run_does_not_launch_word_or_create_output(tmp_path):
    source = tmp_path / "source.docx"
    source.write_bytes(b"original")
    output = tmp_path / "output.docx"
    launched = False

    def factory():
        nonlocal launched
        launched = True
        raise AssertionError("COM must not launch for direct backend dry-run")

    backend = WordNativeBackend(
        com_factory=factory,
        platform_name="Windows",
        word_executable=Path("C:/WINWORD.EXE"),
    )
    result = backend.execute(
        OperationRequest(
            "comment.create",
            input_path=source,
            output_path=output,
            options={"text": "review"},
            dry_run=True,
        )
    )

    assert result.status == "DRY_RUN"
    assert launched is False
    assert source.read_bytes() == b"original"
    assert not output.exists()


def _word_process_ids():
    completed = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq WINWORD.EXE", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        check=False,
    )
    result = set()
    for row in csv.reader(io.StringIO(completed.stdout)):
        if len(row) >= 2 and row[0].casefold() == "winword.exe":
            result.add(int(row[1].replace(",", "")))
    return result


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows process-tree gate")
def test_timed_out_worker_cannot_spawn_a_delayed_word_process():
    baseline = _word_process_ids()
    with pytest.raises(TimeoutError):
        _run_native_worker({"action": "health"}, 0.5)

    observed_new = set()
    for _ in range(8):
        time.sleep(1)
        observed_new.update(_word_process_ids() - baseline)

    assert observed_new == set()


def test_unverified_native_operation_cannot_execute(tmp_path):
    backend, _ = _backend(_Document())
    with pytest.raises(KeyError, match="Unverified"):
        backend.execute(
            OperationRequest(
                "mail-merge.execute",
                input_path=tmp_path / "source.docx",
                output_path=tmp_path / "output.docx",
            )
        )


def test_worker_timeout_kills_only_handed_off_word_pid(monkeypatch):
    run_calls = []
    popen_options = {}

    class _TimedOutWorker:
        pid = 4100
        returncode = -9

        def communicate(self, input_data=None, timeout=None):
            if input_data is not None:
                handoff = Path(json.loads(input_data)["owned_word_pid_handoff"])
                handoff.write_text("5200", encoding="ascii")
                raise subprocess.TimeoutExpired(["native-worker"], timeout)
            return "", ""

        def kill(self):
            return None

    def fake_popen(command, **kwargs):
        popen_options.update(kwargs)
        return _TimedOutWorker()

    def fake_run(command, **kwargs):
        run_calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        "wordassistant.backends.word_native.backend.subprocess.Popen", fake_popen
    )
    monkeypatch.setattr(
        "wordassistant.backends.word_native.backend.subprocess.run", fake_run
    )
    monkeypatch.setattr(
        "wordassistant.backends.word_native.backend._WindowsKillOnCloseJob.for_process",
        lambda process: None,
    )

    with pytest.raises(TimeoutError):
        _run_native_worker({"action": "health", "label": "Tiếng Việt"}, 1)

    assert popen_options["encoding"] == "utf-8"
    assert popen_options["errors"] == "strict"
    assert run_calls == [["taskkill", "/PID", "5200", "/F"]]


def test_word_pid_uses_exact_unique_caption_and_restores_it(monkeypatch):
    class _CaptionOnlyApplication:
        Caption = "Microsoft Word"

        @property
        def Hwnd(self):
            raise AttributeError("Word.Application.Hwnd")

    application = _CaptionOnlyApplication()
    observed_captions = []

    def exact_caption_lookup(caption):
        observed_captions.append(caption)
        assert caption.startswith("WordAssistant-")
        assert application.Caption == caption
        return 5200

    monkeypatch.setattr(
        "wordassistant.backends.word_native.backend.platform.system", lambda: "Windows"
    )
    monkeypatch.setattr(
        "wordassistant.backends.word_native.backend._process_id_for_exact_word_caption",
        exact_caption_lookup,
    )

    assert _word_process_id(application) == 5200
    assert len(observed_captions) == 1
    assert application.Caption == "Microsoft Word"
