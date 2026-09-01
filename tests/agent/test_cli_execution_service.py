import json

from docx import Document

from wordassistant.cli import run
from wordassistant.execution import ExecutionService
from wordassistant.operations.models import Fidelity, OperationResult


def test_generic_cli_uses_execution_service(tmp_path, monkeypatch, capsys):
    source = tmp_path / "source.docx"
    Document().save(source)
    output = tmp_path / "output.docx"
    called = []

    class Service:
        def execute(self, request):
            called.append(request)
            return OperationResult.success(
                request.name,
                "python-docx",
                Fidelity.HIGH,
                output_path=output,
            )

    monkeypatch.setattr(ExecutionService, "default", classmethod(lambda cls: Service()))
    code = run(
        [
            "table",
            "create",
            str(source),
            "--output",
            str(output),
            "--options",
            '{"rows":1,"columns":1}',
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert called[0].name == "table.create"
    assert payload["operation"] == "table.create"


def test_cli_errors_use_stable_envelope(tmp_path, capsys):
    source = tmp_path / "source.docx"
    Document().save(source)

    code = run(["table", "create", str(source), "--options", "{}", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 1
    assert payload["status"] == "ERROR"
    assert set(payload["error"]) == {
        "code",
        "message",
        "backend_required",
        "suggested_action",
    }
