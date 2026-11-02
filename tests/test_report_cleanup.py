import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('report_cleanup', Path(__file__).parents[1] / 'scripts/clean_course_report_workspace.py')
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


def test_cleanup_rejects_escape_before_removing_any_file(tmp_path):
    ws = tmp_path / 'workspace'
    ws.mkdir()
    (ws / 'project.json').write_text(json.dumps({'output_docx': 'final.docx'}))
    candidate = ws / 'temp.txt'
    candidate.write_text('temporary')
    outside = tmp_path / 'outside.txt'
    outside.write_text('keep')
    manifest = {'files': [{'path': 'temp.txt', 'sha256': cleanup.digest(candidate), 'reason': 'generated_cache'},
                          {'path': '../outside.txt', 'sha256': cleanup.digest(outside), 'reason': 'generated_cache'}]}
    with pytest.raises(ValueError, match='escapes'):
        cleanup.clean(ws, manifest, apply=True)
    assert candidate.exists() and outside.exists()


def test_cleanup_protects_canonical_output_and_rejects_stale_hash(tmp_path):
    (tmp_path / 'project.json').write_text(json.dumps({'output_docx': 'final.docx'}))
    target = tmp_path / 'final.docx'
    target.write_bytes(b'current')
    manifest = {'files': [{'path': 'final.docx', 'sha256': cleanup.digest(target), 'reason': 'superseded_intermediate'}]}
    with pytest.raises(ValueError, match='protected'):
        cleanup.clean(tmp_path, manifest, apply=True)
    manifest['files'][0]['path'] = 'old.docx'
    target = tmp_path / 'old.docx'
    target.write_bytes(b'changed')
    with pytest.raises(ValueError, match='changed'):
        cleanup.clean(tmp_path, manifest, apply=True)


def test_cleanup_defaults_to_review_then_removes_only_listed_files(tmp_path):
    (tmp_path / 'project.json').write_text(json.dumps({'output_docx': 'final.docx'}))
    target = tmp_path / 'cache.bin'
    target.write_bytes(b'cache')
    manifest = {'files': [{'path': 'cache.bin', 'sha256': cleanup.digest(target), 'reason': 'generated_cache'}]}
    assert cleanup.clean(tmp_path, manifest)['status'] == 'DRY_RUN'
    assert target.exists()
    assert cleanup.clean(tmp_path, manifest, apply=True)['files'] == 1
    assert not target.exists()
