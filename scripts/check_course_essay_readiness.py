#!/usr/bin/env python3
"""Read-only, fail-closed readiness check for a course-essay workspace."""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit


PASS = "PASS"
INCOMPLETE = "INCOMPLETE"
FAIL = "FAIL"
_VALID_ROW_STATUSES = {PASS, "WAIVED", "NOT_RUN", "BLOCKED", FAIL}
_REQUIRED_ACCEPTANCE_CHECKS = (
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
)
_REQUIRED_ACCEPTANCE_CATEGORIES = (
    "user_requirements",
    "guide_requirements",
    "assignment_rubric_requirements",
    "heading_toc",
    "abstract",
    "screen_hierarchy",
    "runtime_screenshots",
    "diagrams",
    "visual_content",
    "argument_citations",
)
_STRUCTURE_DECISIONS = {"MATCHED", "ADAPTED"}
_COVER_METADATA_FIELDS = {
    "document_type",
    "project_title",
    "course_name",
    "institution",
    "faculty",
    "program_or_major",
    "student_name",
    "student_id",
    "class_or_cohort",
    "supervisor_name",
    "academic_year",
}
_COVER_AUTHORITY_TYPES = {"USER_INSTRUCTION", "ASSIGNMENT_OR_RUBRIC", "OFFICIAL_PROFILE", "NOT_PROVIDED"}


