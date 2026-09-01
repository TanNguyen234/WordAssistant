from __future__ import annotations

from ..operations.models import (
    OperationError,
    OperationRequest,
    OperationResult,
    OperationUnavailable,
)
from ..operations.registry import OperationRegistry
from .base import OperationBackend


class BackendRouter:
    def __init__(
        self, registry: OperationRegistry, backends: list[OperationBackend]
    ) -> None:
        self.registry = registry
        self.backends = {backend.name: backend for backend in backends}

    def route(self, request: OperationRequest) -> OperationBackend:
        spec = self.registry.get(request.name)
        reasons: list[str] = []
        fidelity_rejected = False
        fidelity_rank = {
            "structural": 0,
            "fallback": 0,
            "high": 1,
            "native": 2,
        }
        preference = spec.backend_preference
        if request.name == "render.pdf":
            engine = str(request.options.get("engine", "auto"))
            if engine == "word":
                preference = ("word-native",)
            elif engine == "libreoffice":
                preference = ("libreoffice",)
            elif engine != "auto":
                raise ValueError("render engine must be auto, word, or libreoffice")
        for backend_name in preference:
            backend = self.backends.get(backend_name)
            if backend is None:
                reasons.append(f"{backend_name}: not configured")
                continue
            health = backend.health()
            if not health.available or not health.operational:
                reasons.append(f"{backend_name}: {health.reason}")
                continue
            if not backend.supports(request.name):
                reasons.append(f"{backend_name}: operation not implemented")
                continue
            backend_fidelity = getattr(backend, "fidelity", None)
            if backend_fidelity is None or fidelity_rank[backend_fidelity.value] < fidelity_rank[spec.minimum_fidelity.value]:
                fidelity_rejected = True
                actual = backend_fidelity.value if backend_fidelity is not None else "unknown"
                reasons.append(
                    f"{backend_name}: fidelity {actual} is below {spec.minimum_fidelity.value}"
                )
                continue
            return backend

        required = spec.backend_preference[0]
        action = (
            "Install Microsoft Word and the optional pywin32 dependency, then "
            "run 'wordassistant doctor --json'."
            if required == "word-native"
            else f"Install or enable the {required} backend and run capability discovery."
        )
        raise OperationUnavailable(
            OperationError(
                code="FIDELITY_UNAVAILABLE" if fidelity_rejected else "BACKEND_UNAVAILABLE",
                message=(
                    f"No allowed backend can execute {request.name}. "
                    + "; ".join(reasons)
                ),
                backend_required=required,
                suggested_action=action,
            )
        )

    def execute(self, request: OperationRequest) -> OperationResult:
        return self.route(request).execute(request)
