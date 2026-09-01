from __future__ import annotations

from pathlib import Path
import inspect

from .backends.libreoffice.backend import LibreOfficeBackend
from .backends.ooxml.backend import OoxmlBackend
from .backends.python_docx.backend import PythonDocxBackend
from .backends.router import BackendRouter
from .backends.word_native.backend import NATIVE_OPERATIONS, WordNativeBackend
from .document.render import render_pdf
from .facade import _OPERATIONS, _READ_OPERATIONS
from .operations.models import Fidelity, OperationRequest, OperationResult
from .operations.registry import OperationRegistry, OperationSpec


_PYTHON_DOCX_PREFIXES = ("text.", "format.", "style.", "table.", "section.")
_PYTHON_DOCX_OPERATIONS = {
    "image.insert",
    "header-footer.set_text",
    "bibliography.generate",
}


def _uses_python_docx(operation: str) -> bool:
    return operation.startswith(_PYTHON_DOCX_PREFIXES) or operation in _PYTHON_DOCX_OPERATIONS


def _operation_handler(operation: str):
    def execute(request: OperationRequest):
        if request.input_path is None:
            raise ValueError(f"{operation} requires input_path")
        if operation in _READ_OPERATIONS:
            value = _READ_OPERATIONS[operation](request.input_path, **dict(request.options))
            return OperationResult.success(
                operation,
                "ooxml",
                Fidelity.HIGH,
                {"result": value},
            )
        function = _OPERATIONS[operation]
        kwargs = dict(request.options)
        kwargs["output_path"] = request.output_path
        kwargs["dry_run"] = request.dry_run
        if request.selector is not None:
            signature = inspect.signature(function)
            if "selector" not in signature.parameters and not any(
                parameter.kind == inspect.Parameter.VAR_KEYWORD
                for parameter in signature.parameters.values()
            ):
                raise ValueError(f"{operation} does not support selectors")
            kwargs["selector"] = request.selector
        return function(request.input_path, **kwargs)

    return execute


def _render_handler(request: OperationRequest) -> OperationResult:
    if request.input_path is None:
        raise ValueError("render.pdf requires input_path")
    output_dir = request.output_path.parent if request.output_path else None
    result = render_pdf(
        request.input_path,
        output_dir=output_dir,
        timeout_seconds=int(request.options.get("timeout_seconds", 180)),
        output_path=request.output_path,
    )
    if request.output_path and result.pdf_path != request.output_path:
        Path(result.pdf_path).replace(request.output_path)
        pdf_path = request.output_path
    else:
        pdf_path = result.pdf_path
    return OperationResult.success(
        "render.pdf",
        "libreoffice",
        Fidelity.FALLBACK,
        {
            "file_size_bytes": pdf_path.stat().st_size,
            "duration_seconds": result.duration_seconds,
        },
        output_path=pdf_path,
        manual_review_required=True,
    )


def build_default_registry() -> OperationRegistry:
    registry = OperationRegistry()
    for operation in sorted({*_OPERATIONS, *_READ_OPERATIONS}):
        core = _uses_python_docx(operation)
        area, _, action = operation.partition(".")
        registry.register(
            OperationSpec(
                name=operation,
                mutating=operation not in _READ_OPERATIONS,
                capability=f"{area}.{action or 'use'}",
                backend_preference=("python-docx",) if core else ("ooxml",),
                minimum_fidelity=Fidelity.HIGH,
            )
        )
    native_capabilities = {
        "field.update_all": "fields.update",
        "comment.create": "comments.create",
        "comment.list": "comments.read",
        "comment.reply": "comments.advanced_edit",
        "comment.resolve": "comments.advanced_edit",
        "comment.reopen": "comments.advanced_edit",
        "comment.delete": "comments.delete",
        "revision.enable": "tracked_changes.write",
        "revision.disable": "tracked_changes.write",
        "revision.list": "tracked_changes.read",
        "revision.accept": "tracked_changes.advanced_edit",
        "revision.reject": "tracked_changes.advanced_edit",
        "revision.accept_all": "tracked_changes.advanced_edit",
        "revision.reject_all": "tracked_changes.advanced_edit",
        "compare.documents": "compare.create",
        "merge.documents": "merge.create",
        "protect.native": "protection.native_word",
        "render.pdf": "render.create",
        "mail-merge.execute": "mail_merge.create",
        "chart.insert": "charts.create",
    }
    for operation in sorted(NATIVE_OPERATIONS):
        registry.register(
            OperationSpec(
                operation,
                operation not in {"comment.list", "revision.list"},
                native_capabilities[operation],
                ("word-native", "libreoffice") if operation == "render.pdf" else ("word-native",),
                Fidelity.FALLBACK if operation == "render.pdf" else Fidelity.NATIVE,
            )
        )
    return registry


def build_default_router(registry: OperationRegistry | None = None) -> BackendRouter:
    registry = registry or build_default_registry()
    core_handlers = {
        operation: _operation_handler(operation)
        for operation in {*_OPERATIONS, *_READ_OPERATIONS}
        if _uses_python_docx(operation)
    }
    ooxml_handlers = {
        operation: _operation_handler(operation)
        for operation in {*_OPERATIONS, *_READ_OPERATIONS}
        if not _uses_python_docx(operation)
    }
    return BackendRouter(
        registry,
        [
            PythonDocxBackend(core_handlers),
            OoxmlBackend(ooxml_handlers),
            WordNativeBackend(),
            LibreOfficeBackend({"render.pdf": _render_handler}),
        ],
    )
