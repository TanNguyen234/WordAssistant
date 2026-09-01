"""Installed entry point for the packaged Antigravity workflow runner."""

from __future__ import annotations

from importlib.resources import as_file, files
import runpy
from typing import Any


def main() -> int:
    resource = files("wordassistant.data.agent").joinpath(
        "run_antigravity_workflow.py"
    )
    with as_file(resource) as path:
        namespace: dict[str, Any] = runpy.run_path(str(path))
    return int(namespace["main"]())
