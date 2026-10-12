from __future__ import annotations
from pathlib import Path
from typing import Any
import json
import os
import tempfile
import time
import urllib.parse
import hashlib
import re
import ctypes
import sys
import uuid
from contextlib import contextmanager

class EvidenceError(ValueError):
    pass

_REQUIRED_FIELDS = {'id', 'title', 'authors', 'year', 'url', 'verified_by', 'synthetic'}
_ALLOWED_FIELDS = {
    'id', 'title', 'authors', 'year', 'url', 'verified_by', 'quote', 'claim',
    'doi', 'notes', 'tags', 'synthetic', 'review_status', 'reviewed_by',
    'reviewed_at', 'support_location', 'support_excerpt', 'source_file',
    'source_sha256', 'source_license', 'source_url', 'source_version',
    'retrieved_at', 'oa_url', 'oa_license', 'oa_host', 'author_sort_key',
    'language', 'container_title', 'volume', 'issue', 'pages', 'publisher',
    'publication_place', 'author_metadata',
}

def _is_valid_url_or_doi(val: str) -> bool:
    if not isinstance(val, str) or not val.strip():
        return False
    val = val.strip()
    if val.startswith('doi:'):
        return len(val) > 4 and bool(val[4:].strip())
    try:
        parsed = urllib.parse.urlparse(val)
        if parsed.scheme in ('http', 'https'):
            return bool(parsed.netloc and parsed.netloc.strip() and parsed.hostname)
    except Exception:
        return False
    return False

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
    if not _is_valid_url_or_doi(url):
        raise EvidenceError(f"Field 'url' must be a valid http(s) URL with hostname or doi URI, got {url!r}")
        
    if not isinstance(record['verified_by'], str) or not record['verified_by'].strip():
        raise EvidenceError("Field 'verified_by' must be a non-empty string")

    if 'synthetic' in record and type(record['synthetic']) is not bool:
        raise EvidenceError("Field 'synthetic' must be a boolean")

    for field_name in (
        'reviewed_by', 'reviewed_at', 'support_location', 'support_excerpt',
        'source_file', 'source_sha256', 'source_license', 'source_url',
        'source_version', 'retrieved_at', 'oa_url', 'oa_license', 'oa_host',
        'author_sort_key', 'claim', 'quote', 'notes',
        'language', 'container_title', 'volume', 'issue', 'pages', 'publisher',
        'publication_place',
    ):
        if field_name in record and record[field_name] is not None and not isinstance(record[field_name], str):
            raise EvidenceError(f"Field '{field_name}' must be a string")
    if 'author_metadata' in record:
        metadata = record['author_metadata']
        if not isinstance(metadata, list) or any(not isinstance(item, dict) for item in metadata):
            raise EvidenceError("Field 'author_metadata' must be an array of objects")
        for index, author in enumerate(metadata):
            unknown_author_fields = set(author) - {'given', 'family', 'name'}
            if unknown_author_fields or any(not isinstance(value, str) for value in author.values()):
                raise EvidenceError(
                    f"Field 'author_metadata[{index}]' must contain only string given/family/name values"
                )
    if 'review_status' in record and (
        not isinstance(record['review_status'], str)
        or record['review_status'] not in {'candidate', 'reviewed'}
    ):
        raise EvidenceError("Field 'review_status' must be 'candidate' or 'reviewed'")
    if 'source_sha256' in record and (
        not isinstance(record['source_sha256'], str)
        or not re.fullmatch(r'[0-9a-fA-F]{64}', record['source_sha256'])
    ):
        raise EvidenceError("Field 'source_sha256' must be a 64-character SHA-256 hex digest")
    if 'source_file' in record:
        source_file = record['source_file']
        if not isinstance(source_file, str) or not source_file.strip() or Path(source_file).name != source_file or source_file in {'.', '..'}:
            raise EvidenceError("Field 'source_file' must be a safe file name within the source store")
    if 'review_status' in record and record['review_status'] == 'reviewed':
        required_review = {
            'reviewed_by', 'reviewed_at', 'support_location', 'support_excerpt',
            'source_file', 'source_sha256', 'source_license', 'source_url',
            'retrieved_at', 'claim', 'language', 'author_sort_key',
        }
        missing_review = required_review - set(record)
        if missing_review:
            raise EvidenceError(f"Reviewed source is missing field(s): {sorted(missing_review)}")
        for field_name in sorted(required_review):
            value = record[field_name]
            if not isinstance(value, str) or not value.strip():
                raise EvidenceError(f"Reviewed source field '{field_name}' must be a non-empty string")
        source_url = record['source_url'].strip()
        if (
            not _is_valid_url_or_doi(source_url)
            or urllib.parse.urlparse(source_url).scheme not in ('http', 'https')
            or any(character.isspace() for character in source_url)
        ):
            raise EvidenceError("Reviewed source field 'source_url' must be a valid HTTP(S) URL with hostname")
        language = record['language'].casefold()
        if not (language.startswith('vi') or language.startswith('en')):
            raise EvidenceError("Reviewed source language must be verified as Vietnamese ('vi') or English ('en')")
        if not record['author_sort_key'] or not record['author_sort_key'].strip():
            raise EvidenceError("Reviewed source requires a language-appropriate author_sort_key")

