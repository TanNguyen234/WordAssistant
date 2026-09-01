from __future__ import annotations

from typing import Callable

from ..base import BackendHealth, MappedOperationBackend
from ...operations.models import Fidelity, OperationRequest, OperationResult


class OoxmlBackend(MappedOperationBackend):
    fidelity = Fidelity.HIGH
    def __init__(
        self,
        handlers: dict[str, Callable[[OperationRequest], OperationResult]] | None = None,
    ) -> None:
        super().__init__("ooxml", handlers)

    def health(self) -> BackendHealth:
        return BackendHealth(
            backend=self.name,
            available=True,
            operational=True,
            reason="direct OOXML package support is available",
        )
