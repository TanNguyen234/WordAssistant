from __future__ import annotations

from importlib.util import find_spec
from typing import Callable

from ..base import BackendHealth, MappedOperationBackend
from ...operations.models import Fidelity, OperationRequest, OperationResult


class PythonDocxBackend(MappedOperationBackend):
    fidelity = Fidelity.HIGH
    def __init__(
        self,
        handlers: dict[str, Callable[[OperationRequest], OperationResult]] | None = None,
    ) -> None:
        super().__init__("python-docx", handlers)

    def health(self) -> BackendHealth:
        available = find_spec("docx") is not None
        return BackendHealth(
            backend=self.name,
            available=available,
            operational=available,
            reason="python-docx is importable" if available else "python-docx is not installed",
        )
