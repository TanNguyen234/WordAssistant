from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Callable
import uuid

from ..base import BackendHealth, OperationBackend
from ...operations.models import Fidelity, OperationRequest, OperationResult


class _WindowsKillOnCloseJob:
    """Own a Windows Job Object that terminates assigned processes on close."""

    def __init__(self, handle, kernel32):
        self.handle = handle
        self.kernel32 = kernel32

    @classmethod
    def for_application(cls, application):
        if platform.system() != "Windows":
            return None
        try:
            import ctypes
            from ctypes import wintypes

            class BasicLimit(ctypes.Structure):
                _fields_ = [
                    ("PerProcessUserTimeLimit", ctypes.c_longlong),
                    ("PerJobUserTimeLimit", ctypes.c_longlong),
                    ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t),
                    ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD),
                ]

            class IoCounters(ctypes.Structure):
                _fields_ = [(name, ctypes.c_ulonglong) for name in (
                    "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                    "ReadTransferCount", "WriteTransferCount", "OtherTransferCount",
                )]

            class ExtendedLimit(ctypes.Structure):
                _fields_ = [
                    ("BasicLimitInformation", BasicLimit),
                    ("IoInfo", IoCounters),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t),
                ]

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            kernel32.CreateJobObjectW.restype = wintypes.HANDLE
            kernel32.OpenProcess.restype = wintypes.HANDLE
            handle = kernel32.CreateJobObjectW(None, None)
            if not handle:
                return None
            info = ExtendedLimit()
            info.BasicLimitInformation.LimitFlags = 0x00002000
            if not kernel32.SetInformationJobObject(
                handle, 9, ctypes.byref(info), ctypes.sizeof(info)
            ):
                kernel32.CloseHandle(handle)
                return None
            process_id = wintypes.DWORD()
            user32.GetWindowThreadProcessId(
                int(application.Hwnd), ctypes.byref(process_id)
            )
            process_handle = kernel32.OpenProcess(
                0x0001 | 0x0100 | 0x0400, False, process_id.value
            )
            if not process_handle:
                kernel32.CloseHandle(handle)
                return None
            try:
                if not kernel32.AssignProcessToJobObject(handle, process_handle):
                    kernel32.CloseHandle(handle)
                    return None
            finally:
                kernel32.CloseHandle(process_handle)
            return cls(handle, kernel32)
        except Exception:
            return None

    @classmethod
    def for_process(cls, process):
        if platform.system() != "Windows" or not hasattr(process, "_handle"):
            return None
        try:
            import ctypes
            from ctypes import wintypes

            class BasicLimit(ctypes.Structure):
                _fields_ = [
                    ("PerProcessUserTimeLimit", ctypes.c_longlong),
                    ("PerJobUserTimeLimit", ctypes.c_longlong),
                    ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t),
                    ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD),
                ]

            class IoCounters(ctypes.Structure):
                _fields_ = [
                    (name, ctypes.c_ulonglong)
                    for name in (
                        "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                        "ReadTransferCount", "WriteTransferCount", "OtherTransferCount",
                    )
                ]

            class ExtendedLimit(ctypes.Structure):
                _fields_ = [
                    ("BasicLimitInformation", BasicLimit),
                    ("IoInfo", IoCounters),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t),
                ]

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CreateJobObjectW.restype = wintypes.HANDLE
            handle = kernel32.CreateJobObjectW(None, None)
            if not handle:
                return None
            info = ExtendedLimit()
            info.BasicLimitInformation.LimitFlags = 0x00002000
            if not kernel32.SetInformationJobObject(
                handle, 9, ctypes.byref(info), ctypes.sizeof(info)
            ) or not kernel32.AssignProcessToJobObject(
                handle, wintypes.HANDLE(int(process._handle))
            ):
                kernel32.CloseHandle(handle)
                return None
            return cls(handle, kernel32)
        except Exception:
            return None

    def close(self):
        if self.handle:
            self.kernel32.CloseHandle(self.handle)
            self.handle = None


NATIVE_OPERATIONS = {
    "field.update_all",
    "comment.create",
    "comment.list",
    "comment.reply",
    "comment.resolve",
    "comment.reopen",
    "comment.delete",
    "revision.enable",
    "revision.disable",
    "revision.list",
    "revision.accept",
    "revision.reject",
    "revision.accept_all",
    "revision.reject_all",
    "compare.documents",
    "merge.documents",
    "protect.native",
    "render.pdf",
    "mail-merge.execute",
    "chart.insert",
}

