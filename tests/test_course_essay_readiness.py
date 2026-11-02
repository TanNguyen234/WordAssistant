from __future__ import annotations

import csv
import hashlib
import io
import json
import struct
import sys
import tempfile
import types
import zlib
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_course_essay_readiness as readiness  # noqa: E402


def test_main_emits_ascii_safe_json_for_windows_default_console(monkeypatch, capsys, tmp_path):
    report = {"status": "PASS", "title": "Đồ án chuyên ngành"}
    monkeypatch.setattr(readiness, "assess", lambda _project_dir: report)

    assert readiness.main([str(tmp_path)]) == 0

    output = capsys.readouterr().out
    assert "\\u0110" in output
    assert json.loads(output)["title"] == "Đồ án chuyên ngành"


MATRIX_FIELDS = [
    "requirement_id", "rubric_requirement", "rubric_location", "report_section",
    "evidence_files", "verification", "status", "notes", "waived_by",
]
CLAIM_FIELDS = [
    "claim_id", "report_location", "claim_summary", "evidence_id", "source_file",
    "source_sha256", "source_location", "review_status", "support_confirmed",
    "reviewed_by", "review_date",
]
DISPOSITION_FIELDS = [
    "gate", "finding_index", "decision", "reason", "evidence", "reviewed_by", "review_date",
]
COVER_METADATA_FIELDS = [
    "field", "value", "authority", "authority_type", "status", "reviewed_by", "review_date", "notes",
]
STRUCTURE_PARITY_FIELDS = [
    "item_id", "source_basis", "source_location", "planned_heading", "planned_level", "target_heading", "target_level", "target_order", "decision",
    "include_in_toc", "coverage_note", "evidence_files", "status", "reviewed_by", "review_date",
]
ASSET_PARITY_FIELDS = [
    "asset_id", "asset_type", "source_basis", "source_location",
    "target_section", "target_caption", "decision", "coverage_note", "evidence_files",
    "capture_id", "runtime_route",
    "expected_media_count", "caption_required", "status", "reviewed_by", "review_date",
]
ACCEPTANCE_CATEGORIES = [
    "user_requirements", "guide_requirements", "assignment_rubric_requirements", "heading_toc", "abstract",
    "screen_hierarchy", "runtime_screenshots", "diagrams", "visual_content",
    "argument_citations",
]
ACCEPTANCE_CROSSWALK_FIELDS = [
    "check_id", "category", "authority", "source_location", "acceptance_criterion",
    "report_location", "verification_method", "evidence_files", "evidence_sha256", "status",
    "document_sha256", "reviewed_by", "review_date", "notes",
]


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_docx(
    path: Path,
    outline_rows: list[dict[str, str]],
    captions: list[str] | None = None,
    *,
    toc_rows: list[dict[str, str]] | None = None,
    picture_count: int = 1,
) -> None:
    document = Document()
    toc_rows = outline_rows if toc_rows is None else toc_rows
    for level in {int(row["target_level"]) for row in toc_rows}:
        style_name = f"TOC {level}"
        if style_name not in document.styles:
            document.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
    for row in toc_rows:
        document.add_paragraph(
            f"{row['target_heading']}\t1",
            style=f"TOC {row['target_level']}",
        )
    for row in outline_rows:
        document.add_paragraph(
            row["target_heading"],
            style=f"Heading {row['target_level']}",
        )
        document.add_paragraph("Synthetic section body long enough to preserve every heading in the outline.")
    for _ in range(picture_count):
        paragraph = document.add_paragraph()
        paragraph.add_run().add_picture(io.BytesIO(_tiny_png()), width=Inches(0.1))
    # A table-of-figures-like entry should never be mistaken for the real
    # in-body caption that binds an image to its planned asset.
    for caption in captions or []:
        document.add_paragraph(caption)
    for caption in captions or []:
        document.add_paragraph(caption, style="Caption")
    document.save(path)


def _tiny_png() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
        + chunk(b"IEND", b"")
    )


def _case(root: Path) -> tuple[Path, dict, Path, Path]:
    project_dir = root / "essay"
    project_dir.mkdir()
    qa_dir = project_dir / "qa"
    qa_dir.mkdir()
    (project_dir / "assignment.md").write_text("Assignment", encoding="utf-8")
    (project_dir / "rubric.md").write_text("Rubric", encoding="utf-8")
    source = project_dir / "source.txt"
    source.write_text("Reviewed evidence passage", encoding="utf-8")
    output = project_dir / "output" / "final.docx"
    output.parent.mkdir()
    structure_rows = [
        {"item_id": "S-01", "source_basis": "assignment", "source_location": "section 1", "planned_heading": "Project overview", "planned_level": "1", "target_heading": "Project overview", "target_level": "1", "target_order": "1", "include_in_toc": "true"},
        {"item_id": "S-02", "source_basis": "assignment", "source_location": "section 2", "planned_heading": "System design", "planned_level": "2", "target_heading": "System design", "target_level": "2", "target_order": "2", "include_in_toc": "true"},
        {"item_id": "S-03", "source_basis": "project analysis", "source_location": "report plan", "planned_heading": "Evaluation", "planned_level": "2", "target_heading": "Evaluation", "target_level": "2", "target_order": "3", "include_in_toc": "true"},
    ]
    asset_rows = [
        {"asset_id": "A-01", "asset_type": "DIAGRAM", "source_basis": "project source", "source_location": "architecture config", "target_section": "System design", "target_caption": "Figure 1. Project architecture", "decision": "ADAPTED", "coverage_note": "Derived from checked source", "evidence_files": "source.txt", "expected_media_count": "1", "caption_required": "true", "status": "PASS", "reviewed_by": "Reviewer", "review_date": "2026-10-20"},
        {"asset_id": "A-02", "asset_type": "TABLE", "source_basis": "evaluation record", "source_location": "evaluation.json", "target_section": "Evaluation", "target_caption": "Table 1. Evaluation results", "decision": "MATCHED", "coverage_note": "Derived from checked source", "evidence_files": "source.txt", "expected_media_count": "0", "caption_required": "true", "status": "PASS", "reviewed_by": "Reviewer", "review_date": "2026-10-20"},
    ]
    _write_docx(output, structure_rows, [row["target_caption"] for row in asset_rows])
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()

    project = {
        "schema_version": 1,
        "project_title": "Demo essay",
        "institution_profile": None,
        "profile_variant": "default",
        "assignment_file": "assignment.md",
        "assignment_summary": "",
        "rubric_file": "rubric.md",
        "source_project_root": str(project_dir),
        "output_docx": "output/final.docx",
        "cover_metadata_file": "cover-metadata.csv",
        "structure_parity_matrix_file": "structure-parity.csv",
        "asset_parity_matrix_file": "asset-parity.csv",
        "acceptance_crosswalk_file": "acceptance-crosswalk.csv",
        "requirements_matrix_file": "requirements-matrix.csv",
        "claim_evidence_file": "claim-evidence.csv",
        "evidence_registry_file": "evidence.json",
        "integrity_warning_dispositions_file": "integrity-warning-dispositions.csv",
        "qa_reports": {
            "profile_validation": "qa/profile-validation.json",
            "word_verify": "qa/word-verify.json",
            "integrity_audit": "qa/integrity-audit.json",
        },
        "required_acceptance_checks": [
            "assignment_and_rubric_checked",
            "cover_metadata_fields_verified",
            "project_structure_inventory_reviewed",
            "project_visual_inventory_reviewed",
            "all_required_claims_mapped_to_reviewed_evidence",
            "all_integrity_warnings_reviewed_and_dispositioned",
            "source_routes_and_templates_checked",
            "wireframes_and_runtime_captures_distinguished",
            "figure_list_rebuilt_from_captions",
            "word_fields_updated_and_saved",
            "all_rendered_pages_visually_reviewed",
        ],
        "acceptance_checks": {
            "assignment_and_rubric_checked": True,
            "cover_metadata_fields_verified": True,
            "project_structure_inventory_reviewed": True,
            "project_visual_inventory_reviewed": True,
            "all_required_claims_mapped_to_reviewed_evidence": True,
            "all_integrity_warnings_reviewed_and_dispositioned": True,
            "source_routes_and_templates_checked": True,
            "wireframes_and_runtime_captures_distinguished": True,
            "figure_list_rebuilt_from_captions": True,
            "word_fields_updated_and_saved": True,
            "all_rendered_pages_visually_reviewed": True,
        },
    }
    (project_dir / "project.json").write_text(json.dumps(project), encoding="utf-8")
    _write_csv(
        project_dir / "acceptance-crosswalk.csv",
        ACCEPTANCE_CROSSWALK_FIELDS,
        [{
            "check_id": f"AC-{index:02}", "category": category,
            "authority": "assignment.md", "source_location": f"acceptance item {index}",
            "acceptance_criterion": f"Reviewed {category} criteria for this synthetic report.",
            "report_location": "whole report", "verification_method": "reviewed against evidence",
            "evidence_files": "source.txt", "evidence_sha256": source_digest, "status": "PASS", "document_sha256": digest,
            "reviewed_by": "Reviewer", "review_date": "2026-10-20", "notes": "",
        } for index, category in enumerate(ACCEPTANCE_CATEGORIES, start=1)],
    )
    _write_csv(
        project_dir / "requirements-matrix.csv",
        MATRIX_FIELDS,
        [{
            "requirement_id": "R1", "rubric_requirement": "Discuss the system",
            "rubric_location": "rubric.md", "report_section": "1",
        "evidence_files": "source.txt", "verification": "Opened source and checked passage",
        "status": "PASS", "notes": "", "waived_by": "",
        }],
    )
    metadata_rows = [{
        "field": field, "value": "", "authority": "", "authority_type": "NOT_PROVIDED",
        "status": "PLACEHOLDER", "reviewed_by": "Reviewer", "review_date": "2026-10-20",
        "notes": "Not supplied; leave blank in the document.",
    } for field in readiness._COVER_METADATA_FIELDS]
    _write_csv(project_dir / "cover-metadata.csv", COVER_METADATA_FIELDS, metadata_rows)
    parity_rows = [{
        **row,
        "decision": "MATCHED",
        "coverage_note": "Synthetic mapping for readiness test fixture.",
        "evidence_files": "source.txt",
        "status": "PASS",
        "reviewed_by": "Reviewer",
        "review_date": "2026-10-20",
    } for row in structure_rows]
    _write_csv(project_dir / "structure-parity.csv", STRUCTURE_PARITY_FIELDS, parity_rows)
    _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, asset_rows)
    _write_csv(
        project_dir / "claim-evidence.csv",
        CLAIM_FIELDS,
        [{
            "claim_id": "C1", "report_location": "Section 1", "claim_summary": "Verified claim",
            "evidence_id": "S1", "source_file": "source.txt", "source_sha256": source_digest,
            "source_location": "paragraph 1", "review_status": "reviewed", "support_confirmed": "yes",
            "reviewed_by": "Reviewer", "review_date": "2026-10-20",
        }],
    )
    (project_dir / "evidence.json").write_text(json.dumps({
        "S1": {
            "id": "S1", "review_status": "reviewed", "source_sha256": source_digest,
            "support_location": "paragraph 1",
        }
    }), encoding="utf-8")
    _write_csv(project_dir / "integrity-warning-dispositions.csv", DISPOSITION_FIELDS, [])
    registry_digest = hashlib.sha256((project_dir / "evidence.json").read_bytes()).hexdigest()
    (qa_dir / "word-verify.json").write_text(json.dumps({
        "overall_status": "PASS", "delivery_status": "PASS", "render_status": "PASS", "visual_status": "PASS",
        "render": {"document_sha256": digest},
    }), encoding="utf-8")
    (qa_dir / "integrity-audit.json").write_text(json.dumps({
        "status": "PASS", "document": {"sha256": digest}, "gates": {
            "source_evidence": {
                "status": "PASS", "finding_count": 0, "findings": [],
                "linked_evidence_id_count": 1, "verified_record_count": 1,
                "registry": {"sha256": registry_digest},
            },
            "unresolved_placeholders": {"status": "PASS", "finding_count": 0, "findings": []},
        },
    }), encoding="utf-8")
    return project_dir, project, output, source


