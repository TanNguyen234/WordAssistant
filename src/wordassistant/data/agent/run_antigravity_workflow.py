"""Fail-closed phase runner for Antigravity repository workflows."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
from importlib.resources import files
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import stat
import subprocess
import sys
from typing import Any
from uuid import uuid4


def repository_root(start: Path) -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return Path(completed.stdout.strip()).resolve()


ROOT = Path.cwd().resolve()
DEFAULT_MANIFEST = ROOT / "antigravity-workflow.json"
ACTIVE_RUN_DIR: Path | None = None
PHASE_RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "status",
        "phase",
        "scope",
        "evidence",
        "next_phase",
        "gate_results",
    ],
    "properties": {
        "status": {"type": "string", "enum": ["PASS", "FAIL", "INCOMPLETE"]},
        "phase": {"type": "string"},
        "scope": {"type": "array", "items": {"type": "string"}},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "next_phase": {"type": ["string", "null"]},
        "gate_results": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["gate", "status", "evidence"],
                "properties": {
                    "gate": {"type": "string"},
                    "status": {"type": "string", "enum": ["PASS", "FAIL"]},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "write_allowlist": {"type": "array", "items": {"type": "string"}},
        "focused_test": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["severity", "summary", "evidence"],
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["HIGH", "MEDIUM", "LOW", "INFO"],
                    },
                    "summary": {"type": "string"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "request_contract": {
            "type": "object",
            "required": ["objective", "acceptance_criteria", "exclusions", "blockers"],
            "properties": {
                "objective": {"type": "string"},
                "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                "exclusions": {"type": "array", "items": {"type": "string"}},
                "blockers": {"type": "array", "items": {"type": "string"}},
            },
        },
        "discovery": {
            "type": "object",
            "required": ["bounded_query", "inspected_paths"],
            "properties": {
                "bounded_query": {"type": "string"},
                "inspected_paths": {"type": "array", "items": {"type": "string"}},
            },
        },
        "implementation": {
            "type": "object",
            "required": ["changed_paths"],
            "properties": {
                "changed_paths": {"type": "array", "items": {"type": "string"}}
            },
        },
        "test_result": {
            "type": "object",
            "required": [
                "command",
                "exit_code",
                "expected_invariant",
                "observed_invariant",
                "artifacts"
            ],
            "properties": {
                "command": {"type": "string"},
                "exit_code": {"type": "integer"},
                "expected_invariant": {"type": "string"},
                "observed_invariant": {"type": "string"},
                "artifacts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["path", "sha256", "role"],
                        "properties": {
                            "path": {"type": "string"},
                            "sha256": {"type": "string"},
                            "role": {
                                "type": "string",
                                "enum": ["input", "output", "evidence"]
                            }
                        }
                    }
                },
                "plan_sha256": {"type": "string"},
            },
        },
        "audit": {
            "type": "object",
            "required": ["changed_files", "contradictions", "unsupported_claims"],
            "properties": {
                "changed_files": {"type": "array", "items": {"type": "string"}},
                "contradictions": {"type": "array", "items": {"type": "string"}},
                "unsupported_claims": {"type": "array", "items": {"type": "string"}},
            },
        },
        "final_result": {
            "type": "object",
            "required": ["verdict", "reviewed_result_files", "unresolved_high_medium"],
            "properties": {
                "verdict": {"type": "string", "enum": ["PASS", "FAIL", "INCOMPLETE"]},
                "reviewed_result_files": {"type": "array", "items": {"type": "string"}},
                "unresolved_high_medium": {"type": "integer"},
            },
        },
    },
}


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    path = path or (ROOT / "antigravity-workflow.json")
    if not path.is_file():
        packaged = files("wordassistant.data.agent").joinpath("antigravity-workflow.json")
        return json.loads(packaged.read_text(encoding="utf-8"))
    return json.loads(path.read_text(encoding="utf-8"))


def _normal(path: str) -> str:
    value = path.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return str(PurePosixPath(value))


def _normal_allowed(path: str) -> str:
    normalized = _normal(path)
    return normalized + ("/" if path.replace("\\", "/").endswith("/") else "")


def out_of_scope_paths(
    changed_paths: set[str], allowed_paths: set[str]
) -> set[str]:
    normalized_allowed = {_normal_allowed(path) for path in allowed_paths}
    rejected: set[str] = set()
    for raw_path in changed_paths:
        path = _normal(raw_path)
        accepted = any(
            path == allowed.rstrip("/")
            or (allowed.endswith("/") and path.startswith(allowed))
            for allowed in normalized_allowed
        )
        if not accepted:
            rejected.add(path)
    return rejected


def validate_phase_result(
    result: dict[str, Any],
    *,
    expected_phase: str,
    phase_definition: dict[str, Any] | None = None,
    lane: str | None = None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    for key in ("status", "phase", "scope", "evidence", "next_phase"):
        if key not in result:
            reasons.append(f"missing required key: {key}")
    if result.get("phase") != expected_phase:
        reasons.append(
            f"phase mismatch: expected {expected_phase}, got {result.get('phase')}"
        )
    if result.get("status") not in {"PASS", "FAIL", "INCOMPLETE"}:
        reasons.append("status must be PASS, FAIL, or INCOMPLETE")
    if "scope" in result and not isinstance(result["scope"], list):
        reasons.append("scope must be a list")
    if "evidence" in result and not isinstance(result["evidence"], list):
        reasons.append("evidence must be a list")
    elif not result.get("evidence"):
        reasons.append("evidence must contain at least one observed item")
    if "scope" in result and not isinstance(result["scope"], list):
        reasons.append("scope must be a list")
    elif not result.get("scope"):
        reasons.append("scope must contain at least one bounded item")
    if phase_definition is not None:
        expected_gates = set(phase_definition.get("gates", []))
        gate_results = result.get("gate_results")
        if not isinstance(gate_results, list):
            reasons.append("gate_results must be a list")
        else:
            observed = {item.get("gate") for item in gate_results if isinstance(item, dict)}
            for missing in sorted(expected_gates - observed):
                reasons.append(f"missing gate result: {missing}")
            for extra in sorted(observed - expected_gates):
                reasons.append(f"unexpected gate result: {extra}")
            for item in gate_results:
                if not isinstance(item, dict):
                    reasons.append("gate result must be an object")
                    continue
                if item.get("status") != "PASS":
                    reasons.append(f"gate did not pass: {item.get('gate')}")
                if not item.get("evidence"):
                    reasons.append(f"gate lacks evidence: {item.get('gate')}")
    if expected_phase == "plan" and lane in {"change", "fix", "live_qa"}:
        allowlist = result.get("write_allowlist")
        if not isinstance(allowlist, list) or not allowlist:
            reasons.append("plan must declare a non-empty write_allowlist")
        if not isinstance(result.get("focused_test"), str) or not result.get(
            "focused_test", ""
        ).strip():
            reasons.append("plan must declare one focused_test")
    if expected_phase.startswith("review_") and not isinstance(
        result.get("findings"), list
    ):
        reasons.append("review must return a findings list")
    if expected_phase == "intake":
        contract = result.get("request_contract")
        if not isinstance(contract, dict):
            reasons.append("intake must return request_contract")
        else:
            if not str(contract.get("objective", "")).strip():
                reasons.append("request_contract objective is empty")
            for key in ("acceptance_criteria", "exclusions", "blockers"):
                if not isinstance(contract.get(key), list):
                    reasons.append(f"request_contract {key} must be a list")
            if not contract.get("acceptance_criteria"):
                reasons.append("request_contract acceptance_criteria is empty")
    if expected_phase == "discover":
        discovery = result.get("discovery")
        if not isinstance(discovery, dict) or not discovery.get("inspected_paths"):
            reasons.append("discover must return bounded inspected_paths")
    if expected_phase == "implement":
        implementation = result.get("implementation")
        if not isinstance(implementation, dict) or not isinstance(
            implementation.get("changed_paths"), list
        ):
            reasons.append("implement must return implementation.changed_paths")
        elif lane in {"change", "fix"} and result.get("status") == "PASS" and not implementation.get(
            "changed_paths"
        ):
            reasons.append("successful change/fix implementation cannot be a no-op")
    if expected_phase == "focused_test":
        test_result = result.get("test_result")
        if not isinstance(test_result, dict):
            reasons.append("focused_test must return test_result")
        elif result.get("status") == "PASS":
            if test_result.get("exit_code") != 0:
                reasons.append("focused_test PASS requires exit_code 0")
            for key in ("command", "expected_invariant", "observed_invariant"):
                if not str(test_result.get(key, "")).strip():
                    reasons.append(f"focused_test {key} is empty")
            if not test_result.get("artifacts"):
                reasons.append("focused_test artifacts are empty")
    if expected_phase.startswith("live_"):
        test_result = result.get("test_result")
        if not isinstance(test_result, dict):
            reasons.append(f"{expected_phase} must return test_result")
        elif result.get("status") == "PASS":
            allowed_exit_codes = (
                {0, 1} if expected_phase == "live_native_finalize" else {0}
            )
            if test_result.get("exit_code") not in allowed_exit_codes:
                reasons.append(f"{expected_phase} PASS requires exit_code 0")
            for key in ("command", "expected_invariant", "observed_invariant"):
                if not str(test_result.get(key, "")).strip():
                    reasons.append(f"{expected_phase} {key} is empty")
            if not test_result.get("artifacts"):
                reasons.append(f"{expected_phase} artifacts are empty")
            if len(str(test_result.get("plan_sha256", ""))) != 64:
                reasons.append(f"{expected_phase} requires frozen plan_sha256")
    if expected_phase == "constraint_audit":
        audit = result.get("audit")
        if not isinstance(audit, dict):
            reasons.append("constraint_audit must return audit")
        elif result.get("status") == "PASS" and (
            audit.get("contradictions") or audit.get("unsupported_claims")
        ):
            reasons.append("constraint_audit PASS cannot contain contradictions or unsupported claims")
    if expected_phase == "final_gate":
        final_result = result.get("final_result")
        if not isinstance(final_result, dict):
            reasons.append("final_gate must return final_result")
        elif result.get("status") == "PASS" and (
            final_result.get("verdict") != "PASS"
            or final_result.get("unresolved_high_medium") != 0
        ):
            reasons.append("final_gate PASS requires PASS verdict and zero unresolved high/medium")
        elif result.get("status") == "PASS" and not final_result.get(
            "reviewed_result_files"
        ):
            reasons.append("final_gate PASS requires non-empty reviewed_result_files")
    return not reasons, reasons


def resolve_allowed_paths(
    manifest: dict[str, Any], lane: str, caller_paths: list[str]
) -> set[str]:
    if lane in {"read_only", "live_qa"} and caller_paths:
        raise ValueError(f"{lane} does not accept caller-provided write paths")
    if lane == "live_qa":
        return set(manifest["constraints"]["live_qa_write_roots"])
    if lane == "read_only":
        return set()
    return {_normal_allowed(path) for path in caller_paths}


def resolve_run_dir(root: Path, requested: Path, lane: str) -> Path:
    resolved_root = root.resolve()
    run_dir = requested if requested.is_absolute() else resolved_root / requested
    run_dir = run_dir.resolve()
    safe_root = (
        resolved_root / "artifacts" / "antigravity-live-test"
        if lane == "live_qa"
        else resolved_root / "artifacts" / "antigravity-workflow"
    ).resolve()
    if not run_dir.is_relative_to(safe_root):
        raise ValueError(f"--run-dir must stay below {safe_root}")
    return run_dir


def required_phases(phase: dict[str, Any], lane: str) -> list[str]:
    return phase.get("requires_by_lane", {}).get(lane, phase.get("requires", []))


def phase_access(phase: dict[str, Any], lane: str) -> str:
    return phase.get("access_by_lane", {}).get(lane, phase["access"])


def word_review_applicable(request: str, planned_paths: set[str]) -> bool:
    text = request.casefold()
    semantic_pattern = re.compile(
        r"\b(docx|heading|pagination|field|section|citation|caption|bookmark)\b"
        r"|word document|table of contents|mục lục|phân trang"
    )
    word_prefixes = (
        "src/wordassistant/",
        "tests/core/",
        "tests/integration/",
        "tests/ooxml/",
        "tests/native_word/",
    )
    non_word_source = {"src/wordassistant/agent_runner.py"}
    return bool(semantic_pattern.search(text)) or any(
        path not in non_word_source and path.startswith(word_prefixes)
        for path in planned_paths
    )


def _phase(manifest: dict[str, Any], phase_id: str) -> dict[str, Any]:
    for phase in manifest["phases"]:
        if phase["id"] == phase_id:
            return phase
    raise ValueError(f"Unknown phase: {phase_id}")


def build_agy_command(
    manifest: dict[str, Any],
    *,
    phase_id: str,
    prompt: str,
    executable: str,
    timeout_seconds: int = 1800,
    workspace: Path = ROOT,
    expected_next: str | None = None,
    lane: str = "change",
    isolated_project: bool = False,
) -> list[str]:
    phase = _phase(manifest, phase_id)
    mode = "accept-edits" if phase_access(phase, lane) == "write" else "plan"
    execution = manifest["execution"]
    schema = copy.deepcopy(PHASE_RESULT_SCHEMA)
    if expected_next is not None:
        schema["properties"]["next_phase"] = {"const": expected_next}
    command = [
        executable,
        "--add-dir",
        str(workspace.resolve()),
        "--sandbox",
        "--dangerously-skip-permissions",
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(schema, separators=(",", ":")),
        "--model",
        execution["model"],
        "--mode",
        mode,
        "--print-timeout",
        f"{max(1, timeout_seconds)}s",
        "--print",
        prompt,
    ]
    effort = execution.get("effort")
    if effort:
        command.extend(["--effort", effort])
    if isolated_project:
        command.insert(1, "--new-project")
    return command


def build_phase_prompt(
    manifest: dict[str, Any],
    *,
    phase_id: str,
    request: str,
    previous_result: dict[str, Any] | None,
    allowed_paths: set[str],
    workspace: Path = ROOT,
    expected_next: str | None = None,
) -> str:
    phase = _phase(manifest, phase_id)
    prior = "none"
    if previous_result is not None:
        prior = json.dumps(previous_result, ensure_ascii=False)
        maximum = manifest["execution"]["max_previous_result_chars"]
        if len(prior) > maximum:
            raise ValueError(
                f"dependency handoff exceeds {maximum} characters; preserve a bounded result file instead"
            )
    phase_contracts = {
        "intake": "Also return request_contract with objective, acceptance_criteria[], exclusions[], and blockers[].",
        "discover": "Also return discovery with bounded_query and inspected_paths[].",
        "plan": "Also return write_allowlist[] and focused_test.",
        "implement": "Also return implementation.changed_paths[].",
        "focused_test": "Also return test_result with command, integer exit_code, expected_invariant, observed_invariant, and artifacts[].",
        "live_create_document": "Use wordassistant create followed by exactly one wordassistant compose call with --min-visible-characters 8000 and --max-visible-characters 14000. The content JSON must have 4-8 target sections, 6-12 subsections including at least three level-2 and two level-3 subsections, 45-70 content paragraphs, and 14-20 total citation placements. Content must be written directly as one UTF-8 JSON file; creating or executing Python/PowerShell/batch helper code is forbidden. Also return test_result with the exact public-CLI command log, exit_code, expected content/page invariant, observed invariant, and authored artifacts[].",
        "live_apply_features": "Use one wordassistant apply plan for compatible mutations and direct public commands only for non-batch/native operations. The plan must create a dedicated next-page section around the wide results table, set that section to landscape A4 (29.7 cm x 21.001 cm), and restore the following section to portrait A4 (21.001 cm x 29.7 cm). Creating or executing helper code and exploratory/throwaway DOCX files is forbidden. Also return test_result with the exact public-CLI command log, exit_code, expected feature invariant, observed invariant, and feature artifacts[].",
        "live_native_finalize": "Use field update-all with a distinct final-native DOCX output. Validate and audit that output, create provenance only after its hash is final, then run the first-pass verify with render once and no visual-review attestation. Exit code 1 is expected only when the result truthfully reports REVIEW_REQUIRED with a challenge token; report that exact exit code. Also return test_result with exact commands, expected native/page invariant, observed invariant, and artifacts[].",
        "live_visual_audit": "Inspect every page image from the predecessor render and preserve a visual-audit JSON. Do not mutate the DOCX. Complete the token-bound delivery verify only after inspection. Also return test_result with exact commands, exit_code, expected visual/delivery invariant, observed invariant, and artifacts[].",
        "live_negative_tests": "Also return test_result with the exact negative-suite commands, exit_code, expected rejection invariants, observed results, and artifacts[].",
        "constraint_audit": "Also return audit with changed_files[], contradictions[], and unsupported_claims[].",
        "review_architecture": "Also return findings[] with severity, summary, and evidence[].",
        "review_word_fidelity": "Also return findings[] with severity, summary, and evidence[].",
        "review_test_release": "Also return findings[] with severity, summary, and evidence[].",
        "final_gate": "Also return final_result with verdict, reviewed_result_files[], and unresolved_high_medium.",
    }
    cli_executable = ROOT / ".venv" / "Scripts" / "wordassistant.exe"
    public_cli = str(cli_executable.resolve()) if cli_executable.is_file() else "wordassistant"
    return f"""Follow the declared project phase contract and, for DOCX work, use $wordassistant.