@contextmanager
def _file_lock(lock_path: Path, timeout: float = 10.0):
    lock_file = lock_path.with_name(f"{lock_path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    fd = None
    pid = os.getpid()
    while True:
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            payload = json.dumps({'pid': pid, 'ts': time.time()}).encode('utf-8')
            os.write(fd, payload)
            break
        except FileExistsError:
            elapsed = time.time() - start
            if elapsed > timeout:
                try:
                    content = lock_file.read_text(encoding='utf-8')
                    info = json.loads(content)
                    lock_pid = info.get('pid')
                    is_alive = False
                    if lock_pid and isinstance(lock_pid, int):
                        try:
                            os.kill(lock_pid, 0)
                            is_alive = True
                        except OSError:
                            is_alive = False
                    if not is_alive or (time.time() - info.get('ts', 0) > 30.0):
                        lock_file.unlink(missing_ok=True)
                except Exception:
                    try:
                        lock_file.unlink(missing_ok=True)
                    except Exception:
                        pass
            time.sleep(0.02)
    try:
        yield
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except Exception:
                pass
            try:
                lock_file.unlink(missing_ok=True)
            except Exception:
                pass

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
        for key, record in data.items():
            try:
                validate_record(record)
            except EvidenceError as exc:
                raise EvidenceError(f"Record {key!r}: {exc}") from exc
            if record["id"] != key:
                raise EvidenceError(
                    f"Registry key {key!r} does not match record id {record['id']!r}"
                )
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
            last_err = None
            for _ in range(30):
                try:
                    os.replace(tmp_path, self.path)
                    last_err = None
                    break
                except PermissionError as pe:
                    last_err = pe
                    time.sleep(0.03)
            if last_err is not None:
                raise last_err
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
        with _file_lock(self.path):
            data = self._load()
            if rec_id in data and not replace:
                raise EvidenceError(f"Evidence record with id '{rec_id}' already exists; use replace=True to overwrite.")
            data[rec_id] = record
            self._save(data)

    def get(self, key: str) -> dict[str, Any]:
        with _file_lock(self.path):
            data = self._load()
            if key not in data:
                raise EvidenceError(f"Evidence record '{key}' not found.")
            return data[key]

    def assert_citable(
        self, record: dict[str, Any], *, require_reviewed: bool = False
    ) -> None:
        """Reject discovered candidates and recheck reviewed source bytes."""
        if record.get('review_status') == 'candidate':
            raise EvidenceError(
                f"Evidence '{record.get('id', '')}' is discovery metadata only; inspect and review its source before citing it."
            )
        if require_reviewed and record.get('review_status') != 'reviewed':
            raise EvidenceError(
                f"Evidence '{record.get('id', '')}' has no reviewed, downloaded source; review its supporting passage before citing it."
            )
        if record.get('review_status') != 'reviewed':
            return
        try:
            source_root = (self.path.parent / 'sources').resolve()
            source_path = (source_root / record['source_file']).resolve()
            try:
                source_path.relative_to(source_root)
            except ValueError as exc:
                raise EvidenceError("Reviewed source file escapes the workspace source store") from exc
            if not source_path.is_file():
                raise EvidenceError(f"Reviewed source file is missing: {source_path}")
            digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        except FileNotFoundError as exc:
            raise EvidenceError(f"Reviewed source file is missing for evidence '{record.get('id', '')}'") from exc
        except OSError as exc:
            raise EvidenceError(f"Reviewed source file cannot be read for evidence '{record.get('id', '')}'") from exc
        if digest.casefold() != record['source_sha256'].casefold():
            raise EvidenceError(
                f"Reviewed source hash changed for evidence '{record.get('id', '')}'; review it again before citing."
            )

    def remove(self, key: str) -> bool:
        with _file_lock(self.path):
            data = self._load()
            if key in data:
                del data[key]
                self._save(data)
                return True
            return False

    def list(self) -> list[dict[str, Any]]:
        with _file_lock(self.path):
            return list(self._load().values())

    def validate_all(self) -> list[str]:
        errors = []
        with _file_lock(self.path):
            data = self._load()
            for k, v in data.items():
                try:
                    validate_record(v)
                except EvidenceError as e:
                    errors.append(f"Record '{k}': {e}")
        return errors
