from __future__ import annotations

from pathlib import Path

from ..backends.word_native.backend import WordNativeBackend
from .models import OperationRequest


def execute_mail_merge(template, data_source, *, output_path, backend=None):
    return (backend or WordNativeBackend()).execute(
        OperationRequest(
            "mail-merge.execute",
            Path(template),
            Path(output_path),
            options={"data_source": str(data_source)},
        )
    )

