from __future__ import annotations

import os
from pathlib import Path
import tempfile


def atomic_save(document, output_path: str | Path) -> Path:
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.stem}.", suffix=output.suffix, dir=output.parent
    )
    os.close(descriptor)
    try:
        document.save(temporary_name)
        os.replace(temporary_name, output)
    finally:
        Path(temporary_name).unlink(missing_ok=True)
    return output