You are executing exactly one state-machine phase: {phase_id}.
Single objective: {phase['objective']}
Workspace root: {workspace.resolve()}
Supported WordAssistant CLI executable: {public_cli}
Required next_phase value: {json.dumps(expected_next)}
User request: {request}
Immediate predecessor result only: {prior}
Allowed write paths: {json.dumps(sorted(allowed_paths), ensure_ascii=False)}
Required gates: {json.dumps(phase['gates'])}
Phase-specific result contract: {phase_contracts[phase_id]}

Do not perform another phase. Do not commit, push, rewrite history, delete
working functionality, expand scope, or claim unobserved evidence. Read only
the minimum needed. Do not invoke agy/Antigravity or this workflow runner from
inside a phase. Attempt the same failing invariant at most twice; after the
second failure, stop and report FAIL with exact evidence instead of retrying or
changing scope. Return exactly one JSON object and no Markdown with keys:
status (PASS|FAIL|INCOMPLETE), phase, scope (non-empty paths/contracts inspected
or changed), evidence (non-empty exact commands/artifacts/findings), next_phase,
and gate_results (one object per required gate with gate, PASS|FAIL, and
non-empty evidence). The plan phase must also return write_allowlist containing
exact file paths (or the fixed live-QA artifact root) and one focused_test
command. Reviewer phases must also return findings (an empty list is allowed
when no defect is found). A missing gate is INCOMPLETE. A contradiction or
out-of-scope write is FAIL.
For focused/live test_result artifacts, return objects with path, SHA-256, and
role (input, output, or evidence); every path must exist inside the workspace.
In live_create_document and live_apply_features, do not create scripts or source
files of any kind. A command that embeds a script, uses python -c, or invokes a
generated helper is a gate failure even when its final DOCX appears valid.
For live_visual_audit, preserve visual-audit.json as an object with status,
page_count, and pages[] entries containing path, sha256, status, and issues;
copy the final public verify JSON object verbatim to delivery-report.json.
Treat every predecessor output path as an immutable read-only baton: use it as
input exactly as supplied and always publish mutations to a distinct new path.
Invoke the supported WordAssistant CLI directly. Do not run uv, pip, package
installation, dependency resolution, or create/update any dependency lockfile.
"""


def _git_files(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [part.decode("utf-8") for part in completed.stdout.split(b"\0") if part]


def snapshot(root: Path, ignored_roots: set[str] | None = None) -> dict[str, str]:
    ignored = {_normal(path) for path in (ignored_roots or set())}
    result: dict[str, str] = {}
    for relative in _git_files(root):
        normalized = _normal(relative)
        if any(normalized.startswith(prefix) for prefix in ignored):
            continue
        path = root / relative
        if path.is_file():
            result[normalized] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def changed_since(before: dict[str, str], after: dict[str, str]) -> set[str]:
    return {
        path
        for path in set(before) | set(after)
        if before.get(path) != after.get(path)
    }


def delta_records(before: dict[str, str], after: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "path": path,
            "before_sha256": before.get(path),
            "after_sha256": after.get(path),
        }
        for path in sorted(changed_since(before, after))
    ]


def snapshot_id(value: dict[str, str]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compact_result_reference(
    run_dir: Path, phase_id: str, result: dict[str, Any]
) -> dict[str, Any]:
    path = run_dir / f"{phase_id}.result.json"
    severities = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for finding in result.get("findings", []):
        severity = finding.get("severity")
        if severity in severities:
            severities[severity] += 1
    return {
        "phase": phase_id,
        "status": result.get("status"),
        "result_file": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "severity_counts": severities,
    }


def verify_result_reference(reference: dict[str, Any]) -> None:
    path = Path(reference["result_file"])
    if not path.is_file():
        raise RuntimeError(f"result reference is missing: {path}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != reference["sha256"]:
        raise RuntimeError(
            f"result reference hash changed for {path}: expected {reference['sha256']}, got {actual}"
        )


def verify_artifact_records(
    records: list[dict[str, Any]], workspace: Path
) -> list[dict[str, str]]:
    verified: list[dict[str, str]] = []
    workspace = workspace.resolve()
    for record in records:
        if not isinstance(record, dict):
            raise RuntimeError("artifact record must be an object")
        raw_path = str(record.get("path", "")).strip()
        expected_hash = str(record.get("sha256", "")).casefold()
        role = str(record.get("role", ""))
        if not raw_path or len(expected_hash) != 64 or role not in {
            "input",
            "output",
            "evidence",
        }:
            raise RuntimeError(f"invalid artifact record: {record}")
        path = Path(raw_path)
        path = path.resolve() if path.is_absolute() else (workspace / path).resolve()
        if not path.is_relative_to(workspace):
            raise RuntimeError(f"artifact escapes live workspace: {path}")
        if not path.is_file():
            raise RuntimeError(f"artifact does not exist: {path}")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"artifact hash mismatch for {path}: expected {expected_hash}, got {actual_hash}"
            )
        verified.append({"path": str(path), "sha256": actual_hash, "role": role})
    return verified


_LIVE_HELPER_SUFFIXES = {".py", ".ps1", ".bat", ".cmd", ".js", ".ts"}


def _public_cli_json(arguments: list[str], workspace: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-m", "wordassistant", *arguments, "--json"],
        cwd=workspace,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "public WordAssistant invariant check failed: "
            + (completed.stderr.strip() or completed.stdout.strip())
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("public WordAssistant invariant check returned invalid JSON") from exc


def uses_wordassistant_subcommand(command: str, subcommand: str) -> bool:
    """Recognize a public CLI subcommand in bare or absolute Windows/POSIX form."""
    return bool(
        re.search(
            rf"(?:^|[\\/])wordassistant(?:\.exe)?[\"']?\s+{re.escape(subcommand)}(?:\s|$)",
            command,
            flags=re.IGNORECASE,
        )
    )


def bind_recovered_plan_hash(
    phase_id: str,
    result: dict[str, Any],
    *,
    recovered: bool,
    frozen_plan_sha256: str | None,
) -> None:
    """Bind runner-owned plan identity before validating recovered live output."""
    if not recovered or not phase_id.startswith("live_"):
        return
    if frozen_plan_sha256 is None:
        raise RuntimeError("Cannot resume live phase without a frozen plan")
    test_result = result.get("test_result")
    if isinstance(test_result, dict):
        test_result["plan_sha256"] = frozen_plan_sha256


def verify_live_authoring_invariants(
    phase_id: str,
    result: dict[str, Any],
    execution_root: Path,
    *,
    enforce_workspace_doc_count: bool = True,
) -> None:
    """Enforce deterministic black-box gates beyond an agent's own summary."""
    if phase_id not in {
        "live_create_document",
        "live_apply_features",
        "live_native_finalize",
        "live_visual_audit",
    }:
        return
    command = result["test_result"]["command"]
    forbidden_command = re.search(
        r"(?:\bpython(?:\.exe)?\b|\bpython\s+-c\b|\bpowershell\b|\bpwsh\b|\.(?:py|ps1|bat|cmd|js|ts)\b)",
        command,
        re.IGNORECASE,
    )
    if forbidden_command:
        raise RuntimeError(
            f"{phase_id} used forbidden helper execution: {forbidden_command.group(0)}"
        )
    helpers = sorted(
        str(path.relative_to(execution_root))
        for path in execution_root.rglob("*")
        if path.is_file() and path.suffix.casefold() in _LIVE_HELPER_SUFFIXES
    )
    if helpers:
        raise RuntimeError(f"{phase_id} created forbidden helper files: {', '.join(helpers)}")

    output_doc_records = [
        item
        for item in result["test_result"]["artifacts"]
        if item["role"] == "output" and Path(item["path"]).suffix.casefold() == ".docx"
    ]
    if not output_doc_records:
        raise RuntimeError(f"{phase_id} must publish an output DOCX")
    output_hashes = {item["sha256"] for item in output_doc_records}
    if len(output_doc_records) > 1 and len(output_hashes) == 1:
        selected_duplicate = next(
            (
                item
                for item in output_doc_records
                if ".wordassistant-handoff" in Path(item["path"]).parts
            ),
            output_doc_records[0],
        )
        for item in output_doc_records:
            if item is not selected_duplicate:
                item["role"] = "evidence"
        output_doc_records = [selected_duplicate]
    if len(output_doc_records) > 1 and phase_id != "live_create_document":
        raise RuntimeError(f"{phase_id} must publish exactly one output DOCX")
    if len(output_doc_records) > 1:
        ranked: list[tuple[int, dict[str, Any]]] = []
        for record in output_doc_records:
            candidate = _public_cli_json(["inspect", record["path"]], execution_root)
            visible = sum(
                len(str(item.get("text", "")).strip())
                for item in candidate.get("paragraphs_detail", [])
            )
            ranked.append((visible, record))
        ranked.sort(key=lambda item: item[0], reverse=True)
        if len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
            raise RuntimeError("live_create_document output DOCX baton is ambiguous")
        selected_record = ranked[0][1]
    else:
        selected_record = output_doc_records[0]
    for record in result["test_result"]["artifacts"]:
        if record["role"] == "output" and record is not selected_record:
            record["role"] = "evidence"
    output_docs = [Path(selected_record["path"])]
    if phase_id == "live_visual_audit":
        page_sets = [
            path
            for path in execution_root.rglob("set-*")
            if path.is_dir() and path.parent.name.endswith("-pages")
        ]
        if not page_sets:
            raise RuntimeError("live_visual_audit cannot locate immutable page images")
        latest_set = max(page_sets, key=lambda path: path.stat().st_mtime_ns)
        pages = sorted(latest_set.glob("page-*.png"))
        if not 18 <= len(pages) <= 25 or any(path.stat().st_size < 1024 for path in pages):
            raise RuntimeError(
                f"live_visual_audit page evidence is invalid: count={len(pages)}"
            )
        audit_files = list(execution_root.rglob("visual-audit.json"))
        delivery_files = list(execution_root.rglob("delivery-report.json"))
        if len(audit_files) != 1 or len(delivery_files) != 1:
            raise RuntimeError("live_visual_audit must preserve visual-audit.json and delivery-report.json")
        audit = json.loads(audit_files[0].read_text(encoding="utf-8"))
        delivery = json.loads(delivery_files[0].read_text(encoding="utf-8"))
        if audit.get("page_count") != len(pages) or audit.get("status") != "PASS":
            raise RuntimeError("live_visual_audit report does not cover every page")
        if delivery.get("delivery_status") != "PASS":
            raise RuntimeError("live_visual_audit delivery gate is not PASS")
        return

    all_docs = sorted(
        path
        for path in execution_root.rglob("*.docx")
        if ".wordassistant-handoff" not in path.parts
    )
    if enforce_workspace_doc_count:
        expected_doc_count = {
            "live_create_document": 2,
            "live_apply_features": 3,
            "live_native_finalize": 4,
        }[phase_id]
        if len(all_docs) != expected_doc_count:
            raise RuntimeError(
                f"{phase_id} expected {expected_doc_count} total DOCX artifacts, found {len(all_docs)}"
            )

    inspection = _public_cli_json(["inspect", str(output_docs[0])], execution_root)
    paragraphs = inspection.get("paragraphs_detail", [])
    substantive_characters = sum(len(str(item.get("text", "")).strip()) for item in paragraphs)
    heading_levels = [
        item.get("heading_level") for item in paragraphs if item.get("heading_level")
    ]
    if inspection.get("paragraphs", 0) < 40 or substantive_characters < 8_000:
        raise RuntimeError(
            f"{phase_id} content is not substantive: paragraphs={inspection.get('paragraphs')}, characters={substantive_characters}"
        )
    if heading_levels.count(2) < 3 or heading_levels.count(3) < 2:
        raise RuntimeError(f"{phase_id} lacks real Heading 2/3 hierarchy")

    if phase_id == "live_create_document":
        if substantive_characters > 14_000:
            raise RuntimeError(
                f"live_create_document exceeds the bounded content budget: characters={substantive_characters}"
            )
        if not uses_wordassistant_subcommand(command, "compose"):
            raise RuntimeError("live_create_document did not use wordassistant compose")
        if not re.search(r"--min-visible-characters\s+8000\b", command):
            raise RuntimeError("live_create_document omitted the minimum compose budget")
        if not re.search(r"--max-visible-characters\s+14000\b", command):
            raise RuntimeError("live_create_document omitted the maximum compose budget")
        controls = inspection.get("content_controls", 0)
        if not 14 <= controls <= 20:
            raise RuntimeError(
                f"live_create_document requires 14-20 evidence-linked citations; observed {controls}"
            )
        content_candidates: list[dict[str, Any]] = []
        for artifact in result["test_result"]["artifacts"]:
            path = Path(artifact["path"])
            if artifact["role"] != "input" or path.suffix.casefold() != ".json":
                continue
            try:
                candidate = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(candidate, dict) and isinstance(candidate.get("sections"), list):
                content_candidates.append(candidate)
        if len(content_candidates) != 1:
            raise RuntimeError("live_create_document must preserve exactly one content JSON input")
        content = content_candidates[0]
        sections = content["sections"]
        subsection_count = 0
        subsection_levels: list[int] = []
        content_paragraphs = 0
        citation_placements = 0
        for section in sections:
            raw_paragraphs = section.get("paragraphs", [])
            content_paragraphs += len(raw_paragraphs)
            for paragraph in raw_paragraphs:
                if isinstance(paragraph, dict):
                    citation_placements += len(paragraph.get("citations", []))
            subsections = section.get("subsections", [])
            subsection_count += len(subsections)
            for subsection in subsections:
                subsection_levels.append(subsection.get("level", 2))
                sub_paragraphs = subsection.get("paragraphs", [])
                content_paragraphs += len(sub_paragraphs)
                for paragraph in sub_paragraphs:
                    if isinstance(paragraph, dict):
                        citation_placements += len(paragraph.get("citations", []))
        if not 4 <= len(sections) <= 8:
            raise RuntimeError(f"live_create_document requires 4-8 content sections; observed {len(sections)}")
        if not 6 <= subsection_count <= 12:
            raise RuntimeError(f"live_create_document requires 6-12 subsections; observed {subsection_count}")
        if subsection_levels.count(2) < 3 or subsection_levels.count(3) < 2:
            raise RuntimeError("live_create_document requires at least three level-2 and two level-3 subsections")
        if not 45 <= content_paragraphs <= 70:
            raise RuntimeError(f"live_create_document requires 45-70 content paragraphs; observed {content_paragraphs}")
        if not 14 <= citation_placements <= 20:
            raise RuntimeError(f"live_create_document requires 14-20 citation placements; observed {citation_placements}")
        return

    if phase_id == "live_native_finalize":
        if inspection.get("fields", {}).get("toc_fields") != 3:
            raise RuntimeError("live_native_finalize must contain exactly TOC, LOF, and LOT")
        sidecar = output_docs[0].with_suffix(output_docs[0].suffix + ".wa-evidence.json")
        if not sidecar.is_file():
            raise RuntimeError("live_native_finalize is missing native field evidence")
        final_hash = hashlib.sha256(output_docs[0].read_bytes()).hexdigest()
        native_evidence = json.loads(sidecar.read_text(encoding="utf-8"))
        if native_evidence.get("sha256") != final_hash:
            raise RuntimeError("native field evidence is stale")
        provenance_files = list(execution_root.rglob("*.provenance.json"))
        if len(provenance_files) != 1:
            raise RuntimeError("live_native_finalize must preserve exactly one provenance manifest")
        provenance = json.loads(provenance_files[0].read_text(encoding="utf-8"))
        if provenance.get("document", {}).get("sha256") != final_hash:
            raise RuntimeError("academic provenance is not bound to the final-native DOCX")
        if provenance.get("audit_summary", {}).get("gate_counts", {}).get("FAIL", 0) != 0:
            raise RuntimeError("final-native integrity audit contains a FAIL gate")
        page_sets = [
            path
            for path in execution_root.rglob("set-*")
            if path.is_dir() and path.parent.name.endswith("-pages")
        ]
        if not page_sets:
            raise RuntimeError("live_native_finalize produced no immutable page set")
        latest_set = max(page_sets, key=lambda path: path.stat().st_mtime_ns)
        pages = sorted(latest_set.glob("page-*.png"))
        if not 18 <= len(pages) <= 25 or any(path.stat().st_size < 1024 for path in pages):
            raise RuntimeError(
                f"live_native_finalize must render 18-25 nonempty pages; observed {len(pages)}"
            )
        if not list(execution_root.glob("*.pdf")):
            raise RuntimeError("live_native_finalize produced no PDF")
        return

    if not any(
        item.get("orientation") == "landscape"
        for item in inspection.get("sections_detail", [])
    ):
        raise RuntimeError("live_apply_features produced no landscape section")
    levels = {item.get("level") for item in inspection.get("lists_detail", [])}
    if not {0, 1, 2}.issubset(levels):
        raise RuntimeError("live_apply_features lacks body-scoped three-level numbering")
    first_chapter = next(
        (
            item["index"]
            for item in paragraphs
            if str(item.get("text", "")).strip().casefold().startswith("chương 1:")
        ),
        None,
    )
    if first_chapter is None:
        raise RuntimeError("live_apply_features cannot locate CHƯƠNG 1 heading")
    incorrectly_numbered_front = [
        item.get("text", "")
        for item in paragraphs
        if item.get("index", 0) < first_chapter
        and item.get("heading_level")
        and item.get("numbering") is not None
    ]
    if incorrectly_numbered_front:
        raise RuntimeError("front matter headings are incorrectly numbered")
    images = inspection.get("images_detail", [])
    if not images or any(not item.get("alt_text") or not item.get("title") for item in images):
        raise RuntimeError("live_apply_features image metadata is missing")
    if inspection.get("bookmarks", 0) < 1:
        raise RuntimeError("live_apply_features produced no bookmark")
    field_types = {str(item.get("type", "")).upper() for item in inspection.get("fields_detail", [])}
    required_fields = {"TOC", "PAGE", "SEQ", "REF", "PAGEREF"}
    missing_fields = sorted(required_fields - field_types)
    if missing_fields or inspection.get("fields", {}).get("toc_fields", 0) < 3:
        raise RuntimeError(
            "live_apply_features missing required fields: " + ", ".join(missing_fields)
        )
    bibliography_headings = [
        item
        for item in paragraphs
        if str(item.get("text", "")).strip().casefold()
        in {"danh mục tài liệu tham khảo", "tài liệu tham khảo", "references", "bibliography"}
    ]
    if len(bibliography_headings) != 1:
        raise RuntimeError("live_apply_features must contain exactly one bibliography heading")


