import pytest

from wordassistant.backends.base import BackendHealth, MappedOperationBackend
from wordassistant.backends.router import BackendRouter
from wordassistant.operations.models import Fidelity, OperationRequest, OperationUnavailable
from wordassistant.operations.registry import OperationRegistry, OperationSpec


class _FallbackBackend(MappedOperationBackend):
    fidelity = Fidelity.FALLBACK

    def health(self):
        return BackendHealth(self.name, True, True, "available")


def test_router_rejects_backend_below_minimum_fidelity():
    registry = OperationRegistry()
    registry.register(
        OperationSpec(
            "render.pdf",
            True,
            "render.create",
            ("libreoffice",),
            Fidelity.NATIVE,
        )
    )
    backend = _FallbackBackend("libreoffice", {"render.pdf": lambda request: None})
    router = BackendRouter(registry, [backend])

    with pytest.raises(OperationUnavailable) as raised:
        router.route(OperationRequest("render.pdf"))

    assert raised.value.error.code == "FIDELITY_UNAVAILABLE"

