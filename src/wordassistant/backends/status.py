from __future__ import annotations
from importlib.util import find_spec
from typing import Any
import shutil

def advanced_word_backend_available() -> bool:
    return find_spec('docx_mcp') is not None or shutil.which('docx-mcp') is not None

def get_backend_status() -> dict[str, Any]:
    has_pkg = find_spec('docx_mcp') is not None
    has_cli = shutil.which('docx-mcp') is not None or shutil.which('docx_mcp_server') is not None
    installed = has_pkg or bool(has_cli)
    
    core_caps = [
        'read_docx',
        'structure_indexing',
        'token_bounded_context',
        'safe_text_replace',
        'profile_scaffolding',
        'profile_validation',
        'libreoffice_render_pdf',
        'evidence_registry'
    ]
    
    advanced_caps = [
        'native_tracked_changes',
        'native_comments',
        'native_content_controls_sdt',
        'native_drawingml_shapes',
        'native_complex_fields',
        'native_vba_macros'
    ]
    
    return {
        'installed': installed,
        'adapter_supported': True,
        'operational': True,
        'engine': 'docx-mcp-advanced' if installed else 'python-docx-core',
        'core_capabilities': core_caps,
        'advanced_capabilities': advanced_caps,
        'notes': 'Advanced backend is available for high-fidelity native revision editing.' if installed else 'Running on fast deterministic core backend (python-docx). docx-mcp is optional.'
    }