def freeze_live_output_baton(
    phase_id: str, result: dict[str, Any], execution_root: Path
) -> None:
    """Copy the single DOCX output to a runner-owned immutable handoff path."""
    records = result["test_result"]["artifacts"]
    output_docs = [
        record
        for record in records
        if record["role"] == "output"
        and Path(record["path"]).suffix.casefold() == ".docx"
    ]
    if len(output_docs) != 1:
        return
    record = output_docs[0]
    source = Path(record["path"]).resolve()
    records[:] = [
        item
        for item in records
        if not (
            item is not record
            and item["role"] == "evidence"
            and Path(item["path"]).suffix.casefold() == ".docx"
            and item["sha256"] == record["sha256"]
        )
    ]
    if ".wordassistant-handoff" in source.parts:
        return
    handoff_dir = execution_root / ".wordassistant-handoff"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    destination = handoff_dir / f"{phase_id}-{record['sha256']}.docx"
    if not destination.is_file():
        shutil.copy2(source, destination)
    actual_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
    if actual_hash != record["sha256"]:
        raise RuntimeError(f"{phase_id} immutable handoff hash mismatch")
    os.chmod(destination, stat.S_IREAD)
    record["path"] = str(destination.resolve())


def missing_handoff_outputs(
    predecessor_outputs: set[tuple[str, str]],
    current_inputs: set[tuple[str, str]],
) -> set[tuple[str, str]]:
    current_hashes = {sha256 for _, sha256 in current_inputs}
    return {
        item for item in predecessor_outputs if item[1] not in current_hashes
    }