def _save_project(project_dir: Path, project: dict) -> None:
    (project_dir / "project.json").write_text(json.dumps(project), encoding="utf-8")


def _rebind_qa(project_dir: Path, output: Path) -> None:
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    crosswalk_path = project_dir / "acceptance-crosswalk.csv"
    if crosswalk_path.is_file():
        crosswalk = readiness._rows(crosswalk_path)
        for row in crosswalk:
            row["document_sha256"] = digest
        _write_csv(crosswalk_path, ACCEPTANCE_CROSSWALK_FIELDS, crosswalk)
    verify_path = project_dir / "qa" / "word-verify.json"
    verify = json.loads(verify_path.read_text(encoding="utf-8"))
    verify["render"]["document_sha256"] = digest
    verify_path.write_text(json.dumps(verify), encoding="utf-8")
    audit_path = project_dir / "qa" / "integrity-audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["document"]["sha256"] = digest
    audit_path.write_text(json.dumps(audit), encoding="utf-8")


def _add_official_rubric_appendix(
    project_dir: Path,
    project: dict,
    output: Path,
    *,
    include_all_criteria: bool = True,
) -> Path:
    source_path = project_dir / "official-rubric.docx"
    source = Document()
    source.add_paragraph("Official marking rubric")
    source_table = source.add_table(rows=3, cols=2)
    source_table.cell(0, 0).text = "Criterion"
    source_table.cell(0, 1).text = "Weight"
    source_table.cell(1, 0).text = "Evidence quality"
    source_table.cell(1, 1).text = "40%"
    source_table.cell(2, 0).text = "Analysis quality"
    source_table.cell(2, 1).text = "60%"
    source.save(source_path)

    target = Document(output)
    target.add_page_break()
    target.add_heading("PHỤ LỤC A. RUBRIC CHÍNH THỨC", level=1)
    target.add_paragraph("Official marking rubric")
    target_table = target.add_table(rows=3 if include_all_criteria else 2, cols=2)
    target_table.cell(0, 0).text = "Criterion"
    target_table.cell(0, 1).text = "Weight"
    target_table.cell(1, 0).text = "Evidence quality"
    target_table.cell(1, 1).text = "40%"
    if include_all_criteria:
        target_table.cell(2, 0).text = "Analysis quality"
        target_table.cell(2, 1).text = "60%"
    target.save(output)

    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    output_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    project["rubric_file"] = source_path.name
    project["include_official_rubric_in_docx"] = True
    project["rubric_source_authority"] = "Official course assignment rubric"
    project["rubric_inclusion"] = {
        "source_sha256": source_hash,
        "output_docx_sha256": output_hash,
        "appendix_heading": "PHỤ LỤC A. RUBRIC CHÍNH THỨC",
        "review_status": "PASS",
        "review_method": "verbatim_source_comparison",
        "reviewed_by": "Human reviewer",
        "reviewed_at": "2026-10-24",
    }
    _rebind_qa(project_dir, output)
    _save_project(project_dir, project)
    return source_path


def _add_profile_section_criteria(
    project_dir: Path,
    project: dict,
    output: Path,
    *,
    omit_criterion: str | None = None,
    image_inside_source_section: bool = False,
) -> Path:
    source_path = project_dir / "official-guide.docx"
    source = Document()
    source.add_paragraph("Supervisor assessment criteria")
    source.add_paragraph("Structure and presentation.")
    source.add_paragraph("Theoretical basis.")
    if image_inside_source_section:
        source.add_paragraph().add_run().add_picture(io.BytesIO(_tiny_png()), width=Inches(0.1))
    source.add_paragraph("Practical value and applicability.")
    source.add_paragraph("Outcome: pass or fail; no points on this page.")
    source.add_paragraph("Reviewer instructions")
    source.add_paragraph("State the reviewer's position clearly.")
    source.add_paragraph("Do not award points on this page.")
    source.add_paragraph("Work schedule")
    source.add_paragraph().add_run().add_picture(io.BytesIO(_tiny_png()), width=Inches(0.1))
    source.save(source_path)

    supervisor_criteria = [
        "Structure and presentation.",
        "Theoretical basis.",
        "Practical value and applicability.",
        "Outcome: pass or fail; no points on this page.",
    ]
    reviewer_criteria = [
        "State the reviewer's position clearly.",
        "Do not award points on this page.",
    ]
    target = Document(output)
    target.add_page_break()
    target.add_heading("SUPERVISOR REVIEW", level=1)
    target.add_paragraph("Supervisor: Example")
    target.add_paragraph("Student: Example")
    for criterion in supervisor_criteria:
        if criterion != omit_criterion:
            target.add_paragraph(criterion)
    target.add_heading("REVIEWER REVIEW", level=1)
    target.add_paragraph("Reviewer: Example")
    for criterion in reviewer_criteria:
        target.add_paragraph(criterion)
    target.add_heading("WORK SCHEDULE", level=1)
    target.save(output)

    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    output_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    project["rubric_file"] = source_path.name
    project["include_official_rubric_in_docx"] = True
    project["rubric_source_authority"] = "Official institutional guide bundled with the selected profile"
    project["rubric_inclusion"] = {
        "source_sha256": source_hash,
        "output_docx_sha256": output_hash,
        "review_status": "PASS",
        "review_method": "verbatim_source_section_comparison",
        "reviewed_by": "Human reviewer",
        "reviewed_at": "2026-10-24",
        "source_sections": [
            {
                "source_start": "Supervisor assessment criteria",
                "source_end": "Reviewer instructions",
                "output_start": "SUPERVISOR REVIEW",
                "output_end": "REVIEWER REVIEW",
            },
            {
                "source_start": "Reviewer instructions",
                "source_end": "Work schedule",
                "output_start": "REVIEWER REVIEW",
                "output_end": "WORK SCHEDULE",
            },
        ],
    }
    _rebind_qa(project_dir, output)
    _save_project(project_dir, project)
    return source_path


