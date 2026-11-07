from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Pt

from wordassistant.document.code_blocks import is_code_paragraph, is_code_style_name
from wordassistant.document.integrity import _unresolved_placeholder_findings
from wordassistant.document.validate import validate_document
from wordassistant.profiles.loader import resolve_profile

CODE_SOURCE = "services.safe_create_vlan(job.device,int(job.payload['vlan_id']),str(job.payload['name']))"


def _code_style(document):
    if "Code Listing" not in [style.name for style in document.styles]:
        document.styles.add_style("Code Listing", WD_STYLE_TYPE.PARAGRAPH)
    return document.styles["Code Listing"]


def _codes(path: Path, profile_name: str = "hcmunre_dacn_2026_2027") -> set[str]:
    result = validate_document(path, resolve_profile(profile_name), "report", verify_mode=True)
    return {issue.code for issue in result.issues}


def test_code_style_and_monospace_runs_are_code_paragraphs():
    document = Document()
    by_style = document.add_paragraph(CODE_SOURCE, style=_code_style(document))
    assert is_code_paragraph(by_style)

    by_font = document.add_paragraph()
    by_font.add_run("assign_access_port(device, interface, vlan_id)").font.name = "Courier New"
    assert is_code_paragraph(by_font)

    prose = document.add_paragraph()
    prose.add_run("Đoạn văn thường dùng Times New Roman.").font.name = "Times New Roman"
    assert not is_code_paragraph(prose)

    assert not is_code_paragraph(document.add_paragraph())


def test_code_style_names_match_case_insensitively():
    assert is_code_style_name("Code Listing")
    assert is_code_style_name(" code listing ")
    assert not is_code_style_name("Body Text Essay")
    assert not is_code_style_name(None)


def test_integrity_placeholder_scan_skips_code_but_flags_prose():
    records = [
        {"story": "body", "paragraph_index": 1, "text": "{{ vlan_id }} và job.payload['name']", "style": "Code Listing"},
        {"story": "body", "paragraph_index": 2, "text": "Ghi chú TODO cần bổ sung", "style": "Body Text Essay"},
    ]
    findings = _unresolved_placeholder_findings(records)
    assert [finding["text"] for finding in findings] == ["TODO"]


def test_draft_placeholder_scan_ignores_code_listing(tmp_path: Path):
    code_only = Document()
    code_only.add_paragraph(CODE_SOURCE, style=_code_style(code_only))
    code_path = tmp_path / "code_only.docx"
    code_only.save(code_path)
    assert "draft_placeholder_detected" not in _codes(code_path)

    prose = Document()
    prose.add_paragraph("Nội dung [Nhóm điền tên sinh viên] cần hoàn thiện.")
    prose_path = tmp_path / "prose_placeholder.docx"
    prose.save(prose_path)
    assert "draft_placeholder_detected" in _codes(prose_path)


def test_typography_checks_skip_code_listing(tmp_path: Path):
    def body_document(extra=None):
        document = Document()
        document.add_paragraph("MỞ ĐẦU")
        body = document.add_paragraph()
        run = body.add_run("Đoạn văn chính của tiểu luận.")
        run.font.name = "Times New Roman"
        run.font.size = Pt(13)
        if extra is not None:
            extra(document)
        return document

    def add_code(document):
        code = document.add_paragraph()
        run = code.add_run(CODE_SOURCE)
        run.font.name = "Courier New"
        run.font.size = Pt(8)

    baseline_path = tmp_path / "baseline.docx"
    body_document().save(baseline_path)
    with_code_path = tmp_path / "with_code.docx"
    body_document(add_code).save(with_code_path)

    typography = {"typography_font", "typography_size"}
    assert _codes(with_code_path) & typography == _codes(baseline_path) & typography
