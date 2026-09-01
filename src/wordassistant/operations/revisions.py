from __future__ import annotations

from pathlib import Path

from ..backends.word_native.backend import WordNativeBackend
from .models import OperationRequest


def revision_operation(input_path, *, action, output_path=None, backend=None, **options):
    dry_run = bool(options.pop("dry_run", False))
    request = OperationRequest(
        name=f"revision.{action}",
        input_path=Path(input_path),
        output_path=Path(output_path) if output_path else None,
        options=options,
        dry_run=dry_run,
    )
    if backend is not None:
        return backend.execute(request)
    from ..execution import ExecutionService

    return ExecutionService.default().execute(request)