def test_all_required_evidence_and_word_gates_produce_ready_status() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))

        report = readiness.assess(project_dir)

    assert report["status"] == "PASS"
    assert report["gates"]["word_delivery"]["status"] == "PASS"
    assert report["gates"]["content_and_sources"]["status"] == "PASS"
    assert report["gates"]["submission_readiness"]["status"] == "PASS"


def test_structure_inventory_accepts_a_project_specific_number_of_headings() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "structure-parity.csv")
        for index in range(4, 7):
            rows.append({
                "item_id": f"S-{index:02}", "source_basis": "project plan", "source_location": f"plan row {index}", "planned_level": "2",
                "planned_heading": f"Additional section {index}",
                "target_heading": f"Additional section {index}", "target_level": "2",
                "target_order": str(index), "include_in_toc": "true", "decision": "ADAPTED",
                "coverage_note": "Required by this project plan.", "evidence_files": "source.txt",
                "status": "PASS", "reviewed_by": "Reviewer", "review_date": "2026-10-20",
            })
        _write_csv(project_dir / "structure-parity.csv", STRUCTURE_PARITY_FIELDS, rows)
        captions = [row["target_caption"] for row in readiness._rows(project_dir / "asset-parity.csv")]
        _write_docx(output, rows, captions)
        _rebind_qa(project_dir, output)

        report = readiness.assess(project_dir)

    parity = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_structure_inventory"
    )
    assert parity["status"] == "PASS"
    assert "6 project-planned headings" in parity["detail"]
    assert report["gates"]["submission_readiness"]["status"] == "PASS"


def test_structure_inventory_requires_every_planned_heading_in_the_matrix() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "structure-parity.csv")
        rows[0]["target_heading"] = ""
        _write_csv(project_dir / "structure-parity.csv", STRUCTURE_PARITY_FIELDS, rows)

        report = readiness.assess(project_dir)

    parity = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_structure_inventory"
    )
    assert parity["status"] == "INCOMPLETE"


def test_structure_parity_rejects_changed_heading_level() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "structure-parity.csv")
        rows[0]["target_level"] = "2"
        _write_csv(project_dir / "structure-parity.csv", STRUCTURE_PARITY_FIELDS, rows)

        report = readiness.assess(project_dir)

    parity = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_structure_inventory"
    )
    assert parity["status"] == "FAIL"


def test_structure_parity_rejects_reordered_headings() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "structure-parity.csv")
        rows[0]["target_order"] = "2"
        _write_csv(project_dir / "structure-parity.csv", STRUCTURE_PARITY_FIELDS, rows)

        report = readiness.assess(project_dir)

    parity = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_structure_inventory"
    )
    assert parity["status"] == "FAIL"


def test_structure_inventory_checks_the_actual_docx_outline() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "structure-parity.csv")
        _write_docx(output, rows[:-1], [row["target_caption"] for row in readiness._rows(project_dir / "asset-parity.csv")])

        report = readiness.assess(project_dir)

    outline_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_structure_in_docx"
    )
    assert outline_check["status"] == "FAIL"


def test_structure_inventory_ignores_toc_entries_even_with_outline_level() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        document = Document(output)
        toc_entry = document.add_paragraph("Project overview\t1", style="TOC 1")
        outline_level = OxmlElement("w:outlineLvl")
        outline_level.set(qn("w:val"), "0")
        toc_entry._p.get_or_add_pPr().append(outline_level)
        document.save(output)
        _rebind_qa(project_dir, output)

        report = readiness.assess(project_dir)

    outline_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_structure_in_docx"
    )
    assert outline_check["status"] == "PASS"


def test_toc_parity_rejects_a_missing_visible_toc_heading() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "structure-parity.csv")
        captions = [row["target_caption"] for row in readiness._rows(project_dir / "asset-parity.csv")]
        _write_docx(output, rows, captions, toc_rows=rows[:-1])
        _rebind_qa(project_dir, output)

        report = readiness.assess(project_dir)

    toc_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_toc_parity"
    )
    assert toc_check["status"] == "FAIL"


def test_toc_parity_ignores_paragraph_tab_stops_when_extracting_title() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "structure-parity.csv")
        captions = [row["target_caption"] for row in readiness._rows(project_dir / "asset-parity.csv")]
        _write_docx(output, rows, captions)
        document = Document(output)
        p_pr = document.paragraphs[0]._p.get_or_add_pPr()
        tabs = OxmlElement("w:tabs")
        tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), "right")
        tab.set(qn("w:pos"), "9000")
        tabs.append(tab)
        p_pr.append(tabs)
        document.save(output)
        _rebind_qa(project_dir, output)

        report = readiness.assess(project_dir)

    toc_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_toc_parity"
    )
    assert toc_check["status"] == "PASS"


def test_toc_parity_accepts_a_word_auto_number_prefix() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "structure-parity.csv")
        captions = [row["target_caption"] for row in readiness._rows(project_dir / "asset-parity.csv")]
        _write_docx(output, rows, captions)
        document = Document(output)
        document.paragraphs[0].text = "2.1. Project overview\t1"
        document.save(output)
        _rebind_qa(project_dir, output)

        report = readiness.assess(project_dir)

    toc_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_toc_parity"
    )
    assert toc_check["status"] == "PASS"


def test_toc_parity_accepts_word_auto_number_prefix_without_terminal_dot() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "structure-parity.csv")
        captions = [row["target_caption"] for row in readiness._rows(project_dir / "asset-parity.csv")]
        _write_docx(output, rows, captions)
        document = Document(output)
        document.paragraphs[0].text = "2.1 Project overview\t1"
        document.save(output)
        _rebind_qa(project_dir, output)

        report = readiness.assess(project_dir)

    toc_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_toc_parity"
    )
    assert toc_check["status"] == "PASS"


def test_structure_parity_requires_explicit_toc_inclusion_decision() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "structure-parity.csv")
        rows[0]["include_in_toc"] = ""
        _write_csv(project_dir / "structure-parity.csv", STRUCTURE_PARITY_FIELDS, rows)

        report = readiness.assess(project_dir)

    structure_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_structure_inventory"
    )
    assert structure_check["status"] == "INCOMPLETE"


def test_structure_inventory_rejects_reordered_headings_in_the_actual_docx() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "structure-parity.csv")
        rows[0], rows[1] = rows[1], rows[0]
        _write_docx(output, rows, [row["target_caption"] for row in readiness._rows(project_dir / "asset-parity.csv")])

        report = readiness.assess(project_dir)

    outline_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_structure_in_docx"
    )
    assert outline_check["status"] == "FAIL"


def test_structure_parity_needs_existing_evidence_for_each_mapped_heading() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "structure-parity.csv")
        rows[0]["evidence_files"] = "missing-evidence.md"
        _write_csv(project_dir / "structure-parity.csv", STRUCTURE_PARITY_FIELDS, rows)

        report = readiness.assess(project_dir)

    parity = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_structure_inventory"
    )
    assert parity["status"] == "INCOMPLETE"


def test_visual_inventory_is_project_specific_and_checks_document_captions() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "asset-parity.csv")
        _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, rows[:1])
        structure = readiness._rows(project_dir / "structure-parity.csv")
        _write_docx(output, structure, [rows[0]["target_caption"]])
        _rebind_qa(project_dir, output)

        report = readiness.assess(project_dir)

    parity = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_visual_inventory"
    )
    assert parity["status"] == "PASS"
    assert "1 required captions for the 1 planned visual assets" in parity["detail"]
    assert report["gates"]["submission_readiness"]["status"] == "PASS"


def test_asset_parity_rejects_dropped_visual_slots() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "asset-parity.csv")
        rows[0]["decision"] = "NOT_APPLICABLE"
        _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, rows)

        report = readiness.assess(project_dir)

    parity = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_visual_inventory"
    )
    assert parity["status"] == "FAIL"


def test_visual_inventory_needs_evidence_for_each_planned_artifact() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "asset-parity.csv")
        rows[0]["evidence_files"] = "missing-image-source.png"
        _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, rows)

        report = readiness.assess(project_dir)

    parity = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_visual_inventory"
    )
    assert parity["status"] == "INCOMPLETE"


def test_visual_inventory_requires_each_planned_caption_in_the_docx() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        structure = readiness._rows(project_dir / "structure-parity.csv")
        _write_docx(output, structure, ["Figure 1. Project architecture"])

        report = readiness.assess(project_dir)

    parity = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_visual_inventory"
    )
    assert parity["status"] == "FAIL"


def test_visual_inventory_matches_seq_caption_numbers_split_by_word_runs() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "asset-parity.csv")
        rows[0]["target_caption"] = "Figure 2.1. Project architecture"
        _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, rows)
        structure = readiness._rows(project_dir / "structure-parity.csv")
        _write_docx(output, structure, [row["target_caption"] for row in rows])
        document = Document(output)
        caption = next(p for p in document.paragraphs if p.style.name == "Caption")
        caption.text = "Figure 2. 1 . Project architecture"
        document.save(output)
        _rebind_qa(project_dir, output)

        report = readiness.assess(project_dir)

    visual_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_visual_inventory"
    )
    assert visual_check["status"] == "PASS"


