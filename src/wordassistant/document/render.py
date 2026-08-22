from __future__ import annotations
from pathlib import Path
import shutil,subprocess,tempfile

def render_pdf(docx_path:str|Path,output_dir:str|Path|None=None)->Path:
    src=Path(docx_path).resolve(); outdir=Path(output_dir).resolve() if output_dir else src.parent; outdir.mkdir(parents=True,exist_ok=True)
    exe=shutil.which('libreoffice') or shutil.which('soffice')
    if not exe: raise RuntimeError('LibreOffice/soffice not found; install it to use render.')
    cp=subprocess.run([exe,'--headless','--convert-to','pdf','--outdir',str(outdir),str(src)],capture_output=True,text=True,timeout=180)
    if cp.returncode!=0: raise RuntimeError(f'LibreOffice render failed: {cp.stderr.strip() or cp.stdout.strip()}')
    pdf=outdir/(src.stem+'.pdf')
    if not pdf.exists(): raise RuntimeError('Render reported success but PDF was not created')
    return pdf
