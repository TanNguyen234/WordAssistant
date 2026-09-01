from __future__ import annotations

from pathlib import Path

from ..backends.word_native.backend import WordNativeBackend
from .models import OperationRequest


def compare_documents(original, revised, *, output_path, backend=None):
    return (backend or WordNativeBackend()).execute(
        OperationRequest(
            "compare.documents",
            Path(original),
            Path(output_path),
            options={"other_path": str(revised)},
        )
    )


def merge_documents(base, changes, *, output_path, backend=None):
    return (backend or WordNativeBackend()).execute(
        OperationRequest(
            "merge.documents",
            Path(base),
            Path(output_path),
            options={"other_path": str(changes)},
        )
    )

