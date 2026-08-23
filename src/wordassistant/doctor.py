from __future__ import annotations
import importlib.util
from pathlib import Path
import platform
import shutil

def find_libreoffice_executable() -> str | None:
    exe = shutil.which('libreoffice') or shutil.which('soffice')
    if exe:
        return str(exe)
    candidates = [
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        Path("/usr/bin/libreoffice"),
        Path("/usr/bin/soffice"),
        Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None

def status() -> dict:
    has_lo = bool(find_libreoffice_executable())
    return {
        'python': platform.python_version(),
        'python-docx': bool(importlib.util.find_spec('docx')),
        'libreoffice': has_lo,
        'docx-mcp-server': bool(importlib.util.find_spec('docx_mcp')),
        'core_ready': bool(importlib.util.find_spec('docx')),
        'api_key_required_for_core': False
    }
