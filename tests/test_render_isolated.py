import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from wordassistant.document.render import render_pdf, RenderResult

def test_render_prevents_stale_pdf_and_uses_isolated_dir(tmp_path):
    src_docx = tmp_path / 'sample.docx'
    src_docx.write_bytes(b'PK\x03\x04fake')
    
    out_dir = tmp_path / 'output'
    out_dir.mkdir()
    stale_pdf = out_dir / 'sample.pdf'
    stale_pdf.write_bytes(b'%PDF-1.4-stale')
    
    # Mock subprocess to fail to create a PDF in isolated temp dir
    with patch('shutil.which', return_value='libreoffice'), \
         patch('subprocess.run') as mock_run:
        
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        
        # When subprocess runs, it doesn't write anything into the temp dir
        with pytest.raises(RuntimeError, match="no non-empty PDF|created"):
            render_pdf(src_docx, output_dir=out_dir)
            
    # The stale PDF in out_dir must NOT be returned or counted as success!
    assert stale_pdf.read_bytes() == b'%PDF-1.4-stale'

def test_render_success_metadata(tmp_path):
    src_docx = tmp_path / 'doc.docx'
    src_docx.write_bytes(b'PK\x03\x04fake')
    out_dir = tmp_path / 'out'
    
    def fake_subprocess_run(cmd, **kwargs):
        # Extract --outdir
        outdir_idx = cmd.index('--outdir') + 1
        isolated_dir = Path(cmd[outdir_idx])
        (isolated_dir / 'doc.pdf').write_bytes(b'%PDF-1.7-fresh-content-12345')
        return MagicMock(returncode=0, stdout='Converted', stderr='')
        
    with patch('shutil.which', return_value='libreoffice'), \
         patch('subprocess.run', side_effect=fake_subprocess_run):
        
        res = render_pdf(src_docx, output_dir=out_dir)
        assert isinstance(res, RenderResult)
        assert res.pdf_path.exists()
        assert res.pdf_path == out_dir / 'doc.pdf'
        assert res.file_size_bytes == len(b'%PDF-1.7-fresh-content-12345')
        assert res.engine == 'libreoffice'
        assert res.pdf_path.read_bytes() == b'%PDF-1.7-fresh-content-12345'
