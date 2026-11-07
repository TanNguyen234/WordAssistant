from __future__ import annotations

import json

from wordassistant import cli


def test_locked_output_file_returns_structured_json(monkeypatch, capsys):
    def locked(*args, **kwargs):
        raise PermissionError(
            13,
            "The process cannot access the file because it is being used by another process",
            "out.docx",
        )

    monkeypatch.setattr(cli, "capabilities", locked)
    exit_code = cli.run(["capabilities", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "ERROR"
    assert payload["error"]["code"] == "FILE_ACCESS_DENIED"
    assert "another process" in payload["error"]["message"]
    assert "--output" in payload["error"]["suggested_action"]
