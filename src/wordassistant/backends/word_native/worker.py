from __future__ import annotations

import json
from pathlib import Path
import re
import sys

from .backend import WordNativeBackend, _default_com_factory, _discover_word_executable
from ...operations.models import OperationRequest


def _configure_standard_streams() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="strict")


def _emit_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def _write_owned_word_pid_handoff(destination: Path, process_id: int) -> None:
    temporary = destination.with_name(f"{destination.name}.tmp")
    temporary.write_text(str(process_id), encoding="utf-8")
    temporary.replace(destination)


def _persist_verified_fields(document, data: dict) -> dict:
    document.Save()
    result = dict(data)
    result["document_saved_after_evaluation"] = bool(document.Saved)
    return result


def _normalized_field_results(values: list[dict]) -> list[tuple]:
    def stable_instruction(value: object) -> str:
        # Word regenerates private TOC bookmark identifiers on every TOC
        # update even when the TOC is already current. Their numeric suffixes
        # are implementation details, not a visible/persisted result change.
        return re.sub(
            r"_Toc\d+(?=$|[\s\"'])",
            "_Toc#",
            str(value).strip(),
            flags=re.IGNORECASE,
        )

    # COM story traversal order is not a persistence property and can vary
    # between opens. Compare the field multiset, not enumeration order.
    normalized = []
    for field in values:
        instruction = stable_instruction(field.get("instruction", ""))
        result = str(field.get("result", "")).strip()
        # A PAGE field in a shared header/footer has one cached XML result but
        # Word evaluates it per physical page. COM may report the first or last
        # page represented by that story range across equivalent opens.
        if instruction.split(maxsplit=1)[0].upper() == "PAGE":
            result = "<contextual-page>"
        normalized.append(
            (
                int(field.get("type", 0)),
                instruction,
                result,
                bool(field.get("locked", False)),
            )
        )
    return sorted(normalized)


def _field_results_match(before: list[dict], after: list[dict]) -> bool:
    return bool(before) and _normalized_field_results(before) == _normalized_field_results(after)


def main() -> int:
    _configure_standard_streams()
    try:
        payload = json.loads(sys.stdin.read())
        pid_handoff = payload.get("owned_word_pid_handoff")
        backend = WordNativeBackend(
            com_factory=_default_com_factory,
            platform_name="Windows",
            word_executable=_discover_word_executable(),
            owned_word_pid_callback=(
                lambda process_id: _write_owned_word_pid_handoff(
                    Path(pid_handoff), process_id
                )
            )
            if pid_handoff
            else None,
        )
        if payload.get("action") == "health":
            health = backend.health()
            if not health.operational:
                _emit_json({"status": "ERROR", "message": health.reason})
                return 1
            _emit_json(
                {
                    "status": "SUCCESS",
                    "word_version": (health.details or {}).get("word_version"),
                }
            )
            return 0
        if payload.get("action") == "execute":
            request_data = payload["request"]
            result = backend.execute(
                OperationRequest(
                    name=request_data["name"],
                    input_path=Path(request_data["input_path"]) if request_data.get("input_path") else None,
                    output_path=Path(request_data["output_path"]) if request_data.get("output_path") else None,
                    options=request_data.get("options", {}),
                    dry_run=bool(request_data.get("dry_run", False)),
                    transaction_staging=bool(request_data.get("transaction_staging", False)),
                )
            )
            _emit_json(result.to_dict())
            return 0
        if payload.get("action") == "inspect_heading_numbering":
            path = Path(payload["input_path"])
            with backend._session(path) as (_, document):
                paragraphs = []
                for index in range(1, int(document.Paragraphs.Count) + 1):
                    list_format = document.Paragraphs(index).Range.ListFormat
                    paragraphs.append(
                        {
                            "list_type": int(list_format.ListType),
                            "list_string": str(list_format.ListString),
                        }
                    )
            _emit_json({"status": "SUCCESS", "paragraphs": paragraphs})
            return 0
        if payload.get("action") == "verify_fields":
            path = Path(payload["input_path"])
            with backend._session(path) as (application, document):
                before = backend._field_snapshot(document)
                data = backend._execute_document_operation(
                    application,
                    document,
                    OperationRequest("field.update_all", input_path=path),
                )
                data = _persist_verified_fields(document, data)
                data["source_results_were_current"] = _field_results_match(
                    before, data.get("fields", [])
                )
                if not data["source_results_were_current"]:
                    before_values = _normalized_field_results(before)
                    after_values = _normalized_field_results(data.get("fields", []))
                    data["field_freshness_comparison"] = {
                        "before_count": len(before_values),
                        "after_count": len(after_values),
                        "before_only": [list(value) for value in sorted(set(before_values) - set(after_values))[:10]],
                        "after_only": [list(value) for value in sorted(set(after_values) - set(before_values))[:10]],
                    }
            _emit_json({"status": "SUCCESS", "data": data})
            return 0
        _emit_json({"status": "ERROR", "message": "Unknown worker action"})
        return 2
    except Exception as exc:
        _emit_json({"status": "ERROR", "message": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