def prepare_live_workspace(root: Path, run_dir: Path) -> Path:
    """Expose only public agent contracts to the live black-box agent."""
    if run_dir.exists() and any(run_dir.iterdir()):
        raise ValueError("live-QA run directory must be new and empty")
    run_dir.mkdir(parents=True, exist_ok=True)
    public_files = [
        "GEMINI.md",
        "wordassistant-agent.json",
        "antigravity-workflow.json",
        "README.md",
        "docs/AGENT_USAGE.md",
        "docs/ACADEMIC_INTEGRITY.md",
    ]
    for relative in public_files:
        source = root / relative
        destination = run_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    skill_source = root / ".agents" / "skills"
    skill_destination = run_dir / ".agents" / "skills"
    shutil.copytree(skill_source, skill_destination, dirs_exist_ok=True)
    return run_dir


def _extract_result(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if {"status", "phase"} <= set(value):
            return value
        for key in ("response", "result", "text", "content", "message"):
            if key in value:
                found = _extract_result(value[key])
                if found is not None:
                    return found
        for child in value.values():
            found = _extract_result(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _extract_result(child)
            if found is not None:
                return found
    elif isinstance(value, str):
        text = value.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].lstrip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None
        return _extract_result(parsed)
    return None


def run_phase(
    *,
    command: list[str],
    phase_id: str,
    root: Path,
    log_dir: Path,
    timeout_seconds: int,
    phase_definition: dict[str, Any],
    lane: str,
    environment: dict[str, str] | None = None,
    frozen_plan_sha256: str | None = None,
) -> dict[str, Any]:
    log_dir.mkdir(parents=True, exist_ok=True)
    popen_options: dict[str, Any] = {}
    if os.name == "nt":
        popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_options["start_new_session"] = True
    process = subprocess.Popen(
        command,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        **popen_options,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        _terminate_process_tree(process)
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        (log_dir / f"{phase_id}.stdout.json").write_text(stdout, encoding="utf-8")
        (log_dir / f"{phase_id}.stderr.txt").write_text(stderr, encoding="utf-8")
        raise RuntimeError(
            f"Antigravity phase {phase_id} exceeded {timeout_seconds}s; "
            "process tree terminated and partial logs preserved"
        ) from exc
    (log_dir / f"{phase_id}.stdout.json").write_text(
        stdout, encoding="utf-8"
    )
    (log_dir / f"{phase_id}.stderr.txt").write_text(
        stderr, encoding="utf-8"
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"Antigravity phase {phase_id} exited {process.returncode}; see {log_dir}"
        )
    try:
        envelope = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Phase {phase_id} did not return JSON") from exc
    result = _extract_result(envelope)
    if result is None:
        diagnostic = stderr.strip() or "no diagnostic from Antigravity"
        raise RuntimeError(
            f"Phase {phase_id} response lacks a machine result: {diagnostic}"
        )
    if phase_id.startswith("live_") and frozen_plan_sha256:
        test_result = result.get("test_result")
        if isinstance(test_result, dict):
            # The runner owns the frozen plan reference. Bind it
            # deterministically instead of relying on the model to copy a
            # 64-character value without transcription or omission errors.
            test_result["plan_sha256"] = frozen_plan_sha256
    ok, reasons = validate_phase_result(
        result,
        expected_phase=phase_id,
        phase_definition=phase_definition,
        lane=lane,
    )
    if not ok:
        raise RuntimeError(f"Invalid {phase_id} result: {'; '.join(reasons)}")
    return result


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    """Terminate and reap an Antigravity process group, including descendants."""
    if os.name == "nt":
        # A launcher may exit while a descendant keeps its inherited stdout or
        # stderr pipe open. In that race poll() reports completion although
        # communicate() still times out, and taskkill cannot traverse from a
        # PID that has already disappeared. Snapshot parent relationships and
        # stop descendants explicitly before attempting the root PID.
        shell = shutil.which("pwsh") or shutil.which("powershell.exe") or "powershell.exe"
        tree_script = r"""
$RootProcessId = [int]$env:WORDASSISTANT_ROOT_PROCESS_ID
$all = @(Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId)
$frontier = @($RootProcessId)
$seen = @{}
$seen[$RootProcessId] = $true
$levels = @()
while ($frontier.Count -gt 0) {
    $children = @(
        $all |
            Where-Object {
                $frontier -contains [int]$_.ParentProcessId -and
                -not $seen.ContainsKey([int]$_.ProcessId)
            } |
            ForEach-Object { [int]$_.ProcessId }
    )
    if ($children.Count -eq 0) { break }
    foreach ($childProcessId in $children) { $seen[$childProcessId] = $true }
    $levels += ,$children
    $frontier = $children
}
[array]::Reverse($levels)
foreach ($level in $levels) {
    foreach ($targetProcessId in $level) {
        Stop-Process -Id $targetProcessId -Force -ErrorAction SilentlyContinue
    }
}
Stop-Process -Id $RootProcessId -Force -ErrorAction SilentlyContinue
"""
        subprocess.run(
            [shell, "-NoProfile", "-NonInteractive", "-Command", tree_script],
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "WORDASSISTANT_ROOT_PROCESS_ID": str(process.pid)},
        )
    else:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    if process.poll() is None:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                process.kill()
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait(timeout=10)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Antigravity as small fail-closed repository phases."
    )
    parser.add_argument("--request", required=True)
    parser.add_argument(
        "--lane", choices=("read_only", "change", "fix", "live_qa"), required=True
    )
    parser.add_argument("--agy", default="agy.exe")
    parser.add_argument("--allow-write", action="append", default=[])
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume a validated run directory from its completed phase results.",
    )
    args = parser.parse_args(argv)
    if args.resume and args.run_dir is None:
        parser.error("--resume requires --run-dir")
    if args.resume and args.dry_run:
        parser.error("--resume cannot be combined with --dry-run")
    return args


