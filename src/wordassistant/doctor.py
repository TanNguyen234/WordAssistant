from __future__ import annotations
import importlib.util,platform,shutil

def status():
    return {
        'python':platform.python_version(),
        'python-docx': bool(importlib.util.find_spec('docx')),
        'libreoffice': bool(shutil.which('libreoffice') or shutil.which('soffice')),
        'docx-mcp-server': bool(importlib.util.find_spec('docx_mcp')),
        'core_ready': bool(importlib.util.find_spec('docx')),
        'api_key_required_for_core': False
    }