# Capability discovery may advertise only operations covered by committed
# live-Word integration tests. Callable but unverified paths remain hidden.
VERIFIED_NATIVE_OPERATIONS = {
    "field.update_all",
    "render.pdf",
    "comment.create",
    "comment.list",
    "comment.delete",
    "revision.enable",
    "revision.disable",
    "revision.list",
    "revision.accept_all",
    "compare.documents",
}


def _discover_word_executable() -> Path | None:
    executable = shutil.which("WINWORD.EXE") or shutil.which("winword")
    if executable:
        return Path(executable)
    candidates = [
        Path(r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"),
        Path(r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE"),
        Path(r"C:\Program Files\Microsoft Office\Office15\WINWORD.EXE"),
        Path(r"C:\Program Files (x86)\Microsoft Office\Office15\WINWORD.EXE"),
    ]
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def _default_com_factory():
    try:
        from win32com.client import DispatchEx  # type: ignore
    except ImportError as exc:
        raise RuntimeError("pywin32 is not installed") from exc
    return DispatchEx("Word.Application")


def _initialize_com_runtime():
    import pythoncom  # type: ignore

    pythoncom.CoInitialize()
    return pythoncom


def _process_id_for_exact_word_caption(caption: str) -> int | None:
    if platform.system() != "Windows":
        return None
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    matches: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def inspect_window(window_handle, _):
        title_length = user32.GetWindowTextLengthW(window_handle)
        title = ctypes.create_unicode_buffer(title_length + 1)
        user32.GetWindowTextW(window_handle, title, title_length + 1)
        if title.value != caption:
            return True
        class_name = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(window_handle, class_name, len(class_name))
        if class_name.value != "OpusApp":
            return True
        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(window_handle, ctypes.byref(process_id))
        if process_id.value:
            matches.append(int(process_id.value))
        return True

    user32.EnumWindows(inspect_window, 0)
    return matches[0] if len(matches) == 1 else None


def _word_process_id(application) -> int:
    if platform.system() != "Windows":
        raise RuntimeError("Microsoft Word PID discovery requires Windows")
    try:
        window_handle = int(application.Hwnd)
    except Exception:
        window_handle = 0
    if window_handle:
        import ctypes
        from ctypes import wintypes

        process_id = wintypes.DWORD()
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.GetWindowThreadProcessId(window_handle, ctypes.byref(process_id))
        if process_id.value:
            return int(process_id.value)

    original_caption = str(application.Caption)
    ownership_caption = f"WordAssistant-{uuid.uuid4().hex}"
    try:
        application.Caption = ownership_caption
        for _ in range(20):
            process_id = _process_id_for_exact_word_caption(ownership_caption)
            if process_id is not None:
                return process_id
            time.sleep(0.05)
    finally:
        application.Caption = original_caption
    raise RuntimeError("Microsoft Word did not expose an exact owned process ID")


def _terminate_owned_word_process(process_id: int) -> None:
    if platform.system() != "Windows":
        return
    subprocess.run(
        ["taskkill", "/PID", str(process_id), "/F"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=5,
    )


def _run_native_worker(payload: dict, timeout: int):
    command = [sys.executable, "-m", "wordassistant.backends.word_native.worker"]
    creation_flags = (
        subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
    )
    with tempfile.TemporaryDirectory(prefix="wordassistant-native-") as temp_dir:
        pid_handoff = Path(temp_dir) / "owned-word.pid"
        worker_payload = dict(payload)
        worker_payload["owned_word_pid_handoff"] = str(pid_handoff)
        serialized_payload = json.dumps(worker_payload, ensure_ascii=False)
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="strict",
            creationflags=creation_flags,
        )
        try:
            stdout, stderr = process.communicate(serialized_payload, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            owned_word_pid = None
            try:
                owned_word_pid = int(pid_handoff.read_text(encoding="utf-8").strip())
            except (FileNotFoundError, OSError, ValueError):
                pass
            process.kill()
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
            if owned_word_pid is not None:
                _terminate_owned_word_process(owned_word_pid)
            raise TimeoutError(f"Word-native worker exceeded {timeout} seconds") from exc
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


class WordNativeBackend(OperationBackend):
    name = "word-native"
    fidelity = Fidelity.NATIVE
    verified_operations = VERIFIED_NATIVE_OPERATIONS

    def __init__(
        self,
        *,
        com_factory: Callable[[], object] | None = None,
        worker_runner: Callable[[dict, int], subprocess.CompletedProcess] | None = None,
        timeout_seconds: int = 60,
        platform_name: str | None = None,
        word_executable: Path | None = None,
        owned_word_pid_callback: Callable[[int], None] | None = None,
    ) -> None:
        self._in_process = com_factory is not None
        self.com_factory = com_factory or _default_com_factory
        self._manages_com_runtime = com_factory is None or com_factory is _default_com_factory
        self.worker_runner = worker_runner or _run_native_worker
        self.timeout_seconds = timeout_seconds
        self.platform_name = platform_name or platform.system()
        self.word_executable = word_executable if word_executable is not None else _discover_word_executable()
        self.owned_word_pid_callback = owned_word_pid_callback
        self._health: BackendHealth | None = None

    def supports(self, operation: str) -> bool:
        return operation in self.verified_operations

    def _configure_application(self, application) -> None:
        application.Visible = False
        application.DisplayAlerts = 0
        if self.owned_word_pid_callback is not None:
            self.owned_word_pid_callback(_word_process_id(application))

    def health(self) -> BackendHealth:
        if self._health is not None:
            return self._health
        if self.platform_name != "Windows":
            self._health = BackendHealth(self.name, False, False, "Microsoft Word automation requires Windows")
            return self._health
        if self.word_executable is None:
            self._health = BackendHealth(self.name, False, False, "Microsoft Word executable was not found")
            return self._health
        if not self._in_process:
            try:
                completed = self.worker_runner({"action": "health"}, self.timeout_seconds)
                lines = [line for line in completed.stdout.splitlines() if line.strip()]
                payload = json.loads(lines[-1]) if lines else {}
                operational = completed.returncode == 0 and payload.get("status") == "SUCCESS"
                details = {
                    "executable": str(self.word_executable),
                    "isolated": True,
                    "word_version": payload.get("word_version"),
                }
                if completed.stderr.strip():
                    details["worker_warning"] = completed.stderr.strip()
                self._health = BackendHealth(
                    self.name,
                    True,
                    operational,
                    "Microsoft Word isolated COM launch probe succeeded"
                    if operational
                    else f"Microsoft Word isolated COM launch probe failed: {payload.get('message') or completed.stderr.strip()}",
                    details,
                )
            except Exception as exc:
                self._health = BackendHealth(
                    self.name,
                    True,
                    False,
                    f"Microsoft Word isolated COM launch probe failed: {exc}",
                    {"executable": str(self.word_executable), "isolated": True},
                )
            return self._health

        application = None
        com_runtime = None
        try:
            if self._manages_com_runtime:
                com_runtime = _initialize_com_runtime()
            application = self.com_factory()
            self._configure_application(application)
            self._health = BackendHealth(
                self.name,
                True,
                True,
                "Microsoft Word COM launch probe succeeded",
                {
                    "executable": str(self.word_executable),
                    "word_version": str(getattr(application, "Version", "unknown")),
                },
            )
        except Exception as exc:
            self._health = BackendHealth(
                self.name,
                True,
                False,
                f"Microsoft Word COM launch probe failed: {exc}",
                {"executable": str(self.word_executable)},
            )
        finally:
            if application is not None:
                try:
                    application.Quit()
                except Exception:
                    pass
            if com_runtime is not None:
                com_runtime.CoUninitialize()
        return self._health

    @contextmanager
    def _session(self, input_path: Path):
        application = None
        document = None
        com_runtime = None
        word_job = None
        try:
            if self._manages_com_runtime:
                com_runtime = _initialize_com_runtime()
            application = self.com_factory()
            self._configure_application(application)
            word_job = _WindowsKillOnCloseJob.for_application(application)
            document = application.Documents.Open(
                str(input_path.resolve()), ReadOnly=False, AddToRecentFiles=False
            )
            yield application, document
        finally:
            if document is not None:
                try:
                    document.Close(SaveChanges=0)
                except Exception:
                    pass
            if application is not None:
                try:
                    application.Quit()
                except Exception:
                    pass
            if word_job is not None:
                word_job.close()
            if com_runtime is not None:
                com_runtime.CoUninitialize()

    @staticmethod
    def _save(document, request: OperationRequest) -> Path:
        destination = (request.output_path or request.input_path).resolve()
        if request.transaction_staging:
            document.Save()
        else:
            document.SaveAs2(str(destination))
        return destination

    def execute(self, request: OperationRequest) -> OperationResult:
        if request.name not in self.verified_operations:
            raise KeyError(f"Unverified Word-native operation is disabled: {request.name}")
        if request.input_path is None:
            raise ValueError(f"{request.name} requires input_path")
        mutating = request.name not in {"comment.list", "revision.list", "render.pdf"}
        if request.dry_run:
            return OperationResult(
                status="DRY_RUN",
                operation=request.name,
                backend_used=self.name,
                fidelity=Fidelity.NATIVE,
                output_path=None,
                data={"planned_output": str(request.output_path) if request.output_path else None},
            )
        if mutating and not request.transaction_staging and (
            request.output_path is None
            or request.output_path.resolve() == request.input_path.resolve()
        ):
            raise ValueError(
                f"{request.name} requires a distinct output path; in-place mutation is disabled"
            )
        if not self._in_process:
            return self._execute_isolated(request)
        if request.name in {"compare.documents", "merge.documents"}:
            return self._compare_or_merge(request)

        with self._session(request.input_path) as (application, document):
            data = self._execute_document_operation(application, document, request)
            output = None
            if request.name == "render.pdf":
                output = Path(data["pdf"]).resolve()
            elif request.name not in {"comment.list", "revision.list"}:
                output = self._save(document, request)
            return OperationResult.success(
                request.name,
                self.name,
                Fidelity.NATIVE,
                data,
                output_path=output,
            )

    def _execute_isolated(self, request: OperationRequest) -> OperationResult:
        requested_timeout = request.options.get("timeout_seconds", self.timeout_seconds)
        if isinstance(requested_timeout, bool):
            raise ValueError("timeout_seconds must be an integer between 1 and 3600")
        try:
            operation_timeout = int(requested_timeout)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "timeout_seconds must be an integer between 1 and 3600"
            ) from exc
        if not 1 <= operation_timeout <= 3600:
            raise ValueError("timeout_seconds must be an integer between 1 and 3600")
        worker_payload = {
            "action": "execute",
            "request": {
                "name": request.name,
                "input_path": str(request.input_path) if request.input_path else None,
                "output_path": str(request.output_path) if request.output_path else None,
                "options": dict(request.options),
                "dry_run": request.dry_run,
                "transaction_staging": request.transaction_staging,
            },
        }
        completed = None
        payload = {}
        for attempt in range(2):
            completed = self.worker_runner(worker_payload, operation_timeout)
            lines = [line for line in completed.stdout.splitlines() if line.strip()]
            payload = json.loads(lines[-1]) if lines else {}
            message = payload.get("message") or completed.stderr.strip()
            transient_launch_failure = any(
                marker in str(message).casefold()
                for marker in (
                    "server execution failed",
                    "rpc server is unavailable",
                    "call was rejected by callee",
                )
            )
            if (
                completed.returncode == 0
                and payload.get("status") == "SUCCESS"
            ) or not transient_launch_failure or attempt == 1:
                break
            time.sleep(1)
        assert completed is not None
        if completed.returncode != 0 or payload.get("status") != "SUCCESS":
            message = payload.get("message") or completed.stderr.strip() or "Word-native worker failed"
            raise RuntimeError(message)
        return OperationResult(
            status=payload["status"],
            operation=payload["operation"],
            backend_used=payload["backend_used"],
            fidelity=payload["fidelity"],
            output_path=Path(payload["output_path"]) if payload.get("output_path") else None,
            warnings=[completed.stderr.strip()] if completed.stderr.strip() else list(payload.get("warnings", [])),
            manual_review_required=bool(payload.get("manual_review_required", False)),
            data=dict(payload.get("data", {})),
        )

    @staticmethod
    def _update_collection(collection) -> int:
        if collection is None:
            return 0
        count = int(collection.Count)
        for index in range(1, count + 1):
            collection(index).Update()
        return count

    @staticmethod
    def _update_story_ranges(document) -> int:
        """Update every reachable Word story, including linked text-frame stories."""
        story_ranges = getattr(document, "StoryRanges", None)
        if story_ranges is None:
            return 0
        updated = 0
        # WdStoryType values are sparse but all current Word values fit 1..17.
        for story_type in range(1, 18):
            try:
                story = story_ranges(story_type)
            except Exception:
                continue
            seen = set()
            while story is not None:
                identity = getattr(story, "Start", None), getattr(story, "End", None), story_type
                if identity in seen:
                    break
                seen.add(identity)
                story.Fields.Update()
                updated += 1
                try:
                    story = story.NextStoryRange
                except Exception:
                    story = None
        return updated

    @staticmethod
    def _snapshot_collection(fields, story: str, remaining: int) -> list[dict]:
        if fields is None:
            return []
        snapshot = []
        for index in range(1, min(int(fields.Count), remaining) + 1):
            field = fields(index)
            snapshot.append(
                {
                    "story": story,
                    "type": int(field.Type),
                    "instruction": str(field.Code.Text).strip(),
                    "result": str(field.Result.Text).replace("\r", "").replace("\x07", "").strip(),
                    "locked": bool(getattr(field, "Locked", False)),
                }
            )
        return snapshot

    @classmethod
    def _field_snapshot(cls, document, limit: int = 1000) -> list[dict]:
        snapshot = cls._snapshot_collection(
            getattr(document, "Fields", None), "document", limit
        )
        story_ranges = getattr(document, "StoryRanges", None)
        if story_ranges is None:
            return snapshot
        for story_type in range(2, 18):
            try:
                story = story_ranges(story_type)
            except Exception:
                continue
            seen = set()
            story_index = 0
            while story is not None and len(snapshot) < limit:
                identity = (
                    getattr(story, "Start", None),
                    getattr(story, "End", None),
                    story_type,
                )
                if identity in seen:
                    break
                seen.add(identity)
                snapshot.extend(
                    cls._snapshot_collection(
                        getattr(story, "Fields", None),
                        f"story:{story_type}:{story_index}",
                        limit - len(snapshot),
                    )
                )
                story_index += 1
                try:
                    story = story.NextStoryRange
                except Exception:
                    story = None
        return snapshot

    @staticmethod
    def _stabilize_pagination_fields(document) -> int:
        compute_statistics = getattr(document, "ComputeStatistics", None)
        if not callable(compute_statistics):
            return 0
        total_pages = int(compute_statistics(2))
        updated = 0
        collections = [getattr(document, "Fields", None)]
        story_ranges = getattr(document, "StoryRanges", None)
        if story_ranges is not None:
            for story_type in range(2, 18):
                try:
                    story = story_ranges(story_type)
                except Exception:
                    continue
                seen = set()
                while story is not None:
                    identity = (
                        getattr(story, "Start", None),
                        getattr(story, "End", None),
                        story_type,
                    )
                    if identity in seen:
                        break
                    seen.add(identity)
                    collections.append(getattr(story, "Fields", None))
                    try:
                        story = story.NextStoryRange
                    except Exception:
                        story = None
        for fields in collections:
            if fields is None:
                continue
            for index in range(1, int(fields.Count) + 1):
                field = fields(index)
                instruction = str(field.Code.Text).strip().split()
                if instruction and instruction[0].upper() == "NUMPAGES":
                    field.Update()
                    if str(field.Result.Text).strip() != str(total_pages):
                        field.Result.Text = str(total_pages)
                    updated += 1
        return updated

    def _execute_document_operation(self, application, document, request):
        options = dict(request.options)
        name = request.name
        if name == "field.update_all":
            document.Repaginate()
            document.Fields.Update()
            story_ranges = self._update_story_ranges(document)
            for index in range(1, int(document.Sections.Count) + 1) if hasattr(document, "Sections") else []:
                section = document.Sections(index)
                for story in (section.Headers, section.Footers):
                    for story_index in range(1, int(story.Count) + 1):
                        story(story_index).Range.Fields.Update()
            toc_count = self._update_collection(
                getattr(document, "TablesOfContents", None)
            )
            figure_table_count = self._update_collection(
                getattr(document, "TablesOfFigures", None)
            )
            document.Repaginate()
            document.Fields.Update()
            story_ranges += self._update_story_ranges(document)
            for index in range(1, int(document.Sections.Count) + 1) if hasattr(document, "Sections") else []:
                section = document.Sections(index)
                for story in (section.Headers, section.Footers):
                    for story_index in range(1, int(story.Count) + 1):
                        story(story_index).Range.Fields.Update()
            pagination_fields = self._stabilize_pagination_fields(document)
            fields = self._field_snapshot(document)
            blocked = [
                field
                for field in fields
                if field["locked"] or field["result"].strip().casefold().startswith("error!")
            ]
            if blocked:
                raise ValueError(
                    "Word-native field update left locked or error fields: "
                    + ", ".join(field["instruction"] for field in blocked[:5])
                )
            return {
                "updated": True,
                "repaginated": True,
                "passes": 2,
                "story_ranges_updated": story_ranges,
                "tables_of_contents_updated": toc_count,
                "tables_of_figures_updated": figure_table_count,
                "pagination_fields_stabilized": pagination_fields,
                "fields": fields,
                "field_results_freshness": "UPDATED_NATIVE",
            }
        if name == "comment.create":
            start = int(options.get("start", 0))
            end = int(options.get("end", start))
            comment = document.Comments.Add(document.Range(Start=start, End=end), options["text"])
            if options.get("author"):
                comment.Author = options["author"]
            return {"index": int(comment.Index), "text": options["text"]}
        if name == "comment.list":
            return {
                "comments": [
                    {
                        "index": index,
                        "author": document.Comments(index).Author,
                        "text": document.Comments(index).Range.Text,
                        "date": str(document.Comments(index).Date),
                    }
                    for index in range(1, int(document.Comments.Count) + 1)
                ]
            }
        if name == "comment.delete":
            document.Comments(int(options["index"])).Delete()
            return {"deleted": int(options["index"])}
        if name == "comment.reply":
            comment = document.Comments(int(options["index"]))
            reply = comment.Replies.Add(comment.Scope, options["text"])
            return {"reply_index": int(reply.Index)}
        if name in {"comment.resolve", "comment.reopen"}:
            comment = document.Comments(int(options["index"]))
            comment.Done = name == "comment.resolve"
            return {"index": int(options["index"]), "resolved": bool(comment.Done)}
        if name in {"revision.enable", "revision.disable"}:
            document.TrackRevisions = name == "revision.enable"
            return {"enabled": bool(document.TrackRevisions)}
        if name == "revision.list":
            return {
                "revisions": [
                    {
                        "index": index,
                        "author": document.Revisions(index).Author,
                        "type": int(document.Revisions(index).Type),
                        "text": document.Revisions(index).Range.Text,
                    }
                    for index in range(1, int(document.Revisions.Count) + 1)
                ]
            }
        if name == "revision.accept_all":
            document.AcceptAllRevisions()
            return {"accepted_all": True}
        if name == "revision.reject_all":
            document.RejectAllRevisions()
            return {"rejected_all": True}
        if name in {"revision.accept", "revision.reject"}:
            revision = document.Revisions(int(options["index"]))
            getattr(revision, "Accept" if name.endswith("accept") else "Reject")()
            return {"index": int(options["index"])}
        if name == "protect.native":
            document.Protect(
                Type=int(options["type"]),
                NoReset=True,
                Password=str(options.get("password", "")),
            )
            return {
                "protected": True,
                "password_protected_editing": bool(options.get("password")),
                "secure_encryption": False,
            }
        if name == "render.pdf":
            destination = request.output_path.resolve()
            document.Repaginate()
            page_count = int(document.ComputeStatistics(2))
            document.ExportAsFixedFormat(str(destination), 17)
            return {"pdf": str(destination), "page_count": page_count}
        if name == "mail-merge.execute":
            merge = document.MailMerge
            merge.OpenDataSource(str(Path(options["data_source"]).resolve()))
            merge.Destination = 0
            merge.Execute(Pause=False)
            return {"executed": True}
        if name == "chart.insert":
            chart = document.InlineShapes.AddChart(int(options.get("chart_type", 51))).Chart
            chart.HasTitle = True
            chart.ChartTitle.Text = options.get("title", "Chart")
            return {"inserted": True}
        raise KeyError(name)

    def _compare_or_merge(self, request):
        options = dict(request.options)
        other = Path(options["other_path"]).resolve()
        application = None
        original = revised = result_document = None
        com_runtime = None
        try:
            if self._manages_com_runtime:
                com_runtime = _initialize_com_runtime()
            application = self.com_factory()
            self._configure_application(application)
            original = application.Documents.Open(str(request.input_path.resolve()), ReadOnly=True, AddToRecentFiles=False)
            revised = application.Documents.Open(str(other), ReadOnly=True, AddToRecentFiles=False)
            if request.name == "compare.documents":
                result_document = application.CompareDocuments(original, revised)
            else:
                result_document = application.MergeDocuments(original, revised)
            destination = request.output_path.resolve()
            result_document.SaveAs2(str(destination))
            revisions = int(result_document.Revisions.Count)
            comments = int(result_document.Comments.Count)
            return OperationResult.success(request.name, self.name, Fidelity.NATIVE, {"revisions": revisions, "comments": comments}, output_path=destination)
        finally:
            for document in (result_document, revised, original):
                if document is not None:
                    try:
                        document.Close(SaveChanges=0)
                    except Exception:
                        pass
            if application is not None:
                try:
                    application.Quit()
                except Exception:
                    pass
            if com_runtime is not None:
                com_runtime.CoUninitialize()
