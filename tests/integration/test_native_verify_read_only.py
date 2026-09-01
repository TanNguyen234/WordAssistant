from pathlib import Path

from docx import Document

from wordassistant.document.verify import verify_document
from wordassistant.operations.fields import append_field


def test_native_field_verification_uses_copy_and_preserves_source(tmp_path, monkeypatch):
    source = tmp_path / "source.docx"
    document = Document()
    paragraph = document.add_paragraph("Page ")
    append_field(paragraph, "PAGE", "1")
    document.save(source)
    original = source.read_bytes()
    observed_path = None

    def fake_worker(payload, timeout):
        nonlocal observed_path
        observed_path = Path(payload["input_path"])
        assert observed_path != source
        assert observed_path.read_bytes() == original
        observed_path.write_bytes(observed_path.read_bytes() + b"worker mutation")
        body = (
            '{"status":"SUCCESS","data":{'
            '"fields":[{"instruction":"PAGE","result":"1","locked":false}],'
            '"source_results_were_current":true}}'
        )
        return type("Completed", (), {"returncode": 0, "stdout": body, "stderr": ""})()

    monkeypatch.setattr(
        "wordassistant.backends.word_native.backend._run_native_worker", fake_worker
    )

    report = verify_document(source, native_fields=True)

    assert report["field_freshness_status"] == "PASS"
    assert source.read_bytes() == original
    assert observed_path is not None
    assert not observed_path.exists()
