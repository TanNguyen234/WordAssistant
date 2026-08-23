from __future__ import annotations
import sys
import types
from unittest.mock import patch
from wordassistant.backends.status import get_backend_status, probe_advanced_backend

def test_successful_probe_without_adapters_keeps_capabilities_unsupported():
    fake_mod = types.ModuleType("docx_mcp")
    # Even if probe() returns True
    fake_mod.probe = lambda: (True, "Simulated docx-mcp healthy server.")
    
    with patch.dict(sys.modules, {"docx_mcp": fake_mod}), \
         patch("wordassistant.backends.status.find_spec", return_value=True):
        ok, msg = probe_advanced_backend()
        assert ok is True
        
        st = get_backend_status()
        assert st["installed"] is True
        assert st["operational"] is True
        # Since WordAssistant does not have mutation adapters implemented for comments, etc.
        assert st["adapter_supported"] is False
        assert st["capabilities"]["comments"] == "UNSUPPORTED"
        assert st["capabilities"]["tracked_changes"] == "UNSUPPORTED"
        assert st["capabilities"]["rich_merge"] == "UNSUPPORTED"
        assert st["capabilities"]["compare"] == "UNSUPPORTED"
