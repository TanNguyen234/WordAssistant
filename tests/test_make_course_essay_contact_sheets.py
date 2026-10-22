import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image


SCRIPT = Path(__file__).parents[1] / "scripts" / "make_course_essay_contact_sheets.py"
SPEC = importlib.util.spec_from_file_location("make_course_essay_contact_sheets", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CONTACT_SHEETS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTACT_SHEETS)


def test_contact_sheet_builder_groups_all_rendered_pages(tmp_path: Path, monkeypatch, capsys):
    page_paths = []
    for index in range(3):
        page = tmp_path / f"page-{index + 1}.png"
        Image.new("RGB", (80, 120), "white").save(page)
        page_paths.append(str(page))

    report = tmp_path / "verify.json"
    report.write_text(
        json.dumps({"render": {"page_images": page_paths}}), encoding="utf-8"
    )
    output_dir = tmp_path / "sheets"
    monkeypatch.setattr(
        sys,
        "argv",
        [str(SCRIPT), str(report), str(output_dir), "--columns", "2", "--rows", "1"],
    )

    CONTACT_SHEETS.main()

    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "CREATED"
    assert result["page_count"] == 3
    assert [Path(path).name for path in result["sheets"]] == [
        "contact-001-002.png",
        "contact-003-003.png",
    ]
    assert all(Path(path).is_file() for path in result["sheets"])
