from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "signs-of-ai-writing"
    / "scripts"
    / "ai_writing_linter.py"
)


def test_linter_reports_editorial_prompts_without_authorship_verdict():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--json"],
        input="Đây là minh chứng rõ nét cho kết quả.\n",
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["schema_version"] == "editorial-review.v1"
    assert report["total_findings"] == 1
    assert report["findings"][0]["category"] == "editorial_candidate"
    assert "authorship" in report["notice"]
    assert not {"risk_level", "risk_score", "probability", "verdict"} & report.keys()


def test_style_flags_are_optional_and_do_not_fail_the_command():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input="This stands as a testament to progress.\n",
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Editorial review prompts" in result.stdout
    assert "authorship" in result.stdout


def test_hygiene_artifacts_and_placeholders_are_separate_from_style_findings():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--json"],
        input="Use [Insert URL] and inspect turn0search2.\n",
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )

    report = json.loads(result.stdout)
    assert result.returncode == 0
    assert {item["category"] for item in report["findings"]} == {
        "placeholder",
        "possible_artifact",
    }
