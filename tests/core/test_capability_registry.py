from wordassistant.backends.base import BackendHealth, OperationBackend
from wordassistant.backends.router import BackendRouter
from wordassistant.capabilities import capability_matrix, operation_statuses
from wordassistant.operations.models import Fidelity, OperationRequest, OperationResult
from wordassistant.operations.registry import OperationRegistry, OperationSpec


class _CapabilityBackend(OperationBackend):
    def __init__(self, name, operations, *, available=True, operational=True):
        self.name = name
        self.operations = set(operations)
        self.available = available
        self.operational = operational

    def health(self):
        return BackendHealth(
            backend=self.name,
            available=self.available,
            operational=self.operational,
            reason="ready" if self.operational else "health probe failed",
        )

    def supports(self, operation):
        return operation in self.operations

    def execute(self, request):
        return OperationResult.success(request.name, self.name, Fidelity.HIGH)


def _registry():
    registry = OperationRegistry()
    registry.register(
        OperationSpec(
            "paragraph.write",
            True,
            "paragraph.write",
            ("python-docx",),
        )
    )
    registry.register(
        OperationSpec(
            "comment.create",
            True,
            "comments.create",
            ("word-native",),
            Fidelity.NATIVE,
        )
    )
    registry.register(
        OperationSpec(
            "bookmark.inspect",
            False,
            "bookmarks.read",
            ("ooxml",),
        )
    )
    return registry


def test_capability_requires_registration_implementation_and_health():
    registry = _registry()
    router = BackendRouter(
        registry,
        [
            _CapabilityBackend("python-docx", {"paragraph.write"}),
            _CapabilityBackend(
                "word-native", {"comment.create"}, available=True, operational=False
            ),
            _CapabilityBackend("ooxml", set()),
        ],
    )

    matrix = capability_matrix(registry, router)

    assert matrix["paragraph"]["write"] == "UNVERIFIED"
    assert matrix["comments"]["create"] == "UNAVAILABLE"
    assert matrix["bookmarks"]["read"] == "UNSUPPORTED"


def test_read_only_operation_uses_read_only_state():
    registry = _registry()
    router = BackendRouter(
        registry,
        [_CapabilityBackend("ooxml", {"bookmark.inspect"})],
    )

    matrix = capability_matrix(registry, router)

    assert matrix["bookmarks"]["read"] == "READ_ONLY"


def test_capability_aggregate_does_not_overwrite_a_supported_operation(monkeypatch):
    registry = OperationRegistry()
    for name in ("revision.accept_all", "revision.reject_all"):
        registry.register(
            OperationSpec(
                name,
                True,
                "tracked_changes.advanced_edit",
                ("word-native",),
                Fidelity.NATIVE,
            )
        )
    backend = _CapabilityBackend(
        "word-native", {"revision.accept_all", "revision.reject_all"}
    )
    backend.verified_operations = {"revision.accept_all"}
    router = BackendRouter(registry, [backend])
    monkeypatch.setattr(
        "wordassistant.capabilities.operation_is_verified",
        lambda operation, native: operation == "revision.accept_all",
    )

    statuses = operation_statuses(registry, router)
    matrix = capability_matrix(registry, router, statuses)

    assert statuses["revision.accept_all"] == "SUPPORTED_NATIVE"
    assert statuses["revision.reject_all"] == "UNSUPPORTED"
    assert matrix["tracked_changes"]["advanced_edit"] == "SUPPORTED_NATIVE"