def test_visual_inventory_rejects_caption_without_expected_embedded_media() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        structure = readiness._rows(project_dir / "structure-parity.csv")
        captions = [row["target_caption"] for row in readiness._rows(project_dir / "asset-parity.csv")]
        _write_docx(output, structure, captions, picture_count=0)
        _rebind_qa(project_dir, output)

        report = readiness.assess(project_dir)

    media_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_visual_media"
    )
    assert media_check["status"] == "FAIL"


def test_visual_inventory_binds_images_to_their_caption_not_only_total_count() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        structure = readiness._rows(project_dir / "structure-parity.csv")
        captions = [row["target_caption"] for row in readiness._rows(project_dir / "asset-parity.csv")]
        _write_docx(output, structure, captions, picture_count=0)
        document = Document(output)
        table_caption = next(
            paragraph for paragraph in document.paragraphs
            if paragraph.text == captions[1] and paragraph.style.name == "Caption"
        )
        table_caption.add_run().add_picture(io.BytesIO(_tiny_png()), width=Inches(0.1))
        document.save(output)
        _rebind_qa(project_dir, output)

        report = readiness.assess(project_dir)

    media_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_visual_media"
    )
    assert media_check["status"] == "FAIL"
    assert "caption-bound mismatches" in media_check["detail"]


def test_visual_inventory_accounts_for_uncaptioned_cover_logos_separately() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "asset-parity.csv")
        logos = [
            {
                "asset_id": f"LOGO-{index}", "asset_type": "DECORATIVE_IMAGE",
                "source_basis": "cover metadata", "source_location": f"cover, logo {index}",
                "target_section": "Cover", "target_caption": "", "decision": "MATCHED",
                "coverage_note": "Uncaptioned institutional mark preserved from the source cover.",
                "evidence_files": "source.txt", "expected_media_count": "1",
                "caption_required": "false", "status": "PASS", "reviewed_by": "Reviewer",
                "review_date": "2026-10-20",
            }
            for index in (1, 2)
        ]
        rows = logos + rows
        _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, rows)
        structure = readiness._rows(project_dir / "structure-parity.csv")
        captions = [row["target_caption"] for row in rows if row["target_caption"]]
        _write_docx(output, structure, captions, picture_count=3)
        _rebind_qa(project_dir, output)

        report = readiness.assess(project_dir)

    media_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_visual_media"
    )
    assert media_check["status"] == "PASS"
    assert "3 embedded images" in media_check["detail"]


def test_runtime_capture_provenance_rejects_direct_route_screenshot() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "asset-parity.csv")
        rows[0]["asset_type"] = "RUNTIME_SCREENSHOT"
        rows[0]["capture_id"] = "home"
        rows[0]["runtime_route"] = "/"
        _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, rows)

        capture_dir = project_dir / "runtime-captures"
        capture_dir.mkdir()
        screenshot = capture_dir / "home.png"
        screenshot.write_bytes(_tiny_png())
        screenshot_digest = hashlib.sha256(screenshot.read_bytes()).hexdigest()
        manifest = {
            "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
            "capture_context": {
                "browser_surface": "visible_browser_tab",
                "headless": False,
                "navigation_policy": "visible_ui_clickthrough",
            },
            "captures": [{
                "capture_id": "home", "route": "/",
                "resolved_url": "https://example.test/",
                "http_status": 200, "page_title": "Home",
                "network": {"document_status": 200},
                "console": {"errors": [], "warnings": []},
                "captured_at_local": "2026-10-20T12:00:00+07:00",
                "screenshot_path": "runtime-captures/home.png",
                "screenshot_sha256": screenshot_digest,
                "page_state_review": {
                    "status": "PASS",
                    "summary": "Home page rendered; no visible error state.",
                    "reviewed_by": "Reviewer",
                    "reviewed_at": "2026-10-20",
                    "screenshot_path": "runtime-captures/home.png",
                    "screenshot_sha256": screenshot_digest,
                },
                "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
                "capture_method": "Chrome screenshot",
                "arrival": {
                    "from": "Direct URL load",
                    "local_file_open_for_this_capture": False,
                    "direct_route_load_for_this_capture": True,
                    "ui_steps": ["Opened / directly"],
                },
                "external_side_effect": False,
            }],
        }
        (capture_dir / "capture-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        project["runtime_capture_manifest_file"] = "runtime-captures/capture-manifest.json"
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    provenance = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_runtime_capture_provenance"
    )
    assert provenance["status"] == "FAIL"
    assert "direct-route" in provenance["detail"]


def test_runtime_capture_provenance_accepts_hash_bound_ui_clickthrough() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "asset-parity.csv")
        rows[0]["asset_type"] = "RUNTIME_SCREENSHOT"
        rows[0]["capture_id"] = "home"
        rows[0]["runtime_route"] = "/"
        _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, rows)

        capture_dir = project_dir / "runtime-captures"
        capture_dir.mkdir()
        screenshot = capture_dir / "home.png"
        screenshot.write_bytes(_tiny_png())
        screenshot_digest = hashlib.sha256(screenshot.read_bytes()).hexdigest()
        manifest = {
            "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
            "capture_context": {
                "browser_surface": "visible_browser_tab",
                "headless": False,
                "navigation_policy": "visible_ui_clickthrough",
            },
            "captures": [{
                "capture_id": "home", "route": "/",
                "resolved_url": "https://example.test/",
                "http_status": 200, "page_title": "Home",
                "network": {"document_status": 200},
                "console": {"errors": [], "warnings": []},
                "captured_at_local": "2026-10-20T12:00:00+07:00",
                "screenshot_path": "runtime-captures/home.png",
                "screenshot_sha256": screenshot_digest,
                "page_state_review": {
                    "status": "PASS",
                    "summary": "Home page rendered; no visible error state.",
                    "reviewed_by": "Reviewer",
                    "reviewed_at": "2026-10-20",
                    "screenshot_path": "runtime-captures/home.png",
                    "screenshot_sha256": screenshot_digest,
                },
                "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
                "capture_method": "Chrome screenshot after visible UI interaction",
                "arrival": {
                    "from": "Homepage navigation",
                    "local_file_open_for_this_capture": False,
                    "direct_route_load_for_this_capture": False,
                    "ui_steps": ["Open the home page", "Click visible Hỏi đáp link"],
                },
                "external_side_effect": False,
            }],
        }
        (capture_dir / "capture-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        project["runtime_capture_manifest_file"] = "runtime-captures/capture-manifest.json"
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    provenance = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_runtime_capture_provenance"
    )
    assert provenance["status"] == "PASS"


def test_runtime_capture_provenance_rejects_unreported_http_or_console_error() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "asset-parity.csv")
        rows[0]["asset_type"] = "RUNTIME_SCREENSHOT"
        rows[0]["capture_id"] = "home"
        rows[0]["runtime_route"] = "/"
        _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, rows)

        capture_dir = project_dir / "runtime-captures"
        capture_dir.mkdir()
        screenshot = capture_dir / "home.png"
        screenshot.write_bytes(_tiny_png())
        screenshot_digest = hashlib.sha256(screenshot.read_bytes()).hexdigest()
        manifest = {
            "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
            "capture_context": {
                "browser_surface": "visible_browser_tab",
                "headless": False,
                "navigation_policy": "visible_ui_clickthrough",
            },
            "captures": [{
                "capture_id": "home", "route": "/",
                "resolved_url": "https://example.test/",
                "http_status": 500, "page_title": "Internal Server Error",
                "network": {"document_status": 500},
                "console": {"errors": ["Uncaught application error"], "warnings": []},
                "captured_at_local": "2026-10-20T12:00:00+07:00",
                "screenshot_path": "runtime-captures/home.png",
                "screenshot_sha256": screenshot_digest,
                "page_state_review": {
                    "status": "PASS",
                    "summary": "Home page rendered; no visible error state.",
                    "reviewed_by": "Reviewer",
                    "reviewed_at": "2026-10-20",
                    "screenshot_path": "runtime-captures/home.png",
                    "screenshot_sha256": screenshot_digest,
                },
                "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
                "capture_method": "Chrome screenshot after visible UI interaction",
                "arrival": {
                    "from": "Homepage navigation",
                    "local_file_open_for_this_capture": False,
                    "direct_route_load_for_this_capture": False,
                    "ui_steps": ["Open the home page", "Click visible Hỏi đáp link"],
                },
                "external_side_effect": False,
            }],
        }
        (capture_dir / "capture-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        project["runtime_capture_manifest_file"] = "runtime-captures/capture-manifest.json"
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    provenance = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_runtime_capture_provenance"
    )
    assert provenance["status"] == "FAIL"
    assert "observed HTTP/document status 500/500 and 1 console error(s)" in provenance["detail"]


