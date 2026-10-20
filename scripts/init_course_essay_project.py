#!/usr/bin/env python3
"""Create a new course-essay workspace from the blank, no-overwrite starter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_course_essay_assets import ROOT, initialize_project


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="New project directory; it must not already exist")
    parser.add_argument("--title", required=True, help="Verified essay/project title")
    parser.add_argument("--template-dir", type=Path, default=ROOT / "templates" / "course-essay-starter")
    args = parser.parse_args()

    destination = initialize_project(args.template_dir, args.destination, args.title)
    print(json.dumps({"status": "created", "project_directory": str(destination)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
