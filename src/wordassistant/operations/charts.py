from __future__ import annotations

from pathlib import Path

from ..backends.word_native.backend import WordNativeBackend
from .models import OperationRequest


def insert_chart(input_path, *, output_path, title, chart_type=51, backend=None):
    return (backend or WordNativeBackend()).execute(
        OperationRequest(
            "chart.insert",
            Path(input_path),
            Path(output_path),
            options={"title": title, "chart_type": chart_type},
        )
    )