def test_runtime_capture_provenance_records_page_error_screenshot_and_fails_gate() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "asset-parity.csv")
        rows[0]["asset_type"] = "RUNTIME_SCREENSHOT"
        rows[0]["capture_id"] = "home"
        rows[0]["runtime_route"] = "/"
        _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, rows)

        capture_dir = project_dir / "runtime-captures"
        capture_dir.mkdir()
        screenshot = capture_dir / "home-error.png"
        screenshot.write_bytes(_tiny_png())
        screenshot_digest = hashlib.sha256(screenshot.read_bytes()).hexdigest()
        manifest = {
            "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
            "capture_context": {
                "browser_surface": "visible_browser_tab",
                "headless": False,
                "navigation_policy": "visible_ui_clickthrough",
            },
            "captures": [{
                "capture_id": "home", "route": "/",
                "resolved_url": "https://example.test/",
                "http_status": 503, "page_title": "Service Unavailable",
                "network": {"document_status": 503},
                "console": {"errors": [], "warnings": []},
                "captured_at_local": "2026-10-20T12:00:00+07:00",
                "screenshot_path": "runtime-captures/home-error.png",
                "screenshot_sha256": screenshot_digest,
                "page_state_review": {
                    "status": "FAIL",
                    "summary": "HTTP 503 error screen is visible after click-through.",
                    "reviewed_by": "Reviewer",
                    "reviewed_at": "2026-10-20",
                    "screenshot_path": "runtime-captures/home-error.png",
                    "screenshot_sha256": screenshot_digest,
                },
                "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
                "capture_method": "Chrome screenshot after visible UI interaction",
                "arrival": {
                    "from": "Homepage navigation",
                    "local_file_open_for_this_capture": False,
                    "direct_route_load_for_this_capture": False,
                    "ui_steps": ["Open the home page", "Click visible Hỏi đáp link"],
                },
                "external_side_effect": False,
            }],
        }
        (capture_dir / "capture-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        project["runtime_capture_manifest_file"] = "runtime-captures/capture-manifest.json"
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    provenance = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_runtime_capture_provenance"
    )
    assert provenance["status"] == "FAIL"
    assert "captured page/error state was reviewed as failed" in provenance["detail"]


def test_runtime_capture_provenance_rejects_error_from_unplanned_attempt() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "asset-parity.csv")
        rows[0]["asset_type"] = "RUNTIME_SCREENSHOT"
        rows[0]["capture_id"] = "home"
        rows[0]["runtime_route"] = "/"
        _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, rows)

        capture_dir = project_dir / "runtime-captures"
        capture_dir.mkdir()
        captures = []
        for capture_id, status in (("home", 200), ("supplemental-error", 503)):
            image_name = f"{capture_id}.png"
            screenshot = capture_dir / image_name
            screenshot.write_bytes(_tiny_png())
            screenshot_digest = hashlib.sha256(screenshot.read_bytes()).hexdigest()
            is_error = status >= 400
            relative_image = f"runtime-captures/{image_name}"
            captures.append({
                "capture_id": capture_id,
                "route": "/" if capture_id == "home" else "/supplemental",
                "resolved_url": "https://example.test/" if capture_id == "home" else "https://example.test/supplemental",
                "http_status": status,
                "page_title": "Home" if not is_error else "Service Unavailable",
                "network": {"document_status": status},
                "console": {"errors": [], "warnings": []},
                "captured_at_local": "2026-10-20T12:00:00+07:00",
                "screenshot_path": relative_image,
                "screenshot_sha256": screenshot_digest,
                "page_state_review": {
                    "status": "FAIL" if is_error else "PASS",
                    "summary": "HTTP 503 error page was captured." if is_error else "Home page rendered without errors.",
                    "reviewed_by": "Reviewer",
                    "reviewed_at": "2026-10-20",
                    "screenshot_path": relative_image,
                    "screenshot_sha256": screenshot_digest,
                },
                "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
                "capture_method": "Chrome screenshot after visible UI interaction",
                "arrival": {
                    "from": "Homepage navigation",
                    "local_file_open_for_this_capture": False,
                    "direct_route_load_for_this_capture": False,
                    "ui_steps": ["Open the home page", "Click visible link"],
                },
                "external_side_effect": False,
            })
        manifest = {
            "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
            "capture_context": {
                "browser_surface": "visible_browser_tab",
                "headless": False,
                "navigation_policy": "visible_ui_clickthrough",
            },
            "captures": captures,
        }
        (capture_dir / "capture-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        project["runtime_capture_manifest_file"] = "runtime-captures/capture-manifest.json"
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    provenance = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_runtime_capture_provenance"
    )
    assert provenance["status"] == "FAIL"
    assert "unplanned capture supplemental-error" in provenance["detail"]
    assert "supplemental-error.png" in provenance["detail"] or "failed page/error state" in provenance["detail"]


def test_runtime_capture_provenance_requires_page_error_observability() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "asset-parity.csv")
        rows[0]["asset_type"] = "RUNTIME_SCREENSHOT"
        rows[0]["capture_id"] = "home"
        rows[0]["runtime_route"] = "/"
        _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, rows)

        capture_dir = project_dir / "runtime-captures"
        capture_dir.mkdir()
        screenshot = capture_dir / "home.png"
        screenshot.write_bytes(_tiny_png())
        manifest = {
            "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
            "capture_context": {
                "browser_surface": "visible_browser_tab",
                "headless": False,
                "navigation_policy": "visible_ui_clickthrough",
            },
            "captures": [{
                "capture_id": "home", "route": "/",
                "resolved_url": "https://example.test/",
                "screenshot_path": "runtime-captures/home.png",
                "screenshot_sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
                "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
                "capture_method": "Chrome screenshot after visible UI interaction",
                "arrival": {
                    "from": "Homepage navigation",
                    "local_file_open_for_this_capture": False,
                    "direct_route_load_for_this_capture": False,
                    "ui_steps": ["Open home", "Click visible link"],
                },
                "external_side_effect": False,
            }],
        }
        (capture_dir / "capture-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        project["runtime_capture_manifest_file"] = "runtime-captures/capture-manifest.json"
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    provenance = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_runtime_capture_provenance"
    )
    assert provenance["status"] == "INCOMPLETE"
    assert "HTTP response status" in provenance["detail"]


def test_runtime_capture_provenance_rejects_local_file_ui_capture() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "asset-parity.csv")
        rows[0]["asset_type"] = "RUNTIME_SCREENSHOT"
        rows[0]["capture_id"] = "home"
        rows[0]["runtime_route"] = "/"
        _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, rows)

        capture_dir = project_dir / "runtime-captures"
        capture_dir.mkdir()
        screenshot = capture_dir / "home.png"
        screenshot.write_bytes(_tiny_png())
        manifest = {
            "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
            "capture_context": {
                "browser_surface": "visible_browser_tab",
                "headless": False,
                "navigation_policy": "visible_ui_clickthrough",
            },
            "captures": [{
                "capture_id": "home", "route": "/",
                "resolved_url": "file:///tmp/app/index.html",
                "screenshot_path": "runtime-captures/home.png",
                "screenshot_sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
                "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
                "capture_method": "Visible browser screenshot after UI interaction",
                "arrival": {
                    "from": "Opened local UI file",
                    "local_file_open_for_this_capture": True,
                    "direct_route_load_for_this_capture": False,
                    "ui_steps": ["Opened local interface file"],
                },
                "external_side_effect": False,
            }],
        }
        (capture_dir / "capture-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        project["runtime_capture_manifest_file"] = "runtime-captures/capture-manifest.json"
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    provenance = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_runtime_capture_provenance"
    )
    assert provenance["status"] == "FAIL"
    assert "local UI/file" in provenance["detail"]


def test_runtime_capture_provenance_rejects_headless_context() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "asset-parity.csv")
        rows[0]["asset_type"] = "RUNTIME_SCREENSHOT"
        rows[0]["capture_id"] = "home"
        rows[0]["runtime_route"] = "/"
        _write_csv(project_dir / "asset-parity.csv", ASSET_PARITY_FIELDS, rows)

        capture_dir = project_dir / "runtime-captures"
        capture_dir.mkdir()
        screenshot = capture_dir / "home.png"
        screenshot.write_bytes(_tiny_png())
        manifest = {
            "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
            "capture_context": {
                "browser_surface": "visible_browser_tab",
                "headless": True,
                "navigation_policy": "visible_ui_clickthrough",
            },
            "captures": [{
                "capture_id": "home", "route": "/",
                "resolved_url": "https://example.test/",
                "screenshot_path": "runtime-captures/home.png",
                "screenshot_sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
                "acceptance_status": "ACCEPTED_UI_CLICKTHROUGH_CAPTURE",
                "capture_method": "Headless browser screenshot after UI interaction",
                "arrival": {
                    "from": "Homepage navigation",
                    "local_file_open_for_this_capture": False,
                    "direct_route_load_for_this_capture": False,
                    "ui_steps": ["Open home", "Click visible link"],
                },
                "external_side_effect": False,
            }],
        }
        (capture_dir / "capture-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        project["runtime_capture_manifest_file"] = "runtime-captures/capture-manifest.json"
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    provenance = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "project_runtime_capture_provenance"
    )
    assert provenance["status"] == "FAIL"
    assert "visible browser tab" in provenance["detail"] or "Headless" in provenance["detail"]


