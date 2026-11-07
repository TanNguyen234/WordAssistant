"""Tests for the bounded OOXML package operations integrated from the docx workflow."""

from __future__ import annotations

import json
import stat
import zipfile
from pathlib import Path

import pytest
from docx import Document
from lxml import etree

from wordassistant.cli import run
from wordassistant.ooxml import (
    OOXMLError,
    accept_changes_docx,
    merge_runs_docx,
    pack_directory,
    unpack_docx,
    validate_docx,
)
from wordassistant.ooxml.package import CONTENT_TYPES_PART, WML_NS

W = f"{{{WML_NS}}}"


def _split_run_document(path: Path) -> Path:
    document = Document()
    paragraph = document.add_paragraph()
    for piece in ["Mục ti", "êu nghiên ", "cứu của đề tài"]:
        paragraph.add_run(piece)
    document.save(path)
    return path


def _document_xml(path: Path) -> bytes:
    with zipfile.ZipFile(path) as archive:
        return archive.read("word/document.xml")


def _paragraph_texts(path: Path) -> list[str]:
    root = etree.fromstring(_document_xml(path))
    result = []
    for paragraph in root.iter(f"{W}p"):
        result.append("".join(node.text or "" for node in paragraph.iter(f"{W}t")))
    return result


def _rewrite_document_xml(path: Path, transform) -> None:
    """Rewrite word/document.xml inside a DOCX, keeping every other part."""
    with zipfile.ZipFile(path) as archive:
        entries = {info.filename: archive.read(info) for info in archive.infolist()}
    root = etree.fromstring(entries["word/document.xml"])
    transform(root)
    entries["word/document.xml"] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


def test_unpack_refuses_parent_directory_entries(tmp_path):
    evil = tmp_path / "evil.docx"
    with zipfile.ZipFile(evil, "w") as archive:
        archive.writestr(CONTENT_TYPES_PART, "<Types/>")
        archive.writestr("../escape.xml", "<x/>")
    with pytest.raises(OOXMLError, match="climbs out"):
        unpack_docx(evil, tmp_path / "out")
    assert not (tmp_path / "escape.xml").exists()


def test_unpack_refuses_symlink_entries(tmp_path):
    link = tmp_path / "link.docx"
    info = zipfile.ZipInfo("word/document.xml")
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(link, "w") as archive:
        archive.writestr(info, "target.xml")
    with pytest.raises(OOXMLError, match="symlink entry refused"):
        unpack_docx(link, tmp_path / "out")


def test_unpack_then_pack_round_trip_is_valid(tmp_path):
    source = _split_run_document(tmp_path / "source.docx")
    parts = unpack_docx(source, tmp_path / "pkg")
    assert any(part.name == "word/document.xml" for part in parts)
    packed = pack_directory(tmp_path / "pkg", tmp_path / "repacked.docx")
    assert packed["entries"] == len(parts)
    report = validate_docx(tmp_path / "repacked.docx")
    assert report["valid"] is True
    assert report["error_count"] == 0


def test_pack_refuses_malformed_xml(tmp_path):
    source = _split_run_document(tmp_path / "source.docx")
    unpack_docx(source, tmp_path / "pkg")
    (tmp_path / "pkg" / "word" / "document.xml").write_text("<w:document", encoding="utf-8")
    with pytest.raises(OOXMLError, match="malformed XML"):
        pack_directory(tmp_path / "pkg", tmp_path / "broken.docx")
    assert not (tmp_path / "broken.docx").exists()


def test_merge_runs_coalesces_identical_runs_without_changing_text(tmp_path):
    source = _split_run_document(tmp_path / "split.docx")
    before = _paragraph_texts(source)
    result = merge_runs_docx(source, tmp_path / "merged.docx")
    assert result["runs_before"] == 3
    assert result["runs_after"] == 1
    assert result["runs_merged"] == 2
    assert _paragraph_texts(tmp_path / "merged.docx") == before
    assert validate_docx(tmp_path / "merged.docx", original=source)["tracked_text"]["status"] == "PASS"


def test_merge_runs_refuses_in_place_rewrite(tmp_path):
    source = _split_run_document(tmp_path / "split.docx")
    with pytest.raises(OOXMLError, match="output must differ"):
        merge_runs_docx(source, source)


def test_merge_runs_keeps_separate_revisions_apart(tmp_path):
    source = _split_run_document(tmp_path / "tracked.docx")

    def wrap_second_run_as_insertion(root):
        paragraph = next(root.iter(f"{W}p"))
        runs = paragraph.findall(f"{W}r")
        insertion = etree.Element(f"{W}ins", {f"{W}id": "1", f"{W}author": "Tester", f"{W}date": "2026-11-07T00:00:00Z"})
        paragraph.insert(list(paragraph).index(runs[1]), insertion)
        insertion.append(runs[1])

    _rewrite_document_xml(source, wrap_second_run_as_insertion)
    merged = merge_runs_docx(source, tmp_path / "merged.docx")
    assert merged["runs_merged"] == 0
    root = etree.fromstring(_document_xml(tmp_path / "merged.docx"))
    assert len(root.findall(f".//{W}ins")) == 1


