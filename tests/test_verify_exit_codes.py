import json
from pathlib import Path
from unittest.mock import patch
from wordassistant.cli import run

ROOT = Path(__file__).resolve().parents[1]

def test_verify_fails_with_nonzero_exit_code_when_render_fails(tmp_path, capsys):
    doc_path = tmp_path / "valid.docx"
    run(['scaffold', str(doc_path), '--profile', 'generic', '--variant', 'default', '--json'])
    capsys.readouterr()
    
    with patch('wordassistant.cli.render_pdf', side_effect=RuntimeError("LibreOffice render failed simulated")):
        code = run(['verify', str(doc_path), '--profile', 'generic', '--variant', 'default', '--render', '--json'])
        out_txt = capsys.readouterr().out
        data = json.loads(out_txt)
        
        # When --render fails, exit code MUST be non-zero (e.g. 2)
        assert code != 0, f"Expected non-zero exit code on render failure, got {code}"
        assert data['overall_status'] == 'FAIL'
        assert data['validation_status'] == 'PASS'
        assert data['render_status'] == 'FAIL'
        assert data['manual_review_required'] is True

def test_verify_passes_when_render_not_requested_and_validation_passes(tmp_path, capsys):
    doc_path = tmp_path / "valid2.docx"
    run(['scaffold', str(doc_path), '--profile', 'generic', '--variant', 'default', '--json'])
    capsys.readouterr()
    
    code = run(['verify', str(doc_path), '--profile', 'generic', '--variant', 'default', '--json'])
    out_txt = capsys.readouterr().out
    data = json.loads(out_txt)
    
    assert code == 0
    assert data['overall_status'] == 'PASS'
    assert data['validation_status'] == 'PASS'
    assert data['render_status'] == 'SKIPPED'
    assert data['manual_review_required'] is False
