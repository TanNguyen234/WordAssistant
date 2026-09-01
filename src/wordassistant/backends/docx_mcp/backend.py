from __future__ import annotations

from typing import Callable

from ..base import BackendHealth, MappedOperationBackend
from ..status import advanced_word_backend_available, probe_advanced_backend
from ...operations.models import OperationRequest, OperationResult


class DocxMcpBackend(MappedOperationBackend):
    def __init__(
        self,
        handlers: dict[str, Callable[[OperationRequest], OperationResult]] | None = None,
    ) -> None:
        super().__init__("docx-mcp", handlers)

    def health(self) -> BackendHealth:
        installed = advanced_word_backend_available()
        if not installed:
            return BackendHealth(
                backend=self.name,
                available=False,
                operational=False,
                reason="docx-mcp is not installed",
            )
        operational, reason = probe_advanced_backend()
        return BackendHealth(
            backend=self.name,
            available=True,
            operational=operational,
            reason=reason,
        )