def load_resume_results(
    *,
    run_dir: Path,
    lane: list[str],
    manifest: dict[str, Any],
    lane_name: str,
    execution_root: Path,
) -> dict[str, dict[str, Any]]:
    """Load only a contiguous, validated prefix of completed phase results."""
    loaded: dict[str, dict[str, Any]] = {}
    frozen_plan_sha256: str | None = None
    for phase_index, phase_id in enumerate(lane):
        path = run_dir / f"{phase_id}.result.json"
        recovered = False
        if path.is_file():
            result = json.loads(path.read_text(encoding="utf-8"))
        else:
            stdout_path = run_dir / f"{phase_id}.stdout.json"
            if not stdout_path.is_file():
                break
            raw_output = json.loads(stdout_path.read_text(encoding="utf-8"))
            result = _extract_result(raw_output)
            if result is None:
                break
            recovered = True
        phase = _phase(manifest, phase_id)
        bind_recovered_plan_hash(
            phase_id,
            result,
            recovered=recovered,
            frozen_plan_sha256=frozen_plan_sha256,
        )
        ok, reasons = validate_phase_result(
            result,
            expected_phase=phase_id,
            phase_definition=phase,
            lane=lane_name,
        )
        if not ok:
            raise RuntimeError(
                f"Cannot resume invalid {phase_id} result: {'; '.join(reasons)}"
            )
        expected_next = lane[phase_index + 1] if phase_index + 1 < len(lane) else None
        if result.get("next_phase") != expected_next:
            raise RuntimeError(
                f"Cannot resume {phase_id}: next_phase={result.get('next_phase')!r}, expected {expected_next!r}"
            )
        if phase_id == "plan":
            frozen_plan_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        if phase_id.startswith("live_"):
            if frozen_plan_sha256 is None:
                raise RuntimeError("Cannot resume live phase without a frozen plan")
            test_result = result["test_result"]
            if test_result.get("plan_sha256") != frozen_plan_sha256:
                raise RuntimeError(
                    f"Cannot resume {phase_id}: frozen plan hash mismatch"
                )
            test_result["artifacts"] = verify_artifact_records(
                test_result["artifacts"], execution_root
            )
            verify_live_authoring_invariants(
                phase_id,
                result,
                execution_root,
                enforce_workspace_doc_count=recovered,
            )
            freeze_live_output_baton(phase_id, result, execution_root)
            dependencies = [
                item
                for item in required_phases(phase, lane_name)
                if item in lane
            ]
            if phase_id != "live_create_document" and dependencies:
                predecessor = loaded[dependencies[0]]
                predecessor_outputs = {
                    (str(Path(item["path"]).resolve()), item["sha256"])
                    for item in predecessor["test_result"]["artifacts"]
                    if item["role"] == "output"
                }
                current_inputs = {
                    (item["path"], item["sha256"])
                    for item in test_result["artifacts"]
                    if item["role"] == "input"
                }
                missing = missing_handoff_outputs(
                    predecessor_outputs, current_inputs
                )
                if missing:
                    raise RuntimeError(
                        f"Cannot resume {phase_id}: artifact handoff is incomplete"
                    )
        if recovered:
            path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        loaded[phase_id] = result
    return loaded


