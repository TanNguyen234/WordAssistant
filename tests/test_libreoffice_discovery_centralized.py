from __future__ import annotations
from pathlib import Path
from unittest.mock import patch
from wordassistant.doctor import status, find_libreoffice_executable
from wordassistant.document.render import render_pdf

def test_centralized_libreoffice_discovery():
    with patch("shutil.which", return_value=None), \
         patch.object(Path, "exists", return_value=True):
        exe = find_libreoffice_executable()
        assert exe is not None
        
        st = status()
        assert st["libreoffice"] is True

def test_centralized_libreoffice_absent():
    with patch("shutil.which", return_value=None), \
         patch.object(Path, "exists", return_value=False):
        exe = find_libreoffice_executable()
        assert exe is None
        
        st = status()
        assert st["libreoffice"] is False
