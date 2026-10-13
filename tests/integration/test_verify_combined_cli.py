from pathlib import Path

from docx import Document

from wordassistant import cli


def _prepare_cli(monkeypatch, source, captured):
    monkeypatch.setattr(cli, "load_project_config", lambda _: {})
    monkeypatch.setattr(
        cli,
        "resolve_profile",
        lambda *args, **kwargs: type("Profile", (), {"profile_id": "generic"})(),
    )
    monkeypatch.setattr(
        cli,
        "inspect_document",
        lambda _: {"paragraphs": 1, "tables": 0, "sections": 1, "images": 0, "fields": 0},
    )

    def fake_verify(*args, **kwargs):
        captured.update(kwargs)
        return {
            "overall_status": "PASS",
            "delivery_status": "INCOMPLETE",
            "delivery_gates": {},
            "format_status": "PASS",
            "render_status": "NOT_REQUESTED",
            "issues": [],
        }

    monkeypatch.setattr(cli, "verify_document", fake_verify)
    Document().save(source)


def test_default_verify_cli_leaves_renderer_implicit_for_combined_word_path(
    tmp_path, monkeypatch
):
    source = tmp_path / "report.docx"
    captured = {}
    _prepare_cli(monkeypatch, source, captured)

    assert cli.run(["verify", str(source), "--render", "--native-fields"]) == 0

    assert captured["renderer"] is None


def test_verify_cli_preserves_injected_renderer_and_explicit_engine(
    tmp_path, monkeypatch
):
    source = tmp_path / "report.docx"
    captured = {}
    _prepare_cli(monkeypatch, source, captured)

    injected = lambda path, output_dir=None: None
    monkeypatch.setattr(cli, "render_pdf", injected)
    assert cli.run(["verify", str(source), "--render", "--native-fields"]) == 0
    assert captured["renderer"] is injected

    captured.clear()
    monkeypatch.setattr(cli, "render_pdf", cli.render_document)
    assert cli.run(
        ["verify", str(source), "--render", "--native-fields", "--engine", "libreoffice"]
    ) == 0
    assert callable(captured["renderer"])
