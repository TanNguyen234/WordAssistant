from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid
from typing import Callable

from .operations.models import OperationRequest, OperationResult


@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str
    source_path: str
    snapshot_path: str
    sha256: str
    operation: str
    created_at: str


class CheckpointStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def create(self, source: str | Path, *, operation: str) -> Checkpoint:
        source_path = Path(source).resolve()
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        self.root.mkdir(parents=True, exist_ok=True)
        checkpoint_id = uuid.uuid4().hex
        snapshot = self.root / f"{checkpoint_id}{source_path.suffix}"
        shutil.copy2(source_path, snapshot)
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            source_path=str(source_path),
            snapshot_path=str(snapshot),
            sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
            operation=operation,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        (self.root / f"{checkpoint_id}.json").write_text(
            json.dumps(asdict(checkpoint), indent=2), encoding="utf-8"
        )
        return checkpoint

    def list(self) -> list[Checkpoint]:
        if not self.root.exists():
            return []
        checkpoints: list[Checkpoint] = []
        for metadata in sorted(self.root.glob("*.json")):
            checkpoints.append(
                Checkpoint(**json.loads(metadata.read_text(encoding="utf-8")))
            )
        return checkpoints

    def get(self, checkpoint_id: str) -> Checkpoint:
        metadata = self.root / f"{checkpoint_id}.json"
        if not metadata.is_file():
            raise KeyError(f"Checkpoint not found: {checkpoint_id}")
        return Checkpoint(**json.loads(metadata.read_text(encoding="utf-8")))

    def restore(
        self, checkpoint_id: str, *, output_path: str | Path | None = None
    ) -> Path:
        checkpoint = self.get(checkpoint_id)
        snapshot = Path(checkpoint.snapshot_path)
        if hashlib.sha256(snapshot.read_bytes()).hexdigest() != checkpoint.sha256:
            raise ValueError(f"Checkpoint hash mismatch: {checkpoint_id}")
        destination = Path(output_path or checkpoint.source_path).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(snapshot, destination)
        return destination


class TransactionCoordinator:
    def __init__(self, checkpoint_store: CheckpointStore):
        self.checkpoint_store = checkpoint_store

    def execute(
        self,
        request: OperationRequest,
        mutate: Callable[[Path], OperationResult],
        validate: Callable[[Path], None] | None = None,
    ) -> OperationResult:
        if request.input_path is None:
            raise ValueError("Mutating transaction requires input_path")
        source = request.input_path.resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        output = (request.output_path or source).resolve()

        if request.checkpoint in (True, "auto"):
            self.checkpoint_store.create(source, operation=request.name)

        output.parent.mkdir(parents=True, exist_ok=True)
        fd, staging_name = tempfile.mkstemp(
            prefix=f".{output.stem}.", suffix=output.suffix, dir=output.parent
        )
        os.close(fd)
        staging = Path(staging_name)
        try:
            shutil.copy2(source, staging)
            result = mutate(staging)
            if validate is not None:
                validate(staging)
            if request.dry_run:
                result.status = "DRY_RUN"
                result.output_path = None
                return result
            os.replace(staging, output)
            result.output_path = output
            return result
        finally:
            staging.unlink(missing_ok=True)
