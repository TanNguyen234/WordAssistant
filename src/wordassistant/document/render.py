from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import time

from wordassistant.doctor import find_libreoffice_executable

@dataclass(frozen=True)
class RenderResult:
    pdf_path: Path
    file_size_bytes: int
    engine: str = "libreoffice"
    page_count: int | None = None
    duration_seconds: float = 0.0

def render_pdf(
    docx_path: str | Path,
    output_dir: str | Path | None = None,
    timeout_seconds: int = 180
) -> RenderResult:
    src = Path(docx_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Source document not found: {src}")
        
    outdir = Path(output_dir).resolve() if output_dir else src.parent
    outdir.mkdir(parents=True, exist_ok=True)
    
    exe = find_libreoffice_executable()
    if not exe:
        raise RuntimeError("LibreOffice/soffice executable was not found on PATH; render is unavailable.")
        
    # Create an isolated temporary directory for rendering to prevent stale PDF overwrite/aliasing
    temp_dir = Path(tempfile.mkdtemp(prefix="wa_render_"))
    start_time = time.perf_counter()
    
    try:
        cp = subprocess.run(
            [exe, '--headless', '--convert-to', 'pdf', '--outdir', str(temp_dir), str(src)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        if cp.returncode != 0:
            raise RuntimeError(f"LibreOffice render failed (code {cp.returncode}): {cp.stderr.strip() or cp.stdout.strip()}")
            
        temp_pdf = temp_dir / f"{src.stem}.pdf"
        if not temp_pdf.exists() or temp_pdf.stat().st_size == 0:
            raise RuntimeError("Render reported success, but no non-empty PDF was created in isolated workdir.")
            
        final_pdf = outdir / f"{src.stem}.pdf"
        shutil.copy2(temp_pdf, final_pdf)
        duration = time.perf_counter() - start_time
        
        return RenderResult(
            pdf_path=final_pdf,
            file_size_bytes=final_pdf.stat().st_size,
            engine="libreoffice",
            duration_seconds=round(duration, 3)
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