def _resolve(base: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def _same_document_reference(value: Any, project_dir: Path, output_path: Path | None) -> bool:
    if output_path is None or not isinstance(value, str) or not value.strip():
        return False
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve() == output_path
    return any((base / path).resolve() == output_path for base in (project_dir, Path.cwd()))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_iso_date(value: str) -> bool:
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _final_status(checks: list[dict[str, str]]) -> str:
    statuses = {item["status"] for item in checks}
    if FAIL in statuses:
        return FAIL
    if INCOMPLETE in statuses:
        return INCOMPLETE
    return PASS


def _add(checks: list[dict[str, str]], name: str, status: str, detail: str) -> None:
    checks.append({"check": name, "status": status, "detail": detail})


def _report_file(
    project_dir: Path,
    report_name: str,
    report_path: Path | None,
    checks: list[dict[str, str]],
) -> dict[str, Any] | None:
    if report_path is None:
        _add(checks, report_name, INCOMPLETE, "No report path is configured in project.json.")
        return None
    if not report_path.is_file():
        _add(checks, report_name, INCOMPLETE, f"Report file is missing: {report_path}")
        return None
    try:
        return _load_json(report_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        _add(checks, report_name, FAIL, f"Cannot read a valid JSON report: {exc}")
        return None


def _check_word_delivery(
    project_dir: Path, project: dict[str, Any]
) -> tuple[dict[str, Any], Path | None, str | None]:
    checks: list[dict[str, str]] = []
    output_path = _resolve(project_dir, project.get("output_docx"))
    document_hash: str | None = None
    if output_path is None or not output_path.is_file():
        _add(checks, "output_docx", INCOMPLETE, "The configured output DOCX is missing.")
    else:
        try:
            document_hash = _sha256(output_path)
            _add(checks, "output_docx", PASS, f"Found DOCX with SHA-256 {document_hash}.")
        except OSError as exc:
            _add(checks, "output_docx", FAIL, f"Cannot hash the output DOCX: {exc}")

    qa_reports = project.get("qa_reports")
    verify_value = qa_reports.get("word_verify") if isinstance(qa_reports, dict) else None
    verify_path = _resolve(project_dir, verify_value)
    verify = _report_file(project_dir, "word_verify_report", verify_path, checks)
    if verify is not None:
        delivery = verify.get("delivery_status")
        if delivery == PASS:
            _add(checks, "verify.delivery_status", PASS, "WordAssistant reports delivery PASS.")
        elif delivery == FAIL:
            _add(checks, "verify.delivery_status", FAIL, "WordAssistant reports delivery FAIL.")
        else:
            _add(checks, "verify.delivery_status", INCOMPLETE, f"Word delivery status is {delivery!r}.")
        overall = verify.get("overall_status")
        if delivery == PASS and overall != PASS:
            _add(checks, "verify_status_consistency", FAIL, f"delivery_status is PASS but overall_status is {overall!r}.")
        elif delivery == FAIL and overall != FAIL:
            _add(checks, "verify_status_consistency", FAIL, f"delivery_status is FAIL but overall_status is {overall!r}.")
        elif overall in {PASS, INCOMPLETE, FAIL}:
            _add(checks, "verify_status_consistency", PASS, "Verify overall and delivery statuses are consistent.")
        else:
            _add(checks, "verify_status_consistency", INCOMPLETE, "Verify report has no recognized overall_status.")

        for key in ("render_status", "visual_status"):
            status = verify.get(key)
            if status == PASS:
                _add(checks, f"verify.{key}", PASS, f"{key} passed.")
            elif status == FAIL:
                _add(checks, f"verify.{key}", FAIL, f"{key} failed.")
            else:
                _add(checks, f"verify.{key}", INCOMPLETE, f"{key} is {status!r}.")

        if project.get("institution_profile"):
            status = verify.get("format_status")
            if status == PASS:
                _add(checks, "selected_profile_validation", PASS, "Selected profile validation passed.")
            elif status == FAIL:
                _add(checks, "selected_profile_validation", FAIL, "Selected profile validation failed.")
            else:
                _add(checks, "selected_profile_validation", INCOMPLETE, "No passing validation for the selected profile was found.")
            validation_value = qa_reports.get("profile_validation") if isinstance(qa_reports, dict) else None
            validation_path = _resolve(project_dir, validation_value)
            validation = _report_file(project_dir, "profile_validation_report", validation_path, checks)
            if validation is not None:
                expected_variant = project.get("profile_variant", "default")
                if validation.get("valid") is False:
                    _add(checks, "validate.valid", FAIL, "Saved validate report reports invalid formatting.")
                elif (
                    validation.get("valid") is True
                    and validation.get("profile") == project.get("institution_profile")
                    and validation.get("variant") == expected_variant
                    and output_path is not None
                    and _same_document_reference(validation.get("file"), project_dir, output_path)
                ):
                    _add(checks, "validate.valid", PASS, "Saved validate report passed for the selected profile, variant, and DOCX.")
                else:
                    _add(checks, "validate.valid", INCOMPLETE, "Saved validate report does not match the selected profile, variant, or DOCX.")

        render = verify.get("render")
        rendered_hash = render.get("document_sha256") if isinstance(render, dict) else None
        if not rendered_hash:
            # Reused Word renders bind the DOCX hash in the reuse manifest
            # rather than duplicating it under render.
            reuse_manifest = verify.get("render_reuse_manifest")
            rendered_hash = (
                reuse_manifest.get("document_sha256")
                if isinstance(reuse_manifest, dict)
                else None
            )
        if document_hash is None:
            _add(checks, "verify_document_hash", INCOMPLETE, "Cannot bind verify evidence without the output DOCX.")
        elif not isinstance(rendered_hash, str) or not rendered_hash:
            _add(checks, "verify_document_hash", INCOMPLETE, "Verify report does not contain render.document_sha256.")
        elif rendered_hash.casefold() != document_hash.casefold():
            _add(checks, "verify_document_hash", FAIL, "Verify report refers to a different DOCX hash.")
        else:
            _add(checks, "verify_document_hash", PASS, "Verify render is bound to the current DOCX hash.")

    return {"status": _final_status(checks), "checks": checks}, output_path, document_hash


def _check_requirements(project_dir: Path, project: dict[str, Any], checks: list[dict[str, str]]) -> None:
    rubric_path = _resolve(project_dir, project.get("rubric_file"))
    if rubric_path is not None and rubric_path.is_file():
        _add(checks, "rubric", PASS, f"Rubric is present: {rubric_path}")
    else:
        _add(checks, "rubric", INCOMPLETE, "Rubric is missing; its requirements cannot be confirmed.")

    assignment_path = _resolve(project_dir, project.get("assignment_file"))
    if assignment_path is not None and assignment_path.is_file():
        _add(checks, "assignment", PASS, f"Assignment source is present: {assignment_path}")
    elif str(project.get("assignment_summary", "")).strip():
        _add(checks, "assignment", PASS, "A recorded assignment summary is present.")
    else:
        _add(checks, "assignment", INCOMPLETE, "Assignment source and assignment_summary are missing.")

    matrix_path = _resolve(project_dir, project.get("requirements_matrix_file", "requirements-matrix.csv"))
    if matrix_path is None or not matrix_path.is_file():
        _add(checks, "requirements_matrix", INCOMPLETE, "requirements-matrix.csv is missing.")
        return
    try:
        rows = _rows(matrix_path)
    except (OSError, UnicodeError, csv.Error) as exc:
        _add(checks, "requirements_matrix", FAIL, f"Cannot read the requirements matrix: {exc}")
        return
    if not rows:
        _add(checks, "requirements_matrix", INCOMPLETE, "The matrix has no requirement rows.")
        return

    row_statuses: list[str] = []
    seen_requirement_ids: set[str] = set()
    source_root = _resolve(project_dir, project.get("source_project_root")) or project_dir
    for index, row in enumerate(rows, start=2):
        status = (row.get("status") or "").strip().upper()
        requirement_id = (row.get("requirement_id") or "").strip()
        if requirement_id and requirement_id in seen_requirement_ids:
            row_statuses.append(FAIL)
            _add(checks, f"requirement_row_{index}_id", FAIL, f"Duplicate requirement_id {requirement_id!r}.")
        elif requirement_id:
            seen_requirement_ids.add(requirement_id)
        missing_requirement_fields = [
            field for field in ("requirement_id", "rubric_requirement", "rubric_location", "report_section")
            if not (row.get(field) or "").strip()
        ]
        if missing_requirement_fields:
            row_statuses.append(INCOMPLETE)
            _add(checks, f"requirement_row_{index}", INCOMPLETE, f"Missing requirement fields: {', '.join(missing_requirement_fields)}.")
            continue
        if status not in _VALID_ROW_STATUSES:
            row_statuses.append(INCOMPLETE)
            _add(checks, f"requirement_row_{index}", INCOMPLETE, f"Unknown or blank status {status!r}.")
        elif status == FAIL:
            row_statuses.append(FAIL)
            _add(checks, f"requirement_row_{index}", FAIL, "A requirement is explicitly marked FAIL.")
        elif status in {"NOT_RUN", "BLOCKED"}:
            row_statuses.append(INCOMPLETE)
            _add(checks, f"requirement_row_{index}", INCOMPLETE, f"Requirement is {status}.")
        elif status == "WAIVED":
            if (row.get("notes") or "").strip() and (row.get("verification") or "").strip() and (row.get("waived_by") or "").strip():
                row_statuses.append(PASS)
                _add(checks, f"requirement_row_{index}", PASS, "Requirement waiver has a reason and authority record.")
            else:
                row_statuses.append(INCOMPLETE)
                _add(checks, f"requirement_row_{index}", INCOMPLETE, "Waiver requires waived_by, verification, and a reason in notes.")
        elif (row.get("evidence_files") or "").strip() and (row.get("verification") or "").strip():
            evidence_files = [item.strip() for item in row["evidence_files"].split(";") if item.strip()]
            missing_evidence = [
                item for item in evidence_files
                if (_resolve(source_root, item) is None or not _resolve(source_root, item).is_file())
            ]
            if missing_evidence:
                row_statuses.append(INCOMPLETE)
                _add(checks, f"requirement_row_{index}", INCOMPLETE, f"Evidence file(s) are missing: {', '.join(missing_evidence)}.")
            else:
                row_statuses.append(PASS)
                _add(checks, f"requirement_row_{index}", PASS, "Requirement has existing evidence files and a verification record.")
        else:
            row_statuses.append(INCOMPLETE)
            _add(checks, f"requirement_row_{index}", INCOMPLETE, "PASS requires evidence_files and verification details.")

    if not row_statuses:
        _add(checks, "requirements_matrix", INCOMPLETE, "The matrix contains no usable requirement rows.")


def _normalized_rubric_text(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").replace("\u202f", " ").split())


def _docx_body_text_and_media(path: Path) -> tuple[list[str], int]:
    blocks = _docx_body_blocks_with_media(path)
    return [text for text, _media_count in blocks], sum(media_count for _text, media_count in blocks)


def _docx_body_blocks_with_media(path: Path) -> list[tuple[str, int]]:
    from docx import Document
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    document = Document(path)
    blocks: list[tuple[str, int]] = []
    for element in document.element.body.iterchildren():
        media_count = sum(
            1 for blip in element.xpath(".//a:blip")
            if blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
        )
        if element.tag == qn("w:p"):
            blocks.append((Paragraph(element, document).text, media_count))
        elif element.tag == qn("w:tbl"):
            table = Table(element, document)
            cells = [cell for row in table.rows for cell in row.cells]
            blocks.extend(
                (cell.text, media_count if index == 0 else 0)
                for index, cell in enumerate(cells)
            )
    return blocks


def _docx_text_between_markers(
    path: Path,
    start_marker: str,
    end_marker: str,
    *,
    reject_media: bool,
) -> list[str]:
    blocks = _docx_body_blocks_with_media(path)
    normalized_start = _normalized_rubric_text(start_marker)
    normalized_end = _normalized_rubric_text(end_marker)
    start_indexes = [
        index for index, (text, _media_count) in enumerate(blocks)
        if _normalized_rubric_text(text) == normalized_start
    ]
    end_indexes = [
        index for index, (text, _media_count) in enumerate(blocks)
        if _normalized_rubric_text(text) == normalized_end
    ]
    if len(start_indexes) != 1 or len(end_indexes) != 1:
        raise ValueError("source/output section markers must each occur exactly once")
    start_index, end_index = start_indexes[0], end_indexes[0]
    if end_index <= start_index:
        raise ValueError("section end marker must follow its start marker")
    section_blocks = blocks[start_index + 1:end_index]
    if reject_media and any(media_count for _text, media_count in blocks[start_index:end_index]):
        raise ValueError("selected source section contains embedded images; visual content cannot be verified by text parity")
    return [text for text, _media_count in section_blocks if _normalized_rubric_text(text)]


def _contains_exact_paragraph_sequence(actual: list[str], expected: list[str]) -> bool:
    normalized_actual = [_normalized_rubric_text(text) for text in actual]
    normalized_expected = [_normalized_rubric_text(text) for text in expected]
    if not normalized_expected or len(normalized_expected) > len(normalized_actual):
        return False
    if any(normalized_actual.count(text) != 1 for text in normalized_expected):
        return False
    cursor = 0
    for expected_text in normalized_expected:
        while cursor < len(normalized_actual) and normalized_actual[cursor] != expected_text:
            cursor += 1
        if cursor == len(normalized_actual):
            return False
        cursor += 1
    return True


def _check_profile_section_inclusion(
    rubric_path: Path,
    output_path: Path,
    inclusion: dict[str, Any],
) -> tuple[str, str]:
    if rubric_path.suffix.casefold() != ".docx":
        return INCOMPLETE, "Profile-section inclusion currently requires a DOCX source with extractable paragraph boundaries."
    source_sections = inclusion.get("source_sections")
    if not isinstance(source_sections, list) or not source_sections:
        return INCOMPLETE, "rubric_inclusion.source_sections must list each official source section and its Word review page."

    try:
        for index, section in enumerate(source_sections, start=1):
            if not isinstance(section, dict):
                return INCOMPLETE, f"Official source section {index} has invalid metadata."
            source_text = _docx_text_between_markers(
                rubric_path,
                str(section.get("source_start", "")),
                str(section.get("source_end", "")),
                reject_media=True,
            )
            output_text = _docx_text_between_markers(
                output_path,
                str(section.get("output_start", "")),
                str(section.get("output_end", "")),
                reject_media=False,
            )
            if not source_text:
                return INCOMPLETE, f"Official source section {index} contains no extractable text."
            if not _contains_exact_paragraph_sequence(output_text, source_text):
                return FAIL, f"Official source and Word review section {index} do not exactly match the complete official criteria text."
    except Exception as exc:
        return INCOMPLETE, f"Official source section cannot be verified safely: {exc}."
    return PASS, "Each complete official criteria section exactly matches its corresponding Word review page and is bound to current source/output hashes."


def _rubric_source_text(path: Path) -> str:
    if path.suffix.casefold() == ".docx":
        blocks, media_count = _docx_body_text_and_media(path)
        if media_count:
            raise ValueError("the source rubric contains embedded images; text parity cannot confirm image content")
        return " ".join(blocks)

    if path.suffix.casefold() == ".pdf":
        import pypdfium2 as pdfium

        page_text: list[str] = []
        with pdfium.PdfDocument(path) as pdf:
            if len(pdf) == 0:
                raise ValueError("the source rubric PDF contains no pages")
            for page in pdf:
                text_page = page.get_textpage()
                try:
                    page_text.append(text_page.get_text_bounded())
                finally:
                    text_page.close()
                    page.close()
        if any(not _normalized_rubric_text(text) for text in page_text):
            raise ValueError("the source rubric has a page with no extractable text; scanned/facsimile inclusion is not auto-verified")
        return " ".join(page_text)

    raise ValueError("supported official rubric sources are DOCX and text-readable PDF")


def _check_official_rubric_in_docx(
    project_dir: Path,
    project: dict[str, Any],
    output_path: Path | None,
    document_hash: str | None,
    checks: list[dict[str, str]],
) -> None:
    if project.get("include_official_rubric_in_docx") is not True:
        _add(checks, "official_rubric_in_docx", PASS, "Official rubric appendix was not requested for this project.")
        return

    rubric_path = _resolve(project_dir, project.get("rubric_file"))
    if rubric_path is None or not rubric_path.is_file():
        _add(checks, "official_rubric_in_docx", INCOMPLETE, "The official rubric source is missing; no rubric content may be generated or inferred.")
        return
    if output_path is None or not output_path.is_file() or not document_hash:
        _add(checks, "official_rubric_in_docx", INCOMPLETE, "A saved output DOCX is required before checking the rubric appendix.")
        return
    if not str(project.get("rubric_source_authority", "")).strip():
        _add(checks, "official_rubric_in_docx", INCOMPLETE, "Record the official rubric authority or source URL in project.json.")
        return

    inclusion = project.get("rubric_inclusion")
    if not isinstance(inclusion, dict):
        _add(checks, "official_rubric_in_docx", INCOMPLETE, "rubric_inclusion review metadata is missing from project.json.")
        return
    try:
        source_hash = _sha256(rubric_path)
    except OSError as exc:
        _add(checks, "official_rubric_in_docx", INCOMPLETE, f"Cannot read/hash the official rubric source: {exc}.")
        return
    recorded_source_hash = str(inclusion.get("source_sha256", "")).strip().casefold()
    if not recorded_source_hash or recorded_source_hash != source_hash.casefold():
        _add(checks, "official_rubric_in_docx", FAIL, "Recorded rubric source SHA-256 is missing or stale.")
        return
    recorded_output_hash = str(inclusion.get("output_docx_sha256", "")).strip().casefold()
    if not recorded_output_hash or recorded_output_hash != document_hash.casefold():
        _add(checks, "official_rubric_in_docx", FAIL, "Rubric inclusion review is not bound to the current output DOCX SHA-256.")
        return
    if str(inclusion.get("review_status", "")).strip().upper() != PASS:
        _add(checks, "official_rubric_in_docx", INCOMPLETE, "Official rubric/assessment criteria inclusion has not passed review.")
        return
    review_method = str(inclusion.get("review_method", "")).strip()
    if review_method not in {"verbatim_source_comparison", "verbatim_source_section_comparison"}:
        _add(checks, "official_rubric_in_docx", INCOMPLETE, "Review method must be verbatim_source_comparison or verbatim_source_section_comparison.")
        return
    if not str(inclusion.get("reviewed_by", "")).strip() or not _valid_iso_date(
        str(inclusion.get("reviewed_at", ""))[:10]
    ):
        _add(checks, "official_rubric_in_docx", INCOMPLETE, "Official criteria review requires reviewer and valid review date.")
        return

    if review_method == "verbatim_source_section_comparison":
        status, detail = _check_profile_section_inclusion(rubric_path, output_path, inclusion)
        _add(checks, "official_rubric_in_docx", status, detail)
        return

    appendix_heading = _normalized_rubric_text(str(inclusion.get("appendix_heading", "")))
    if not appendix_heading:
        _add(checks, "official_rubric_in_docx", INCOMPLETE, "The rubric appendix heading is missing.")
        return
    try:
        source_text = _rubric_source_text(rubric_path)
        output_blocks, _output_media_count = _docx_body_text_and_media(output_path)
    except Exception as exc:
        _add(checks, "official_rubric_in_docx", INCOMPLETE, f"Rubric source cannot be verified safely: {exc}.")
        return

    source_text = _normalized_rubric_text(source_text)
    if not source_text:
        _add(checks, "official_rubric_in_docx", INCOMPLETE, "The official rubric has no extractable text; no substitute rubric may be created.")
        return
    normalized_blocks = [_normalized_rubric_text(block) for block in output_blocks]
    try:
        heading_index = normalized_blocks.index(appendix_heading)
    except ValueError:
        _add(checks, "official_rubric_in_docx", FAIL, f"The declared rubric appendix heading is missing from the output DOCX: {appendix_heading!r}.")
        return
    appendix_text = _normalized_rubric_text(" ".join(output_blocks[heading_index + 1:]))
    if appendix_text != source_text:
        _add(checks, "official_rubric_in_docx", FAIL, "The rubric appendix text is not an exact full-text match to the official source; content may be missing, altered, or added.")
        return
    _add(checks, "official_rubric_in_docx", PASS, "The rubric appendix text exactly matches the complete extractable official source and is bound to the source and current DOCX hashes.")


def _check_cover_metadata(project_dir: Path, project: dict[str, Any], checks: list[dict[str, str]]) -> None:
    metadata_path = _resolve(project_dir, project.get("cover_metadata_file", "cover-metadata.csv"))
    if metadata_path is None or not metadata_path.is_file():
        _add(checks, "cover_metadata", INCOMPLETE, "cover-metadata.csv is missing.")
        return
    try:
        rows = _rows(metadata_path)
    except (OSError, UnicodeError, csv.Error) as exc:
        _add(checks, "cover_metadata", FAIL, f"Cannot read cover-metadata.csv: {exc}")
        return
    if not rows:
        _add(checks, "cover_metadata", INCOMPLETE, "cover-metadata.csv has no identity fields.")
        return

    by_field: dict[str, dict[str, str]] = {}
    duplicate_fields: set[str] = set()
    for row in rows:
        field = (row.get("field") or "").strip()
        if not field:
            continue
        if field in by_field:
            duplicate_fields.add(field)
        by_field[field] = row
    if duplicate_fields:
        _add(checks, "cover_metadata", FAIL, f"Duplicate metadata fields: {sorted(duplicate_fields)}.")
        return

    missing_fields = _COVER_METADATA_FIELDS - by_field.keys()
    if missing_fields:
        _add(checks, "cover_metadata", INCOMPLETE, f"Missing metadata fields: {sorted(missing_fields)}.")
        return

    incomplete: list[str] = []
    invalid: list[str] = []
    for field in sorted(_COVER_METADATA_FIELDS):
        row = by_field[field]
        authority_type = (row.get("authority_type") or "").strip().upper()
        status = (row.get("status") or "").strip().upper()
        value = (row.get("value") or "").strip()
        authority = (row.get("authority") or "").strip()
        notes = (row.get("notes") or "").strip()
        reviewer = (row.get("reviewed_by") or "").strip()
        review_date = (row.get("review_date") or "").strip()

        if authority_type == "REFERENCE_SAMPLE":
            invalid.append(field)
            continue
        if authority_type not in _COVER_AUTHORITY_TYPES:
            incomplete.append(field)
            continue
        if status == "VERIFIED":
            if (
                not value
                or not authority
                or authority_type not in {"USER_INSTRUCTION", "ASSIGNMENT_OR_RUBRIC", "OFFICIAL_PROFILE"}
                or not reviewer
                or not _valid_iso_date(review_date)
            ):
                incomplete.append(field)
        elif status == "PLACEHOLDER":
            if value or authority_type != "NOT_PROVIDED" or not notes or not reviewer or not _valid_iso_date(review_date):
                incomplete.append(field)
        elif status == "NOT_APPLICABLE":
            if value or not authority or authority_type == "NOT_PROVIDED" or not notes or not reviewer or not _valid_iso_date(review_date):
                incomplete.append(field)
        elif status == "FAIL":
            invalid.append(field)
        else:
            incomplete.append(field)

    if invalid:
        _add(checks, "cover_metadata", FAIL, f"Metadata uses a sample as authority or contains a failed field: {sorted(invalid)}.")
    elif incomplete:
        _add(checks, "cover_metadata", INCOMPLETE, f"Metadata needs a verified authority or deliberate placeholder: {sorted(incomplete)}.")
    else:
        _add(checks, "cover_metadata", PASS, "All cover identity fields have a verified authority or an explicit placeholder/non-applicability record.")


def _check_structure_parity(
    project_dir: Path,
    project: dict[str, Any],
    checks: list[dict[str, str]],
    output_path: Path | None,
) -> None:
    matrix_path = _resolve(project_dir, project.get("structure_parity_matrix_file", "structure-parity.csv"))
    if matrix_path is None or not matrix_path.is_file():
        _add(checks, "project_structure_inventory", INCOMPLETE, "structure-parity.csv is missing.")
        return
    try:
        rows = _rows(matrix_path)
    except (OSError, UnicodeError, csv.Error) as exc:
        _add(checks, "project_structure_inventory", FAIL, f"Cannot read structure-parity.csv: {exc}")
        return
    if not rows:
        _add(checks, "project_structure_inventory", INCOMPLETE, "structure-parity.csv has no project-planned headings.")
        return

    source_root = _resolve(project_dir, project.get("source_project_root")) or project_dir
    incomplete: list[str] = []
    invalid: list[str] = []
    seen_ids: set[str] = set()
    for row_index, row in enumerate(rows, start=2):
        item_id = (row.get("item_id") or "").strip()
        if not item_id or item_id in seen_ids:
            invalid.append(item_id or f"row-{row_index}:blank-id")
            continue
        seen_ids.add(item_id)
        planned_heading = (row.get("planned_heading") or "").strip()
        planned_level_raw = (row.get("planned_level") or "").strip()
        source_basis = (row.get("source_basis") or "").strip()
        source_location = (row.get("source_location") or "").strip()
        decision = (row.get("decision") or "").strip().upper()
        status = (row.get("status") or "").strip().upper()
        target_heading = (row.get("target_heading") or "").strip()
        target_level_raw = (row.get("target_level") or "").strip()
        target_order_raw = (row.get("target_order") or "").strip()
        include_in_toc_raw = (row.get("include_in_toc") or "").strip().casefold()
        coverage_note = (row.get("coverage_note") or "").strip()
        evidence_values = [item.strip() for item in (row.get("evidence_files") or "").split(";") if item.strip()]
        reviewer = (row.get("reviewed_by") or "").strip()
        review_date = (row.get("review_date") or "").strip()
        if status == FAIL or decision not in _STRUCTURE_DECISIONS:
            invalid.append(item_id)
            continue
        if not all((planned_heading, planned_level_raw, source_basis, source_location, target_heading, target_level_raw, target_order_raw)):
            incomplete.append(item_id)
            continue
        if include_in_toc_raw not in {"true", "false"}:
            incomplete.append(item_id)
            continue
        try:
            planned_level = int(planned_level_raw)
            target_level = int(target_level_raw)
            target_order = int(target_order_raw)
        except ValueError:
            incomplete.append(item_id)
            continue
        if (
            planned_level not in range(1, 10)
            or target_level not in range(1, 10)
            or target_level != planned_level
            or target_order != row_index - 1
        ):
            invalid.append(item_id)
            continue
        if status != PASS or not coverage_note or not evidence_values or not reviewer or not _valid_iso_date(review_date):
            incomplete.append(item_id)
            continue
        missing_evidence = []
        for evidence in evidence_values:
            candidates = (_resolve(project_dir, evidence), _resolve(source_root, evidence))
            if not any(candidate is not None and candidate.is_file() for candidate in candidates):
                missing_evidence.append(evidence)
        if missing_evidence:
            incomplete.append(item_id)

    if invalid:
        _add(checks, "project_structure_inventory", FAIL, f"Structure inventory has duplicate IDs, invalid levels/order, or failed decisions: {sorted(invalid)[:8]}.")
    elif incomplete:
        _add(checks, "project_structure_inventory", INCOMPLETE, f"{len(incomplete)} planned headings lack a complete, evidence-backed mapping; first IDs: {sorted(incomplete)[:8]}.")
    else:
        _add(checks, "project_structure_inventory", PASS, f"All {len(rows)} project-planned headings have reviewed, evidence-backed mappings.")
        if output_path is None or not output_path.is_file():
            _add(checks, "project_structure_in_docx", INCOMPLETE, "The final DOCX is missing; its actual heading outline cannot be checked.")
            return
        try:
            from docx import Document
            from docx.oxml.ns import qn
            from docx.text.paragraph import Paragraph
            from wordassistant.selectors import _heading_level

            document = Document(output_path)
            outline = [
                (paragraph.text, _heading_level(paragraph))
                for paragraph in document.paragraphs
                if paragraph.text.strip()
                and not paragraph.style.name.casefold().startswith("toc")
                and _heading_level(paragraph) is not None
            ]
        except Exception as exc:
            _add(checks, "project_structure_in_docx", FAIL, f"Cannot inspect the final DOCX heading outline: {exc}")
            return

        actual = [
            (" ".join(str(title).split()).casefold(), level)
            for title, level in outline
        ]
        expected = [
            (" ".join(row["target_heading"].split()).casefold(), int(row["target_level"]))
            for row in rows
        ]
        expected_toc = [
            (" ".join(row["target_heading"].split()).casefold(), int(row["target_level"]))
            for row in rows
            if (row.get("include_in_toc") or "").strip().casefold() == "true"
        ]
        if actual != expected:
            _add(checks, "project_structure_in_docx", FAIL, f"The DOCX outline does not exactly match the project inventory (planned {len(expected)}, found {len(actual)} headings; missing/reordered/extra headings must be reviewed).")
        else:
            _add(checks, "project_structure_in_docx", PASS, f"All {len(expected)} project-inventoried headings appear in the final DOCX at the planned levels and order.")

        actual_toc = []
        expected_toc_lookup = set(expected_toc)
        for paragraph_element in document._element.xpath(".//w:p"):
            paragraph = Paragraph(paragraph_element, document._body)
            style_name = paragraph.style.name.casefold().replace(" ", "").replace("_", "")
            if not style_name.startswith("toc") or not style_name[3:].isdigit():
                continue
            title_parts: list[str] = []
            # A tab stop in w:pPr is layout metadata, not the tab that
            # separates a visible TOC title from its page number. Only stop
            # at a tab inside a run.
            page_number_tab_found = False
            for run in paragraph_element.xpath(".//w:r"):
                for node in run.iter():
                    if node.tag == qn("w:tab"):
                        page_number_tab_found = True
                        break
                    if node.tag == qn("w:t"):
                        title_parts.append(node.text or "")
                if page_number_tab_found:
                    break
            title = "".join(title_parts).split("\t", 1)[0].strip()
            if title:
                level = int(style_name[3:])
                normalized_title = _normalized_text(title)
                # Word may render a multilevel heading prefix either with or
                # without a terminal dot (for example, "1.1 Title" or
                # "1.1. Title"). Strip it only when the unnumbered title is
                # present in the reviewed outline at the same level.
                numbered_title = re.match(r"^\d+(?:\.\d+)*\.?\s+(.+)$", title)
                if numbered_title:
                    unnumbered = _normalized_text(numbered_title.group(1))
                    if (unnumbered, level) in expected_toc_lookup:
                        normalized_title = unnumbered
                actual_toc.append((normalized_title, level))
        if actual_toc != expected_toc:
            _add(checks, "project_toc_parity", FAIL, f"The visible Word TOC does not exactly match the headings marked include_in_toc=true (planned {len(expected_toc)}, found {len(actual_toc)} entries). Update the TOC and check its levels and order.")
        else:
            _add(checks, "project_toc_parity", PASS, f"All {len(expected_toc)} required TOC entries appear at the planned levels and order.")


def _normalized_text(value: str) -> str:
    normalized = " ".join(value.split()).casefold()
    # Word may serialize a SEQ label and number as split runs, leaving spaces
    # around the dots (for example, "HÌNH 2. 1 . title"). Normalize only
    # numbering punctuation so those captions still match their visible text.
    normalized = re.sub(r"(?<=[0-9a-z])\s*\.\s*(?=[0-9])", ".", normalized)
    return re.sub(r"(?<=\d)\s+\.", ".", normalized)


def _embedded_media_counts_by_caption(document: Any, rows: list[dict[str, str]]) -> tuple[int, list[int], list[str]]:
    from docx.enum.style import WD_STYLE_TYPE

    office_relationship_namespace = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
    caption_rows = [
        row for row in rows
        if (row.get("caption_required") or "").strip().casefold() == "true"
    ]
    uncaptioned_media_count = 0
    anchored_rows: list[tuple[dict[str, str], int, str]] = []
    for row in rows:
        if (row.get("caption_required") or "").strip().casefold() != "false":
            continue
        try:
            count = int((row.get("expected_media_count") or "0").strip() or "0")
            anchor = _normalized_text((row.get("uncaptioned_anchor") or "").strip())
            if anchor and count > 0:
                anchored_rows.append((row, count, anchor))
            else:
                uncaptioned_media_count += count
        except ValueError:
            # The inventory check reports malformed counts; media inspection
            # should still produce diagnostics instead of aborting assessment.
            continue
    targets = [_normalized_text((row.get("target_caption") or "").strip()) for row in caption_rows]
    caption_style_ids = {
        style.style_id
        for style in document.styles
        if style.type == WD_STYLE_TYPE.PARAGRAPH and style.name.strip().casefold() == "caption"
    }
    paragraphs: list[tuple[str, int, bool]] = []
    for paragraph in document._element.xpath(".//w:p"):
        media_count = sum(
            1 for blip in paragraph.xpath(".//a:blip")
            if blip.get(office_relationship_namespace)
        )
        visible_text = " ".join(node.text or "" for node in paragraph.xpath(".//w:t"))
        style_nodes = paragraph.xpath("./w:pPr/w:pStyle")
        paragraph_style_id = style_nodes[0].get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val") if style_nodes else ""
        paragraphs.append((_normalized_text(visible_text), media_count, paragraph_style_id in caption_style_ids))

    total_media = sum(media_count for _text, media_count, _is_caption in paragraphs)
    anchored_indices: set[int] = set()
    anchor_errors: list[str] = []
    for row, expected_count, anchor in anchored_rows:
        matches = [index for index, (text, _count, _caption) in enumerate(paragraphs) if text == anchor]
        if len(matches) != 1:
            anchor_errors.append((row.get("asset_id") or "").strip())
            continue
        image_index = matches[0] + 1
        if (image_index >= len(paragraphs) or image_index in anchored_indices
                or paragraphs[image_index][1] != expected_count or paragraphs[image_index][2]):
            anchor_errors.append((row.get("asset_id") or "").strip())
            continue
        anchored_indices.add(image_index)
    # Anchored images are excluded at their actual locations. Legacy rows
    # without anchors consume the first media items (normally cover logos).
    # Captioned assets are counted between consecutive captions.
    uncaptioned_remaining = uncaptioned_media_count
    per_caption: list[int] = []
    missing: list[str] = list(anchor_errors)
    previous_caption_paragraph = -1
    target_index = 0
    for paragraph_index, (normalized_text, _media_count, is_caption) in enumerate(paragraphs):
        if not is_caption:
            continue
        while target_index < len(targets) and targets[target_index] and targets[target_index] in normalized_text:
            segment_count = sum(
                paragraphs[index][1] for index in range(previous_caption_paragraph + 1, paragraph_index + 1)
                if index not in anchored_indices
            )
            uncaptioned_in_segment = min(uncaptioned_remaining, segment_count)
            per_caption.append(segment_count - uncaptioned_in_segment)
            uncaptioned_remaining -= uncaptioned_in_segment
            previous_caption_paragraph = paragraph_index
            target_index += 1
    for row in caption_rows[target_index:]:
        missing.append((row.get("asset_id") or "").strip())
    return total_media, per_caption, missing


def _check_runtime_capture_provenance(
    project_dir: Path,
    project: dict[str, Any],
    source_root: Path,
    rows: list[dict[str, str]],
    checks: list[dict[str, str]],
) -> None:
    runtime_rows = [
        row for row in rows
        if "runtime" in (row.get("asset_type") or "").casefold()
        and "screenshot" in (row.get("asset_type") or "").casefold()
    ]
    if not runtime_rows:
        _add(checks, "project_runtime_capture_provenance", PASS, "No runtime screenshots are planned in the visual inventory.")
        return

    manifest_path = _resolve(project_dir, project.get("runtime_capture_manifest_file"))
    if manifest_path is None or not manifest_path.is_file():
        _add(checks, "project_runtime_capture_provenance", INCOMPLETE, "Runtime screenshot assets require runtime_capture_manifest_file in project.json.")
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _add(checks, "project_runtime_capture_provenance", FAIL, f"Cannot read runtime capture manifest: {exc}.")
        return

    accepted_status = "ACCEPTED_UI_CLICKTHROUGH_CAPTURE"
    manifest_status = str(manifest.get("acceptance_status", "")).strip().upper()
    if manifest_status != accepted_status:
        if "DIRECT" in manifest_status or "PROVISIONAL" in manifest_status or "NOT_ACCEPTED" in manifest_status:
            _add(checks, "project_runtime_capture_provenance", FAIL, f"Runtime capture manifest is not accepted user-style click-through evidence ({manifest_status or 'status missing'}).")
        else:
            _add(checks, "project_runtime_capture_provenance", INCOMPLETE, "Runtime capture manifest must declare acceptance_status=ACCEPTED_UI_CLICKTHROUGH_CAPTURE.")
        return

    captures = manifest.get("captures")
    if not isinstance(captures, list):
        _add(checks, "project_runtime_capture_provenance", FAIL, "Runtime capture manifest must contain a captures list.")
        return
    capture_context = manifest.get("capture_context")
    if not isinstance(capture_context, dict):
        _add(checks, "project_runtime_capture_provenance", INCOMPLETE, "Runtime capture manifest must record capture_context for visible-browser and non-headless provenance.")
        return
    if capture_context.get("browser_surface") != "visible_browser_tab":
        _add(checks, "project_runtime_capture_provenance", FAIL, "Runtime screenshots must be captured from a visible browser tab.")
        return
    if capture_context.get("headless") is not False:
        _add(checks, "project_runtime_capture_provenance", FAIL, "Headless browser screenshots are not accepted as user-style runtime captures.")
        return
    if capture_context.get("navigation_policy") != "visible_ui_clickthrough":
        _add(checks, "project_runtime_capture_provenance", INCOMPLETE, "Capture context must declare navigation_policy=visible_ui_clickthrough.")
        return
    by_id: dict[str, dict[str, Any]] = {}
    duplicate_ids: set[str] = set()
    for capture in captures:
        if not isinstance(capture, dict):
            continue
        capture_id = str(capture.get("capture_id", "")).strip()
        if not capture_id:
            continue
        if capture_id in by_id:
            duplicate_ids.add(capture_id)
        by_id[capture_id] = capture

    failed: list[str] = []
    incomplete: list[str] = []
    accepted = 0
    planned_capture_ids = {
        (row.get("capture_id") or "").strip()
        for row in runtime_rows
        if (row.get("capture_id") or "").strip()
    }
    for capture in captures:
        if not isinstance(capture, dict):
            continue
        capture_id = str(capture.get("capture_id", "")).strip() or "unnamed"
        if capture_id in planned_capture_ids:
            continue
        network = capture.get("network")
        document_status = network.get("document_status") if isinstance(network, dict) else None
        http_status = capture.get("http_status")
        console = capture.get("console")
        console_errors = console.get("errors", []) if isinstance(console, dict) else []
        page_review = capture.get("page_state_review")
        review_failed = (
            isinstance(page_review, dict)
            and str(page_review.get("status", "")).strip().upper() == FAIL
        )
        response_failed = (
            type(http_status) is int and not 200 <= http_status < 300
        ) or (
            type(document_status) is int and not 200 <= document_status < 300
        )
        if not (review_failed or response_failed or bool(console_errors)):
            continue

        screenshot_rel = str(capture.get("screenshot_path", "")).strip()
        screenshot_sha = str(capture.get("screenshot_sha256", "")).strip().casefold()
        review_summary = str(page_review.get("summary", "")).strip() if isinstance(page_review, dict) else ""
        if not review_summary:
            incomplete.append(f"unplanned capture {capture_id}: failed page state has no error summary")
        if (
            not isinstance(page_review, dict)
            or str(page_review.get("status", "")).strip().upper() != FAIL
            or str(page_review.get("screenshot_path", "")).strip() != screenshot_rel
            or str(page_review.get("screenshot_sha256", "")).strip().casefold() != screenshot_sha
        ):
            failed.append(f"unplanned capture {capture_id}: observed error is not reviewed and bound to its screenshot")
        if not screenshot_rel or len(screenshot_sha) != 64:
            incomplete.append(f"unplanned capture {capture_id}: error screenshot path/hash is missing")
            continue
        screenshot_path = next(
            (
                candidate for candidate in (
                    _resolve(project_dir, screenshot_rel),
                    _resolve(source_root, screenshot_rel),
                )
                if candidate is not None and candidate.is_file()
            ),
            None,
        )
        if screenshot_path is None:
            incomplete.append(f"unplanned capture {capture_id}: error screenshot file is missing")
        elif _sha256(screenshot_path).casefold() != screenshot_sha:
            failed.append(f"unplanned capture {capture_id}: error screenshot hash mismatch")
        else:
            failed.append(f"unplanned capture {capture_id}: failed page/error state was captured ({review_summary})")

    for row in runtime_rows:
        asset_id = (row.get("asset_id") or "").strip() or "unnamed asset"
        capture_id = (row.get("capture_id") or "").strip()
        expected_route = (row.get("runtime_route") or "").strip()
        if not capture_id or not expected_route:
            incomplete.append(f"{asset_id}: capture_id/runtime_route missing")
            continue
        if capture_id in duplicate_ids:
            failed.append(f"{asset_id}: duplicate capture_id {capture_id}")
            continue
        capture = by_id.get(capture_id)
        if capture is None:
            incomplete.append(f"{asset_id}: capture_id {capture_id} absent from manifest")
            continue

        screenshot_rel = str(capture.get("screenshot_path", "")).strip()
        screenshot_sha = str(capture.get("screenshot_sha256", "")).strip().casefold()
        if not screenshot_rel or len(screenshot_sha) != 64:
            incomplete.append(f"{asset_id}: screenshot path/hash missing")
            continue
        screenshot_path = next(
            (
                candidate for candidate in (
                    _resolve(project_dir, screenshot_rel),
                    _resolve(source_root, screenshot_rel),
                )
                if candidate is not None and candidate.is_file()
            ),
            None,
        )
        if screenshot_path is None:
            incomplete.append(f"{asset_id}: screenshot file {screenshot_rel} is missing")
            continue
        if _sha256(screenshot_path).casefold() != screenshot_sha:
            failed.append(f"{asset_id}: screenshot hash mismatch")
            continue

        route = str(capture.get("route", "")).strip()
        if route != expected_route:
            failed.append(f"{asset_id}: route mismatch ({expected_route} != {route or 'missing'})")
            continue
        capture_status = str(capture.get("acceptance_status", "")).strip().upper()
        if capture_status != accepted_status:
            failed.append(f"{asset_id}: capture is not accepted UI click-through evidence ({capture_status or 'status missing'})")
            continue

        arrival = capture.get("arrival")
        arrival = arrival if isinstance(arrival, dict) else {}
        if arrival.get("local_file_open_for_this_capture") is True:
            failed.append(f"{asset_id}: local UI/file opening is not accepted as a runtime screenshot")
            continue
        if arrival.get("local_file_open_for_this_capture") is not False:
            incomplete.append(f"{asset_id}: manifest does not confirm that no local UI/file was opened")
            continue
        if arrival.get("direct_route_load_for_this_capture") is True:
            failed.append(f"{asset_id}: direct-route screenshot is not accepted")
            continue
        if arrival.get("direct_route_load_for_this_capture") is not False:
            incomplete.append(f"{asset_id}: manifest does not confirm navigation without a direct route load")
            continue
        capture_method = " ".join(
            str(value).strip()
            for value in (manifest.get("capture_method"), capture.get("capture_method"))
            if str(value or "").strip()
        ).casefold()
        arrival_from = str(arrival.get("from", "")).strip()
        if not arrival_from or not any(token in capture_method for token in ("visible", "click", "interaction", "click-through", "clickthrough")):
            incomplete.append(f"{asset_id}: visible UI arrival method/history is missing")
            continue
        ui_steps = arrival.get("ui_steps")
        if not isinstance(ui_steps, list) or not ui_steps or any(not str(step).strip() for step in ui_steps):
            incomplete.append(f"{asset_id}: visible UI navigation steps are missing")
            continue
        resolved_url = capture.get("resolved_url")
        if not isinstance(resolved_url, str) or not resolved_url.strip():
            incomplete.append(f"{asset_id}: final web URL is missing")
            continue
        try:
            parsed_url = urlsplit(resolved_url.strip())
            expected_url = urlsplit(expected_route)
            is_web_url = parsed_url.scheme.casefold() in {"http", "https"} and bool(parsed_url.netloc)
            route_matches = (parsed_url.path or "/") == (expected_url.path or "/") and parsed_url.query == expected_url.query
        except ValueError:
            is_web_url = False
            route_matches = False
        if not is_web_url:
            failed.append(f"{asset_id}: screenshot URL must be a real HTTP(S) page, not a local file or non-web UI")
            continue
        if not route_matches:
            failed.append(f"{asset_id}: resolved web URL does not match the inventoried page route")
            continue
        if capture.get("external_side_effect") is not False:
            incomplete.append(f"{asset_id}: no-side-effect status is not confirmed")
            continue

        http_status = capture.get("http_status")
        network = capture.get("network")
        document_status = network.get("document_status") if isinstance(network, dict) else None
        console = capture.get("console")
        if type(http_status) is not int or not 100 <= http_status <= 599:
            incomplete.append(f"{asset_id}: HTTP response status was not recorded")
            continue
        if type(document_status) is not int or not 100 <= document_status <= 599:
            incomplete.append(f"{asset_id}: main document network status was not recorded")
            continue
        if not isinstance(console, dict) or any(
            not isinstance(console.get(key), list)
            for key in ("errors", "warnings")
        ):
            incomplete.append(f"{asset_id}: console error/warning state was not recorded")
            continue
        if not isinstance(capture.get("page_title"), str) or not capture["page_title"].strip():
            incomplete.append(f"{asset_id}: visible page title/state was not recorded")
            continue

        captured_at = str(capture.get("captured_at_local", "")).strip()
        try:
            captured_at_value = datetime.fromisoformat(captured_at)
        except ValueError:
            incomplete.append(f"{asset_id}: capture timestamp is missing or invalid")
            continue
        if captured_at_value.tzinfo is None:
            incomplete.append(f"{asset_id}: capture timestamp must include a timezone")
            continue

        page_review = capture.get("page_state_review")
        if not isinstance(page_review, dict):
            incomplete.append(f"{asset_id}: screenshot has no reviewed page/error state")
            continue
        page_review_status = str(page_review.get("status", "")).strip().upper()
        page_review_summary = str(page_review.get("summary", "")).strip()
        if page_review_status not in {PASS, FAIL}:
            incomplete.append(f"{asset_id}: page_state_review.status must be PASS or FAIL")
            continue
        if not page_review_summary:
            incomplete.append(f"{asset_id}: page/error state review summary is missing")
            continue
        if not str(page_review.get("reviewed_by", "")).strip() or not _valid_iso_date(
            str(page_review.get("reviewed_at", ""))[:10]
        ):
            incomplete.append(f"{asset_id}: page/error state reviewer and date are required")
            continue
        if (
            str(page_review.get("screenshot_path", "")).strip() != screenshot_rel
            or str(page_review.get("screenshot_sha256", "")).strip().casefold()
            != screenshot_sha
        ):
            failed.append(f"{asset_id}: page/error state review is not bound to this screenshot")
            continue

        has_http_error = not 200 <= http_status < 300 or not 200 <= document_status < 300
        console_errors = console.get("errors", [])
        has_console_error = bool(console_errors)
        if page_review_status == FAIL:
            failed.append(f"{asset_id}: captured page/error state was reviewed as failed ({page_review_summary})")
            continue
        if has_http_error or has_console_error:
            observed = []
            if has_http_error:
                observed.append(f"HTTP/document status {http_status}/{document_status}")
            if has_console_error:
                observed.append(f"{len(console_errors)} console error(s)")
            failed.append(
                f"{asset_id}: observed {' and '.join(observed)} but page_state_review says PASS"
            )
            continue
        accepted += 1

    if failed:
        _add(checks, "project_runtime_capture_provenance", FAIL, f"Runtime screenshot provenance failed: {failed[:8]}.")
    elif incomplete:
        _add(checks, "project_runtime_capture_provenance", INCOMPLETE, f"Runtime screenshot provenance is incomplete: {incomplete[:8]}.")
    else:
        _add(checks, "project_runtime_capture_provenance", PASS, f"All {accepted} runtime screenshots are route-matched, captured after visible UI click-through, and hash-bound to their image files.")


def _check_asset_parity(project_dir: Path, project: dict[str, Any], checks: list[dict[str, str]]) -> None:
    matrix_path = _resolve(project_dir, project.get("asset_parity_matrix_file", "asset-parity.csv"))
    if matrix_path is None or not matrix_path.is_file():
        _add(checks, "project_visual_inventory", INCOMPLETE, "asset-parity.csv is missing.")
        return
    try:
        rows = _rows(matrix_path)
    except (OSError, UnicodeError, csv.Error) as exc:
        _add(checks, "project_visual_inventory", FAIL, f"Cannot read asset-parity.csv: {exc}")
        return
    if not rows:
        _check_runtime_capture_provenance(project_dir, project, _resolve(project_dir, project.get("source_project_root")) or project_dir, rows, checks)
        review = project.get("visual_inventory_review")
        if (
            isinstance(review, dict)
            and review.get("decision") == "NONE_REQUIRED"
            and str(review.get("reason", "")).strip()
            and str(review.get("reviewed_by", "")).strip()
            and _valid_iso_date(str(review.get("review_date", "")))
        ):
            output_path = _resolve(project_dir, project.get("output_docx"))
            if output_path is None or not output_path.is_file():
                _add(checks, "project_visual_inventory", INCOMPLETE, "The final DOCX is missing; the no-visual decision cannot be checked against embedded media.")
            else:
                try:
                    from docx import Document

                    media_count, _per_caption, _missing = _embedded_media_counts_by_caption(Document(output_path), [])
                except Exception as exc:
                    _add(checks, "project_visual_inventory", FAIL, f"Cannot inspect embedded media in the final DOCX: {exc}")
                else:
                    if media_count:
                        _add(checks, "project_visual_inventory", FAIL, f"The inventory says no visuals are required, but the DOCX contains {media_count} embedded images.")
                        _add(checks, "project_visual_media", FAIL, "Embedded images are missing from the visual inventory.")
                    else:
                        _add(checks, "project_visual_inventory", PASS, "A reviewer recorded that this project requires no figures or tables, and the DOCX contains no embedded images.")
                        _add(checks, "project_visual_media", PASS, "The DOCX contains no embedded images, matching the reviewed NONE_REQUIRED decision.")
        else:
            _add(checks, "project_visual_inventory", INCOMPLETE, "asset-parity.csv is empty; add the project-required assets or record a reviewed NONE_REQUIRED decision with its reason.")
        return

    source_root = _resolve(project_dir, project.get("source_project_root")) or project_dir
    _check_runtime_capture_provenance(project_dir, project, source_root, rows, checks)
    incomplete: list[str] = []
    invalid: list[str] = []
    seen_ids: set[str] = set()
    expected_media_counts: list[int] = []
    for row_index, row in enumerate(rows, start=2):
        asset_id = (row.get("asset_id") or "").strip()
        if not asset_id or asset_id in seen_ids:
            invalid.append(asset_id or f"row-{row_index}:blank-id")
            continue
        seen_ids.add(asset_id)
        decision = (row.get("decision") or "").strip().upper()
        status = (row.get("status") or "").strip().upper()
        asset_type = (row.get("asset_type") or "").strip()
        source_basis = (row.get("source_basis") or "").strip()
        source_location = (row.get("source_location") or "").strip()
        target_section = (row.get("target_section") or "").strip()
        target_caption = (row.get("target_caption") or "").strip()
        expected_media_raw = (row.get("expected_media_count") or "").strip()
        caption_required_raw = (row.get("caption_required") or "").strip().casefold()
        coverage_note = (row.get("coverage_note") or "").strip()
        evidence_values = [item.strip() for item in (row.get("evidence_files") or "").split(";") if item.strip()]
        reviewer = (row.get("reviewed_by") or "").strip()
        review_date = (row.get("review_date") or "").strip()
        try:
            expected_media_count = int(expected_media_raw)
            if expected_media_count < 0:
                raise ValueError("negative media count")
        except ValueError:
            incomplete.append(asset_id)
            continue
        expected_media_counts.append(expected_media_count)
        if caption_required_raw not in {"true", "false"}:
            incomplete.append(asset_id)
            continue
        if asset_type.upper() not in {"TABLE", "TEXT_TABLE"} and expected_media_count < 1:
            invalid.append(asset_id)
            continue
        if status == FAIL or decision not in _STRUCTURE_DECISIONS:
            invalid.append(asset_id)
            continue
        caption_fields_valid = bool(target_caption) if caption_required_raw == "true" else not target_caption
        if not all((asset_type, source_basis, source_location, target_section, coverage_note)) or not caption_fields_valid or status != PASS or not evidence_values or not reviewer or not _valid_iso_date(review_date):
            incomplete.append(asset_id)
            continue
        if any(
            not any(
                candidate is not None and candidate.is_file()
                for candidate in (_resolve(project_dir, evidence), _resolve(source_root, evidence))
            )
            for evidence in evidence_values
        ):
            incomplete.append(asset_id)

    if invalid:
        _add(checks, "project_visual_inventory", FAIL, f"Visual inventory has duplicate IDs or failed/unsupported decisions: {sorted(invalid)[:8]}.")
    elif incomplete:
        _add(checks, "project_visual_inventory", INCOMPLETE, f"{len(incomplete)} of {len(rows)} planned figures/tables lack complete, evidence-backed records; first IDs: {sorted(incomplete)[:8]}.")
    else:
        if project.get("output_docx"):
            output_path = _resolve(project_dir, project.get("output_docx"))
        else:
            output_path = None
        if output_path is None or not output_path.is_file():
            _add(checks, "project_visual_inventory", INCOMPLETE, "The final DOCX is missing; visible captions cannot be checked.")
            return
        try:
            from docx import Document

            document = Document(output_path)
            total_media, media_by_caption, media_missing_captions = _embedded_media_counts_by_caption(document, rows)
        except Exception as exc:
            _add(checks, "project_visual_inventory", FAIL, f"Cannot inspect the final DOCX captions and embedded media: {exc}")
            return
        captioned_rows = [
            row for row in rows
            if (row.get("caption_required") or "").strip().casefold() == "true"
        ]
        missing_captions = media_missing_captions
        if missing_captions:
            _add(checks, "project_visual_inventory", FAIL, f"Planned captions or uncaptioned asset anchors are missing or ambiguous: {missing_captions[:8]}.")
        else:
            _add(checks, "project_visual_inventory", PASS, f"All {len(captioned_rows)} required captions for the {len(rows)} planned visual assets appear in the final DOCX.")
        captioned_expected_counts = [
            int((row.get("expected_media_count") or "0").strip())
            for row in captioned_rows
            if (row.get("expected_media_count") or "").strip().isdigit()
        ]
        media_mismatches = [
            (captioned_rows[index].get("asset_id") or "").strip()
            for index, expected_count in enumerate(captioned_expected_counts)
            if index >= len(media_by_caption) or media_by_caption[index] != expected_count
        ]
        expected_total = sum(expected_media_counts)
        if total_media != expected_total or media_mismatches:
            _add(checks, "project_visual_media", FAIL, f"Embedded image coverage differs from asset-parity.csv: expected {expected_total} images total, found {total_media}; caption-bound mismatches={media_mismatches[:8]}.")
        else:
            _add(checks, "project_visual_media", PASS, f"All {total_media} embedded images are accounted for by the planned assets and attached to the expected caption sequence.")


def _check_claim_evidence(project_dir: Path, project: dict[str, Any], checks: list[dict[str, str]]) -> set[str]:
    claim_path = _resolve(project_dir, project.get("claim_evidence_file", "claim-evidence.csv"))
    if claim_path is None or not claim_path.is_file():
        _add(checks, "claim_evidence", INCOMPLETE, "claim-evidence.csv is missing.")
        return set()
    try:
        rows = _rows(claim_path)
    except (OSError, UnicodeError, csv.Error) as exc:
        _add(checks, "claim_evidence", FAIL, f"Cannot read claim-evidence.csv: {exc}")
        return set()
    if not rows:
        _add(checks, "claim_evidence", INCOMPLETE, "No factual claims are mapped to evidence.")
        return set()

    registry_path = _resolve(project_dir, project.get("evidence_registry_file", "evidence.json"))
    registry: dict[str, Any] | None = None
    if registry_path is None or not registry_path.is_file():
        _add(checks, "evidence_registry", INCOMPLETE, "The configured evidence registry is missing.")
    else:
        try:
            registry = _load_json(registry_path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            _add(checks, "evidence_registry", FAIL, f"Cannot read a valid evidence registry: {exc}")

    source_root = _resolve(project_dir, project.get("source_project_root")) or project_dir
    evidence_ids: set[str] = set()
    seen_claim_ids: set[str] = set()
    for index, row in enumerate(rows, start=2):
        prefix = f"claim_row_{index}"
        required = (
            "claim_id", "report_location", "claim_summary", "evidence_id", "source_file",
            "source_sha256", "source_location", "reviewed_by", "review_date",
        )
        missing = [name for name in required if not (row.get(name) or "").strip()]
        if missing:
            _add(checks, prefix, INCOMPLETE, f"Missing fields: {', '.join(missing)}.")
            continue
        claim_id = row["claim_id"].strip()
        if claim_id in seen_claim_ids:
            _add(checks, prefix, FAIL, f"Duplicate claim_id {claim_id!r}.")
            continue
        seen_claim_ids.add(claim_id)
        evidence_ids.add(row["evidence_id"].strip())
        source_path = _resolve(source_root, row["source_file"])
        if source_path is None or not source_path.is_file():
            _add(checks, prefix, INCOMPLETE, f"Evidence source file is missing: {row['source_file']}.")
            continue
        expected_hash = row["source_sha256"].strip().casefold()
        try:
            source_hash = _sha256(source_path)
        except OSError as exc:
            _add(checks, prefix, INCOMPLETE, f"Cannot read evidence source file: {exc}")
            continue
        if source_hash.casefold() != expected_hash:
            _add(checks, prefix, FAIL, f"Evidence source hash changed for {row['source_file']}.")
            continue
        if (row.get("review_status") or "").strip().casefold() != "reviewed":
            _add(checks, prefix, INCOMPLETE, "Evidence has not been marked reviewed.")
            continue
        if (row.get("support_confirmed") or "").strip().casefold() not in {"yes", "true"}:
            _add(checks, prefix, INCOMPLETE, "A reviewer has not confirmed that the source supports the claim.")
            continue
        if registry is None:
            _add(checks, prefix, INCOMPLETE, f"Evidence ID {row['evidence_id']} cannot be checked without the evidence registry.")
            continue
        record = registry.get(row["evidence_id"].strip())
        if not isinstance(record, dict):
            _add(checks, prefix, INCOMPLETE, f"Evidence ID {row['evidence_id']} is missing from the registry.")
            continue
        if record.get("id") != row["evidence_id"].strip():
            _add(checks, prefix, FAIL, f"Registry key and record ID differ for {row['evidence_id']}.")
            continue
        if record.get("review_status") != "reviewed":
            _add(checks, prefix, INCOMPLETE, f"Evidence ID {row['evidence_id']} is not reviewed in the registry.")
            continue
        if str(record.get("source_sha256", "")).casefold() != expected_hash:
            _add(checks, prefix, FAIL, f"Evidence registry source hash differs for {row['evidence_id']}.")
            continue
        if str(record.get("support_location", "")).strip() != row["source_location"].strip():
            _add(checks, prefix, INCOMPLETE, f"Evidence registry support location differs for {row['evidence_id']}.")
            continue
        if not _valid_iso_date(row["review_date"].strip()):
            _add(checks, prefix, INCOMPLETE, "review_date must use YYYY-MM-DD format.")
            continue
        _add(checks, prefix, PASS, f"Claim {row['claim_id']} maps to reviewed source {row['source_file']} with a current hash.")
    return evidence_ids


def _check_acceptance(project: dict[str, Any], checks: list[dict[str, str]]) -> None:
    acceptance = project.get("acceptance_checks")
    required = project.get("required_acceptance_checks")
    if (
        not isinstance(acceptance, dict)
        or not isinstance(required, list)
        or not required
        or any(not isinstance(name, str) or not name for name in required)
    ):
        _add(checks, "acceptance_checks", INCOMPLETE, "Required acceptance checks are not configured.")
        return
    required_names = dict.fromkeys((*_REQUIRED_ACCEPTANCE_CHECKS, *required))
    for name in required_names:
        if name not in acceptance:
            _add(checks, f"acceptance_{name}", INCOMPLETE, "Required acceptance check is not defined.")
        elif acceptance[name] is True:
            _add(checks, f"acceptance_{name}", PASS, "Required human review is recorded as complete.")
        else:
            _add(checks, f"acceptance_{name}", INCOMPLETE, "Required human review has not been recorded as complete.")


def _check_acceptance_crosswalk(
    project_dir: Path,
    project: dict[str, Any],
    document_hash: str | None,
    checks: list[dict[str, str]],
) -> None:
    matrix_path = _resolve(project_dir, project.get("acceptance_crosswalk_file", "acceptance-crosswalk.csv"))
    if matrix_path is None or not matrix_path.is_file():
        _add(checks, "acceptance_crosswalk", INCOMPLETE, "acceptance-crosswalk.csv is missing.")
        return
    try:
        rows = _rows(matrix_path)
    except (OSError, UnicodeError, csv.Error) as exc:
        _add(checks, "acceptance_crosswalk", FAIL, f"Cannot read acceptance-crosswalk.csv: {exc}")
        return
    if not rows:
        _add(checks, "acceptance_crosswalk", INCOMPLETE, "The acceptance crosswalk has no reviewed criteria.")
        return

    source_root = _resolve(project_dir, project.get("source_project_root")) or project_dir
    seen_ids: set[str] = set()
    categories: set[str] = set()
    incomplete: list[str] = []
    invalid: list[str] = []
    required_fields = (
        "check_id", "category", "authority", "source_location", "acceptance_criterion",
        "report_location", "verification_method", "evidence_files", "evidence_sha256", "document_sha256",
        "reviewed_by", "review_date",
    )
    for row_index, row in enumerate(rows, start=2):
        check_id = (row.get("check_id") or "").strip()
        category = (row.get("category") or "").strip().casefold()
        if not check_id or check_id in seen_ids:
            invalid.append(check_id or f"row-{row_index}:blank-id")
        else:
            seen_ids.add(check_id)
        if category:
            categories.add(category)
        if category not in _REQUIRED_ACCEPTANCE_CATEGORIES:
            invalid.append(check_id or f"row-{row_index}:unknown-category")
        missing_fields = [field for field in required_fields if not (row.get(field) or "").strip()]
        if missing_fields:
            incomplete.append(check_id or f"row-{row_index}:missing-fields")
            continue

        status = (row.get("status") or "").strip().upper()
        if status == FAIL:
            invalid.append(check_id)
        elif status not in {PASS, "WAIVED", "NOT_RUN", "BLOCKED"}:
            incomplete.append(check_id)
        elif status in {"NOT_RUN", "BLOCKED"}:
            incomplete.append(check_id)
        elif status == "WAIVED" and not (row.get("notes") or "").strip():
            incomplete.append(check_id)

        if not _valid_iso_date((row.get("review_date") or "").strip()):
            incomplete.append(check_id)
        if document_hash is None:
            incomplete.append(check_id)
        elif (row.get("document_sha256") or "").strip().casefold() != document_hash.casefold():
            invalid.append(f"{check_id}:stale-document-hash")

        evidence_values = [item.strip() for item in (row.get("evidence_files") or "").split(";") if item.strip()]
        evidence_hashes = [item.strip().casefold() for item in (row.get("evidence_sha256") or "").split(";") if item.strip()]
        if not evidence_values or len(evidence_values) != len(evidence_hashes):
            incomplete.append(check_id)
            continue
        for evidence, expected_hash in zip(evidence_values, evidence_hashes):
            evidence_path = next(
                (
                    candidate for candidate in (_resolve(project_dir, evidence), _resolve(source_root, evidence))
                    if candidate is not None and candidate.is_file()
                ),
                None,
            )
            if evidence_path is None:
                incomplete.append(check_id)
                continue
            try:
                actual_hash = _sha256(evidence_path)
            except OSError:
                incomplete.append(check_id)
                continue
            if len(expected_hash) != 64 or actual_hash.casefold() != expected_hash:
                invalid.append(f"{check_id}:stale-evidence-hash")

    missing_categories = sorted(set(_REQUIRED_ACCEPTANCE_CATEGORIES) - categories)
    if invalid:
        _add(checks, "acceptance_crosswalk", FAIL, f"Crosswalk has duplicate IDs, unknown categories, failed criteria, or stale DOCX bindings: {sorted(set(invalid))[:8]}.")
    elif incomplete or missing_categories:
        _add(checks, "acceptance_crosswalk", INCOMPLETE, f"Acceptance rows need complete, evidence-backed review: rows={sorted(set(incomplete))[:8]}, missing_categories={missing_categories}.")
    else:
        _add(checks, "acceptance_crosswalk", PASS, f"All {len(rows)} acceptance criteria cover the required categories and are reviewed against DOCX SHA-256 {document_hash}.")


def _check_integrity_audit(
    project_dir: Path,
    project: dict[str, Any],
    document_hash: str | None,
    expected_evidence_ids: set[str],
    checks: list[dict[str, str]],
) -> None:
    qa_reports = project.get("qa_reports")
    audit_value = qa_reports.get("integrity_audit") if isinstance(qa_reports, dict) else None
    audit_path = _resolve(project_dir, audit_value)
    audit = _report_file(project_dir, "integrity_audit_report", audit_path, checks)
    if audit is None:
        return

    audit_status = audit.get("status")
    if audit_status == FAIL:
        _add(checks, "integrity_report_status", FAIL, "Integrity audit overall status is FAIL.")
    elif audit_status not in {PASS, "WARN"}:
        _add(checks, "integrity_report_status", INCOMPLETE, f"Integrity audit status is {audit_status!r}.")

    audit_hash = audit.get("document", {}).get("sha256") if isinstance(audit.get("document"), dict) else None
    if document_hash is None:
        _add(checks, "integrity_document_hash", INCOMPLETE, "Cannot bind integrity audit without the output DOCX.")
    elif not isinstance(audit_hash, str) or not audit_hash:
        _add(checks, "integrity_document_hash", INCOMPLETE, "Integrity audit has no document SHA-256.")
    elif audit_hash.casefold() != document_hash.casefold():
        _add(checks, "integrity_document_hash", FAIL, "Integrity audit refers to a different DOCX hash.")
    else:
        _add(checks, "integrity_document_hash", PASS, "Integrity audit is bound to the current DOCX hash.")

    gates = audit.get("gates")
    if not isinstance(gates, dict) or not gates:
        _add(checks, "integrity_gates", INCOMPLETE, "Integrity audit has no gate results.")
        return
    invalid_gate_statuses = [
        name for name, item in gates.items()
        if not isinstance(item, dict) or item.get("status") not in {PASS, "WARN", FAIL}
    ]
    if invalid_gate_statuses:
        _add(checks, "integrity_gate_statuses", INCOMPLETE, f"Integrity gates have missing or unrecognized statuses: {', '.join(invalid_gate_statuses)}.")
    else:
        _add(checks, "integrity_gate_statuses", PASS, "Every integrity gate has a recognized status.")
    source_gate = gates.get("source_evidence")
    source_status = source_gate.get("status") if isinstance(source_gate, dict) else None
    if source_status == PASS:
        registry_gate = source_gate
        linked_count = registry_gate.get("linked_evidence_id_count")
        verified_count = registry_gate.get("verified_record_count")
        required_count = len(expected_evidence_ids)
        registry_meta = registry_gate.get("registry")
        audited_registry_hash = registry_meta.get("sha256") if isinstance(registry_meta, dict) else None
        # Project/source claims and Word bibliography citations can use different
        # registries. Bind the integrity audit to the registry it actually read,
        # while _check_claim_evidence continues to use evidence_registry_file.
        citation_registry_value = project.get("report_citation_registry_file")
        if not citation_registry_value:
            citation_registry_value = project.get("evidence_registry_file", "evidence.json")
        current_registry_path = _resolve(project_dir, citation_registry_value)
        try:
            current_registry_hash = (
                _sha256(current_registry_path)
                if current_registry_path is not None and current_registry_path.is_file()
                else None
            )
        except OSError:
            current_registry_hash = None
        if not audited_registry_hash or not current_registry_hash:
            _add(checks, "integrity_registry_hash", INCOMPLETE, "Audit and workspace must both identify the evidence registry SHA-256.")
        elif audited_registry_hash.casefold() != current_registry_hash.casefold():
            _add(checks, "integrity_registry_hash", FAIL, "Integrity audit refers to a different evidence registry hash.")
        else:
            _add(checks, "integrity_registry_hash", PASS, "Integrity audit is bound to the current evidence registry.")
        if (
            not isinstance(linked_count, int)
            or isinstance(linked_count, bool)
            or not isinstance(verified_count, int)
            or isinstance(verified_count, bool)
        ):
            _add(checks, "integrity_source_evidence", INCOMPLETE, "Audit does not report linked and verified evidence counts.")
        else:
            citation_gate = gates.get("numeric_citation_bibliography_consistency")
            citation_numbers = citation_gate.get("citation_numbers") if isinstance(citation_gate, dict) else None
            if (
                isinstance(citation_numbers, list)
                and all(type(number) is int and number > 0 for number in citation_numbers)
            ):
                required_citation_count = len(set(citation_numbers))
                coverage_label = "unique in-text citation numbers"
            else:
                # Older reports did not expose citation numbers. Keep their
                # fail-closed check by falling back to mapped project claims.
                required_citation_count = required_count
                coverage_label = "mapped project evidence IDs"
            if linked_count < required_citation_count or verified_count < linked_count:
                _add(
                    checks,
                    "integrity_source_evidence",
                    INCOMPLETE,
                    f"The report has {required_citation_count} {coverage_label}; audit links {linked_count} and records {verified_count} registry records.",
                )
            else:
                _add(
                    checks,
                    "integrity_source_evidence",
                    PASS,
                    f"Integrity source_evidence passed and covers {required_citation_count} {coverage_label}.",
                )
    elif source_status == FAIL:
        _add(checks, "integrity_source_evidence", FAIL, "Integrity source_evidence gate failed.")
    else:
        _add(checks, "integrity_source_evidence", INCOMPLETE, f"Integrity source_evidence gate is {source_status!r}.")

    non_warning_failures = [name for name, item in gates.items() if isinstance(item, dict) and item.get("status") == FAIL]
    if non_warning_failures:
        _add(checks, "integrity_hard_gates", FAIL, f"Failing integrity gates: {', '.join(non_warning_failures)}.")
    else:
        _add(checks, "integrity_hard_gates", PASS, "No integrity gate is marked FAIL.")

    warning_keys: set[tuple[str, int]] = set()
    warning_detail_complete = True
    for gate_name, gate in gates.items():
        if not isinstance(gate, dict) or gate.get("status") != "WARN":
            continue
        findings = gate.get("findings")
        count = gate.get("finding_count")
        if (
            not isinstance(findings, list)
            or not findings
            or not isinstance(count, int)
            or isinstance(count, bool)
            or count != len(findings)
        ):
            warning_detail_complete = False
            continue
        warning_keys.update((gate_name, index) for index in range(1, len(findings) + 1))

    if audit_status == PASS and warning_keys:
        _add(checks, "integrity_report_consistency", FAIL, "Overall audit status is PASS while one or more gates are WARN.")
    elif audit_status == "WARN" and not warning_keys:
        _add(checks, "integrity_report_consistency", FAIL, "Overall audit status is WARN but no gate contains a warning.")
    elif audit_status in {PASS, "WARN"}:
        _add(checks, "integrity_report_consistency", PASS, "Overall audit status matches its warning gates.")

    dispositions_path = _resolve(
        project_dir, project.get("integrity_warning_dispositions_file", "integrity-warning-dispositions.csv")
    )
    dispositions: list[dict[str, str]] = []
    if dispositions_path is not None and dispositions_path.is_file():
        try:
            dispositions = _rows(dispositions_path)
        except (OSError, UnicodeError, csv.Error) as exc:
            _add(checks, "integrity_warning_dispositions", FAIL, f"Cannot read warning dispositions: {exc}")
            return
    elif warning_keys:
        _add(checks, "integrity_warning_dispositions", INCOMPLETE, "Integrity warnings exist but no disposition file is present.")
        return

    mapped: dict[tuple[str, int], dict[str, str]] = {}
    duplicate = False
    for row in dispositions:
        try:
            key = ((row.get("gate") or "").strip(), int((row.get("finding_index") or "").strip()))
        except ValueError:
            continue
        if key in mapped:
            duplicate = True
        mapped[key] = row
    if duplicate:
        _add(checks, "integrity_warning_dispositions", FAIL, "Duplicate gate/finding_index dispositions exist.")
    elif not warning_detail_complete:
        _add(checks, "integrity_warning_dispositions", INCOMPLETE, "The audit warning details are truncated or incomplete.")
    else:
        missing = warning_keys - mapped.keys()
        stale = mapped.keys() - warning_keys
        invalid = []
        for key in warning_keys & mapped.keys():
            row = mapped[key]
            if (row.get("decision") or "").strip().casefold() not in {"accepted", "not_applicable"}:
                invalid.append(key)
            if not all((row.get(field) or "").strip() for field in ("reason", "evidence", "reviewed_by", "review_date")):
                invalid.append(key)
            elif not _valid_iso_date(row["review_date"].strip()):
                invalid.append(key)
        if stale:
            _add(checks, "integrity_warning_dispositions", FAIL, f"Disposition entries do not match current audit warnings: {sorted(stale)}.")
        elif missing or invalid:
            _add(checks, "integrity_warning_dispositions", INCOMPLETE, f"Undispositioned or incomplete warning entries: missing={sorted(missing)}, invalid={sorted(set(invalid))}.")
        else:
            _add(checks, "integrity_warning_dispositions", PASS, "Every integrity warning has a recorded human disposition.")


def assess(project_dir: str | Path) -> dict[str, Any]:
    directory = Path(project_dir).expanduser().resolve()
    project_path = directory / "project.json"
    if not project_path.is_file():
        return {
            "schema_version": 1,
            "project_dir": str(directory),
            "status": FAIL,
            "gates": {
                "word_delivery": {"status": INCOMPLETE, "checks": []},
                "content_and_sources": {"status": INCOMPLETE, "checks": []},
                "submission_readiness": {"status": FAIL, "checks": [
                    {"check": "project_json", "status": FAIL, "detail": "project.json is missing."}
                ]},
            },
        }
    try:
        project = _load_json(project_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return {
            "schema_version": 1,
            "project_dir": str(directory),
            "status": FAIL,
            "gates": {
                "word_delivery": {"status": INCOMPLETE, "checks": []},
                "content_and_sources": {"status": INCOMPLETE, "checks": []},
                "submission_readiness": {"status": FAIL, "checks": [
                    {"check": "project_json", "status": FAIL, "detail": f"Cannot read project.json: {exc}"}
                ]},
            },
        }

    word_gate, _output_path, document_hash = _check_word_delivery(directory, project)
    content_checks: list[dict[str, str]] = []
    _check_requirements(directory, project, content_checks)
    _check_official_rubric_in_docx(directory, project, _output_path, document_hash, content_checks)
    _check_cover_metadata(directory, project, content_checks)
    _check_structure_parity(directory, project, content_checks, _output_path)
    _check_asset_parity(directory, project, content_checks)
    evidence_ids = _check_claim_evidence(directory, project, content_checks)
    _check_acceptance(project, content_checks)
    _check_acceptance_crosswalk(directory, project, document_hash, content_checks)
    _check_integrity_audit(directory, project, document_hash, evidence_ids, content_checks)
    if project.get("content_review_plan_file"):
        from wordassistant.document.report_review import assess_content_review
        content_review = assess_content_review(directory, project)
        _add(content_checks, "project_content_review", content_review["status"],
             "; ".join(item["detail"] for item in content_review["checks"] if item["status"] != PASS)
             or "Subject-specific models and argument/prose reviews are bound to this DOCX.")
    content_status = _final_status(content_checks)
    content_gate = {"status": content_status, "checks": content_checks}

    combined = [
        {"check": "word_delivery", "status": word_gate["status"], "detail": "See word_delivery checks."},
        {"check": "content_and_sources", "status": content_status, "detail": "See content_and_sources checks."},
    ]
    submission_status = _final_status(combined)
    submission_gate = {"status": submission_status, "checks": combined}
    return {
        "schema_version": 1,
        "project_dir": str(directory),
        "output_docx": str(_resolve(directory, project.get("output_docx")) or ""),
        "document_sha256": document_hash,
        "status": submission_status,
        "gates": {
            "word_delivery": word_gate,
            "content_and_sources": content_gate,
            "submission_readiness": submission_gate,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path, help="Course-essay workspace containing project.json")
    args = parser.parse_args(argv)
    report = assess(args.project_dir)
    # Keep the CLI output safe for Windows consoles using legacy code pages.
    # JSON consumers decode these escapes back to the original Unicode text.
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return {PASS: 0, INCOMPLETE: 1, FAIL: 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
