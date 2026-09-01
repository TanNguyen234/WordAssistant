from __future__ import annotations

from copy import deepcopy
import inspect
from pathlib import Path
import types
from typing import Any, get_args, get_origin, get_type_hints

from .backends.router import BackendRouter
from .backends.status import get_backend_status
from .doctor import status
from .operations.registry import OperationRegistry
from .operation_evidence import evidence_for, operation_is_verified
from .selectors import SELECTOR_SCHEMA
from .cli_contracts import (
    NATIVE_OPTION_CONTRACTS,
    OPERATION_OPTION_OVERRIDES,
    TEXT_ROUTE_OPTION_CONTRACTS,
    cli_routes_for,
)


_BACKEND_STATE = {
    "python-docx": "SUPPORTED_CORE",
    "ooxml": "SUPPORTED_OOXML",
    "word-native": "SUPPORTED_NATIVE",
    "libreoffice": "SUPPORTED_FALLBACK",
    "docx-mcp": "SUPPORTED_FALLBACK",
}


def operation_statuses(
    registry: OperationRegistry, router: BackendRouter
) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for spec in registry.all():
        state = "UNSUPPORTED"
        implementation_found = False
        unhealthy_implementation = False
        selected_backend: str | None = None

        for backend_name in spec.backend_preference:
            backend = router.backends.get(backend_name)
            if backend is None or not backend.supports(spec.name):
                continue
            implementation_found = True
            verified = getattr(backend, "verified_operations", None)
            if verified is not None and spec.name not in verified:
                continue
            health = backend.health()
            if health.available and health.operational:
                selected_backend = backend_name
                break
            unhealthy_implementation = True

        if selected_backend is not None:
            if not operation_is_verified(
                spec.name, native=selected_backend == "word-native"
            ):
                state = "UNVERIFIED"
            else:
                state = (
                    "READ_ONLY"
                    if not spec.mutating
                    else _BACKEND_STATE.get(selected_backend, "SUPPORTED_FALLBACK")
                )
        elif implementation_found and unhealthy_implementation:
            state = "UNAVAILABLE"

        statuses[spec.name] = state
    return statuses


def capability_matrix(
    registry: OperationRegistry,
    router: BackendRouter,
    statuses: dict[str, str] | None = None,
) -> dict[str, dict[str, str]]:
    statuses = statuses or operation_statuses(registry, router)
    matrix: dict[str, dict[str, str]] = {}
    rank = {
        "UNSUPPORTED": 0,
        "UNVERIFIED": 1,
        "UNAVAILABLE": 2,
        "READ_ONLY": 3,
        "SUPPORTED_FALLBACK": 4,
        "SUPPORTED_OOXML": 5,
        "SUPPORTED_CORE": 5,
        "SUPPORTED_NATIVE": 6,
    }
    for spec in registry.all():
        area, _, action = spec.capability.partition(".")
        action = action or "use"
        state = statuses[spec.name]
        existing = matrix.setdefault(area, {}).get(action)
        if existing is None or rank[state] > rank[existing]:
            matrix[area][action] = state
    return matrix


def backend_health(router: BackendRouter) -> dict[str, dict[str, Any]]:
    return {
        name: backend.health().to_dict()
        for name, backend in sorted(router.backends.items())
    }


def _annotation_name(annotation) -> str:
    if annotation is inspect.Parameter.empty:
        return "any"
    if isinstance(annotation, str):
        return annotation
    return getattr(annotation, "__name__", str(annotation).replace("typing.", ""))


def _normalized_annotation_type(annotation) -> str:
    if annotation is inspect.Parameter.empty or annotation is Any:
        return "any"
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in {types.UnionType} or str(origin) == "typing.Union":
        non_null = [item for item in args if item is not type(None)]
        if len(non_null) == 1:
            return _normalized_annotation_type(non_null[0])
        normalized = {_normalized_annotation_type(item) for item in non_null}
        if normalized <= {"string", "path"} and "path" in normalized:
            return "path"
        return normalized.pop() if len(normalized) == 1 else "any"
    if annotation in {str, Path}:
        return "path" if annotation is Path else "string"
    if annotation is bool:
        return "boolean"
    if annotation is int:
        return "integer"
    if annotation is float:
        return "number"
    if annotation is dict or origin is dict:
        return "object"
    if annotation in {list, tuple, set} or origin in {list, tuple, set} or "Sequence" in str(origin):
        item_type = _normalized_annotation_type(args[0]) if args else "any"
        return f"array[{item_type}]"
    return "any"


