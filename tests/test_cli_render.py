from __future__ import annotations
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from wordassistant.cli import run
from wordassistant.document.render import RenderResult

def test_cli_render_success(tmp_path: Path, monkeypatch):
    test_docx = tmp_path / "doc.docx"
    test_docx.write_bytes(b"PK mock docx")
    expected_pdf = tmp_path / "doc.pdf"
    expected_pdf.write_bytes(b"%PDF mock pdf")
    
    mock_result = RenderResult(
        pdf_path=expected_pdf,
        file_size_bytes=13,
        engine="libreoffice",
        duration_seconds=0.123
    )
    
    with patch("wordassistant.cli.render_pdf", return_value=mock_result) as mock_render:
        code = run(["render", str(test_docx), "--outdir", str(tmp_path), "--timeout", "120", "--json"])
        assert code == 0
        mock_render.assert_called_once_with(str(test_docx), output_dir=str(tmp_path), timeout_seconds=120)

def test_cli_render_failure(tmp_path: Path):
    test_docx = tmp_path / "doc.docx"
    test_docx.write_bytes(b"PK mock docx")
    
    with patch("wordassistant.cli.render_pdf", side_effect=RuntimeError("LibreOffice timed out")):
        code = run(["render", str(test_docx), "--json"])
        assert code != 0

def test_verify_render_flag_integration(tmp_path: Path):
    test_docx = tmp_path / "doc.docx"
    test_docx.write_bytes(b"PK mock docx")
    
    with patch("wordassistant.cli.render_pdf", side_effect=RuntimeError("LibreOffice missing")), \
         patch("wordassistant.cli.inspect_document", return_value={"paragraphs": 1, "tables": 0, "sections": 1, "images": 0, "fields": {}}), \
         patch("wordassistant.cli.validate_document") as mock_val:
        from wordassistant.document.validate import ValidationResult
        mock_val.return_value = ValidationResult(valid=True, issues=())
        
        code = run(["verify", str(test_docx), "--render", "--json"])
        assert code == 2  # Render failed, so verify must return non-zero exit code