def _tracked_document(path: Path) -> Path:
    """P1 holds kept, deleted and inserted runs. P2's paragraph mark is deleted, so P2 joins P3."""
    document = Document()
    document.add_paragraph("Giữ bỏ")
    document.add_paragraph("Đoạn bị xóa")
    document.add_paragraph("Kết")
    document.save(path)

    def markup(root):
        paragraphs = list(root.iter(f"{W}p"))
        first = paragraphs[0]
        for run in list(first.findall(f"{W}r")):
            first.remove(run)
        plain = etree.SubElement(first, f"{W}r")
        etree.SubElement(plain, f"{W}t").text = "Giữ "
        deletion = etree.SubElement(first, f"{W}del", {f"{W}id": "2", f"{W}author": "T", f"{W}date": "2026-11-07T00:00:00Z"})
        dr = etree.SubElement(deletion, f"{W}r")
        etree.SubElement(dr, f"{W}delText").text = "bỏ"
        insertion = etree.SubElement(first, f"{W}ins", {f"{W}id": "3", f"{W}author": "T", f"{W}date": "2026-11-07T00:00:00Z"})
        ir = etree.SubElement(insertion, f"{W}r")
        etree.SubElement(ir, f"{W}t").text = "thêm"
        second = paragraphs[1]
        ppr = second.find(f"{W}pPr")
        if ppr is None:
            ppr = etree.Element(f"{W}pPr")
            second.insert(0, ppr)
        mark = etree.SubElement(ppr, f"{W}rPr")
        etree.SubElement(mark, f"{W}del", {f"{W}id": "4", f"{W}author": "T", f"{W}date": "2026-11-07T00:00:00Z"})

    _rewrite_document_xml(path, markup)
    return path


def test_accept_changes_keeps_insertions_removes_deletions_and_joins_marked_paragraph(tmp_path):
    source = _tracked_document(tmp_path / "tracked.docx")
    result = accept_changes_docx(source, tmp_path / "accepted.docx")
    assert result["insertions_accepted"] == 1
    assert result["deletions_removed"] == 1
    assert result["paragraph_marks_joined"] == 1
    assert _paragraph_texts(tmp_path / "accepted.docx") == ["Giữ thêm", "Đoạn bị xóaKết"]


def test_validate_reports_untracked_text_change_against_original(tmp_path):
    original = _split_run_document(tmp_path / "original.docx")
    edited = tmp_path / "edited.docx"
    edited.write_bytes(original.read_bytes())
    _rewrite_document_xml(edited, lambda root: setattr(next(root.iter(f"{W}t")), "text", "Mục tiêu"))
    report = validate_docx(edited, original=original)
    assert report["tracked_text"]["status"] == "FAIL"
    assert report["valid"] is False
    assert any(issue["code"] == "untracked_text_change" for issue in report["issues"])


def test_validate_flags_missing_relationship_target(tmp_path):
    source = _split_run_document(tmp_path / "rel.docx")
    unpack_docx(source, tmp_path / "pkg")
    rels = tmp_path / "pkg" / "word" / "_rels" / "document.xml.rels"
    text = rels.read_text(encoding="utf-8")
    rels.write_text(text.replace('Target="styles.xml"', 'Target="missing-styles.xml"'), encoding="utf-8")
    pack_directory(tmp_path / "pkg", tmp_path / "broken-rel.docx")
    report = validate_docx(tmp_path / "broken-rel.docx")
    assert report["valid"] is False
    assert any(issue["code"] == "relationship_target_missing" for issue in report["issues"])


def test_schema_check_reports_not_run_without_schema_directory(tmp_path):
    source = _split_run_document(tmp_path / "schema.docx")
    report = validate_docx(source)
    assert report["schema"]["status"] == "NOT_RUN"
    missing = validate_docx(source, schema_dir=tmp_path / "no-such-dir")
    assert missing["schema"]["status"] == "NOT_RUN"


def test_cli_ooxml_merge_runs_and_validate_emit_json(tmp_path, capsys):
    source = _split_run_document(tmp_path / "cli.docx")
    code = run(["ooxml", "merge-runs", str(source), "--output", str(tmp_path / "cli-merged.docx"), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["operation"] == "ooxml.merge-runs"
    assert payload["runs_after"] == 1
    code = run(["ooxml", "validate", str(tmp_path / "cli-merged.docx"), "--original", str(source), "--json"])
    verdict = json.loads(capsys.readouterr().out)
    assert code == 0
    assert verdict["valid"] is True
    assert verdict["tracked_text"]["status"] == "PASS"


def test_cli_doctor_reports_render_engines_and_lxml(capsys):
    code = run(["doctor", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert "render_engines" in payload
    assert isinstance(payload["render_engines"], list)
    assert payload["lxml"] is True
    assert isinstance(payload["microsoft_word"], bool)
