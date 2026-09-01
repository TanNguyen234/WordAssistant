from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import time
import uuid

from wordassistant.doctor import find_libreoffice_executable

@dataclass(frozen=True)
class RenderResult:
    pdf_path: Path
    file_size_bytes: int
    engine: str = "libreoffice"
    page_count: int | None = None
    duration_seconds: float = 0.0


def _page_number(path: Path) -> int:
    try:
        return int(path.stem.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return 2**31 - 1


def _atomic_copy_replace(source: Path, destination: Path) -> None:
    """Copy to a same-directory temporary file, then atomically publish it."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.stem}.publish-",
        suffix=destination.suffix,
        dir=destination.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        shutil.copy2(source, temporary)
        if temporary.stat().st_size == 0:
            raise RuntimeError("Refusing to publish an empty rendered file.")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _publish_page_set(staged_pages: tuple[Path, ...], destination: Path) -> tuple[Path, ...]:
    """Atomically publish one immutable page-set version.

    The stable destination is only a container. Each complete render is renamed
    into a fresh child directory in one filesystem operation, so readers never
    observe a missing or partially replaced set and later publishers cannot
    mutate paths already returned as evidence.
    """
    staging = staged_pages[0].parent
    names = tuple(page.name for page in staged_pages)
    destination.mkdir(parents=True, exist_ok=True)
    published = destination / f"set-{uuid.uuid4().hex}"
    os.replace(staging, published)
    return tuple(published / name for name in names)


def _render_pages_with_pdfium(source: Path, staging: Path, dpi: int) -> None:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise RuntimeError("Packaged PDF page rendering requires pypdfium2.") from exc
    scale = int(dpi) / 72
    document = pdfium.PdfDocument(source)
    try:
        for page_index in range(len(document)):
            page = document[page_index]
            try:
                bitmap = page.render(scale=scale)
                try:
                    image = bitmap.to_pil()
                    try:
                        image.save(staging / f"page-{page_index + 1}.png")
                    finally:
                        image.close()
                finally:
                    bitmap.close()
            finally:
                page.close()
    finally:
        document.close()


def _validate_png_page_set(staged_pages: tuple[Path, ...]) -> None:
    from PIL import Image, UnidentifiedImageError

    for page in staged_pages:
        if page.stat().st_size == 0:
            raise RuntimeError(f"PDF page renderer produced an empty PNG: {page.name}")
        try:
            with Image.open(page) as image:
                if image.format != "PNG" or image.width <= 0 or image.height <= 0:
                    raise RuntimeError(
                        f"PDF page renderer produced an invalid PNG: {page.name}"
                    )
                image.verify()
        except (OSError, UnidentifiedImageError) as exc:
            raise RuntimeError(
                f"PDF page renderer produced an invalid PNG: {page.name}"
            ) from exc


def render_pdf_pages(
    pdf_path: str | Path,
    output_dir: str | Path | None = None,
    *,
    dpi: int = 120,
) -> tuple[Path, ...]:
    source = Path(pdf_path).resolve()
    if int(dpi) <= 0:
        raise ValueError("dpi must be a positive integer")
    executable = shutil.which("pdftoppm")
    destination = (
        Path(output_dir).resolve()
        if output_dir
        else source.parent / f"{source.stem}-pages"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=".wordassistant-pages-stage-", dir=destination.parent)
    )
    try:
        poppler_error = None
        if executable:
            prefix = staging / "page"
            try:
                completed = subprocess.run(
                    [executable, "-png", "-r", str(int(dpi)), str(source), str(prefix)],
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                if completed.returncode != 0:
                    raise RuntimeError(
                        completed.stderr.strip() or completed.stdout.strip() or "pdftoppm failed"
                    )
                poppler_pages = tuple(
                    sorted(staging.glob("page-*.png"), key=_page_number)
                )
                if not poppler_pages:
                    raise RuntimeError("pdftoppm produced no PNG pages")
                _validate_png_page_set(poppler_pages)
            except Exception as exc:
                poppler_error = str(exc)
        if not executable or poppler_error is not None:
            for stale in staging.glob("page-*.png"):
                stale.unlink()
            try:
                _render_pages_with_pdfium(source, staging, int(dpi))
            except Exception as exc:
                if poppler_error is not None:
                    raise RuntimeError(
                        f"PDF page rendering failed in Poppler ({poppler_error}) and PDFium ({exc})."
                    ) from exc
                raise
        staged_pages = tuple(sorted(staging.glob("page-*.png"), key=_page_number))
        if not staged_pages:
            raise RuntimeError("PDF page rendering reported success but produced no PNG pages.")
        _validate_png_page_set(staged_pages)
        return _publish_page_set(staged_pages, destination)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

def render_pdf(
    docx_path: str | Path,
    output_dir: str | Path | None = None,
    timeout_seconds: int = 180,
    *,
    output_path: str | Path | None = None,
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
            
        final_pdf = (
            Path(output_path).resolve()
            if output_path is not None
            else outdir / f"{src.stem}.pdf"
        )
        final_pdf.parent.mkdir(parents=True, exist_ok=True)
        _atomic_copy_replace(temp_pdf, final_pdf)
        duration = time.perf_counter() - start_time
        
        return RenderResult(
            pdf_path=final_pdf,
            file_size_bytes=final_pdf.stat().st_size,
            engine="libreoffice",
            duration_seconds=round(duration, 3)
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def render_document(
    docx_path: str | Path,
    output_dir: str | Path | None = None,
    *,
    engine: str = "auto",
    timeout_seconds: int = 180,
) -> RenderResult:
    if engine not in {"auto", "word", "libreoffice"}:
        raise ValueError("engine must be auto, word, or libreoffice")
    source = Path(docx_path).resolve()
    destination_dir = Path(output_dir).resolve() if output_dir else source.parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{source.stem}.pdf"
    native_error = None
    if engine in {"auto", "word"}:
        try:
            from wordassistant.backends.word_native.backend import WordNativeBackend
            from wordassistant.operations.models import OperationRequest

            backend = WordNativeBackend(timeout_seconds=timeout_seconds)
            health = backend.health()
            if not health.operational:
                raise RuntimeError(health.reason)
            started = time.perf_counter()
            descriptor, staging_name = tempfile.mkstemp(
                prefix=f".{destination.stem}.word-stage-",
                suffix=destination.suffix,
                dir=destination.parent,
            )
            os.close(descriptor)
            staging = Path(staging_name)
            staging.unlink(missing_ok=True)
            try:
                result = backend.execute(
                    OperationRequest(
                        "render.pdf", input_path=source, output_path=staging
                    )
                )
                if not staging.exists() or staging.stat().st_size == 0:
                    raise RuntimeError(
                        "Microsoft Word reported success but produced no non-empty PDF."
                    )
                os.replace(staging, destination)
            finally:
                staging.unlink(missing_ok=True)
            return RenderResult(
                pdf_path=destination,
                file_size_bytes=destination.stat().st_size,
                engine="word",
                page_count=result.data.get("page_count"),
                duration_seconds=round(time.perf_counter() - started, 3),
            )
        except Exception as exc:
            native_error = exc
            if engine == "word":
                raise RuntimeError(f"Microsoft Word render unavailable: {exc}") from exc
    try:
        return render_pdf(source, output_dir=destination_dir, timeout_seconds=timeout_seconds)
    except Exception as exc:
        if native_error is not None:
            raise RuntimeError(
                f"No render backend succeeded; Word: {native_error}; LibreOffice: {exc}"
            ) from exc
        raise
