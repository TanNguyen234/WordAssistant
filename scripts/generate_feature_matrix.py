from __future__ import annotations

import json
from pathlib import Path
import sys

from wordassistant.capabilities import export_feature_matrix
from wordassistant.runtime import build_default_registry, build_default_router


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    registry = build_default_registry()
    matrix = export_feature_matrix(registry, build_default_router(registry))
    destination = ROOT / "docs" / "word_feature_matrix.json"
    serialized = json.dumps(matrix, ensure_ascii=False, indent=2) + "\n"
    if "--check" in sys.argv[1:]:
        if not destination.is_file() or destination.read_text(encoding="utf-8") != serialized:
            print("feature-matrix: OUT_OF_SYNC")
            return 1
        print("feature-matrix: IN_SYNC")
        return 0
    destination.write_text(serialized, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
