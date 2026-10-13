import tempfile
import sys
import types
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from wordassistant.document.render import render_document, render_pdf, render_pdf_pages, RenderResult


def _write_test_png(path: Path, color="white") -> None:
    from PIL import Image

    image = Image.new("RGB", (2, 2), color=color)
    image.save(path, "PNG")
    image.close()


@pytest.mark.parametrize("dpi", [0, -1])
def test_page_render_rejects_non_positive_dpi(tmp_path, dpi):
    source = tmp_path / "report.pdf"
    source.write_bytes(b"%PDF")

    with pytest.raises(ValueError, match="dpi must be a positive integer"):
        render_pdf_pages(source, dpi=dpi)


def test_page_render_falls_back_to_packaged_pdfium(tmp_path):
    source = tmp_path / "report.pdf"
    source.write_bytes(b"%PDF")
    saved = []

    class FakeImage:
        def save(self, path):
            destination = Path(path)
            _write_test_png(destination)
            saved.append(destination.name)

        def close(self):
            return None

    class FakeBitmap:
        def to_pil(self):
            return FakeImage()

        def close(self):
            return None

    class FakePage:
        def render(self, *, scale):
            assert scale == 120 / 72
            return FakeBitmap()

        def close(self):
            return None

    class FakeDocument:
        def __len__(self):
            return 2

        def __getitem__(self, index):
            return FakePage()

        def close(self):
            return None

    fake_pdfium = types.SimpleNamespace(
        PdfDocument=lambda path: FakeDocument(),
    )

    with patch("wordassistant.document.render.shutil.which", return_value=None), patch.dict(
        sys.modules, {"pypdfium2": fake_pdfium}
    ):
        result = render_pdf_pages(source)

    assert [path.name for path in result] == ["page-1.png", "page-2.png"]
    assert saved == ["page-1.png", "page-2.png"]


def test_successful_poppler_pngs_are_validated_once(tmp_path, monkeypatch):
    source = tmp_path / "one.pdf"
    source.write_bytes(b"%PDF")
    def fake_run(command, **kwargs):
        _write_test_png(Path(command[-1]).with_name("page-1.png"))
        return MagicMock(returncode=0, stdout="", stderr="")
    calls = []
    original = __import__("wordassistant.document.render", fromlist=["_validate_png_page_set"])._validate_png_page_set
    def count_validation(pages):
        calls.append(tuple(pages))
        return original(pages)
    monkeypatch.setattr("wordassistant.document.render.shutil.which", lambda _: "pdftoppm")
    monkeypatch.setattr("wordassistant.document.render.subprocess.run", fake_run)
    monkeypatch.setattr("wordassistant.document.render._validate_png_page_set", count_validation)
    render_pdf_pages(source)
    assert len(calls) == 1


def test_packaged_pdfium_fallback_renders_a_real_pdf(tmp_path):
    from PIL import Image

    source = tmp_path / "real.pdf"
    image = Image.new("RGB", (200, 300), color="white")
    image.save(source, "PDF")
    image.close()

    with patch("wordassistant.document.render.shutil.which", return_value=None):
        result = render_pdf_pages(source)

    assert [path.name for path in result] == ["page-1.png"]
    assert result[0].read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_failed_poppler_render_falls_back_to_packaged_pdfium(tmp_path):
    from PIL import Image

    source = tmp_path / "real.pdf"
    image = Image.new("RGB", (200, 300), color="white")
    image.save(source, "PDF")
    image.close()

    with patch("wordassistant.document.render.shutil.which", return_value="pdftoppm"), patch(
        "wordassistant.document.render.subprocess.run",
        return_value=MagicMock(returncode=1, stdout="", stderr="poppler failed"),
    ):
        result = render_pdf_pages(source)

    assert len(result) == 1
    assert result[0].read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.parametrize("failure", ["timeout", "corrupt-success"])
def test_poppler_exception_or_invalid_output_falls_back_to_pdfium(tmp_path, failure):
    from PIL import Image

    source = tmp_path / "real.pdf"
    image = Image.new("RGB", (200, 300), color="white")
    image.save(source, "PDF")
    image.close()

    def fail_run(command, **kwargs):
        if failure == "timeout":
            raise __import__("subprocess").TimeoutExpired(command, 180)
        Path(command[-1]).with_name("page-1.png").write_bytes(b"corrupt")
        return MagicMock(returncode=0, stdout="", stderr="")

    with patch("wordassistant.document.render.shutil.which", return_value="pdftoppm"), patch(
        "wordassistant.document.render.subprocess.run", side_effect=fail_run
    ):
        result = render_pdf_pages(source)

    assert len(result) == 1
    assert result[0].read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

