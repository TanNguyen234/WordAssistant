from pathlib import Path

import pytest

from wordassistant.backends.base import BackendHealth, OperationBackend
from wordassistant.backends.router import BackendRouter
from wordassistant.operations.models import (
    Fidelity,
    OperationRequest,
    OperationResult,
    OperationUnavailable,
)
from wordassistant.operations.registry import OperationRegistry, OperationSpec


class _Backend(OperationBackend):
    def __init__(self, name: str, operations: set[str], available: bool = True):
        self.name = name
        self._operations = operations
        self._available = available

    def health(self) -> BackendHealth:
        return BackendHealth(
            backend=self.name,
            available=self._available,
            operational=self._available,
            reason="ready" if self._available else "not installed",
        )

    def supports(self, operation: str) -> bool:
        return operation in self._operations

    def execute(self, request: OperationRequest) -> OperationResult:
        return OperationResult.success(
            request.name,
            self.name,
            Fidelity.HIGH,
            data={"handled": True},
        )


def test_result_envelope_exposes_backend_fidelity_and_review():
    result = OperationResult.success(
        "table.create", "python-docx", Fidelity.HIGH, {"table_index": 0}
    )

    payload = result.to_dict()

    assert payload["status"] == "SUCCESS"
    assert payload["backend_used"] == "python-docx"
    assert payload["fidelity"] == "high"
    assert payload["manual_review_required"] is False
    assert payload["data"] == {"table_index": 0}


def test_router_refuses_semantic_fidelity_substitution():
    registry = OperationRegistry()
    registry.register(
        OperationSpec(
            name="revision.accept_all",
            mutating=True,
            capability="revisions.accept",
            backend_preference=("word-native",),
            minimum_fidelity=Fidelity.NATIVE,
        )
    )
    router = BackendRouter(
        registry,
        [
            _Backend("word-native", {"revision.accept_all"}, available=False),
            _Backend("python-docx", {"revision.accept_all"}),
        ],
    )

    with pytest.raises(OperationUnavailable) as exc:
        router.route(
            OperationRequest(
                name="revision.accept_all", input_path=Path("document.docx")
            )
        )

    assert exc.value.error.code == "BACKEND_UNAVAILABLE"
    assert exc.value.error.backend_required == "word-native"
    assert "Word" in exc.value.error.suggested_action


def test_registry_rejects_duplicate_operation_names():
    registry = OperationRegistry()
    spec = OperationSpec(
        name="paragraph.format",
        mutating=True,
        capability="paragraph.format",
        backend_preference=("python-docx",),
    )
    registry.register(spec)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(spec)