def test_visual_media_binding_ignores_table_of_figures_entries() -> None:
    document = Document()
    captions = ["Figure 1. First diagram", "Figure 2. Second diagram"]
    for caption in captions:
        document.add_paragraph(caption)
    for caption in captions:
        image_paragraph = document.add_paragraph()
        image_paragraph.add_run().add_picture(io.BytesIO(_tiny_png()), width=Inches(0.1))
        document.add_paragraph(caption, style="Caption")

    rows = [
        {
            "asset_id": f"FIG-{index}", "target_caption": caption,
            "caption_required": "true", "expected_media_count": "1",
        }
        for index, caption in enumerate(captions, start=1)
    ]

    total_media, media_by_caption, missing = readiness._embedded_media_counts_by_caption(document, rows)

    assert total_media == 2
    assert media_by_caption == [1, 1]
    assert missing == []


def test_visual_media_binding_places_uncaptioned_asset_by_exact_anchor() -> None:
    document = Document()
    document.add_paragraph().add_run().add_picture(io.BytesIO(_tiny_png()), width=Inches(0.1))
    document.add_paragraph().add_run().add_picture(io.BytesIO(_tiny_png()), width=Inches(0.1))
    document.add_paragraph("Figure 1. Overview", style="Caption")
    document.add_paragraph("Detail A – supporting diagram")
    document.add_paragraph().add_run().add_picture(io.BytesIO(_tiny_png()), width=Inches(0.1))
    document.add_paragraph().add_run().add_picture(io.BytesIO(_tiny_png()), width=Inches(0.1))
    document.add_paragraph("Figure 2. Next", style="Caption")
    rows = [
        {"asset_id": "LOGO", "caption_required": "false", "expected_media_count": "1"},
        {"asset_id": "F1", "caption_required": "true", "target_caption": "Figure 1. Overview", "expected_media_count": "1"},
        {"asset_id": "F2", "caption_required": "true", "target_caption": "Figure 2. Next", "expected_media_count": "1"},
        {"asset_id": "DETAIL", "caption_required": "false", "uncaptioned_anchor": "Detail A – supporting diagram", "expected_media_count": "1"},
    ]
    total, counts, missing = readiness._embedded_media_counts_by_caption(document, rows)
    assert (total, counts, missing) == (4, [1, 1], [])


def test_visual_media_binding_rejects_ambiguous_uncaptioned_anchor() -> None:
    document = Document()
    for _ in range(2):
        document.add_paragraph("Detail A")
        document.add_paragraph().add_run().add_picture(io.BytesIO(_tiny_png()), width=Inches(0.1))
    rows = [{"asset_id": "DETAIL", "caption_required": "false", "uncaptioned_anchor": "Detail A", "expected_media_count": "1"}]
    _total, _counts, missing = readiness._embedded_media_counts_by_caption(document, rows)
    assert "DETAIL" in missing


def test_visual_media_binding_rejects_missing_or_reused_anchor() -> None:
    document = Document()
    document.add_paragraph("Detail A")
    document.add_paragraph().add_run().add_picture(io.BytesIO(_tiny_png()), width=Inches(0.1))
    rows = [
        {"asset_id": "A", "caption_required": "false", "uncaptioned_anchor": "Detail A", "expected_media_count": "1"},
        {"asset_id": "DUPLICATE", "caption_required": "false", "uncaptioned_anchor": "Detail A", "expected_media_count": "1"},
        {"asset_id": "MISSING", "caption_required": "false", "uncaptioned_anchor": "Detail B", "expected_media_count": "1"},
    ]
    _total, _counts, missing = readiness._embedded_media_counts_by_caption(document, rows)
    assert missing == ["DUPLICATE", "MISSING"]


def test_acceptance_crosswalk_requires_every_category() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "acceptance-crosswalk.csv")
        rows = [row for row in rows if row["category"] != "abstract"]
        _write_csv(project_dir / "acceptance-crosswalk.csv", ACCEPTANCE_CROSSWALK_FIELDS, rows)

        report = readiness.assess(project_dir)

    crosswalk_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "acceptance_crosswalk"
    )
    assert crosswalk_check["status"] == "INCOMPLETE"
    assert "abstract" in crosswalk_check["detail"]


def test_acceptance_crosswalk_rejects_stale_document_hash() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "acceptance-crosswalk.csv")
        rows[0]["document_sha256"] = "0" * 64
        _write_csv(project_dir / "acceptance-crosswalk.csv", ACCEPTANCE_CROSSWALK_FIELDS, rows)

        report = readiness.assess(project_dir)

    crosswalk_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "acceptance_crosswalk"
    )
    assert crosswalk_check["status"] == "FAIL"


def test_acceptance_crosswalk_requires_existing_review_evidence() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "acceptance-crosswalk.csv")
        rows[0]["evidence_files"] = "qa/missing-review.md"
        _write_csv(project_dir / "acceptance-crosswalk.csv", ACCEPTANCE_CROSSWALK_FIELDS, rows)

        report = readiness.assess(project_dir)

    crosswalk_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "acceptance_crosswalk"
    )
    assert crosswalk_check["status"] == "INCOMPLETE"


def test_acceptance_crosswalk_rejects_changed_review_evidence() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, source = _case(Path(temp))
        source.write_text("Evidence changed after review", encoding="utf-8")

        report = readiness.assess(project_dir)

    crosswalk_check = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "acceptance_crosswalk"
    )
    assert crosswalk_check["status"] == "FAIL"
    assert "stale-evidence-hash" in crosswalk_check["detail"]


def test_cover_metadata_cannot_use_the_reference_sample_as_authority() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "cover-metadata.csv")
        supervisor = next(row for row in rows if row["field"] == "supervisor_name")
        supervisor.update({
            "value": "Sample Supervisor", "authority": "StrongWine sample",
            "authority_type": "REFERENCE_SAMPLE", "status": "VERIFIED",
        })
        _write_csv(project_dir / "cover-metadata.csv", COVER_METADATA_FIELDS, rows)

        report = readiness.assess(project_dir)

    metadata = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "cover_metadata"
    )
    assert metadata["status"] == "FAIL"
    assert report["gates"]["submission_readiness"]["status"] == "FAIL"


def test_cover_metadata_requires_every_identity_field_to_be_resolved() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "cover-metadata.csv")
        rows = [row for row in rows if row["field"] != "supervisor_name"]
        _write_csv(project_dir / "cover-metadata.csv", COVER_METADATA_FIELDS, rows)

        report = readiness.assess(project_dir)

    metadata = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "cover_metadata"
    )
    assert metadata["status"] == "INCOMPLETE"


def test_word_delivery_pass_with_missing_rubric_is_not_ready() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        project["rubric_file"] = ""
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    assert report["gates"]["word_delivery"]["status"] == "PASS"
    assert report["gates"]["content_and_sources"]["status"] == "INCOMPLETE"
    assert report["gates"]["submission_readiness"]["status"] == "INCOMPLETE"


def test_rubric_absence_cannot_be_waived_into_submission_readiness() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        project["rubric_file"] = ""
        project["rubric_waiver"] = {"authorized_by": "Instructor", "reason": "No rubric supplied"}
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    assert report["gates"]["word_delivery"]["status"] == "PASS"
    assert report["gates"]["content_and_sources"]["status"] == "INCOMPLETE"
    assert report["gates"]["submission_readiness"]["status"] == "INCOMPLETE"


def test_official_rubric_appendix_is_optional_unless_requested() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        project["include_official_rubric_in_docx"] = False
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    inclusion = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "official_rubric_in_docx"
    )
    assert inclusion["status"] == "PASS"
    assert "not requested" in inclusion["detail"]


def test_official_rubric_appendix_missing_source_stays_incomplete() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        project["rubric_file"] = ""
        project["include_official_rubric_in_docx"] = True
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    inclusion = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "official_rubric_in_docx"
    )
    assert inclusion["status"] == "INCOMPLETE"
    assert "official rubric source is missing" in inclusion["detail"]


def test_official_rubric_appendix_passes_when_complete_source_is_hash_bound() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, output, _source = _case(Path(temp))
        _add_official_rubric_appendix(project_dir, project, output)

        report = readiness.assess(project_dir)

    inclusion = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "official_rubric_in_docx"
    )
    assert inclusion["status"] == "PASS"
    assert "exactly matches" in inclusion["detail"]


def test_profile_assessment_sections_in_image_bearing_guide_pass_when_exact_and_hash_bound() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, output, _source = _case(Path(temp))
        _add_profile_section_criteria(project_dir, project, output)

        report = readiness.assess(project_dir)

    inclusion = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "official_rubric_in_docx"
    )
    assert inclusion["status"] == "PASS"
    assert "complete official criteria section exactly matches" in inclusion["detail"].casefold()


def test_profile_assessment_section_rejects_an_omitted_official_criterion() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, output, _source = _case(Path(temp))
        _add_profile_section_criteria(
            project_dir,
            project,
            output,
            omit_criterion="Theoretical basis.",
        )

        report = readiness.assess(project_dir)

    inclusion = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "official_rubric_in_docx"
    )
    assert inclusion["status"] == "FAIL"
    assert "do not exactly match" in inclusion["detail"]


