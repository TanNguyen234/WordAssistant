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
    def __init__(self, name, operations, *, healthy=True):
        self.name = name
        self.operations = set(operations)
        self.healthy = healthy

    def health(self):
        return BackendHealth(self.name, self.healthy, self.healthy, "ready" if self.healthy else "offline")

    def supports(self, operation):
        return operation in self.operations

    def execute(self, request):
        return OperationResult.success(request.name, self.name, Fidelity.HIGH)


def test_router_uses_declared_fallback_order():
    registry = OperationRegistry()
    registry.register(
        OperationSpec(
            "render.pdf",
            False,
            "render.create",
            ("word-native", "libreoffice"),
            Fidelity.FALLBACK,
        )
    )
    router = BackendRouter(
        registry,
        [
            _Backend("word-native", {"render.pdf"}, healthy=False),
            _Backend("libreoffice", {"render.pdf"}),
        ],
    )

    backend = router.route(
        OperationRequest("render.pdf", input_path=Path("report.docx"))
    )

    assert backend.name == "libreoffice"


def test_render_engine_option_is_a_hard_backend_constraint():
    registry = OperationRegistry()
    registry.register(
        OperationSpec(
            "render.pdf",
            True,
            "render.create",
            ("word-native", "libreoffice"),
            Fidelity.FALLBACK,
        )
    )
    router = BackendRouter(
        registry,
        [
            _Backend("word-native", {"render.pdf"}),
            _Backend("libreoffice", {"render.pdf"}),
        ],
    )

    selected = router.route(
        OperationRequest("render.pdf", options={"engine": "libreoffice"})
    )

    assert selected.name == "libreoffice"


def test_router_does_not_use_backend_outside_declared_policy():
    registry = OperationRegistry()
    registry.register(
        OperationSpec(
            "comment.create",
            True,
            "comments.create",
            ("word-native",),
            Fidelity.NATIVE,
        )
    )
    router = BackendRouter(
        registry,
        [
            _Backend("word-native", {"comment.create"}, healthy=False),
            _Backend("ooxml", {"comment.create"}),
        ],
    )

    with pytest.raises(OperationUnavailable):
        router.route(OperationRequest("comment.create"))
