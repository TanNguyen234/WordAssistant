#!/usr/bin/env python3
"""Read-only, fail-closed readiness check for a course-essay workspace."""

from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


PASS = "PASS"
INCOMPLETE = "INCOMPLETE"
FAIL = "FAIL"
_VALID_ROW_STATUSES = {PASS, "WAIVED", "NOT_RUN", "BLOCKED", FAIL}
_REQUIRED_ACCEPTANCE_CHECKS = (
    "assignment_and_rubric_checked",
    "cover_metadata_fields_verified",
    "strongwine_structure_parity_reviewed",
    "strongwine_asset_parity_reviewed",
    "all_required_claims_mapped_to_reviewed_evidence",
    "all_integrity_warnings_reviewed_and_dispositioned",
    "source_routes_and_templates_checked",
    "wireframes_and_runtime_captures_distinguished",
    "figure_list_rebuilt_from_captions",
    "word_fields_updated_and_saved",
    "all_rendered_pages_visually_reviewed",
)
_STRONGWINE_STRUCTURE_BASELINE = (
    Path(__file__).resolve().parents[1] / "docs" / "strongwine-course-essay-structure-baseline.csv"
)
_STRONGWINE_STRUCTURE_BASELINE_SHA256 = "d9ca607623378dac0d9e5b8f065748406b74a636e93ec059baa131723569bd33"
_STRONGWINE_ASSET_BASELINE = (
    Path(__file__).resolve().parents[1] / "docs" / "strongwine-course-essay-asset-baseline.csv"
)
_STRONGWINE_ASSET_BASELINE_SHA256 = "68424c135917a2814a4c893a4bb3b9ce0f12d1626bbf12090bf92ea6d9a5d04a"
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
    baseline_path = _STRONGWINE_STRUCTURE_BASELINE
    if not baseline_path.is_file():
        _add(checks, "strongwine_structure_parity", FAIL, f"Canonical StrongWine structure baseline is missing: {baseline_path}.")
        return
    try:
        baseline_hash = _sha256(baseline_path)
        baseline_rows = _rows(baseline_path)
    except (OSError, UnicodeError, csv.Error) as exc:
        _add(checks, "strongwine_structure_parity", FAIL, f"Cannot read the canonical structure baseline: {exc}")
        return
    if baseline_hash.casefold() != _STRONGWINE_STRUCTURE_BASELINE_SHA256:
        _add(checks, "strongwine_structure_parity", FAIL, "Canonical StrongWine structure baseline hash changed; update the baseline and checker together after review.")
        return

    baseline_by_id: dict[str, dict[str, str]] = {}
    for row in baseline_rows:
        reference_id = (row.get("reference_id") or "").strip()
        if not reference_id or reference_id in baseline_by_id:
            _add(checks, "strongwine_structure_parity", FAIL, "Canonical structure baseline has a blank or duplicate reference_id.")
            return
        if not (row.get("reference_heading") or "").strip() or not (row.get("reference_level") or "").strip():
            _add(checks, "strongwine_structure_parity", FAIL, f"Canonical baseline row {reference_id} is missing its heading or level.")
            return
        baseline_by_id[reference_id] = row
    if not baseline_by_id:
        _add(checks, "strongwine_structure_parity", FAIL, "Canonical StrongWine structure baseline contains no headings.")
        return

    matrix_path = _resolve(project_dir, project.get("structure_parity_matrix_file", "structure-parity.csv"))
    if matrix_path is None or not matrix_path.is_file():
        _add(checks, "strongwine_structure_parity", INCOMPLETE, "structure-parity.csv is missing.")
        return
    try:
        rows = _rows(matrix_path)
    except (OSError, UnicodeError, csv.Error) as exc:
        _add(checks, "strongwine_structure_parity", FAIL, f"Cannot read structure-parity.csv: {exc}")
        return
    if not rows:
        _add(checks, "strongwine_structure_parity", INCOMPLETE, "structure-parity.csv has no mapped headings.")
        return

    mapped: dict[str, dict[str, str]] = {}
    duplicate_ids: set[str] = set()
    for row in rows:
        reference_id = (row.get("reference_id") or "").strip()
        if not reference_id:
            continue
        if reference_id in mapped:
            duplicate_ids.add(reference_id)
        mapped[reference_id] = row
    unknown_ids = mapped.keys() - baseline_by_id.keys()
    if duplicate_ids or unknown_ids:
        _add(checks, "strongwine_structure_parity", FAIL, f"Structure map has duplicate IDs {sorted(duplicate_ids)} or IDs outside the baseline {sorted(unknown_ids)}.")
        return
    missing_ids = baseline_by_id.keys() - mapped.keys()
    if missing_ids:
        _add(checks, "strongwine_structure_parity", INCOMPLETE, f"Structure map is missing {len(missing_ids)} of {len(baseline_by_id)} StrongWine headings; first missing IDs: {sorted(missing_ids)[:8]}.")
        return

    source_root = _resolve(project_dir, project.get("source_project_root")) or project_dir
    incomplete: list[str] = []
    invalid: list[str] = []
    for expected_order, (reference_id, baseline) in enumerate(baseline_by_id.items(), start=1):
        row = mapped[reference_id]
        if (
            (row.get("reference_heading") or "").strip() != baseline["reference_heading"].strip()
            or (row.get("reference_level") or "").strip() != baseline["reference_level"].strip()
        ):
            invalid.append(reference_id)
            continue
        decision = (row.get("decision") or "").strip().upper()
        status = (row.get("status") or "").strip().upper()
        target_heading = (row.get("target_heading") or "").strip()
        target_level_raw = (row.get("target_level") or "").strip()
        target_order_raw = (row.get("target_order") or "").strip()
        coverage_note = (row.get("coverage_note") or "").strip()
        evidence_values = [item.strip() for item in (row.get("evidence_files") or "").split(";") if item.strip()]
        reviewer = (row.get("reviewed_by") or "").strip()
        review_date = (row.get("review_date") or "").strip()
        if decision in {"OMIT", "NOT_APPLICABLE", "SKIP"} or status == FAIL:
            invalid.append(reference_id)
            continue
        if not target_level_raw or not target_order_raw:
            incomplete.append(reference_id)
            continue
        try:
            target_level = int(target_level_raw)
            target_order = int(target_order_raw)
        except ValueError:
            incomplete.append(reference_id)
            continue
        if target_level != int(baseline["reference_level"]) or target_order != expected_order:
            invalid.append(reference_id)
            continue
        if decision not in _STRUCTURE_DECISIONS or status != PASS or not target_heading or not coverage_note or not evidence_values or not reviewer or not _valid_iso_date(review_date):
            incomplete.append(reference_id)
            continue
        missing_evidence = []
        for evidence in evidence_values:
            candidates = (_resolve(project_dir, evidence), _resolve(source_root, evidence))
            if not any(candidate is not None and candidate.is_file() for candidate in candidates):
                missing_evidence.append(evidence)
        if missing_evidence:
            incomplete.append(reference_id)

    if invalid:
        _add(checks, "strongwine_structure_parity", FAIL, f"Some mapped sections were omitted, changed from the baseline, or marked failed: {sorted(invalid)[:8]}.")
    elif incomplete:
        _add(checks, "strongwine_structure_parity", INCOMPLETE, f"{len(incomplete)} StrongWine sections lack a complete, evidence-backed target mapping; first IDs: {sorted(incomplete)[:8]}.")
    else:
        _add(checks, "strongwine_structure_parity", PASS, f"All {len(baseline_by_id)} StrongWine headings map to reviewed, evidence-backed target sections.")
        if output_path is None or not output_path.is_file():
            _add(checks, "strongwine_structure_in_docx", INCOMPLETE, "The final DOCX is missing; its actual heading outline cannot be checked.")
            return
        try:
            from docx import Document
            from wordassistant.selectors import _heading_level

            document = Document(output_path)
            outline = [
                (paragraph.text, _heading_level(paragraph))
                for paragraph in document.paragraphs
                if paragraph.text.strip() and _heading_level(paragraph) is not None
            ]
        except Exception as exc:
            _add(checks, "strongwine_structure_in_docx", FAIL, f"Cannot inspect the final DOCX heading outline: {exc}")
            return

        actual = [
            (" ".join(str(title).split()).casefold(), level)
            for title, level in outline
        ]
        cursor = 0
        missing_targets: list[str] = []
        for reference_id, _baseline in baseline_by_id.items():
            row = mapped[reference_id]
            expected_title = " ".join(row["target_heading"].split()).casefold()
            expected_level = int(row["target_level"])
            found = next(
                (
                    index
                    for index in range(cursor, len(actual))
                    if actual[index] == (expected_title, expected_level)
                ),
                None,
            )
            if found is None:
                missing_targets.append(reference_id)
            else:
                cursor = found + 1
        if missing_targets:
            _add(checks, "strongwine_structure_in_docx", FAIL, f"The final DOCX outline is missing, mis-leveling, or reordering mapped headings; first reference IDs: {missing_targets[:8]}.")
        else:
            _add(checks, "strongwine_structure_in_docx", PASS, f"All {len(baseline_by_id)} mapped headings appear in the final DOCX outline at the required levels and in order.")


