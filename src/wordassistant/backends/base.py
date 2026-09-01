from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from ..operations.models import Fidelity, OperationRequest, OperationResult


@dataclass(frozen=True)
class BackendHealth:
    backend: str
    available: bool
    operational: bool
    reason: str
    details: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend,
            "available": self.available,
            "operational": self.operational,
            "reason": self.reason,
            "details": dict(self.details or {}),
        }


class OperationBackend(ABC):
    name: str
    fidelity: Fidelity = Fidelity.STRUCTURAL

    @abstractmethod
    def health(self) -> BackendHealth:
        raise NotImplementedError

    @abstractmethod
    def supports(self, operation: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def execute(self, request: OperationRequest) -> OperationResult:
        raise NotImplementedError


class MappedOperationBackend(OperationBackend):
    def __init__(
        self,
        name: str,
        handlers: dict[str, Callable[[OperationRequest], OperationResult]] | None = None,
    ) -> None:
        self.name = name
        self.handlers = dict(handlers or {})

    def supports(self, operation: str) -> bool:
        return operation in self.handlers

    def execute(self, request: OperationRequest) -> OperationResult:
        try:
            handler = self.handlers[request.name]
        except KeyError as exc:
            raise KeyError(
                f"Backend {self.name} does not implement {request.name}"
            ) from exc
        return handler(request)