def _option_type(operation: str, parameter: inspect.Parameter, annotation=None) -> str:
    normalized = _normalized_annotation_type(
        parameter.annotation if annotation is None else annotation
    )
    if normalized != "any":
        return normalized
    if annotation is not None:
        return "any"
    annotated = _annotation_name(parameter.annotation)
    if annotated != "any":
        return annotated
    if parameter.default is not inspect.Parameter.empty and parameter.default is not None:
        return {
            bool: "boolean",
            int: "integer",
            float: "number",
            str: "string",
            list: "array",
            tuple: "array",
            dict: "object",
        }.get(type(parameter.default), "any")
    special = {
        ("table.merge", "start"): "array[integer, integer]",
        ("table.merge", "end"): "array[integer, integer]",
        ("table.set_row", "values"): "array[string]",
        ("table.set_column", "values"): "array[string]",
        ("bibliography.generate", "evidence_registry"): "path",
        ("citation.insert", "evidence_registry"): "path",
    }
    if (operation, parameter.name) in special:
        return special[(operation, parameter.name)]
    if parameter.name.endswith("_path") or parameter.name in {"data_source"}:
        return "path"
    if parameter.name in {
        "different_odd_even",
        "autofit",
        "repeat_header",
        "keep_rows_together",
    }:
        return "boolean"
    if parameter.name.endswith(("_cm", "_pt")):
        return "number"
    if parameter.name == "values":
        return "array[string]"
    if parameter.name == "custom":
        return "object"
    return "string"


_EXAMPLE_VALUES = {
    ("bookmark.rename", "old_name"): "OldBookmark",
    ("bookmark.rename", "new_name"): "NewBookmark",
    ("caption.insert", "label"): "Figure",
    ("content-control.create", "control_type"): "plain_text",
    ("field.insert", "field_type"): "PAGE",
    ("header-footer.set_text", "story"): "header",
    ("image.insert", "image_path"): "IMAGE.png",
    ("image.replace", "image_path"): "IMAGE.png",
    ("image.resize", "width_cm"): 5.0,
    ("mail-merge.execute", "data_source"): "DATA.csv",
    ("protection.protect", "mode"): "read_only",
    ("reference.hyperlink", "url"): "https://example.com",
    ("section.add", "break_type"): "new_page",
    ("style.clone", "source_name"): "Normal",
    **{
        (operation, "index"): 1
        for operation in (
            "comment.delete",
            "comment.reply",
            "comment.resolve",
            "comment.reopen",
            "revision.accept",
            "revision.reject",
        )
    },
}


def _option_example(operation: str, option: dict[str, Any]):
    explicit = _EXAMPLE_VALUES.get((operation, option["name"]))
    if explicit is not None:
        return explicit
    if "default" in option and option["default"] is not None:
        return option["default"]
    type_name = option["type"]
    if type_name == "integer":
        if option["name"] in {"rows", "columns"}:
            return 2
        return 0
    if type_name == "number":
        return 1.0
    if type_name == "boolean":
        return True
    if type_name.startswith("array[integer"):
        return [0, 0]
    if type_name.startswith("array"):
        return ["value"]
    if type_name == "object":
        return {}
    if type_name == "path":
        if "image" in option["name"]:
            return "IMAGE.png"
        return "EVIDENCE.json"
    return "value"


def _minimal_options_example(operation: str, options: list[dict[str, Any]]) -> dict:
    selected = [option for option in options if option["required"]]
    if operation == "reference.hyperlink":
        selected += [option for option in options if option["name"] == "url"]
    if operation == "image.resize":
        selected += [option for option in options if option["name"] == "width_cm"]
    return {
        option["name"]: _option_example(operation, option) for option in selected
    }


