"""Remove only exact reviewed generated files; default is dry-run.

The manifest lists path, SHA-256, reason and optionally a verified ZIP backup.
This helper never recursively deletes a directory or discovers deletion targets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(workspace: Path, manifest: dict, *, apply=False):
    workspace = workspace.resolve(strict=True)
    project_path = workspace / 'project.json'
    project = json.loads(project_path.read_text(encoding='utf-8-sig'))
    protected = {project_path, (workspace / project['output_docx']).resolve()}
    protected.update((workspace / p).resolve() for p in manifest.get('protected_files', []))
    for value in project.get('qa_reports', {}).values():
        if isinstance(value, str):
            protected.add((workspace / value).resolve())
    verified, seen = [], set()
    for item in manifest.get('files', []):
        path = (workspace / item['path']).resolve(strict=True)
        if not path.is_relative_to(workspace) or path in protected or path in seen:
            raise ValueError('Cleanup target escapes workspace, is protected or is duplicated')
        relative = path.relative_to(workspace)
        if relative.parts[0] in {'source', 'sources'} or not path.is_file():
            raise ValueError('Source evidence and directories cannot be cleanup targets')
        if digest(path) != item['sha256']:
            raise ValueError('Cleanup target changed after review')
        reason = item.get('reason')
        if reason == 'archived_adapter':
            archive = (workspace / item['archive']).resolve(strict=True)
            if not archive.is_relative_to(workspace):
                raise ValueError('Archive escapes workspace')
            with ZipFile(archive) as package:
                data = package.read(relative.as_posix())
            if hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError('Archive does not preserve the exact adapter')
        elif reason not in {'generated_cache', 'superseded_intermediate'}:
            raise ValueError('Unrecognized cleanup reason')
        verified.append(path)
        seen.add(path)
    bytes_total = sum(p.stat().st_size for p in verified)
    if apply:
        for path in verified:
            path.unlink()
    return {'status': 'REMOVED' if apply else 'DRY_RUN', 'files': len(verified),
            'bytes': bytes_total, 'workspace': str(workspace)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace', type=Path)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(clean(args.workspace, json.loads(args.manifest.read_text(encoding='utf-8-sig')),
                           apply=args.apply), indent=2))


if __name__ == '__main__':
    main()
