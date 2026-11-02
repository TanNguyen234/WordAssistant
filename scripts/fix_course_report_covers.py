"""Create hash-bound Word copies with duplicate course-report covers removed.

The core WordAssistant API does not expose paragraph deletion. This helper uses
an isolated, hidden Microsoft Word COM instance and deletes only a verified
duplicate cover range from explicit input hashes. It never overwrites an input.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import win32com.client as win32


ROOT = Path(__file__).resolve().parents[1]

TASKS: list[dict[str, Any]] = [
    {
        "id": "lms",
        "input": ROOT / "artifacts/course-essay/lms-qlpm-trello-drawio/output/LMS_wbs_can_chinh_dang_kiem_tra.docx",
        "output": ROOT / "artifacts/course-essay/lms-qlpm-trello-drawio/output/LMS_20261027_bia_chuan_prefields.docx",
        "expected_sha256": "8c7f2242d1948a8776c043737d296515d4253c8b57416623de0e2a8551623694",
        "school": "TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP.HCM",
        "school_after": "TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP. HỒ CHÍ MINH",
        "body_anchor": "LỜI CẢM ƠN",
        "cover_mode": "delete_to_body",
        "format_cover": "lms",
    },
    {
        "id": "strongwine",
        "input": ROOT / "artifacts/course-essay/strongwine-revision-20261027/StrongWine_field_300.docx",
        "output": ROOT / "artifacts/course-essay/strongwine-revision-20261027/StrongWine_20261027_bia_chuan_prefields.docx",
        "expected_sha256": "cdde02c878e6766dd3ec5a7dd28f7ecc0a14a45b78f93887e09b9450d741d526",
        "school": "TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP. HỒ CHÍ MINH",
        "school_after": "TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP. HỒ CHÍ MINH",
        "body_anchor": "LỜI CẢM ƠN",
        "cover_mode": "delete_to_body",
        "format_cover": None,
    },
    {
        "id": "vietlex",
        "input": Path(r"D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020/output/VietLex_20261027_dang_kiem_tra.docx"),
        "output": Path(r"D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020/output/VietLex_20261027_bia_chuan_prefields.docx"),
        "expected_sha256": "b8490a3766649c05ca5ac4d3de49d144376d8149bbb2862dc4871f380a68a7cf",
        "school": "TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP.HCM",
        "school_after": "TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP. HỒ CHÍ MINH",
        "body_anchor": "LỜI CẢM ƠN",
        "cover_mode": "delete_to_date_text",
        "format_cover": "vietlex",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def find_match(document: Any, text: str, start: int = 0) -> Any:
    search = document.Range(start, document.Content.End)
    finder = search.Find
    finder.ClearFormatting()
    finder.Text = text
    finder.Forward = True
    finder.Wrap = 0  # wdFindStop
    finder.MatchCase = True
    finder.MatchWholeWord = False
    finder.MatchWildcards = False
    if not finder.Execute():
        raise ValueError(f"Exact Word text not found after character {start}: {text!r}")
    return document.Range(search.Start, search.End)


def set_paragraph(document: Any, index: int, text: str, *, size: float, bold: bool, spacing_after: float = 4.0) -> None:
    paragraph = document.Paragraphs.Item(index)
    if paragraph.Range.End <= paragraph.Range.Start:
        raise ValueError(f"Invalid paragraph range at index {index}")
    body = document.Range(paragraph.Range.Start, paragraph.Range.End - 1)
    body.Text = text
    paragraph = document.Paragraphs.Item(index)
    paragraph.Range.ParagraphFormat.Alignment = 1  # wdAlignParagraphCenter
    paragraph.Range.ParagraphFormat.SpaceBefore = 0
    paragraph.Range.ParagraphFormat.SpaceAfter = spacing_after
    paragraph.Range.ParagraphFormat.LineSpacingRule = 0  # wdLineSpaceSingle
    paragraph.Range.Font.Name = "Times New Roman"
    paragraph.Range.Font.Size = size
    paragraph.Range.Font.Bold = bold


def format_lms(document: Any) -> None:
    school = find_match(document, "TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP.HCM")
    school.Text = "TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP. HỒ CHÍ MINH"
    school.Paragraphs.Item(1).Range.ParagraphFormat.Alignment = 1
    school.Paragraphs.Item(1).Range.Font.Name = "Times New Roman"
    school.Paragraphs.Item(1).Range.Font.Bold = True

    if "TIỂU LUẬN MÔN HỌC" not in document.Paragraphs.Item(4).Range.Text:
        raise ValueError("LMS cover type is not at the expected cover location")
    if "ĐỀ TÀI:" not in document.Paragraphs.Item(5).Range.Text:
        raise ValueError("LMS topic is not at the expected cover location")
    if "Nguyễn Thành Duy Tân" not in document.Paragraphs.Item(6).Range.Text:
        raise ValueError("LMS student metadata is not at the expected cover location")

    document.Paragraphs.Item(4).Range.InsertParagraphAfter()
    if document.Paragraphs.Item(5).Range.Text.strip() not in ("", "\r"):
        raise ValueError("Could not create a clean LMS course-title paragraph")
    set_paragraph(document, 5, "QUẢN LÝ DỰ ÁN PHẦN MỀM", size=14, bold=True, spacing_after=8)
    set_paragraph(
        document,
        6,
        "QUẢN LÝ DỰ ÁN XÂY DỰNG HỆ THỐNG QUẢN LÝ HỌC TẬP TRỰC TUYẾN (LMS) CHO TRƯỜNG ĐẠI HỌC",
        size=16,
        bold=True,
        spacing_after=12,
    )
    set_paragraph(
        document,
        7,
        "Giảng viên hướng dẫn: ThS. Định Thị Hồng Loan\v"
        "Sinh viên thực hiện: Nguyễn Thành Duy Tân\v"
        "MSSV: 1250080266\v"
        "Lớp: 12_ĐH_CNPM3",
        size=12,
        bold=False,
        spacing_after=6,
    )
    set_paragraph(document, 8, "TP. Hồ Chí Minh, tháng 10 năm 2026", size=12, bold=False, spacing_after=0)


def format_vietlex(document: Any) -> None:
    school = find_match(document, "TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP.HCM")
    school.Text = "TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP. HỒ CHÍ MINH"
    school.Paragraphs.Item(1).Range.ParagraphFormat.Alignment = 1
    school.Paragraphs.Item(1).Range.Font.Name = "Times New Roman"
    school.Paragraphs.Item(1).Range.Font.Bold = True

    if "BÁO CÁO ĐỒ ÁN CHUYÊN NGÀNH" not in document.Paragraphs.Item(4).Range.Text:
        raise ValueError("VietLex report type is not at the expected cover location")
    set_paragraph(
        document,
        5,
        "PHÂN TÍCH VÀ ĐÁNH GIÁ HỆ THỐNG VIETLEX HỖ TRỢ TRA CỨU PHÁP LUẬT VIỆT NAM THEO HƯỚNG RAG",
        size=16,
        bold=True,
        spacing_after=10,
    )
    set_paragraph(document, 6, "Giảng viên hướng dẫn: ThS. Định Thị Hồng Loan", size=12, bold=False)
    set_paragraph(document, 7, "Sinh viên thực hiện: Nguyễn Thành Duy Tân", size=12, bold=False)
    set_paragraph(document, 8, "MSSV: 1250080266", size=12, bold=False)
    set_paragraph(document, 9, "Lớp: 12_ĐH_CNPM3", size=12, bold=False, spacing_after=0)
    # The report type is already the cover's main heading; remove its duplicate detail line.
    document.Paragraphs.Item(10).Range.Delete()
    set_paragraph(document, 10, "TP. Hồ Chí Minh, tháng 10 năm 2026", size=12, bold=False, spacing_after=0)


def process(task: dict[str, Any], application: Any) -> dict[str, Any]:
    source = task["input"].resolve()
    output = task["output"].resolve()
    sidecar = output.with_suffix(output.suffix + ".cover-review.json")
    if not source.is_file():
        raise FileNotFoundError(source)
    before_hash = sha256(source)
    if before_hash != task["expected_sha256"]:
        raise ValueError(f"Stale input hash for {task['id']}: {before_hash}")
    if output.exists() and sidecar.is_file():
        prior = json.loads(sidecar.read_text(encoding="utf-8-sig"))
        if (
            prior.get("status") == "SUCCESS"
            and prior.get("input_sha256") == before_hash
            and prior.get("output_sha256") == sha256(output)
        ):
            return prior
    if output.exists() and sha256(output) != before_hash:
        raise FileExistsError(f"Refusing to overwrite prior work: {output}")

    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, output)
    document = application.Documents.Open(
        str(output),
        ConfirmConversions=False,
        ReadOnly=False,
        AddToRecentFiles=False,
        Visible=False,
    )
    try:
        pages_before = int(document.ComputeStatistics(2))  # wdStatisticPages
        sections_before = int(document.Sections.Count)
        first = find_match(document, task["school"])
        second = find_match(document, task["school"], first.End)
        body = find_match(document, task["body_anchor"], second.End)
        if not (first.Start < second.Start < body.Start):
            raise ValueError(f"Cover duplicate/body anchors are out of order for {task['id']}")
        if body.Start > 9000:
            raise ValueError(f"Second cover is not in the expected document preamble for {task['id']}")

        if task["cover_mode"] == "delete_to_body":
            document.Range(second.Start, body.Start).Delete()
        elif task["cover_mode"] == "delete_to_date_text":
            date = find_match(document, "TP. HỒ CHÍ MINH, 2026", second.End)
            if not (second.End <= date.Start < body.Start):
                raise ValueError("VietLex duplicate cover date is not between the duplicate title and front matter")
            # Keep the existing paragraph mark and cover-section properties after deleting the repeated page.
            document.Range(second.Start, date.End).Delete()
        else:
            raise ValueError(f"Unsupported cover-removal mode: {task['cover_mode']}")

        if task["format_cover"] == "lms":
            format_lms(document)
        elif task["format_cover"] == "vietlex":
            format_vietlex(document)

        document.Repaginate()
        pages_after = int(document.ComputeStatistics(2))
        sections_after = int(document.Sections.Count)
        remaining_title = find_match(document, task["school_after"])
        try:
            second_title_remaining = find_match(document, task["school_after"], remaining_title.End)
        except ValueError:
            second_title_remaining = None
        if second_title_remaining is not None and second_title_remaining.Start < 9000:
            raise ValueError(f"Repeated cover title remains near the beginning of {task['id']}")
        if pages_after > pages_before:
            raise ValueError(f"Removing the duplicate cover unexpectedly increased pages for {task['id']}: {pages_before}->{pages_after}")
        if task["cover_mode"] == "delete_to_body" and sections_after != sections_before - 1:
            raise ValueError(f"Expected the duplicate cover section removed for {task['id']}, got {sections_before}->{sections_after}")
        if task["cover_mode"] == "delete_to_date_text" and sections_after != sections_before:
            raise ValueError("VietLex cover section boundary changed unexpectedly")
        document.Save()
    finally:
        document.Close(SaveChanges=False)

    after_hash = sha256(output)
    if sha256(source) != before_hash:
        raise RuntimeError(f"Source changed during cover revision: {source}")
    result = {
        "status": "SUCCESS",
        "document_id": task["id"],
        "input": str(source),
        "input_sha256": before_hash,
        "output": str(output),
        "output_sha256": after_hash,
        "operation": "native Word COM; remove one duplicate cover; preserve original input",
        "cover_mode": task["cover_mode"],
        "cover_reformatted": task["format_cover"] is not None,
        "pages_before": pages_before,
        "pages_after": pages_after,
        "sections_before": sections_before,
        "sections_after": sections_after,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    sidecar.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    application = win32.DispatchEx("Word.Application")
    application.Visible = False
    application.DisplayAlerts = 0
    application.ScreenUpdating = False
    results = []
    try:
        for task in TASKS:
            results.append(process(task, application))
    finally:
        application.Quit()
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