def _json_default(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return list(value)
    return repr(value)


def _callable_contract(operation: str) -> tuple[bool, list[dict[str, Any]]]:
    from .facade import _OPERATIONS, _READ_OPERATIONS

    function = (_OPERATIONS | _READ_OPERATIONS).get(operation)
    override = OPERATION_OPTION_OVERRIDES.get(operation)
    if function is None:
        override = NATIVE_OPTION_CONTRACTS.get(operation, override or [])
    if override is not None:
        selector_supported = bool(
            function is not None and "selector" in inspect.signature(function).parameters
        )
        return selector_supported, [
            {
                "name": name,
                "required": required,
                "type": type_name,
                **({} if required else {"default": default}),
            }
            for name, required, default, type_name in override
        ]
    if function is None:
        return False, []
    signature = inspect.signature(function)
    try:
        hints = get_type_hints(function)
    except (NameError, TypeError):
        hints = {}
    selector_supported = "selector" in signature.parameters
    options = []
    excluded = {"input_path", "source", "path", "output_path", "selector", "dry_run"}
    for parameter in signature.parameters.values():
        if (
            parameter.name in excluded
            or (operation == "text.edit" and parameter.name == "action")
            or parameter.kind in {
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
            }
        ):
            continue
        required = parameter.default is inspect.Parameter.empty
        option = {
            "name": parameter.name,
            "required": required,
            "type": _option_type(operation, parameter, hints.get(parameter.name)),
        }
        if not required:
            option["default"] = _json_default(parameter.default)
        options.append(option)
    return selector_supported, options


def operation_contracts(registry: OperationRegistry) -> dict[str, dict[str, Any]]:
    contracts = {}
    for spec in registry.all():
        selector_supported, options = _callable_contract(spec.name)
        routes = cli_routes_for(spec.name)
        rendered_routes = []
        for route in routes:
            family = route["family"]
            action = route["action"]
            command = f"wordassistant {family}"
            route_options = options
            if spec.name == "text.edit" and action in TEXT_ROUTE_OPTION_CONTRACTS:
                route_options = [
                    {
                        "name": name,
                        "required": required,
                        "type": type_name,
                        **({} if required else {"default": default}),
                    }
                    for name, required, default, type_name in TEXT_ROUTE_OPTION_CONTRACTS[action]
                ]
            if action:
                command += f" {action} INPUT.docx"
                if spec.mutating:
                    command += " --output OUTPUT.docx"
                if route_options:
                    command += " --options '{...}'"
            elif family in {"compare", "merge"}:
                command += " INPUT.docx OTHER.docx --output OUTPUT.docx"
            else:
                command += " INPUT.docx"
            command += " --json"
            rendered_routes.append({
                **route,
                "command_template": command,
                "options": route_options,
                "options_example": {
                    **_minimal_options_example(spec.name, route_options)
                },
            })
        contracts[spec.name] = {
            "mutating": spec.mutating,
            "output_required": spec.mutating,
            "selector_supported": selector_supported,
            "options": options,
            "options_example": _minimal_options_example(spec.name, options),
            "cli_routes": rendered_routes,
        }
    return contracts


def export_feature_matrix(registry: OperationRegistry, router: BackendRouter) -> dict:
    operations = []
    for spec in registry.all():
        records = evidence_for(spec.name)
        evidence = {}
        evidence_sources = {}
        evidence_runs = {}
        evidence_scope = {}
        for dimension in ("structural", "native_roundtrip", "dynamic_result", "visual"):
            record = records.get(dimension)
            if record is None:
                applicable = (
                    dimension == "structural" and spec.backend_preference[0] in {"python-docx", "ooxml"}
                ) or (dimension == "native_roundtrip" and "word-native" in spec.backend_preference)
                evidence[dimension] = "UNVERIFIED" if applicable else "NOT_APPLICABLE"
                evidence_sources[dimension] = []
                evidence_runs[dimension] = []
                evidence_scope[dimension] = None
            else:
                evidence[dimension] = str(record["status"])
                evidence_sources[dimension] = list(record.get("tests", []))
                evidence_runs[dimension] = list(record.get("runs", []))
                evidence_scope[dimension] = record.get("scope")
        operations.append(
            {
                "name": spec.name,
                "capability": spec.capability,
                "mutating": spec.mutating,
                "backend_preference": list(spec.backend_preference),
                "minimum_fidelity": spec.minimum_fidelity.value,
                "evidence": evidence,
                "evidence_sources": evidence_sources,
                "evidence_runs": evidence_runs,
                "evidence_scope": evidence_scope,
            }
        )
    return {"version": 1, "operations": operations}


def capabilities(
    registry: OperationRegistry | None = None,
    router: BackendRouter | None = None,
) -> dict:
    if registry is None and router is None:
        from .runtime import build_default_registry, build_default_router

        registry = build_default_registry()
        router = build_default_router(registry)
    elif (registry is None) != (router is None):
        raise ValueError("registry and router must be provided together")
    doc_status = status()
    backend_status = get_backend_status()
    result: dict[str, Any] = {
        "version": 1,
        "core": {
            "ready": doc_status["core_ready"],
            "commands": [
                "doctor", "capabilities", "inspect", "context", "create",
                "edit", "format", "list", "table", "image", "section",
                "page-number", "field", "toc", "caption", "reference",
                "comment", "revision", "protect", "properties", "mail-merge",
                "compare", "merge",
                "validate", "verify", "render", "profiles"
            ],
            "api_key_required": False,
        },
        "advanced_word": backend_status,
        "selector_schema": deepcopy(SELECTOR_SCHEMA),
    }
    if registry is not None and router is not None:
        statuses = operation_statuses(registry, router)
        result["backends"] = backend_health(router)
        result["operations"] = [spec.name for spec in registry.all()]
        result["operation_statuses"] = statuses
        result["matrix"] = capability_matrix(registry, router, statuses)
        result["operation_contracts"] = operation_contracts(registry)
    return result
