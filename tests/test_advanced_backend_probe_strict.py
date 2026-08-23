from __future__ import annotations
import sys
import types
from unittest.mock import patch
from wordassistant.backends.status import get_backend_status, probe_advanced_backend

def test_version_alone_does_not_make_backend_operational():
    # Create a fake module with only __version__
    fake_mod = types.ModuleType("docx_mcp")
    fake_mod.__version__ = "1.2.3"
    
    with patch.dict(sys.modules, {"docx_mcp": fake_mod}), \
         patch("wordassistant.backends.status.find_spec", return_value=True):
        ok, msg = probe_advanced_backend()
        assert ok is False
        assert "no active adapter bridge" in msg.lower() or "not configured" in msg.lower()
        
        st = get_backend_status()
        assert st["installed"] is True
        assert st["operational"] is False
        assert st["adapter_supported"] is False
        assert st["capabilities"]["comments"] == "UNSUPPORTED"
