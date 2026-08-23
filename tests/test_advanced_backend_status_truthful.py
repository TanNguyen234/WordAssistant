from __future__ import annotations
from unittest.mock import patch
from wordassistant.backends.status import get_backend_status

def test_status_absent_backend():
    with patch("wordassistant.backends.status.find_spec", return_value=None), \
         patch("wordassistant.backends.status.shutil.which", return_value=None):
        st = get_backend_status()
        assert st["installed"] is False
        assert st["adapter_supported"] is False
        assert st["operational"] is False
        assert "not installed" in st["reason"].lower()
        assert st["capabilities"]["comments"] == "UNAVAILABLE"
        assert st["capabilities"]["tracked_changes"] == "UNAVAILABLE"

def test_status_package_found_but_probe_fails():
    with patch("wordassistant.backends.status.find_spec", return_value=True), \
         patch("wordassistant.backends.status.shutil.which", return_value="/mock/docx-mcp"), \
         patch("wordassistant.backends.status.probe_advanced_backend", return_value=(False, "Connection refused")):
        st = get_backend_status()
        assert st["installed"] is True
        assert st["adapter_supported"] is False
        assert st["operational"] is False
        assert "probe failed" in st["reason"].lower() or "connection refused" in st["reason"].lower()
        assert st["capabilities"]["comments"] == "UNSUPPORTED"

def test_status_successful_probe():
    with patch("wordassistant.backends.status.find_spec", return_value=True), \
         patch("wordassistant.backends.status.shutil.which", return_value="/mock/docx-mcp"), \
         patch("wordassistant.backends.status.probe_advanced_backend", return_value=(True, "OK")):
        st = get_backend_status()
        assert st["installed"] is True
        assert st["operational"] is True
        # Since WordAssistant does not yet implement mutation adapters for comments/tracked changes
        assert st["adapter_supported"] is False
        assert "operational" in st["reason"].lower()
        assert st["capabilities"]["comments"] == "UNSUPPORTED"
        assert st["capabilities"]["tracked_changes"] == "UNSUPPORTED"