def test_profile_assessment_section_with_embedded_image_stays_incomplete() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, output, _source = _case(Path(temp))
        _add_profile_section_criteria(
            project_dir,
            project,
            output,
            image_inside_source_section=True,
        )

        report = readiness.assess(project_dir)

    inclusion = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "official_rubric_in_docx"
    )
    assert inclusion["status"] == "INCOMPLETE"
    assert "selected source section contains embedded images" in inclusion["detail"]


def test_official_rubric_appendix_rejects_omitted_criterion() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, output, _source = _case(Path(temp))
        _add_official_rubric_appendix(
            project_dir, project, output, include_all_criteria=False
        )

        report = readiness.assess(project_dir)

    inclusion = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "official_rubric_in_docx"
    )
    assert inclusion["status"] == "FAIL"
    assert "exact full-text match" in inclusion["detail"]


def test_official_rubric_appendix_rejects_extra_or_altered_text() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, output, _source = _case(Path(temp))
        _add_official_rubric_appendix(project_dir, project, output)
        target = Document(output)
        target.add_paragraph("Unrelated text after the rubric")
        target.save(output)
        project["rubric_inclusion"]["output_docx_sha256"] = hashlib.sha256(
            output.read_bytes()
        ).hexdigest()
        _rebind_qa(project_dir, output)
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    inclusion = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "official_rubric_in_docx"
    )
    assert inclusion["status"] == "FAIL"
    assert "exact full-text match" in inclusion["detail"]


def test_official_rubric_appendix_rejects_stale_source_hash() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, output, _source = _case(Path(temp))
        source_path = _add_official_rubric_appendix(project_dir, project, output)
        source_path.write_bytes(source_path.read_bytes() + b"changed after review")
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    inclusion = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "official_rubric_in_docx"
    )
    assert inclusion["status"] == "FAIL"
    assert "source SHA-256" in inclusion["detail"]


def test_official_rubric_appendix_rejects_stale_output_hash() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, output, _source = _case(Path(temp))
        _add_official_rubric_appendix(project_dir, project, output)
        output.write_bytes(output.read_bytes() + b"changed after review")
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    inclusion = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "official_rubric_in_docx"
    )
    assert inclusion["status"] == "FAIL"
    assert "current output DOCX SHA-256" in inclusion["detail"]


def test_official_rubric_appendix_rejects_unsupported_source_format() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, output, _source = _case(Path(temp))
        _add_official_rubric_appendix(project_dir, project, output)
        project["rubric_file"] = "rubric.md"
        project["rubric_inclusion"]["source_sha256"] = hashlib.sha256(
            (project_dir / "rubric.md").read_bytes()
        ).hexdigest()
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    inclusion = next(
        item for item in report["gates"]["content_and_sources"]["checks"]
        if item["check"] == "official_rubric_in_docx"
    )
    assert inclusion["status"] == "INCOMPLETE"
    assert "supported official rubric sources" in inclusion["detail"]


def test_official_rubric_pdf_extracts_all_pages_and_closes_pdf_objects(
    monkeypatch, tmp_path: Path
) -> None:
    source_path = tmp_path / "official-rubric.pdf"
    source_path.write_bytes(b"PDF test fixture")
    lifecycle: list[str] = []

    class FakeTextPage:
        def __init__(self, text: str):
            self.text = text

        def get_text_bounded(self) -> str:
            return self.text

        def close(self) -> None:
            lifecycle.append("text")

    class FakePage:
        def __init__(self, text: str):
            self.text = text

        def get_textpage(self) -> FakeTextPage:
            return FakeTextPage(self.text)

        def close(self) -> None:
            lifecycle.append("page")

    class FakePdf:
        def __init__(self, _path: Path):
            self.pages = [FakePage("Criterion one 40%"), FakePage("Criterion two 60%")]

        def __enter__(self):
            return self

        def __exit__(self, *_exc) -> None:
            lifecycle.append("pdf")

        def __len__(self) -> int:
            return len(self.pages)

        def __iter__(self):
            return iter(self.pages)

    monkeypatch.setitem(
        sys.modules,
        "pypdfium2",
        types.SimpleNamespace(PdfDocument=FakePdf),
    )

    extracted = readiness._rubric_source_text(source_path)

    assert extracted == "Criterion one 40% Criterion two 60%"
    assert lifecycle == ["text", "page", "text", "page", "pdf"]


def test_official_rubric_pdf_with_unreadable_page_is_rejected(
    monkeypatch, tmp_path: Path
) -> None:
    source_path = tmp_path / "scanned-rubric.pdf"
    source_path.write_bytes(b"PDF test fixture")

    class FakeTextPage:
        def get_text_bounded(self) -> str:
            return "   "

        def close(self) -> None:
            pass

    class FakePage:
        def get_textpage(self) -> FakeTextPage:
            return FakeTextPage()

        def close(self) -> None:
            pass

    class FakePdf:
        def __init__(self, _path: Path):
            self.pages = [FakePage()]

        def __enter__(self):
            return self

        def __exit__(self, *_exc) -> None:
            pass

        def __len__(self) -> int:
            return len(self.pages)

        def __iter__(self):
            return iter(self.pages)

    monkeypatch.setitem(
        sys.modules,
        "pypdfium2",
        types.SimpleNamespace(PdfDocument=FakePdf),
    )

    try:
        readiness._rubric_source_text(source_path)
    except ValueError as exc:
        assert "page with no extractable text" in str(exc)
    else:
        raise AssertionError("a scanned/unreadable rubric page must not pass")


def test_course_essay_starter_requests_official_rubric_by_default() -> None:
    starter = Path(__file__).parents[1] / "templates" / "course-essay-starter" / "project.json"

    project = json.loads(starter.read_text(encoding="utf-8"))

    assert project["include_official_rubric_in_docx"] is True
    assert project["rubric_file"] == ""
    assert project["rubric_inclusion"] is None


def test_all_core_human_acceptance_checks_are_required_even_if_config_is_shortened() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        project["required_acceptance_checks"] = ["assignment_and_rubric_checked"]
        project["acceptance_checks"] = {"assignment_and_rubric_checked": True}
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    assert report["gates"]["content_and_sources"]["status"] == "INCOMPLETE"
    assert report["gates"]["submission_readiness"]["status"] == "INCOMPLETE"


def test_unreviewed_claim_evidence_blocks_content_readiness() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        rows = readiness._rows(project_dir / "claim-evidence.csv")
        rows[0]["review_status"] = "candidate"
        _write_csv(project_dir / "claim-evidence.csv", CLAIM_FIELDS, rows)

        report = readiness.assess(project_dir)

    assert report["gates"]["word_delivery"]["status"] == "PASS"
    assert report["gates"]["content_and_sources"]["status"] == "INCOMPLETE"
    assert report["gates"]["submission_readiness"]["status"] == "INCOMPLETE"


def test_integrity_warnings_need_one_complete_disposition_each() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        audit_path = project_dir / "qa" / "integrity-audit.json"
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        audit["status"] = "WARN"
        audit["gates"]["style_review"] = {
            "status": "WARN", "finding_count": 1, "findings": [{"kind": "repeated_phrase"}],
        }
        audit_path.write_text(json.dumps(audit), encoding="utf-8")

        incomplete = readiness.assess(project_dir)
        _write_csv(project_dir / "integrity-warning-dispositions.csv", DISPOSITION_FIELDS, [{
            "gate": "style_review", "finding_index": "1", "decision": "not_applicable",
            "reason": "Reviewed as a section title repeated in the contents page.",
            "evidence": "qa/integrity-audit.json:style_review:1", "reviewed_by": "Reviewer",
            "review_date": "2026-10-20",
        }])
        complete = readiness.assess(project_dir)

    assert incomplete["gates"]["submission_readiness"]["status"] == "INCOMPLETE"
    assert complete["gates"]["submission_readiness"]["status"] == "PASS"


def test_changed_docx_hash_fails_delivery_and_stale_audit_binding() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        output.write_bytes(b"changed after QA")

        report = readiness.assess(project_dir)

    assert report["gates"]["word_delivery"]["status"] == "FAIL"
    assert report["gates"]["content_and_sources"]["status"] == "FAIL"
    assert report["gates"]["submission_readiness"]["status"] == "FAIL"


def test_reused_render_manifest_binds_word_delivery_to_the_docx_hash() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, output, _source = _case(Path(temp))
        verify_path = project_dir / "qa" / "word-verify.json"
        verify = json.loads(verify_path.read_text(encoding="utf-8"))
        document_digest = hashlib.sha256(output.read_bytes()).hexdigest()
        verify["render"].pop("document_sha256")
        verify["render_reuse_manifest"] = {"document_sha256": document_digest}
        verify_path.write_text(json.dumps(verify), encoding="utf-8")

        report = readiness.assess(project_dir)

    assert report["gates"]["word_delivery"]["status"] == "PASS"
    assert report["gates"]["content_and_sources"]["status"] == "PASS"


