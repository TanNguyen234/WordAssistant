from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# VietLex paths used for this report. Supply --paths for another project; this
# list is intentionally not presented as a universal software-project inventory.
DEFAULT_FILES = [
    "README.md",
    "FEATURE_STATUS.md",
    "app/main.py",
    "app/config.py",
    "app/api/routes.py",
    "app/api/legal_routes.py",
    "app/api/legal_registry_routes.py",
    "app/api/workspace_routes.py",
    "app/services/rag_pipeline.py",
    "app/services/retrieval.py",
    "app/services/vertex_qdrant_retrieval.py",
    "app/services/v3_article_expansion.py",
    "app/ingestion/legal_text.py",
    "app/templates/index.html",
    "app/templates/legal_search.html",
    "app/templates/legal_document.html",
    "app/templates/chat_message.html",
    "app/templates/product_nav.html",
    "docs/CURRENT_ARCHITECTURE.md",
    "docs/evaluation/CURRENT_STATUS.md",
    "docs/verification/production-release-20261018-01/cancel-fix-20261019-01/REPORT.md",
]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _git_status(root: Path, workspace: Path) -> str:
    command = ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"]
    pathspecs = [".", ":(exclude)artifacts/**", ":(exclude).tmp-*"]
    try:
        relative_workspace = workspace.relative_to(root).as_posix()
    except ValueError:
        pass
    else:
        if not relative_workspace.startswith("artifacts/"):
            pathspecs.append(f":(exclude){relative_workspace}/**")
    command.extend(["--", *pathspecs])
    return subprocess.check_output(command, text=True)


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def capture(project_root: Path, workspace: Path, relative_files: list[str]) -> dict[str, Any]:
    root = project_root.resolve()
    report_workspace = workspace.resolve()
    project_path = report_workspace / "project.json"
    if not (root / ".git").exists() and not (root / ".git").is_file():
        raise ValueError(f"Project root is not a Git checkout: {root}")
    if not project_path.is_file():
        raise FileNotFoundError(f"Workspace project.json does not exist: {project_path}")

    head = _git(root, "rev-parse", "HEAD")
    status = _git_status(root, report_workspace)
    status_hash = _sha256(status.encode("utf-8"))
    captured_at = datetime.now().astimezone().isoformat(timespec="seconds")
    files = []
    for relative in relative_files:
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"Source path escapes the project root: {relative}")
        if not path.is_file():
            continue
        content = path.read_bytes()
        files.append(
            {
                "path": Path(relative).as_posix(),
                "sha256": _sha256(content),
                "bytes": len(content),
                "lines": len(content.decode("utf-8", errors="replace").splitlines()),
            }
        )

    manifest = {
        "schema_version": 1,
        "captured_at": captured_at,
        "project_root": str(root),
        "git_head": head,
        "git_worktree": "dirty" if status else "clean",
        "git_status_line_count": len(status.splitlines()),
        "git_status_sha256": status_hash,
        "source_read_policy": "read-only; .env values, database contents, live providers and runtime were not read or called",
        "files": files,
        "source_hierarchy": [
            "current source/config",
            "current architecture and evaluation status documents",
            "historical receipts with their dated labels",
            "academic literature for general methods only",
        ],
    }

    project = json.loads(project_path.read_text(encoding="utf-8"))
    project.update(
        {
            "source_project_root": str(root),
            "source_revision": f"{head} ({'dirty' if status else 'clean'} source worktree; status SHA-256 {status_hash})",
            "source_manifest_file": "source/source_manifest.json",
            "source_snapshot_rerun": captured_at,
        }
    )
    _atomic_json(report_workspace / "source" / "source_manifest.json", manifest)
    _atomic_json(project_path, project)
    return {
        "status": "PASS",
        "captured_at": captured_at,
        "project_root": str(root),
        "workspace": str(report_workspace),
        "git_head": head,
        "git_worktree": manifest["git_worktree"],
        "file_count": len(files),
        "manifest": str(report_workspace / "source" / "source_manifest.json"),
        "project": str(project_path),
    }


def _discover_git_root(start: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(f"Could not find a Git project root from {start}")
    return Path(result.stdout.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Capture hashes for selected source files without changing the source project."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        help="Source project Git root (default: nearest Git root above this script)",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Essay workspace containing project.json (default: this script's directory)",
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        default=DEFAULT_FILES,
        metavar="RELATIVE_PATH",
        help="Source files to hash; defaults to the VietLex inventory in this case workspace",
    )
    args = parser.parse_args(argv)
    try:
        root = args.project_root or _discover_git_root(args.workspace.resolve())
        result = capture(root, args.workspace, args.paths)
    except (OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"capture_source_snapshot: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
