from __future__ import annotations

import json
import subprocess

import pytest

from wordassistant.backends.word_native.backend import WordNativeBackend
from wordassistant.operations.models import OperationRequest


def _successful_worker(observed: list[int]):
    def run(payload: dict, timeout: int):
        observed.append(timeout)
        response = {
            "status": "SUCCESS",
            "operation": payload["request"]["name"],
            "backend_used": "word-native",
            "fidelity": "NATIVE",
            "output_path": payload["request"]["output_path"],
            "data": {"page_count": 1},
        }
        return subprocess.CompletedProcess([], 0, json.dumps(response), "")

    return run


def test_request_timeout_reaches_isolated_worker(tmp_path):
    observed: list[int] = []
    source = tmp_path / "long-reference.docx"
    source.write_bytes(b"placeholder")
    output = tmp_path / "long-reference.pdf"
    backend = WordNativeBackend(
        worker_runner=_successful_worker(observed),
        timeout_seconds=60,
        platform_name="Windows",
        word_executable=tmp_path / "WINWORD.EXE",
    )

    backend.execute(
        OperationRequest(
            "render.pdf",
            input_path=source,
            output_path=output,
            options={"timeout_seconds": 600},
        )
    )

    assert observed == [600]


@pytest.mark.parametrize("value", [0, -1, 3601, True, "not-a-number"])
def test_request_timeout_rejects_invalid_values(tmp_path, value):
    source = tmp_path / "source.docx"
    source.write_bytes(b"placeholder")
    backend = WordNativeBackend(
        worker_runner=_successful_worker([]),
        platform_name="Windows",
        word_executable=tmp_path / "WINWORD.EXE",
    )

    with pytest.raises(ValueError, match="timeout_seconds"):
        backend.execute(
            OperationRequest(
                "render.pdf",
                input_path=source,
                output_path=tmp_path / "out.pdf",
                options={"timeout_seconds": value},
            )
        )