def test_selected_profile_must_have_a_passing_format_gate() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        project["institution_profile"] = "course-profile"
        _save_project(project_dir, project)

        report = readiness.assess(project_dir)

    assert report["gates"]["word_delivery"]["status"] == "INCOMPLETE"
    assert report["gates"]["submission_readiness"]["status"] == "INCOMPLETE"


def test_selected_profile_requires_matching_saved_validate_report() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        project["institution_profile"] = "course-profile"
        _save_project(project_dir, project)
        verify_path = project_dir / "qa" / "word-verify.json"
        verify = json.loads(verify_path.read_text(encoding="utf-8"))
        verify["format_status"] = "PASS"
        verify_path.write_text(json.dumps(verify), encoding="utf-8")
        (project_dir / "qa" / "profile-validation.json").write_text(json.dumps({
            "file": "output/final.docx", "profile": "course-profile", "variant": "default", "valid": True,
        }), encoding="utf-8")

        report = readiness.assess(project_dir)

    assert report["gates"]["word_delivery"]["status"] == "PASS"
    assert report["gates"]["submission_readiness"]["status"] == "PASS"


def test_vacuous_generic_source_gate_does_not_cover_claim_evidence_ids() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        audit_path = project_dir / "qa" / "integrity-audit.json"
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        audit["gates"]["source_evidence"]["linked_evidence_id_count"] = 0
        audit["gates"]["source_evidence"]["verified_record_count"] = 0
        audit_path.write_text(json.dumps(audit), encoding="utf-8")

        report = readiness.assess(project_dir)

    assert report["gates"]["word_delivery"]["status"] == "PASS"
    assert report["gates"]["content_and_sources"]["status"] == "INCOMPLETE"
    assert report["gates"]["submission_readiness"]["status"] == "INCOMPLETE"


def test_report_citation_registry_is_separate_from_project_claim_registry() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, project, _output, _source = _case(Path(temp))
        citation_registry = project_dir / "report-evidence.json"
        citation_registry.write_text(json.dumps({"[1]": "reviewed paper"}), encoding="utf-8")
        project["report_citation_registry_file"] = "report-evidence.json"
        _save_project(project_dir, project)

        audit_path = project_dir / "qa" / "integrity-audit.json"
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        audit["gates"]["source_evidence"]["linked_evidence_id_count"] = 3
        audit["gates"]["source_evidence"]["verified_record_count"] = 3
        audit["gates"]["source_evidence"]["registry"]["sha256"] = hashlib.sha256(
            citation_registry.read_bytes()
        ).hexdigest()
        audit["gates"]["numeric_citation_bibliography_consistency"] = {
            "status": "PASS",
            "finding_count": 0,
            "findings": [],
            "citation_numbers": [1, 2, 3],
            "bibliography_numbers": [1, 2, 3],
        }
        audit_path.write_text(json.dumps(audit), encoding="utf-8")

        report = readiness.assess(project_dir)

    assert report["gates"]["content_and_sources"]["status"] == "PASS"
    assert report["gates"]["submission_readiness"]["status"] == "PASS"
    checks = report["gates"]["content_and_sources"]["checks"]
    registry_check = next(item for item in checks if item["check"] == "integrity_registry_hash")
    source_check = next(item for item in checks if item["check"] == "integrity_source_evidence")
    assert registry_check["status"] == "PASS"
    assert "3 unique in-text citation numbers" in source_check["detail"]


def test_integrity_evidence_counts_must_be_integers_not_booleans() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        audit_path = project_dir / "qa" / "integrity-audit.json"
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        source_gate = audit["gates"]["source_evidence"]
        source_gate["linked_evidence_id_count"] = True
        source_gate["verified_record_count"] = True
        audit_path.write_text(json.dumps(audit), encoding="utf-8")

        report = readiness.assess(project_dir)

    assert report["gates"]["content_and_sources"]["status"] == "INCOMPLETE"


def test_integrity_warning_count_must_be_an_integer_not_boolean() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        audit_path = project_dir / "qa" / "integrity-audit.json"
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        audit["status"] = "WARN"
        audit["gates"]["style_review"] = {
            "status": "WARN", "finding_count": True, "findings": [{"kind": "review"}],
        }
        audit_path.write_text(json.dumps(audit), encoding="utf-8")
        _write_csv(project_dir / "integrity-warning-dispositions.csv", DISPOSITION_FIELDS, [{
            "gate": "style_review", "finding_index": "1", "decision": "accepted",
            "reason": "Reviewed", "evidence": "qa/integrity-audit.json:style_review:1",
            "reviewed_by": "Reviewer", "review_date": "2026-10-20",
        }])

        report = readiness.assess(project_dir)

    assert report["gates"]["content_and_sources"]["status"] == "FAIL"


def test_integrity_audit_with_unknown_gate_status_is_not_ready() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        audit_path = project_dir / "qa" / "integrity-audit.json"
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        audit["gates"]["runtime_capture"] = {"status": "NOT_RUN"}
        audit_path.write_text(json.dumps(audit), encoding="utf-8")

        report = readiness.assess(project_dir)

    assert report["gates"]["content_and_sources"]["status"] == "INCOMPLETE"
    assert report["gates"]["submission_readiness"]["status"] == "INCOMPLETE"


def test_claim_review_date_requires_exact_iso_format() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        claims = readiness._rows(project_dir / "claim-evidence.csv")
        claims[0]["review_date"] = "20261020"
        _write_csv(project_dir / "claim-evidence.csv", CLAIM_FIELDS, claims)

        report = readiness.assess(project_dir)

    assert report["gates"]["content_and_sources"]["status"] == "INCOMPLETE"


def test_duplicate_claim_ids_fail_claim_mapping() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        claims = readiness._rows(project_dir / "claim-evidence.csv")
        duplicate = dict(claims[0], evidence_id="S1")
        claims.append(duplicate)
        _write_csv(project_dir / "claim-evidence.csv", CLAIM_FIELDS, claims)

        report = readiness.assess(project_dir)

    assert report["gates"]["content_and_sources"]["status"] == "FAIL"
    assert report["gates"]["submission_readiness"]["status"] == "FAIL"


def test_claim_id_must_exist_as_the_same_id_in_reviewed_registry() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, source = _case(Path(temp))
        source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
        (project_dir / "evidence.json").write_text(json.dumps({
            "S2": {
                "id": "S2", "review_status": "reviewed", "source_sha256": source_digest,
                "support_location": "paragraph 1",
            }
        }), encoding="utf-8")
        audit_path = project_dir / "qa" / "integrity-audit.json"
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        registry_digest = hashlib.sha256((project_dir / "evidence.json").read_bytes()).hexdigest()
        audit["gates"]["source_evidence"]["registry"]["sha256"] = registry_digest
        audit_path.write_text(json.dumps(audit), encoding="utf-8")

        report = readiness.assess(project_dir)

    assert report["gates"]["word_delivery"]["status"] == "PASS"
    assert report["gates"]["content_and_sources"]["status"] == "INCOMPLETE"
    assert report["gates"]["submission_readiness"]["status"] == "INCOMPLETE"


def test_evidence_registry_change_after_audit_fails_hash_binding() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        registry_path = project_dir / "evidence.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["S2"] = dict(registry["S1"], id="S2")
        registry_path.write_text(json.dumps(registry), encoding="utf-8")

        report = readiness.assess(project_dir)

    assert report["gates"]["content_and_sources"]["status"] == "FAIL"
    assert report["gates"]["submission_readiness"]["status"] == "FAIL"


def test_requirement_pass_needs_existing_evidence_files() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        matrix = readiness._rows(project_dir / "requirements-matrix.csv")
        matrix[0]["evidence_files"] = "missing-source.txt"
        _write_csv(project_dir / "requirements-matrix.csv", MATRIX_FIELDS, matrix)

        report = readiness.assess(project_dir)

    assert report["gates"]["word_delivery"]["status"] == "PASS"
    assert report["gates"]["content_and_sources"]["status"] == "INCOMPLETE"
    assert report["gates"]["submission_readiness"]["status"] == "INCOMPLETE"


def test_duplicate_requirement_ids_fail_the_requirements_matrix() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        matrix = readiness._rows(project_dir / "requirements-matrix.csv")
        matrix.append(dict(matrix[0]))
        _write_csv(project_dir / "requirements-matrix.csv", MATRIX_FIELDS, matrix)

        report = readiness.assess(project_dir)

    assert report["gates"]["content_and_sources"]["status"] == "FAIL"
    assert report["gates"]["submission_readiness"]["status"] == "FAIL"


def test_failed_word_delivery_is_never_submission_ready() -> None:
    with tempfile.TemporaryDirectory() as temp:
        project_dir, _project, _output, _source = _case(Path(temp))
        verify_path = project_dir / "qa" / "word-verify.json"
        verify = json.loads(verify_path.read_text(encoding="utf-8"))
        verify["delivery_status"] = "FAIL"
        verify_path.write_text(json.dumps(verify), encoding="utf-8")

        report = readiness.assess(project_dir)

    assert report["gates"]["word_delivery"]["status"] == "FAIL"
    assert report["gates"]["submission_readiness"]["status"] == "FAIL"
