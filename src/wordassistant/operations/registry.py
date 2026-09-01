from __future__ import annotations

from dataclasses import dataclass

from .models import Fidelity


_NON_COMPOSABLE_BATCH_OPERATIONS = frozenset(
    {
        "render.pdf",
        "compare.documents",
        "merge.documents",
        "mail-merge.execute",
    }
)


@dataclass(frozen=True)
class OperationSpec:
    name: str
    mutating: bool
    capability: str
    backend_preference: tuple[str, ...]
    minimum_fidelity: Fidelity = Fidelity.STRUCTURAL


class OperationRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, OperationSpec] = {}

    def register(self, spec: OperationSpec) -> None:
        if spec.name in self._specs:
            raise ValueError(f"Operation already registered: {spec.name}")
        if not spec.backend_preference:
            raise ValueError(f"Operation requires a backend preference: {spec.name}")
        self._specs[spec.name] = spec

    def get(self, name: str) -> OperationSpec:
        try:
            return self._specs[name]
        except KeyError as exc:
            raise KeyError(f"Unknown operation: {name}") from exc

    def all(self) -> tuple[OperationSpec, ...]:
        return tuple(self._specs[name] for name in sorted(self._specs))

    def require_batch_composable(self, name: str) -> OperationSpec:
        if name == "batch.apply" or name.startswith("batch."):
            raise ValueError("Nested batch operations are not allowed")
        spec = self.get(name)
        if not spec.mutating:
            raise ValueError(f"{name} is not a composable mutating operation")
        if name in _NON_COMPOSABLE_BATCH_OPERATIONS:
            raise ValueError(f"{name} is not batch-composable")
        return spec

    def __contains__(self, name: str) -> bool:
        return name in self._specs