def test_render_prevents_stale_pdf_and_uses_isolated_dir(tmp_path):
    src_docx = tmp_path / 'sample.docx'
    src_docx.write_bytes(b'PK\x03\x04fake')
    
    out_dir = tmp_path / 'output'
    out_dir.mkdir()
    stale_pdf = out_dir / 'sample.pdf'
    stale_pdf.write_bytes(b'%PDF-1.4-stale')
    
    # Mock subprocess to fail to create a PDF in isolated temp dir
    with patch('shutil.which', return_value='libreoffice'), \
         patch('subprocess.run') as mock_run:
        
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        
        # When subprocess runs, it doesn't write anything into the temp dir
        with pytest.raises(RuntimeError, match="no non-empty PDF|created"):
            render_pdf(src_docx, output_dir=out_dir)
            
    # The stale PDF in out_dir must NOT be returned or counted as success!
    assert stale_pdf.read_bytes() == b'%PDF-1.4-stale'

def test_render_success_metadata(tmp_path):
    src_docx = tmp_path / 'doc.docx'
    src_docx.write_bytes(b'PK\x03\x04fake')
    out_dir = tmp_path / 'out'
    
    def fake_subprocess_run(cmd, **kwargs):
        # Extract --outdir
        outdir_idx = cmd.index('--outdir') + 1
        isolated_dir = Path(cmd[outdir_idx])
        (isolated_dir / 'doc.pdf').write_bytes(b'%PDF-1.7-fresh-content-12345')
        return MagicMock(returncode=0, stdout='Converted', stderr='')
        
    with patch('shutil.which', return_value='libreoffice'), \
         patch('subprocess.run', side_effect=fake_subprocess_run):
        
        res = render_pdf(src_docx, output_dir=out_dir)
        assert isinstance(res, RenderResult)
        assert res.pdf_path.exists()
        assert res.pdf_path == out_dir / 'doc.pdf'
        assert res.file_size_bytes == len(b'%PDF-1.7-fresh-content-12345')
        assert res.engine == 'libreoffice'
        assert res.pdf_path.read_bytes() == b'%PDF-1.7-fresh-content-12345'


def test_render_exact_output_path_never_aliases_source_stem_destination(tmp_path):
    source = tmp_path / "report.docx"
    source.write_bytes(b"PK\x03\x04fake")
    real_destination = tmp_path / "report.pdf"
    real_destination.write_bytes(b"%PDF-ORIGINAL")
    staging = tmp_path / ".report.transaction.pdf"

    def fake_subprocess_run(command, **kwargs):
        isolated = Path(command[command.index("--outdir") + 1])
        (isolated / "report.pdf").write_bytes(b"%PDF-FRESH")
        return MagicMock(returncode=0, stdout="Converted", stderr="")

    with patch("shutil.which", return_value="libreoffice"), patch(
        "subprocess.run", side_effect=fake_subprocess_run
    ):
        result = render_pdf(
            source,
            output_dir=tmp_path,
            output_path=staging,
        )

    assert result.pdf_path == staging
    assert staging.read_bytes() == b"%PDF-FRESH"
    assert real_destination.read_bytes() == b"%PDF-ORIGINAL"


def test_page_render_failure_preserves_existing_page_evidence(tmp_path):
    source = tmp_path / "report.pdf"
    source.write_bytes(b"%PDF-broken")
    pages = tmp_path / "pages"
    pages.mkdir()
    existing = pages / "page-1.png"
    existing.write_bytes(b"previous-good-evidence")

    with patch("wordassistant.document.render.shutil.which", return_value="pdftoppm"), patch(
        "wordassistant.document.render.subprocess.run",
        return_value=MagicMock(returncode=1, stdout="", stderr="invalid PDF"),
    ):
        with pytest.raises(RuntimeError, match="invalid PDF"):
            render_pdf_pages(source, pages)

    assert existing.read_bytes() == b"previous-good-evidence"


@pytest.mark.parametrize("rendered_bytes", [b"", b"not-a-png"])
def test_page_render_rejects_invalid_png_evidence_and_preserves_existing(
    tmp_path, rendered_bytes
):
    source = tmp_path / "report.pdf"
    source.write_bytes(b"%PDF")
    pages = tmp_path / "pages"
    pages.mkdir()
    existing = pages / "page-1.png"
    existing.write_bytes(b"previous-good-evidence")

    def fake_run(command, **kwargs):
        prefix = Path(command[-1])
        prefix.with_name("page-1.png").write_bytes(rendered_bytes)
        return MagicMock(returncode=0, stdout="", stderr="")

    with patch("wordassistant.document.render.shutil.which", return_value="pdftoppm"), patch(
        "wordassistant.document.render.subprocess.run", side_effect=fake_run
    ):
        with pytest.raises(RuntimeError, match="invalid PNG|empty PNG"):
            render_pdf_pages(source, pages)

    assert existing.read_bytes() == b"previous-good-evidence"