def _execute(argv: list[str] | None = None) -> int:
    global ACTIVE_RUN_DIR, ROOT, DEFAULT_MANIFEST
    ACTIVE_RUN_DIR = None
    args = parse_args(argv)
    ROOT = repository_root(Path.cwd().resolve())
    DEFAULT_MANIFEST = ROOT / "antigravity-workflow.json"
    manifest = load_manifest(DEFAULT_MANIFEST)
    lane = manifest["lanes"][args.lane]
    requested_run_dir = args.run_dir or (
        ROOT
        / "artifacts"
        / ("antigravity-live-test" if args.lane == "live_qa" else "antigravity-workflow")
        / (
            datetime.now().strftime("run_%Y%m%d_%H%M%S_%f")
            + "_"
            + uuid4().hex[:8]
        )
    )
    try:
        write_ceiling = resolve_allowed_paths(manifest, args.lane, args.allow_write)
        run_dir = resolve_run_dir(ROOT, requested_run_dir, args.lane)
        ACTIVE_RUN_DIR = run_dir
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    allowed_paths = (
        set(manifest["constraints"]["live_qa_write_roots"])
        if args.lane == "live_qa"
        else set()
    )
    run_relative = run_dir.relative_to(ROOT.resolve())
    ignored = {_normal(str(run_relative)) + "/"}
    baseline = snapshot(ROOT, ignored)
    baseline_digest = snapshot_id(baseline)
    results: dict[str, dict[str, Any]] = {}
    frozen_plan_reference: dict[str, Any] | None = None

    if not args.dry_run and args.lane != "live_qa":
        run_dir.mkdir(parents=True, exist_ok=True)
    execution_root = ROOT
    phase_environment = os.environ.copy()
    if args.lane == "live_qa" and not args.dry_run:
        if args.resume:
            if not (run_dir / "GEMINI.md").is_file():
                raise ValueError("live-QA resume directory is missing public contracts")
            execution_root = run_dir
        else:
            execution_root = prepare_live_workspace(ROOT, run_dir)
        allowed_paths = {_normal_allowed(str(execution_root) + "/")}
        venv_scripts = ROOT / ".venv" / "Scripts"
        if venv_scripts.is_dir():
            phase_environment["PATH"] = (
                str(venv_scripts) + os.pathsep + phase_environment.get("PATH", "")
            )

    if args.resume:
        results.update(
            load_resume_results(
                run_dir=run_dir,
                lane=lane,
                manifest=manifest,
                lane_name=args.lane,
                execution_root=execution_root,
            )
        )

    for phase_index, phase_id in enumerate(lane):
        if phase_id in results:
            if phase_id == "plan":
                frozen_plan_reference = compact_result_reference(
                    run_dir, "plan", results["plan"]
                )
            continue
        phase = _phase(manifest, phase_id)
        phase_dependencies = [
            dependency
            for dependency in required_phases(phase, args.lane)
            if dependency in lane
        ]
        missing = [
            dependency
            for dependency in phase_dependencies
            if dependency not in results
        ]
        if missing:
            raise RuntimeError(
                f"phase {phase_id} is missing prerequisites: {', '.join(missing)}"
            )
        dependencies = phase_dependencies
        prior_results = [results[item] for item in dependencies]
        previous: dict[str, Any] | None
        if not prior_results:
            previous = None
        elif len(prior_results) == 1:
            previous = prior_results[0]
        else:
            if phase_id == "final_gate" and not args.dry_run:
                previous = {
                    "dependency_result_files": [
                        compact_result_reference(run_dir, dependency, results[dependency])
                        for dependency in dependencies
                    ]
                }
            else:
                previous = {"dependency_results": prior_results}
        if phase_id == "constraint_audit":
            monitor_records = delta_records(baseline, snapshot(ROOT, ignored))
            delta_path = run_dir / "workflow-delta-before-audit.json"
            if not args.dry_run:
                delta_path.write_text(
                    json.dumps(monitor_records, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            previous = {
                "dependency_result": previous,
                "deterministic_monitor": {
                    "baseline_sha256": baseline_digest,
                    "delta_file": str(delta_path),
                    "changed_files": monitor_records,
                },
            }
        if phase_id.startswith("live_"):
            if frozen_plan_reference is None:
                if args.dry_run:
                    frozen_plan_reference = {
                        "phase": "plan",
                        "status": "PASS",
                        "result_file": "dry-run://plan.result.json",
                        "sha256": "0" * 64,
                        "severity_counts": {
                            "HIGH": 0,
                            "MEDIUM": 0,
                            "LOW": 0,
                            "INFO": 0,
                        },
                    }
                else:
                    frozen_plan_reference = compact_result_reference(
                        run_dir, "plan", results["plan"]
                    )
            if not args.dry_run:
                verify_result_reference(frozen_plan_reference)
            previous = {
                "dependency_result": previous,
                "frozen_plan": frozen_plan_reference,
            }
        expected_next = lane[phase_index + 1] if phase_index + 1 < len(lane) else None
        prompt = build_phase_prompt(
            manifest,
            phase_id=phase_id,
            request=args.request,
            previous_result=previous,
            allowed_paths=allowed_paths,
            workspace=execution_root,
            expected_next=expected_next,
        )
        command = build_agy_command(
            manifest,
            phase_id=phase_id,
            prompt=prompt,
            executable=args.agy,
            timeout_seconds=args.timeout_seconds,
            workspace=execution_root,
            expected_next=expected_next,
            lane=args.lane,
            isolated_project=args.lane == "live_qa",
        )
        if args.dry_run:
            print(json.dumps({"phase": phase_id, "command": command}, ensure_ascii=False))
            results[phase_id] = {
                "status": "PASS",
                "phase": phase_id,
                "scope": ["dry-run"],
                "evidence": ["command emitted"],
                "next_phase": (
                    lane[phase_index + 1] if phase_index + 1 < len(lane) else None
                ),
            }
            continue
        phase_before = snapshot(ROOT, ignored)
        result: dict[str, Any] | None = None
        phase_error: Exception | None = None
        try:
            result = run_phase(
                command=command,
                phase_id=phase_id,
                root=execution_root,
                log_dir=run_dir,
                timeout_seconds=args.timeout_seconds,
                phase_definition=phase,
                lane=args.lane,
                environment=phase_environment,
                frozen_plan_sha256=(
                    frozen_plan_reference["sha256"]
                    if phase_id.startswith("live_") and frozen_plan_reference
                    else None
                ),
            )
        except Exception as exc:
            phase_error = exc
        current = snapshot(ROOT, ignored)
        phase_allowed = (
            allowed_paths if phase_access(phase, args.lane) == "write" else set()
        )
        phase_violations = out_of_scope_paths(
            changed_since(phase_before, current), phase_allowed
        )
        if phase_violations:
            raise RuntimeError(
                f"constraint monitor rejected {phase_id} changes: "
                + ", ".join(sorted(phase_violations))
            ) from phase_error
        if phase_error is not None:
            raise phase_error
        assert result is not None
        observed_phase_paths = sorted(changed_since(phase_before, current))
        if phase_id == "implement":
            claimed = sorted(result["implementation"]["changed_paths"])
            if claimed != observed_phase_paths:
                raise RuntimeError(
                    f"implement changed_paths mismatch: claimed={claimed}, observed={observed_phase_paths}"
                )
        if phase_id == "focused_test" and args.lane in {"change", "fix"}:
            if result["test_result"]["command"] != results["plan"]["focused_test"]:
                raise RuntimeError("focused_test command differs from the frozen plan")
        if phase_id == "constraint_audit":
            expected_audit_paths = sorted(changed_since(baseline, current))
            claimed_audit_paths = sorted(result["audit"]["changed_files"])
            if claimed_audit_paths != expected_audit_paths:
                raise RuntimeError(
                    "constraint audit changed_files mismatch: "
                    f"claimed={claimed_audit_paths}, observed={expected_audit_paths}"
                )
        if phase_id.startswith("live_"):
            plan_reference = previous["frozen_plan"] if previous else None
            verify_result_reference(plan_reference)
            if result["test_result"]["plan_sha256"] != plan_reference["sha256"]:
                raise RuntimeError(f"{phase_id} did not bind to the frozen plan hash")
            verified_artifacts = verify_artifact_records(
                result["test_result"]["artifacts"], execution_root
            )
            result["test_result"]["artifacts"] = verified_artifacts
            verify_live_authoring_invariants(phase_id, result, execution_root)
            freeze_live_output_baton(phase_id, result, execution_root)
            outputs = {
                (item["path"], item["sha256"])
                for item in verified_artifacts
                if item["role"] == "output"
            }
            if phase_id in {
                "live_create_document",
                "live_apply_features",
                "live_native_finalize",
                "live_visual_audit",
            } and not outputs:
                raise RuntimeError(f"{phase_id} produced no output artifact")
            if phase_id != "live_create_document":
                predecessor_id = dependencies[0]
                predecessor_outputs = {
                    (str(Path(item["path"]).resolve()), item["sha256"])
                    for item in results[predecessor_id]["test_result"]["artifacts"]
                    if item["role"] == "output"
                }
                current_inputs = {
                    (item["path"], item["sha256"])
                    for item in verified_artifacts
                    if item["role"] == "input"
                }
                missing_inputs = missing_handoff_outputs(
                    predecessor_outputs, current_inputs
                )
                if not predecessor_outputs or missing_inputs:
                    raise RuntimeError(
                        f"{phase_id} artifact handoff is missing {predecessor_id} outputs: "
                        + ", ".join(path for path, _ in sorted(missing_inputs))
                    )
        if phase_id == "final_gate":
            references = previous.get("dependency_result_files", []) if previous else []
            expected_files = sorted(item["result_file"] for item in references)
            reviewed_files = sorted(result["final_result"]["reviewed_result_files"])
            if reviewed_files != expected_files:
                raise RuntimeError(
                    "final_gate reviewed_result_files mismatch: "
                    f"claimed={reviewed_files}, expected={expected_files}"
                )
            stale_references = [
                item["result_file"]
                for item in references
                if hashlib.sha256(Path(item["result_file"]).read_bytes()).hexdigest()
                != item["sha256"]
            ]
            if stale_references:
                raise RuntimeError(
                    "final_gate reviewer evidence hash mismatch: "
                    + ", ".join(stale_references)
                )
        if result["next_phase"] != expected_next:
            raise RuntimeError(
                f"phase {phase_id} proposed next_phase={result['next_phase']!r}; "
                f"expected {expected_next!r}"
            )
        if phase_id == "plan":
            raw_planned = result.get("write_allowlist", [])
            planned = {_normal_allowed(path) for path in raw_planned}
            if args.lane == "live_qa":
                fixed = allowed_paths
                outside_fixed = out_of_scope_paths(planned, fixed)
                if not fixed.issubset(planned) or outside_fixed:
                    raise RuntimeError("live_qa plan changed its fixed artifact-only allowlist")
            else:
                directory_entries = {
                    path for path in raw_planned if path.replace("\\", "/").endswith("/")
                }
                if directory_entries:
                    raise RuntimeError(
                        "change/fix plan must list exact files, not directories: "
                        + ", ".join(sorted(directory_entries))
                    )
                if write_ceiling:
                    outside_ceiling = out_of_scope_paths(planned, write_ceiling)
                    if outside_ceiling:
                        raise RuntimeError(
                            "plan exceeds caller write ceiling: "
                            + ", ".join(sorted(outside_ceiling))
                        )
                allowed_paths = planned
                if not word_review_applicable(args.request, planned):
                    lane.remove("review_word_fidelity")
        results[phase_id] = result
        result_path = run_dir / f"{phase_id}.result.json"
        result_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        violations = out_of_scope_paths(changed_since(baseline, current), allowed_paths)
        if violations:
            raise RuntimeError(
                "constraint monitor rejected out-of-scope changes: "
                + ", ".join(sorted(violations))
            )
        if result["status"] != "PASS":
            raise RuntimeError(
                f"phase {phase_id} stopped fail-closed with {result['status']}"
            )
        if phase_id.startswith("review_"):
            unresolved = [
                finding
                for review_id, review in results.items()
                if review_id.startswith("review_")
                for finding in review.get("findings", [])
                if finding.get("severity") in {"HIGH", "MEDIUM"}
            ]
            if expected_next == "final_gate" and unresolved:
                raise RuntimeError(
                    f"review council blocked final_gate with {len(unresolved)} unresolved high/medium findings"
                )
    if not args.dry_run:
        summary = {
            "status": "PASS",
            "lane": args.lane,
            "run_dir": str(run_dir),
            "phases": [compact_result_reference(run_dir, item, results[item]) for item in lane],
        }
        (run_dir / "workflow-summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(summary, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return _execute(argv)
    except Exception as exc:
        summary: dict[str, Any] = {
            "status": "FAIL",
            "reason": str(exc),
            "run_dir": None,
        }
        try:
            args = parse_args(argv)
            if ACTIVE_RUN_DIR is not None:
                run_dir = ACTIVE_RUN_DIR
            else:
                requested = args.run_dir or (
                    ROOT
                    / "artifacts"
                    / (
                        "antigravity-live-test"
                        if args.lane == "live_qa"
                        else "antigravity-workflow"
                    )
                    / datetime.now().strftime("run_%Y%m%d_%H%M%S")
                )
                run_dir = resolve_run_dir(ROOT, requested, args.lane)
            summary["lane"] = args.lane
            summary["run_dir"] = str(run_dir)
            safe_to_record = not args.dry_run and (
                args.lane != "live_qa" or (
                run_dir.is_dir() and (run_dir / "GEMINI.md").is_file()
                )
            )
            if safe_to_record:
                run_dir.mkdir(parents=True, exist_ok=True)
                result_files = sorted(run_dir.glob("*.result.json"))
                summary["completed_results"] = [str(path) for path in result_files]
                (run_dir / "workflow-summary.json").write_text(
                    json.dumps(summary, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
        except Exception as summary_error:
            summary["summary_error"] = str(summary_error)
        print(json.dumps(summary, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
