from __future__ import annotations
from importlib.util import find_spec
from typing import Any
import shutil

CAPABILITY_KEYS = (
    'comments',
    'tracked_changes',
    'footnotes',
    'endnotes',
    'bookmarks',
    'fields',
    'captions',
    'rich_merge',
    'compare',
    'ooxml_audit',
)

def advanced_word_backend_available() -> bool:
    has_pkg = find_spec('docx_mcp') is not None
    has_cli = shutil.which('docx-mcp') is not None or shutil.which('docx_mcp_server') is not None
    return has_pkg or bool(has_cli)

def probe_advanced_backend() -> tuple[bool, str]:
    """
    Deterministic probe to check if docx-mcp adapter is available and responsive.
    Currently, WordAssistant provides the deterministic core; an active docx-mcp bridge
    must be verified before reporting operational.
    """
    if not advanced_word_backend_available():
        return False, "docx-mcp optional backend is not installed in current environment."
    try:
        import docx_mcp  # type: ignore
        if hasattr(docx_mcp, 'probe') and callable(docx_mcp.probe):
            return docx_mcp.probe()
        return False, "docx-mcp package is installed but no active adapter bridge is configured."
    except Exception as exc:
        return False, f"docx-mcp probe failed: {exc}"

def get_backend_status() -> dict[str, Any]:
    installed = advanced_word_backend_available()
    
    if not installed:
        adapter_supported = False
        operational = False
        reason = "docx-mcp optional backend is not installed in current environment."
        caps = {k: "UNAVAILABLE" for k in CAPABILITY_KEYS}
    else:
        ok, probe_msg = probe_advanced_backend()
        if ok:
            adapter_supported = True
            operational = True
            reason = f"docx-mcp is operational ({probe_msg})" if probe_msg else "docx-mcp is installed and operational."
            caps = {k: "SUPPORTED" for k in CAPABILITY_KEYS}
        else:
            adapter_supported = False
            operational = False
            reason = probe_msg or "docx-mcp is installed but probe failed."
            caps = {k: "UNSUPPORTED" for k in CAPABILITY_KEYS}
            
    return {
        'installed': installed,
        'adapter_supported': adapter_supported,
        'operational': operational,
        'reason': reason,
        'capabilities': caps,
        'advanced_capabilities': caps,
        'core_capabilities': ['inspect', 'context', 'scaffold', 'replace', 'validate', 'verify', 'render', 'evidence'],
        'engine': 'docx-mcp-advanced' if operational else 'python-docx-core',
        'notes': 'Advanced backend is available for high-fidelity native revision editing.' if operational else 'Running on fast deterministic core backend (python-docx). docx-mcp is optional.'
    }
