from __future__ import annotations

from typing import Callable

from ..base import BackendHealth, MappedOperationBackend
from ...doctor import find_libreoffice_executable
from ...operations.models import Fidelity, OperationRequest, OperationResult


class LibreOfficeBackend(MappedOperationBackend):
    fidelity = Fidelity.FALLBACK
    def __init__(
        self,
        handlers: dict[str, Callable[[OperationRequest], OperationResult]] | None = None,
    ) -> None:
        super().__init__("libreoffice", handlers)

    def health(self) -> BackendHealth:
        executable = find_libreoffice_executable()
        return BackendHealth(
            backend=self.name,
            available=bool(executable),
            operational=bool(executable),
            reason=(
                f"LibreOffice executable found: {executable}"
                if executable
                else "LibreOffice executable was not found"
            ),
            details={"executable": executable},
        )
