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

def find_microsoft_word() -> str | None:
    """Locate WINWORD.EXE through the App Paths registry key (Windows only)."""
    if platform.system().lower() != 'windows':
        return None
    try:
        import winreg
    except ImportError:  # pragma: no cover - non-Windows interpreters
        return None
    key_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WINWORD.EXE'
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(hive, key_path) as key:
                value, _ = winreg.QueryValueEx(key, '')
        except OSError:
            continue
        if value and Path(value).is_file():
            return str(value)
    return None

def status() -> dict:
    has_lo = bool(find_libreoffice_executable())
    word_path = find_microsoft_word()
    engines = []
    if word_path:
        engines.append('word')
    if has_lo:
        engines.append('libreoffice')
    return {
        'python': platform.python_version(),
        'python-docx': bool(importlib.util.find_spec('docx')),
        'lxml': bool(importlib.util.find_spec('lxml')),
        'libreoffice': has_lo,
        'microsoft_word': bool(word_path),
        'microsoft_word_path': word_path,
        'render_engines': engines,
        'docx-mcp-server': bool(importlib.util.find_spec('docx_mcp')),
        'core_ready': bool(importlib.util.find_spec('docx')),
        'api_key_required_for_core': False
    }
