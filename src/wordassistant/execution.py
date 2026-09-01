from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from docx import Document

from .backends.router import BackendRouter
from .operations.fields import inspect_fields, inspect_field_structure
from .operations.models import (
    BatchExecutionError,
    BatchExecutionResult,
    BatchPlan,
    Fidelity,
    OperationError,
    OperationRequest,
    OperationResult,
    OperationUnavailable,
)
from .operations.registry import OperationRegistry
from .operation_evidence import operation_is_verified
from .transactions import CheckpointStore, TransactionCoordinator


_OUTPUT_ONLY_OPERATIONS = {"render.pdf", "compare.documents", "merge.documents"}


class ExecutionService:
    """Single safe execution path used by the CLI and Python facade."""

    def __init__(
        self,
        registry: OperationRegistry,
        router: BackendRouter,
        checkpoint_store: CheckpointStore | None = None,
    ) -> None:
        self.registry = registry
        self.router = router
        self.checkpoint_store = checkpoint_store or CheckpointStore(
            Path.cwd() / ".wordassistant" / "checkpoints"
        )

    @classmethod
    def default(cls) -> "ExecutionService":
        from .runtime import build_default_registry, build_default_router

        registry = build_default_registry()
        return cls(registry, build_default_router(registry))

    @staticmethod
    def _validate_docx(path: Path) -> None:
        if path.suffix.casefold() == ".docx":
            Document(path)

    @classmethod
    def _validate_field_update(cls, path: Path) -> None:
        cls._validate_docx(path)
        structure = inspect_field_structure(path)
        fields = inspect_fields(path)
        blocked = [
            field
            for field in fields
            if field["locked"] or field["freshness"] == "PLACEHOLDER"
        ]
        if structure["status"] != "PASS" or blocked:
            raise ValueError(
                "Native field update did not produce a structurally valid, unlocked result"
            )

    @classmethod
    def _validate_output(cls, path: Path) -> None:
        if path.suffix.casefold() == ".pdf":
            if not path.is_file() or not path.read_bytes()[:5] == b"%PDF-":
                raise ValueError("Backend did not produce a valid PDF signature")
            return
        cls._validate_docx(path)

    @staticmethod
    def _normalize_result(
        result: OperationResult, request: OperationRequest, backend_name: str
    ) -> OperationResult:
        result.operation = request.name
        result.backend_used = backend_name
        return result

    @staticmethod
    def _fidelity_value(value: Fidelity | str) -> str:
        return value.value if isinstance(value, Fidelity) else str(value)

    @staticmethod
    def _batch_option_matches(value: object, expected: str) -> bool:
        if expected in {"any", "array"}:
            return expected == "any" or isinstance(value, list)
        if expected in {"string", "path"}:
            return isinstance(value, str)
        if expected == "boolean":
            return isinstance(value, bool)
        if expected == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if expected == "object":
            return isinstance(value, dict)
        if expected.startswith("array"):
            if not isinstance(value, list):
                return False
            if expected == "array[string]":
                return all(isinstance(item, str) for item in value)
            if expected == "array[integer]":
                return all(isinstance(item, int) and not isinstance(item, bool) for item in value)
            if expected == "array[integer, integer]":
                return (
                    len(value) == 2
                    and all(isinstance(item, int) and not isinstance(item, bool) for item in value)
                )
            return True
        return True

    @classmethod
    def _validate_batch_options(
        cls,
        operation: str,
        options: dict[str, object],
        contract: list[dict[str, object]],
    ) -> None:
        from .cli_contracts import TEXT_ROUTE_OPTION_CONTRACTS

        checked = dict(options)
        if operation == "text.edit":
            action = checked.pop("action", None)
            if not isinstance(action, str) or action not in TEXT_ROUTE_OPTION_CONTRACTS:
                raise ValueError(
                    "text.edit batch steps require action: replace, append, prepend, or insert"
                )
            contract = [
                {
                    "name": name,
                    "required": required,
                    "type": type_name,
                }
                for name, required, _, type_name in TEXT_ROUTE_OPTION_CONTRACTS[action]
            ]
        specs = {str(item["name"]): item for item in contract}
        unknown = sorted(set(checked) - set(specs))
        if unknown:
            raise ValueError(
                f"Unsupported options for {operation}: " + ", ".join(unknown)
            )
        missing = sorted(
            name
            for name, item in specs.items()
            if bool(item.get("required")) and name not in checked
        )
        if missing:
            raise ValueError(
                f"Missing required options for {operation}: " + ", ".join(missing)
            )
        for name, value in checked.items():
            expected = str(specs[name].get("type", "any"))
            if not cls._batch_option_matches(value, expected):
                raise ValueError(f"Option {name!r} for {operation} must be {expected}")

    def execute_batch(
        self,
        input_path: str | Path,
        output_path: str | Path,
        plan: BatchPlan,
        *,
        checkpoint: str | bool | None = None,
    ) -> BatchExecutionResult:
        """Validate, execute, and atomically publish a version-1 operation plan."""
        if not isinstance(plan, BatchPlan):
            raise TypeError("plan must be a validated BatchPlan")
        if checkpoint not in (None, False, True, "auto"):
            raise ValueError("checkpoint must be true, false, auto, or omitted")

        source = Path(input_path).resolve()
        output = Path(output_path).resolve()
        if source == output:
            raise ValueError("batch.apply requires distinct input and final output paths")
        if source.suffix.casefold() != ".docx" or output.suffix.casefold() != ".docx":
            raise ValueError("batch.apply input and output must use the .docx extension")
        if not source.is_file():
            raise FileNotFoundError(source)
        self._validate_docx(source)

        # Complete all schema, selector, option, capability, backend, and evidence
        # checks before creating a checkpoint, output directory, or staging file.
        prepared: list[tuple[OperationRequest, object]] = []
        from .capabilities import _callable_contract
        from .cli_contracts import validate_overridden_options
        from .selectors import Selector

        for index, step in enumerate(plan.steps):
            self.registry.require_batch_composable(step.operation)
            validate_overridden_options(step.operation, dict(step.options))
            selector_supported, option_contract = _callable_contract(step.operation)
            self._validate_batch_options(
                step.operation, dict(step.options), option_contract
            )
            if step.selector is not None:
                if not selector_supported:
                    raise ValueError(
                        f"Batch step {index} operation {step.operation} does not support selectors"
                    )
                Selector.from_value(dict(step.selector))
            request = OperationRequest(
                step.operation,
                input_path=source,
                output_path=output,
                selector=dict(step.selector) if step.selector is not None else None,
                options=dict(step.options),
            )
            backend = self.router.route(request)
            if not operation_is_verified(
                request.name, native=backend.name == "word-native"
            ):
                raise OperationUnavailable(
                    OperationError(
                        code="EVIDENCE_UNVERIFIED",
                        message=(
                            f"{request.name} is implemented but lacks required "
                            "verification evidence"
                        ),
                        backend_required=backend.name,
                        suggested_action=(
                            "Use wordassistant capabilities --json and choose a "
                            "VERIFIED operation."
                        ),
                    )
                )
            prepared.append((request, backend))

        checkpoint_created = False
        if checkpoint in (True, "auto"):
            self.checkpoint_store.create(source, operation="batch.apply")
            checkpoint_created = True

        output.parent.mkdir(parents=True, exist_ok=True)
        descriptor, staging_name = tempfile.mkstemp(
            prefix=f".{output.stem}.batch-", suffix=".docx", dir=output.parent
        )
        os.close(descriptor)
        staging = Path(staging_name)
        evidence: list[dict[str, object]] = []
        try:
            shutil.copy2(source, staging)
            for index, (request, backend) in enumerate(prepared):
                before_sha256 = hashlib.sha256(staging.read_bytes()).hexdigest()
                staged_request = replace(
                    request,
                    input_path=staging,
                    output_path=staging,
                    dry_run=False,
                    checkpoint=None,
                    transaction_staging=True,
                )
                try:
                    result = self._normalize_result(
                        backend.execute(staged_request), request, backend.name
                    )
                    validator = (
                        self._validate_field_update
                        if request.name == "field.update_all"
                        else self._validate_docx
                    )
                    validator(staging)
                    if result.status != "SUCCESS":
                        raise ValueError(
                            f"backend returned non-success status {result.status!r}"
                        )
                except Exception as exc:
                    safe_message = str(exc).replace(str(staging), "<private-staging>")
                    raise BatchExecutionError(
                        code="BATCH_STEP_FAILED",
                        message=(
                            f"Batch step {index} ({request.name}) failed: "
                            f"{type(exc).__name__}: {safe_message}"
                        ),
                        step_index=index,
                        operation=request.name,
                        completed_steps=evidence,
                    ) from exc
                after_sha256 = hashlib.sha256(staging.read_bytes()).hexdigest()
                evidence.append(
                    {
                        "index": index,
                        "operation": request.name,
                        "status": "SUCCESS",
                        "backend_used": backend.name,
                        "fidelity": self._fidelity_value(result.fidelity),
                        "before_sha256": before_sha256,
                        "after_sha256": after_sha256,
                        "warnings": [
                            str(warning).replace(str(staging), "<private-staging>")
                            for warning in result.warnings
                        ],
                        "manual_review_required": result.manual_review_required,
                    }
                )

            final_sha256 = hashlib.sha256(staging.read_bytes()).hexdigest()
            try:
                os.replace(staging, output)
            except OSError as exc:
                safe_message = str(exc).replace(str(staging), "<private-staging>")
                raise BatchExecutionError(
                    code="BATCH_PUBLISH_FAILED",
                    message=(
                        "Atomic batch publication failed: "
                        f"{type(exc).__name__}: {safe_message}"
                    ),
                    completed_steps=evidence,
                ) from exc
            return BatchExecutionResult(
                output_path=output,
                steps=tuple(evidence),
                sha256=final_sha256,
                checkpoint_created=checkpoint_created,
            )
        finally:
            staging.unlink(missing_ok=True)

    def execute(self, request: OperationRequest) -> OperationResult:
        spec = self.registry.get(request.name)
        from .cli_contracts import validate_overridden_options

        validate_overridden_options(request.name, request.options)
        if request.selector is not None:
            from .capabilities import _callable_contract

            selector_supported, _ = _callable_contract(request.name)
            if not selector_supported:
                raise ValueError(f"{request.name} does not support --selector")
        if request.checkpoint not in (None, False, True, "auto"):
            raise ValueError("checkpoint must be true, false, auto, or omitted")
        if spec.mutating and request.output_path is not None:
            expected_suffix = ".pdf" if request.name == "render.pdf" else ".docx"
            if request.output_path.suffix.casefold() != expected_suffix:
                raise ValueError(
                    f"{request.name} output must use the {expected_suffix} extension"
                )
        if request.name in {"compare.documents", "merge.documents"} and request.output_path is not None:
            other_path = request.options.get("other_path")
            if other_path is not None and Path(other_path).resolve() == request.output_path.resolve():
                raise ValueError(
                    f"{request.name} output must differ from every input artifact"
                )
        if spec.mutating:
            if request.input_path is None or request.output_path is None:
                raise ValueError(
                    f"{request.name} requires a distinct output path; in-place mutation is disabled"
                )
            source = request.input_path.resolve()
            output = request.output_path.resolve()
            if source == output:
                raise ValueError(
                    f"{request.name} requires a distinct output path; in-place mutation is disabled"
                )
        if request.dry_run and spec.mutating:
            return OperationResult(
                status="DRY_RUN",
                operation=request.name,
                backend_used=None,
                fidelity=spec.minimum_fidelity,
                output_path=None,
                data={
                    "planned_output": str(request.output_path) if request.output_path else None,
                    "backend_preference": list(spec.backend_preference),
                    "backend_probed": False,
                },
            )
        backend = self.router.route(request)
        if not operation_is_verified(
            request.name, native=backend.name == "word-native"
        ):
            raise OperationUnavailable(
                OperationError(
                    code="EVIDENCE_UNVERIFIED",
                    message=f"{request.name} is implemented but lacks required verification evidence",
                    backend_required=backend.name,
                    suggested_action="Use wordassistant capabilities --json and choose a VERIFIED operation.",
                )
            )
        if not spec.mutating:
            return self._normalize_result(backend.execute(request), request, backend.name)

        if request.name in _OUTPUT_ONLY_OPERATIONS:
            if request.dry_run:
                return OperationResult(
                    status="DRY_RUN",
                    operation=request.name,
                    backend_used=backend.name,
                    fidelity=spec.minimum_fidelity,
                    output_path=None,
                    data={"planned_output": str(output)},
                )
            output.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{output.stem}.", suffix=output.suffix, dir=output.parent
            )
            os.close(descriptor)
            staging_output = Path(temporary_name)
            staging_output.unlink(missing_ok=True)
            try:
                staged_request = replace(request, output_path=staging_output)
                result = self._normalize_result(
                    backend.execute(staged_request), request, backend.name
                )
                self._validate_output(staging_output)
                os.replace(staging_output, output)
                result.output_path = output
                return result
            finally:
                staging_output.unlink(missing_ok=True)

        coordinator = TransactionCoordinator(self.checkpoint_store)

        def mutate(staging: Path) -> OperationResult:
            staged_request = replace(
                request,
                input_path=staging,
                output_path=staging,
                dry_run=False,
                checkpoint=None,
                transaction_staging=True,
            )
            result = backend.execute(staged_request)
            return self._normalize_result(result, request, backend.name)

        validator = (
            self._validate_field_update
            if request.name == "field.update_all"
            else self._validate_docx
        )
        result = coordinator.execute(request, mutate, validator)
        if request.name == "field.update_all" and result.status == "SUCCESS":
            evidence_path = output.with_suffix(output.suffix + ".wa-evidence.json")
            temporary_evidence = None
            try:
                descriptor, temporary_name = tempfile.mkstemp(
                    prefix=f".{evidence_path.name}.",
                    suffix=".tmp",
                    dir=evidence_path.parent,
                )
                os.close(descriptor)
                temporary_evidence = Path(temporary_name)
                temporary_evidence.write_text(
                    json.dumps(
                        {
                            "version": 1,
                            "operation": request.name,
                            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "backend": result.backend_used,
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                os.replace(temporary_evidence, evidence_path)
                result.data["evidence_path"] = str(evidence_path)
            except OSError as exc:
                result.warnings.append(
                    f"Output committed, but informational evidence sidecar could not be written: {exc}"
                )
            finally:
                if temporary_evidence is not None:
                    temporary_evidence.unlink(missing_ok=True)
        return result
