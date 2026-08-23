from __future__ import annotations
from pathlib import Path
from typing import Any
import json
import os
import tempfile

class EvidenceError(ValueError):
    pass

_REQUIRED_FIELDS = {'id', 'title', 'authors', 'year', 'url', 'verified_by'}
_ALLOWED_FIELDS = {'id', 'title', 'authors', 'year', 'url', 'verified_by', 'quote', 'claim', 'doi', 'notes', 'tags'}

def validate_record(record: Any) -> None:
    if not isinstance(record, dict):
        raise EvidenceError("Evidence record must be a JSON object")
    
    missing = _REQUIRED_FIELDS - set(record.keys())
    if missing:
        raise EvidenceError(f"Missing evidence field(s): {sorted(missing)}")
        
    unknown = set(record.keys()) - _ALLOWED_FIELDS
    if unknown:
        raise EvidenceError(f"Unknown evidence field(s): {sorted(unknown)}")
        
    if not isinstance(record['id'], str) or not record['id'].strip():
        raise EvidenceError("Field 'id' must be a non-empty string")
        
    if not isinstance(record['title'], str) or not record['title'].strip():
        raise EvidenceError("Field 'title' must be a non-empty string")
        
    authors = record['authors']
    if not isinstance(authors, list) or not authors or any(not isinstance(a, str) or not a.strip() for a in authors):
        raise EvidenceError("Field 'authors' must be a non-empty array of non-empty strings")
        
    year = record['year']
    if type(year) is not int or not (1800 <= year <= 2100):
        raise EvidenceError(f"Field 'year' must be an integer between 1800 and 2100, got {year!r}")
        
    url = str(record['url']).strip()
    if not (url.startswith(('http://', 'https://', 'doi:'))):
        raise EvidenceError("Field 'url' must be an absolute http(s) URL or doi URI")
        
    if not isinstance(record['verified_by'], str) or not record['verified_by'].strip():
        raise EvidenceError("Field 'verified_by' must be a non-empty string")

class EvidenceRegistry:
    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        
    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except Exception as exc:
            raise EvidenceError(f"Failed to read evidence registry {self.path}: {exc}") from exc
        if not isinstance(data, dict):
            raise EvidenceError("Registry must be a JSON object")
        return data

    def _save(self, data: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(
            prefix=f".{self.path.name}_",
            suffix=".tmp",
            dir=self.path.parent
        )
        os.close(tmp_fd)
        try:
            Path(tmp_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            os.replace(tmp_path, self.path)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            raise

    def add(self, record: dict[str, Any], replace: bool = False) -> None:
        validate_record(record)
        rec_id = str(record['id']).strip()
        data = self._load()
        if rec_id in data and not replace:
            raise EvidenceError(f"Evidence record with id '{rec_id}' already exists; use replace=True to overwrite.")
        data[rec_id] = record
        self._save(data)

    def get(self, key: str) -> dict[str, Any]:
        data = self._load()
        if key not in data:
            raise EvidenceError(f"Evidence record '{key}' not found.")
        return data[key]

    def remove(self, key: str) -> bool:
        data = self._load()
        if key in data:
            del data[key]
            self._save(data)
            return True
        return False

    def list(self) -> list[dict[str, Any]]:
        return list(self._load().values())

    def validate_all(self) -> list[str]:
        errors = []
        data = self._load()
        for k, v in data.items():
            try:
                validate_record(v)
            except EvidenceError as e:
                errors.append(f"Record '{k}': {e}")
        return errors