def _check_asset_parity(project_dir: Path, project: dict[str, Any], checks: list[dict[str, str]]) -> None:
    baseline_path = _STRONGWINE_ASSET_BASELINE
    if not baseline_path.is_file():
        _add(checks, "strongwine_asset_parity", FAIL, f"Canonical StrongWine asset baseline is missing: {baseline_path}.")
        return
    try:
        baseline_hash = _sha256(baseline_path)
        baseline_rows = _rows(baseline_path)
    except (OSError, UnicodeError, csv.Error) as exc:
        _add(checks, "strongwine_asset_parity", FAIL, f"Cannot read the canonical asset baseline: {exc}")
        return
    if baseline_hash.casefold() != _STRONGWINE_ASSET_BASELINE_SHA256:
        _add(checks, "strongwine_asset_parity", FAIL, "Canonical StrongWine asset baseline hash changed; update the baseline and checker together after review.")
        return

    baseline_by_id: dict[str, dict[str, str]] = {}
    for row in baseline_rows:
        reference_id = (row.get("reference_id") or "").strip()
        if not reference_id or reference_id in baseline_by_id:
            _add(checks, "strongwine_asset_parity", FAIL, "Canonical asset baseline has a blank or duplicate reference_id.")
            return
        baseline_by_id[reference_id] = row
    if not baseline_by_id:
        _add(checks, "strongwine_asset_parity", FAIL, "Canonical StrongWine asset baseline contains no image or table entries.")
        return

    matrix_path = _resolve(project_dir, project.get("asset_parity_matrix_file", "asset-parity.csv"))
    if matrix_path is None or not matrix_path.is_file():
        _add(checks, "strongwine_asset_parity", INCOMPLETE, "asset-parity.csv is missing.")
        return
    try:
        rows = _rows(matrix_path)
    except (OSError, UnicodeError, csv.Error) as exc:
        _add(checks, "strongwine_asset_parity", FAIL, f"Cannot read asset-parity.csv: {exc}")
        return
    if not rows:
        _add(checks, "strongwine_asset_parity", INCOMPLETE, "asset-parity.csv has no mapped images or tables.")
        return

    mapped: dict[str, dict[str, str]] = {}
    duplicate_ids: set[str] = set()
    for row in rows:
        reference_id = (row.get("reference_id") or "").strip()
        if not reference_id:
            continue
        if reference_id in mapped:
            duplicate_ids.add(reference_id)
        mapped[reference_id] = row
    unknown_ids = mapped.keys() - baseline_by_id.keys()
    if duplicate_ids or unknown_ids:
        _add(checks, "strongwine_asset_parity", FAIL, f"Asset map has duplicate IDs {sorted(duplicate_ids)} or IDs outside the baseline {sorted(unknown_ids)}.")
        return
    missing_ids = baseline_by_id.keys() - mapped.keys()
    if missing_ids:
        _add(checks, "strongwine_asset_parity", INCOMPLETE, f"Asset map is missing {len(missing_ids)} of {len(baseline_by_id)} StrongWine images/tables; first missing IDs: {sorted(missing_ids)[:8]}.")
        return

    source_root = _resolve(project_dir, project.get("source_project_root")) or project_dir
    incomplete: list[str] = []
    invalid: list[str] = []
    for reference_id, baseline in baseline_by_id.items():
        row = mapped[reference_id]
        fixed_fields = ("item_type", "reference_index", "reference_caption", "reference_description")
        if any((row.get(field) or "").strip() != (baseline.get(field) or "").strip() for field in fixed_fields):
            invalid.append(reference_id)
            continue
        decision = (row.get("decision") or "").strip().upper()
        status = (row.get("status") or "").strip().upper()
        target_section = (row.get("target_section") or "").strip()
        target_caption = (row.get("target_caption") or "").strip()
        coverage_note = (row.get("coverage_note") or "").strip()
        evidence_values = [item.strip() for item in (row.get("evidence_files") or "").split(";") if item.strip()]
        reviewer = (row.get("reviewed_by") or "").strip()
        review_date = (row.get("review_date") or "").strip()
        if decision in {"OMIT", "NOT_APPLICABLE", "SKIP"} or status == FAIL:
            invalid.append(reference_id)
            continue
        if decision not in _STRUCTURE_DECISIONS or status != PASS or not target_section or not target_caption or not coverage_note or not evidence_values or not reviewer or not _valid_iso_date(review_date):
            incomplete.append(reference_id)
            continue
        if any(
            not any(
                candidate is not None and candidate.is_file()
                for candidate in (_resolve(project_dir, evidence), _resolve(source_root, evidence))
            )
            for evidence in evidence_values
        ):
            incomplete.append(reference_id)

    if invalid:
        _add(checks, "strongwine_asset_parity", FAIL, f"Some reference image/table slots were omitted, altered, or marked failed: {sorted(invalid)[:8]}.")
    elif incomplete:
        _add(checks, "strongwine_asset_parity", INCOMPLETE, f"{len(incomplete)} of {len(baseline_by_id)} StrongWine image/table slots lack a complete, evidence-backed target equivalent; first IDs: {sorted(incomplete)[:8]}.")
    else:
        _add(checks, "strongwine_asset_parity", PASS, f"All {len(baseline_by_id)} StrongWine image/table slots map to reviewed, evidence-backed target equivalents.")


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
    _check_cover_metadata(directory, project, content_checks)
    _check_structure_parity(directory, project, content_checks, _output_path)
    _check_asset_parity(directory, project, content_checks)
    evidence_ids = _check_claim_evidence(directory, project, content_checks)
    _check_acceptance(project, content_checks)
    _check_integrity_audit(directory, project, document_hash, evidence_ids, content_checks)
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
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return {PASS: 0, INCOMPLETE: 1, FAIL: 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
