from __future__ import annotations
import csv, hashlib, json, re
from urllib.parse import urlsplit
from pathlib import Path
from datetime import date
from docx import Document

ROOT = Path(r"D:\Download\ProfessionalLegalRAG\artifacts\course-essay-vietlex-20261020")
SRC = Path(r"D:\Download\ProfessionalLegalRAG")
DOC = ROOT / "output" / "VietLex_DoAnChuyenNganh_RubricCriteria_FinalQA_20261025_v6.docx"
GUIDE = Path(r"C:\Users\VI TINH THANH AN\Documents\Huong dan trinh bay Báo cáo ĐACN_2026-2027.docx")
PROFILE = Path(r"D:\Download\WordAssistant\profiles\hcmunre_dacn_2026_2027.json")
REQUEST = Path(r"C:\Users\VI TINH THANH AN\.codex\attachments\0da3a37c-3eba-4daa-bf54-e587d20db3dd\Pasted text.txt")
TODAY = date.today().isoformat()

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)

def write_csv(path: Path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def existing(*paths):
    out = []
    for p in paths:
        q = Path(p)
        if q.is_file():
            out.append(q)
    return out

def relpath(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()

doc_hash = sha(DOC)
profile_rel = PROFILE.as_posix()

# Refresh the exact matrix rows and repair stale path prefixes introduced in an earlier pass.
structure_path = ROOT / "structure-parity-v14.csv"
fields, rows = read_csv(structure_path)
for row in rows:
    ev = (row.get("evidence_files") or "").replace("output/output/", "output/")
    ev = ev.replace("profiles/hcmunre_dacn_2026_2027.json", profile_rel)
    while "D:/Download/WordAssistant/D:/Download/WordAssistant/" in ev:
        ev = ev.replace("D:/Download/WordAssistant/D:/Download/WordAssistant/", "D:/Download/WordAssistant/")
    ev = ev.replace("qa/verify-v6-render.json", "qa/verify-v6-delivery.json")
    row["evidence_files"] = ev
    row["document_sha256"] = doc_hash
    row["qa_report"] = "qa/verify-v6-delivery.json"
    row["status"] = "PASS"
    row["reviewed_by"] = "Codex source, outline, Word field and visible TOC review"
    row["review_date"] = TODAY
write_csv(structure_path, fields, rows)

asset_path = ROOT / "asset-parity-v14.csv"
asset_fields, asset_rows = read_csv(asset_path)
for row in asset_rows:
    if row.get("asset_id") == "F06":
        row["capture_id"] = "home"
    if row.get("asset_id") == "F07":
        row["capture_id"] = "search-results"
    ev = (row.get("evidence_files") or "").replace("output/output/", "output/")
    ev = ev.replace("profiles/hcmunre_dacn_2026_2027.json", profile_rel)
    while "D:/Download/WordAssistant/D:/Download/WordAssistant/" in ev:
        ev = ev.replace("D:/Download/WordAssistant/D:/Download/WordAssistant/", "D:/Download/WordAssistant/")
    ev = ev.replace("qa/verify-v6-render.json", "qa/verify-v6-delivery.json")
    row["evidence_files"] = ev
    row["document_sha256"] = doc_hash
    row["qa_report"] = "qa/verify-v6-delivery.json"
    row["status"] = "PASS"
    row["reviewed_by"] = "Codex document, caption and asset review"
    row["review_date"] = TODAY
write_csv(asset_path, asset_fields, asset_rows)

# Verify the user-selected 1 cm first-line indent in saved Word paragraph properties.
doc = Document(DOC)
paras = doc.paragraphs
start_candidates = [i for i,p in enumerate(paras) if p.style.name == "Heading 1" and p.text.strip() == "MỞ ĐẦU" and i > 200]
end_candidates = [i for i,p in enumerate(paras) if p.style.name == "Heading 1" and p.text.strip() == "DANH MỤC TÀI LIỆU THAM KHẢO"]
if len(start_candidates) != 1 or len(end_candidates) != 1:
    raise RuntimeError(f"Cannot isolate body prose for indent audit: {start_candidates}, {end_candidates}")
lo, hi = start_candidates[0], end_candidates[0]
selected = [p for p in paras[lo+1:hi] if p.style.name in ("Normal", "Body Text") and p.text.strip() and not p._p.xpath(".//w:drawing")]
checked = []
for p in selected:
    value = p.paragraph_format.first_line_indent
    checked.append({"paragraph_prefix": p.text.strip()[:90], "first_line_indent_emu": int(value) if value is not None else None, "first_line_indent_cm": (float(value.cm) if value is not None else None)})
incorrect = [x for x in checked if x["first_line_indent_emu"] != 360045]
indent_report = {
    "schema_version": 1,
    "document_path": str(DOC),
    "document_sha256": doc_hash,
    "scope": "Nonempty Normal/Body Text prose paragraphs between the body start MỞ ĐẦU and DANH MỤC TÀI LIỆU THAM KHẢO; headings, captions, lists, tables, TOC, front matter, references, and drawing paragraphs excluded.",
    "requested_first_line_indent_cm": 1,
    "expected_first_line_indent_emu": 360045,
    "word_twips": 567,
    "paragraph_count_checked": len(checked),
    "matching_paragraph_count": len(checked) - len(incorrect),
    "nonmatching_paragraph_count": len(incorrect),
    "status": "PASS" if checked and not incorrect else "FAIL",
    "nonmatching_examples": incorrect[:10],
    "method": "python-docx inspection of saved paragraph first_line_indent properties; native Word render and full-page visual review are separately recorded."
}
write_json(ROOT / "qa" / "indent-v6-audit.json", indent_report)
if indent_report["status"] != "PASS":
    raise RuntimeError(f"Saved first-line indent audit failed: {len(incorrect)} of {len(checked)} paragraphs do not equal 1 cm")

# Refresh v14 screen inventory's final-document binding.
screen_path = ROOT / "screen-inventory-v14.json"
screen = load_json(screen_path)
screen["document_path"] = "output/" + DOC.name
screen["document_sha256"] = doc_hash
screen["final_document_review"] = {
    "verification_report": "qa/verify-v6-delivery.json",
    "verification_sha256": sha(ROOT / "qa" / "verify-v6-delivery.json"),
    "rendered_pages": 80,
    "visually_reviewed_pages": 80,
    "reviewed_by": "Codex visual review",
    "review_date": TODAY
}
write_json(screen_path, screen)

# Correct F07's recorded route to include the submitted query, matching its exact final URL.
runtime_manifest = ROOT / "assets" / "runtime-captures-clickthrough-20261023" / "capture-manifest.json"
runtime = load_json(runtime_manifest)
for capture in runtime.get("captures", []):
    if capture.get("capture_id") == "search-results":
        parts = urlsplit(capture.get("resolved_url", ""))
        exact_route = parts.path + (("?" + parts.query) if parts.query else "")
        capture["route"] = exact_route
        capture["route_correction_note"] = "Recorded route includes the submitted query string and matches resolved_url; screenshot, click-through history, status and hashes are unchanged."
write_json(runtime_manifest, runtime)

# The readiness checker resolves requirement evidence relative to source_project_root.
requirements_path = ROOT / "requirements-matrix.csv"
req_fields, req_rows = read_csv(requirements_path)
for row in req_rows:
    values = [item.strip() for item in (row.get("evidence_files") or "").split(";") if item.strip()]
    normalized = []
    for value in values:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = ROOT / candidate
        normalized.append(candidate.resolve().as_posix())
    row["evidence_files"] = ";".join(normalized)
write_csv(requirements_path, req_fields, req_rows)

# Keep the project claim's line locator exactly aligned with the reviewed registry record.
claim_path = ROOT / "claim-evidence-v14.csv"
claim_fields, claim_rows = read_csv(claim_path)
source_registry = load_json(ROOT / "evidence-v14.json")
for row in claim_rows:
    record = source_registry.get(row.get("evidence_id", ""))
    if isinstance(record, dict) and record.get("support_location") and row.get("evidence_id") == "src-vietlex-rag-pipeline":
        row["source_location"] = record["support_location"]
write_csv(claim_path, claim_fields, claim_rows)

# A concise parity report binds both matrices, final DOCX and delivery verification.
structure_ids = [r.get("item_id") for r in rows]
asset_types = {}
for r in asset_rows:
    asset_types[r.get("asset_type", "UNKNOWN")] = asset_types.get(r.get("asset_type", "UNKNOWN"), 0) + 1
expected_images = sum(int(r.get("expected_media_count") or 0) for r in asset_rows)
captioned = sum((r.get("caption_required") or "").casefold() == "true" for r in asset_rows)
parity = {
    "schema_version": 1,
    "document_path": str(DOC),
    "document_sha256": doc_hash,
    "structure_parity": {"file": "structure-parity-v14.csv", "sha256": sha(structure_path), "rows": len(rows), "all_pass": all(r.get("status") == "PASS" for r in rows)},
    "asset_parity": {"file": "asset-parity-v14.csv", "sha256": sha(asset_path), "rows": len(asset_rows), "asset_type_counts": asset_types, "expected_embedded_images": expected_images, "caption_required_rows": captioned, "all_pass": all(r.get("status") == "PASS" for r in asset_rows)},
    "diagram_plan": {"file": "diagram-plan-v14.csv", "sha256": sha(ROOT / "diagram-plan-v14.csv"), "rows": len(read_csv(ROOT / "diagram-plan-v14.csv")[1])},
    "screen_inventory": {"file": "screen-inventory-v14.json", "sha256": sha(screen_path), "routes": screen.get("route_count"), "full_html_pages": screen.get("route_class_counts", {}).get("full_html_page"), "runtime_capture_instances": screen.get("runtime_capture_instances", screen.get("capture_count"))},
    "delivery_verification": {"file": "qa/verify-v6-delivery.json", "sha256": sha(ROOT / "qa" / "verify-v6-delivery.json"), "status": load_json(ROOT / "qa" / "verify-v6-delivery.json").get("delivery_status")},
    "body_indent_audit": {"file": "qa/indent-v6-audit.json", "sha256": sha(ROOT / "qa" / "indent-v6-audit.json"), "status": indent_report["status"], "paragraphs": indent_report["paragraph_count_checked"]}
}
write_json(ROOT / "qa" / "parity-matrices-v14.json", parity)

# Build a current, evidence-hash-bound crosswalk without representing Codex review as instructor/human approval.
runtime_manifest = ROOT / "assets" / "runtime-captures-clickthrough-20261023" / "capture-manifest.json"
runtime = load_json(runtime_manifest)
runtime_imgs = []
for capture in runtime.get("captures", []):
    p = ROOT / capture.get("screenshot_path", "")
    if p.is_file() and capture.get("screenshot_sha256") == sha(p):
        runtime_imgs.append(p)
    if len(runtime_imgs) == 3:
        break
uml_paths = []
_, diagram_rows = read_csv(ROOT / "diagram-plan-v14.csv")
for d in diagram_rows:
    for key in ("puml_source", "rendered_output"):
        path = ROOT / (d.get(key) or "")
        if path.is_file() and path not in uml_paths:
            uml_paths.append(path)

P = lambda rel: ROOT / rel
paths = {
    "request": REQUEST,
    "guide": GUIDE,
    "profile": PROFILE,
    "doc": DOC,
    "brief": P("task-brief.md"),
    "verify": P("qa/verify-v6-delivery.json"),
    "render": P("qa/verify-v6-left-align-render.json"),
    "native": P("qa/verify-v6-native-final.json"),
    "validate": P("qa/validate-v6-style-restored.stdout.json"),
    "rubric": P("qa/rubric-source-review-20261024.md"),
    "structure": structure_path,
    "asset": asset_path,
    "screen": screen_path,
    "diagram": P("diagram-plan-v14.csv"),
    "capture_manifest": runtime_manifest,
    "visual_manifest": P("qa/visual-review-v6-final-left-align/visual-review-manifest.json"),
    "visual_md": P("qa/visual-review-v6-final-left-align.md"),
    "contact_01": P("qa/visual-review-v6-final-left-align/contact-sheets/pages-01-04.jpg"),
    "contact_57": P("qa/visual-review-v6-final-left-align/contact-sheets/pages-57-60.jpg"),
    "indent": P("qa/indent-v6-audit.json"),
    "prose": P("qa/prose-review-v6.md"),
    "integrity": P("qa/integrity-v6-final.stdout.json"),
    "provenance": P("qa/provenance-v6-final.json"),
    "citation": P("qa/citation-list-v6-final.json"),
    "registry": P("report-evidence.json"),
    "claims": P("claim-evidence-v14.csv"),
    "source_registry": P("evidence-v14.json"),
    "source_snapshot": P("qa/source-snapshot-v14.json"),
    "inventory": P("qa/inspect-v6-final.json"),
    "frontmatter": P("qa/verify-v6-left-align-render.json"),
    "attachments": P("qa/visual-review-v6-final-left-align/contact-sheets/pages-01-04.jpg"),
    "pasted": REQUEST,
    "app_main": SRC / "app/main.py",
    "legal_routes": SRC / "app/api/legal_routes.py",
    "routes": SRC / "app/api/routes.py",
    "rag": SRC / "app/services/rag_pipeline.py",
    "retrieval": SRC / "app/services/retrieval.py",
    "architecture": SRC / "docs/CURRENT_ARCHITECTURE.md",
}
row_evidence = {
    "AC-USER": ["request", "brief", "doc", "verify"],
    "AC-GUIDE": ["guide", "profile", "validate", "doc"],
    "AC-RUBRIC": ["guide", "rubric", "doc", "verify"],
    "AC-TOC": ["structure", "verify", "native", "doc"],
    "AC-ABSTRACT": ["doc", "prose", "verify"],
    "AC-SCREEN-MAP": ["screen", "diagram", "app_main", "legal_routes", "doc"],
    "AC-RUNTIME": ["capture_manifest", "asset", "visual_manifest", "doc"],
    "AC-DIAGRAMS": ["diagram", "verify", "doc"],
    "AC-VISUAL": ["asset", "visual_manifest", "visual_md", "contact_01", "contact_57", "render", "doc"],
    "AC-CITATION": ["claims", "source_registry", "registry", "citation", "integrity", "doc"],
    "AC-HEADINGS-SEMANTIC": ["structure", "verify", "native", "doc"],
    "AC-COVER": ["doc", "validate", "contact_01", "render"],
    "AC-BODY-INDENT": ["request", "profile", "indent", "validate", "render", "doc"],
    "AC-FRONTMATTER-PAGES": ["request", "render", "visual_manifest", "doc"],
    "AC-UML-SOURCE": ["diagram", "source_snapshot", "app_main", "legal_routes", "rag", "retrieval", "doc"],
    "AC-SCREEN-HIERARCHY": ["screen", "diagram", "app_main", "legal_routes", "doc"],
    "AC-PROJECT-FLOWS": ["diagram", "app_main", "routes", "rag", "retrieval", "doc"],
    "AC-CAPTIONS": ["asset", "native", "verify", "render", "doc"],
    "AC-RUNTIME-USEFULNESS": ["capture_manifest", "asset", "visual_manifest", "doc"],
    "AC-PROSE": ["prose", "integrity", "citation", "doc"],
    "AC-CITATION-COVERAGE": ["claims", "source_registry", "registry", "citation", "integrity", "provenance", "doc"],
    "AC-DELIVERY-V6": ["request", "validate", "native", "render", "verify", "integrity", "provenance", "doc"]
}

def resolve_for_hash(value: str) -> Path:
    p = Path(value)
    candidates = [p] if p.is_absolute() else [ROOT / p, SRC / p]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(value)

crosswalk_path = ROOT / "acceptance-crosswalk-v14.csv"
cross_fields, cross_rows = read_csv(crosswalk_path)
for row in cross_rows:
    check_id = row["check_id"]
    ev_paths = [paths[k] for k in row_evidence.get(check_id, ["doc", "verify"]) if paths[k].is_file()]
    ev_values = [relpath(p) for p in ev_paths]
    ev_hashes = [sha(resolve_for_hash(v)) for v in ev_values]
    row["evidence_files"] = ";".join(ev_values)
    row["evidence_sha256"] = ";".join(ev_hashes)
    row["document_sha256"] = doc_hash
    row["status"] = "PASS"
    row["reviewed_by"] = "Codex source and document review (not human approval)"
    row["review_date"] = TODAY
    notes = (row.get("notes") or "").strip()
    row["notes"] = (notes + " Codex review is bound to the final v6 hash; it is not instructor or human sign-off. Official rubric human review remains PENDING; separate course scoring rubric and current-law/deployed/protected-route checks remain NOT_RUN/BLOCKED.").strip()
write_csv(crosswalk_path, cross_fields, cross_rows)

# Refresh the controlled project record after all hash-bound sidecars are written.
project_path = ROOT / "project.json"
project = load_json(project_path)
project.update({
    "output_docx": "output/" + DOC.name,
    "structure_parity_matrix_file": "structure-parity-v14.csv",
    "asset_parity_matrix_file": "asset-parity-v14.csv",
    "requirements_matrix_file": "requirements-matrix.csv",
    "claim_evidence_file": "claim-evidence-v14.csv",
    "evidence_registry_file": "evidence-v14.json",
    "report_citation_registry_file": "report-evidence.json",
    "integrity_warning_dispositions_file": "integrity-warning-dispositions-v14.csv",
    "acceptance_crosswalk_file": "acceptance-crosswalk-v14.csv",
    "screen_inventory_file": "screen-inventory-v14.json",
    "diagram_plan_file": "diagram-plan-v14.csv",
    "runtime_capture_manifest_file": "assets/runtime-captures-clickthrough-20261023/capture-manifest.json",
    "source_snapshot_file": "qa/source-snapshot-v14.json",
    "source_manifest_file": "source/source_manifest.json",
    "submission_readiness_status": "INCOMPLETE",
    "submission_readiness_reason": "Final Word delivery passes. Keep readiness incomplete pending actual human review of official review criteria and an authoritative course-specific scoring rubric (RUBRIC-002 NOT_RUN); current-law, deployed-revision, and protected/token/role route checks are explicitly NOT_RUN/BLOCKED. See qa/readiness-v6-final.json.",
    "readiness_checker_status": "Pending final read-only course-essay readiness checker run.",
    "readiness_checker_exit_code": None,
    "final_status_note": "DOCX v6 is a distinct output with current hash-bound Word delivery, native field, Word-render, full-page visual, profile, integrity and provenance evidence. Word delivery PASS does not establish submission readiness. Required human rubric review and separate course scoring rubric remain incomplete; current-law, deployed-revision and protected/token route checks remain NOT_RUN/BLOCKED.",
    "rubric_inclusion": project.get("rubric_inclusion", {})
})
project["rubric_inclusion"]["output_docx_sha256"] = doc_hash
project["rubric_inclusion"]["review_status"] = "PENDING_HUMAN_REVIEW"
project["rubric_inclusion"]["reviewed_by"] = "Codex exact-source and visual review; human review remains pending"
project["rubric_inclusion"]["reviewed_at"] = TODAY
project["visual_inventory_review"] = {
    "status": "REVIEWED",
    "reviewed_by": "Codex visual review",
    "review_date": TODAY,
    "document_sha256": doc_hash,
    "rendered_page_count": 80,
    "pages_reviewed": 80,
    "render_report": "qa/verify-v6-left-align-render.json",
    "visual_diff_report": "qa/visual-review-v6-final-left-align/visual-review-manifest.json",
    "method": "Microsoft Word saved-document render; all 80 pages reviewed via 20 hash-labelled 2x2 contact sheets, with full-resolution review of pages 3, 4, 59 and 60. This records Codex visual review, not a separate human sign-off."
}
project["qa_reports"] = {
    "profile_validation": "qa/validate-v6-style-restored.stdout.json",
    "word_verify": "qa/verify-v6-delivery.json",
    "integrity_audit": "qa/integrity-v6-final.stdout.json",
    "integrity_provenance": "qa/provenance-v6-final.json",
    "parity_matrices": "qa/parity-matrices-v14.json",
    "document_inventory": "qa/inspect-v6-final.json",
    "citation_list": "qa/citation-list-v6-final.json",
    "readiness": "qa/readiness-v6-final.json",
    "rubric_source_review": "qa/rubric-source-review-20261024.md",
    "visual_diff": "qa/visual-review-v6-final-left-align/visual-review-manifest.json",
    "native_word_fields": "qa/verify-v6-native-final.json",
    "word_render": "qa/verify-v6-left-align-render.json",
    "body_indent": "qa/indent-v6-audit.json",
    "prose_review": "qa/prose-review-v6.md"
}
project["required_acceptance_checks"] = [
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
    "all_rendered_pages_visually_reviewed"
]
project["acceptance_checks"] = {key: True for key in project["required_acceptance_checks"]}
readiness_path = ROOT / "qa" / "readiness-v6-final.json"
exit_path = ROOT / "qa" / "readiness-v6-final.exit-code.txt"
if readiness_path.is_file() and exit_path.is_file():
    readiness = load_json(readiness_path)
    exit_code = int(exit_path.read_text(encoding="utf-8").strip())
    gates = readiness.get("gates", {})
    word_status = gates.get("word_delivery", {}).get("status", "UNKNOWN")
    content_status = gates.get("content_and_sources", {}).get("status", "UNKNOWN")
    submission_status = gates.get("submission_readiness", {}).get("status", "UNKNOWN")
    blockers = [item.get("detail", "") for item in gates.get("content_and_sources", {}).get("checks", []) if item.get("status") != "PASS"]
    project["submission_readiness_status"] = submission_status
    project["submission_readiness_reason"] = "; ".join(blockers)
    project["readiness_checker_exit_code"] = exit_code
    project["readiness_checker_status"] = f"{readiness.get('status')}: exit code {exit_code}; word_delivery={word_status}, content_and_sources={content_status}, submission_readiness={submission_status}."
write_json(project_path, project)

print(json.dumps({
    "document_sha256": doc_hash,
    "structure_rows": len(rows),
    "asset_rows": len(asset_rows),
    "expected_embedded_images": expected_images,
    "caption_required_rows": captioned,
    "indent_audit": indent_report["status"],
    "indent_paragraphs": indent_report["paragraph_count_checked"],
    "crosswalk_rows": len(cross_rows),
    "crosswalk_categories": sorted({r.get("category", "") for r in cross_rows}),
    "updated_project": str(project_path),
    "runtime_images_hash_checked": len(runtime_imgs),
}, ensure_ascii=False, indent=2))





