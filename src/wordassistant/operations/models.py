from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


_BATCH_PLAN_KEYS = frozenset({"version", "steps"})
_BATCH_STEP_KEYS = frozenset({"operation", "selector", "options"})
_BATCH_RESERVED_OPTIONS = frozenset(
    {"input_path", "output_path", "checkpoint", "dry_run", "transaction_staging"}
)


class Fidelity(str, Enum):
    STRUCTURAL = "structural"
    HIGH = "high"
    NATIVE = "native"
    FALLBACK = "fallback"


@dataclass(frozen=True)
class OperationError:
    code: str
    message: str
    backend_required: str | None = None
    suggested_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OperationUnavailable(RuntimeError):
    def __init__(self, error: OperationError):
        super().__init__(error.message)
        self.error = error


@dataclass(frozen=True)
class BatchStep:
    operation: str
    selector: Mapping[str, Any] | None = None
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.operation, str) or not self.operation.strip():
            raise ValueError("Batch step operation must be a non-empty string")
        if self.selector is not None and not isinstance(self.selector, Mapping):
            raise TypeError("Batch step selector must be a mapping or null")
        if not isinstance(self.options, Mapping):
            raise TypeError("Batch step options must be a mapping")
        reserved = sorted(_BATCH_RESERVED_OPTIONS & set(self.options))
        if reserved:
            raise ValueError(
                "Batch step contains reserved control options: "
                + ", ".join(reserved)
            )

    @classmethod
    def from_dict(cls, value: Any, *, index: int) -> "BatchStep":
        if not isinstance(value, dict):
            raise TypeError(f"Batch step {index} must be a JSON object")
        unknown = sorted(set(value) - _BATCH_STEP_KEYS)
        if unknown:
            raise ValueError(
                f"Unsupported batch step keys at index {index}: " + ", ".join(unknown)
            )
        operation = value.get("operation")
        if not isinstance(operation, str) or not operation.strip():
            raise ValueError(f"Batch step {index} operation must be a non-empty string")
        selector = value.get("selector")
        if selector is not None and not isinstance(selector, dict):
            raise TypeError(f"Batch step {index} selector must be a JSON object or null")
        options = value.get("options", {})
        if not isinstance(options, dict):
            raise TypeError(f"Batch step {index} options must be a JSON object")
        reserved = sorted(_BATCH_RESERVED_OPTIONS & set(options))
        if reserved:
            raise ValueError(
                f"Batch step {index} contains reserved control options: "
                + ", ".join(reserved)
            )
        return cls(
            operation=operation.strip(),
            selector=dict(selector) if selector is not None else None,
            options=dict(options),
        )


@dataclass(frozen=True)
class BatchPlan:
    version: int
    steps: tuple[BatchStep, ...]

    def __post_init__(self) -> None:
        if self.version != 1 or isinstance(self.version, bool):
            raise ValueError("Batch plan version must be 1")
        if not isinstance(self.steps, tuple) or not self.steps:
            raise ValueError("Batch plan steps must be a non-empty tuple")
        if not all(isinstance(step, BatchStep) for step in self.steps):
            raise TypeError("Batch plan steps must contain only BatchStep values")

    @classmethod
    def from_dict(cls, value: Any) -> "BatchPlan":
        if not isinstance(value, dict):
            raise TypeError("Batch plan must be a JSON object")
        unknown = sorted(set(value) - _BATCH_PLAN_KEYS)
        if unknown:
            raise ValueError("Unsupported batch plan keys: " + ", ".join(unknown))
        if value.get("version") != 1 or isinstance(value.get("version"), bool):
            raise ValueError("Batch plan version must be 1")
        raw_steps = value.get("steps")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise ValueError("Batch plan steps must be a non-empty JSON array")
        return cls(
            version=1,
            steps=tuple(
                BatchStep.from_dict(step, index=index)
                for index, step in enumerate(raw_steps)
            ),
        )


class BatchExecutionError(RuntimeError):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        step_index: int | None = None,
        operation: str | None = None,
        completed_steps: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.step_index = step_index
        self.operation = operation
        self.completed_steps = list(completed_steps or [])

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": str(self),
            "completed_steps": list(self.completed_steps),
        }
        if self.step_index is not None:
            payload["step_index"] = self.step_index
        if self.operation is not None:
            payload["operation"] = self.operation
        return payload


@dataclass(frozen=True)
class OperationRequest:
    name: str
    input_path: Path | None = None
    output_path: Path | None = None
    selector: Any | None = None
    options: Mapping[str, Any] = field(default_factory=dict)
    dry_run: bool = False
    checkpoint: str | bool | None = None
    transaction_staging: bool = False

    def __post_init__(self) -> None:
        if self.input_path is not None and not isinstance(self.input_path, Path):
            object.__setattr__(self, "input_path", Path(self.input_path))
        if self.output_path is not None and not isinstance(self.output_path, Path):
            object.__setattr__(self, "output_path", Path(self.output_path))


@dataclass
class OperationResult:
    status: str
    operation: str
    backend_used: str | None
    fidelity: Fidelity | str
    output_path: Path | None = None
    warnings: list[str] = field(default_factory=list)
    manual_review_required: bool = False
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(
        cls,
        operation: str,
        backend_used: str,
        fidelity: Fidelity | str,
        data: dict[str, Any] | None = None,
        *,
        output_path: Path | str | None = None,
        warnings: list[str] | None = None,
        manual_review_required: bool = False,
    ) -> "OperationResult":
        return cls(
            status="SUCCESS",
            operation=operation,
            backend_used=backend_used,
            fidelity=fidelity,
            output_path=Path(output_path) if output_path is not None else None,
            warnings=list(warnings or []),
            manual_review_required=manual_review_required,
            data=dict(data or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        fidelity = (
            self.fidelity.value
            if isinstance(self.fidelity, Fidelity)
            else str(self.fidelity)
        )
        return {
            "status": self.status,
            "operation": self.operation,
            "backend_used": self.backend_used,
            "fidelity": fidelity,
            "output_path": str(self.output_path) if self.output_path else None,
            "warnings": list(self.warnings),
            "manual_review_required": self.manual_review_required,
            "data": dict(self.data),
        }


@dataclass(frozen=True)
class BatchExecutionResult:
    output_path: Path
    steps: tuple[dict[str, Any], ...]
    sha256: str
    checkpoint_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "SUCCESS",
            "operation": "batch.apply",
            "plan_version": 1,
            "output_path": str(self.output_path),
            "sha256": self.sha256,
            "checkpoint_created": self.checkpoint_created,
            "steps": [dict(step) for step in self.steps],
        }