def test_page_publish_failure_preserves_existing_evidence(tmp_path):
    source = tmp_path / "report.pdf"
    source.write_bytes(b"%PDF")
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "page-1.png").write_bytes(b"old-one")
    (pages / "page-3.png").write_bytes(b"old-three")

    def fake_run(command, **kwargs):
        prefix = Path(command[-1])
        _write_test_png(prefix.with_name("page-1.png"), "red")
        _write_test_png(prefix.with_name("page-2.png"), "blue")
        return MagicMock(returncode=0, stdout="", stderr="")

    real_replace = __import__("os").replace
    def fail_publication(source_path, destination_path):
        source_path = Path(source_path)
        destination_path = Path(destination_path)
        if "stage" in source_path.name and destination_path.parent == pages:
            raise OSError("simulated publish failure")
        return real_replace(source_path, destination_path)

    with patch("wordassistant.document.render.shutil.which", return_value="pdftoppm"), patch(
        "wordassistant.document.render.subprocess.run", side_effect=fake_run
    ), patch("wordassistant.document.render.os.replace", side_effect=fail_publication):
        with pytest.raises(OSError, match="simulated publish failure"):
            render_pdf_pages(source, pages)

    assert {path.name: path.read_bytes() for path in pages.glob("page-*.png")} == {
        "page-1.png": b"old-one",
        "page-3.png": b"old-three",
    }


def test_page_publish_returns_immutable_versioned_paths(tmp_path):
    source = tmp_path / "report.pdf"
    source.write_bytes(b"%PDF")
    pages = tmp_path / "pages"
    def fake_run(command, **kwargs):
        prefix = Path(command[-1])
        _write_test_png(prefix.with_name("page-1.png"))
        return MagicMock(returncode=0, stdout="", stderr="")

    with patch("wordassistant.document.render.shutil.which", return_value="pdftoppm"), patch(
        "wordassistant.document.render.subprocess.run", side_effect=fake_run
    ):
        first = render_pdf_pages(source, pages)
        first_bytes = first[0].read_bytes()
        second = render_pdf_pages(source, pages)

    assert first[0].parent != second[0].parent
    assert first[0].read_bytes() == first_bytes
    assert second[0].exists()


def test_libreoffice_publish_uses_same_directory_atomic_replace(tmp_path):
    source = tmp_path / "report.docx"
    source.write_bytes(b"PK\x03\x04fake")
    destination = tmp_path / "report.pdf"
    destination.write_bytes(b"old-pdf")
    replacements = []
    real_replace = __import__("os").replace

    def fake_run(command, **kwargs):
        isolated = Path(command[command.index("--outdir") + 1])
        (isolated / "report.pdf").write_bytes(b"new-pdf")
        return MagicMock(returncode=0, stdout="", stderr="")

    def record_replace(source_path, destination_path):
        replacements.append((Path(source_path), Path(destination_path)))
        return real_replace(source_path, destination_path)

    with patch("wordassistant.document.render.find_libreoffice_executable", return_value="soffice"), patch(
        "wordassistant.document.render.subprocess.run", side_effect=fake_run
    ), patch("wordassistant.document.render.os.replace", side_effect=record_replace):
        result = render_pdf(source, output_path=destination)

    assert result.pdf_path == destination
    assert destination.read_bytes() == b"new-pdf"
    assert len(replacements) == 1
    assert replacements[0][0].parent == destination.parent
    assert replacements[0][1] == destination


def test_word_render_exports_to_staging_then_atomically_replaces(tmp_path):
    source = tmp_path / "report.docx"
    source.write_bytes(b"PK\x03\x04fake")
    destination = tmp_path / "report.pdf"
    destination.write_bytes(b"old-pdf")
    exported_to = []
    replacements = []
    real_replace = __import__("os").replace

    def fake_execute(self, request):
        exported_to.append(Path(request.output_path))
        Path(request.output_path).write_bytes(b"word-pdf")
        return MagicMock(data={"page_count": 2})

    def record_replace(source_path, destination_path):
        replacements.append((Path(source_path), Path(destination_path)))
        return real_replace(source_path, destination_path)

    with patch(
        "wordassistant.backends.word_native.backend.WordNativeBackend.health",
        return_value=MagicMock(operational=True, reason=None),
    ), patch(
        "wordassistant.backends.word_native.backend.WordNativeBackend.execute",
        new=fake_execute,
    ), patch("wordassistant.document.render.os.replace", side_effect=record_replace):
        result = render_document(source, engine="word")

    assert result.pdf_path == destination
    assert result.page_count == 2
    assert destination.read_bytes() == b"word-pdf"
    assert exported_to[0] != destination
    assert exported_to[0].parent == destination.parent
    assert replacements == [(exported_to[0], destination)]
