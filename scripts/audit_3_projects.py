"""Comprehensive Text Audit Runner for the 3 Newest WordAssistant Projects."""

import sys
import os
import json
import time
from pathlib import Path

# Ensure utf-8 output in Windows terminal
sys.stdout.reconfigure(encoding='utf-8')

# Ensure viet-text-audit and WordAssistant are discoverable
sys.path.insert(0, r"D:\Download\viet-text-audit\src")
sys.path.insert(0, r"D:\Download\WordAssistant\src")

from wordassistant.document.integrity import audit_integrity

PROJECTS = [
    {
        "name": "StrongWine",
        "description": "Báo cáo Tiểu luận Hệ thống Bán rượu Vang StrongWine (Spring Boot)",
        "docx": Path(r"D:\Download\WordAssistant\artifacts\course-essay\strongwine-revision-20261027\output\StrongWine_20261102_academic_standardized.docx"),
        "evidence": Path(r"D:\Download\WordAssistant\artifacts\course-essay\strongwine-revision-20261027\evidence.json"),
        "corpus": Path(r"D:\Download\WordAssistant\artifacts\course-essay\strongwine-revision-20261027\sources"),
        "qa_dir": Path(r"D:\Download\WordAssistant\artifacts\course-essay\strongwine-revision-20261027\qa"),
    },
    {
        "name": "VietLex",
        "description": "Đồ án Chuyên ngành Hệ thống Tra cứu Pháp luật Việt Nam VietLex RAG",
        "docx": Path(r"D:\Download\WordAssistant\artifacts\course-essay\vietlex-dacn-20261020\output\VietLex_20261102_academic_standardized.docx"),
        "evidence": Path(r"D:\Download\WordAssistant\artifacts\course-essay\vietlex-dacn-20261020\evidence.json"),
        "corpus": Path(r"D:\Download\WordAssistant\artifacts\course-essay\vietlex-dacn-20261020\sources"),
        "qa_dir": Path(r"D:\Download\WordAssistant\artifacts\course-essay\vietlex-dacn-20261020\qa"),
    },
    {
        "name": "LMS",
        "description": "Tiểu luận Quản lý Dự án Phần mềm Hệ thống LMS (Trello & Draw.io)",
        "docx": Path(r"D:\Download\WordAssistant\artifacts\course-essay\lms-qlpm-trello-drawio\output\LMS_20261102_standardized.docx"),
        "evidence": Path(r"D:\Download\WordAssistant\artifacts\course-essay\lms-qlpm-trello-drawio\evidence.json"),
        "corpus": Path(r"D:\Download\WordAssistant\artifacts\course-essay\lms-qlpm-trello-drawio\sources"),
        "qa_dir": Path(r"D:\Download\WordAssistant\artifacts\course-essay\lms-qlpm-trello-drawio\qa"),
    },
]

all_results = []

print("================================================================================")
print("  VIET-TEXT-AUDIT RUNNER: AUDITING 3 NEWEST WORDASSISTANT PROJECTS")
print("================================================================================")

for p in PROJECTS:
    name = p["name"]
    desc = p["description"]
    docx = p["docx"]
    ev = p["evidence"]
    corpus = p["corpus"]
    qa_dir = p["qa_dir"]
    qa_dir.mkdir(parents=True, exist_ok=True)
    
    html_out = qa_dir / f"text_audit_{name.lower()}_v2.html"
    json_out = qa_dir / f"text_audit_{name.lower()}_v2.json"
    
    print(f"\n[{name.upper()}] - {desc}")
    print(f"  > DOCX:     {docx} ({docx.stat().st_size:,} bytes)")
    print(f"  > Evidence: {ev} (exists: {ev.is_file()})")
    print(f"  > Corpus:   {corpus} (exists: {corpus.is_dir()})")
    print(f"  > HTML Out: {html_out}")
    print(f"  > JSON Out: {json_out}")
    print("  ... Đang tiến hành quét và phân tích ...")
    
    start_t = time.time()
    try:
        report = audit_integrity(
            docx_path=docx,
            evidence_registry_path=ev if ev.is_file() else None,
            corpus_dir=corpus if corpus.is_dir() else None,
            output_html=html_out,
            auto_evidence_corpus=True,
        )
        elapsed = time.time() - start_t
        report["elapsed_seconds"] = round(elapsed, 2)
        report["project_name"] = name
        report["project_description"] = desc
        
        # Save JSON report
        json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        
        summary = report.get("summary", {})
        gates = report.get("gates", {})
        ext_sim = gates.get("external_corpus_similarity", {})
        fidelity = gates.get("evidence_source_attribution_fidelity", {})
        stylometry = gates.get("stylometric_profile_review", {})
        citations = gates.get("numeric_citation_bibliography_consistency", {})
        
        result_entry = {
            "name": name,
            "description": desc,
            "docx": str(docx),
            "html_report": str(html_out),
            "json_report": str(json_out),
            "elapsed_seconds": round(elapsed, 2),
            "overall_status": report.get("status"),
            "summary": summary,
            "external_corpus_similarity": {
                "status": ext_sim.get("status"),
                "total_similarity_score": ext_sim.get("total_similarity_score", 0.0),
                "lexical_score": ext_sim.get("lexical_score", 0.0),
                "semantic_score": ext_sim.get("semantic_score", 0.0),
                "corpus_size": ext_sim.get("corpus_size", 0),
                "findings_count": len(ext_sim.get("findings", [])),
                "findings": ext_sim.get("findings", [])[:5],
            },
            "evidence_source_attribution_fidelity": {
                "status": fidelity.get("status"),
                "cited_evidence_count": fidelity.get("cited_evidence_count", 0),
                "evaluated_evidence_count": fidelity.get("evaluated_evidence_count", 0),
                "findings_count": len(fidelity.get("findings", [])),
            },
            "stylometric_profile_review": {
                "status": stylometry.get("status"),
                "decision": stylometry.get("decision"),
                "metrics": stylometry.get("metrics", {}),
            },
            "numeric_citation_bibliography_consistency": {
                "status": citations.get("status"),
                "citation_numbers": citations.get("citation_numbers", []),
                "bibliography_numbers": citations.get("bibliography_numbers", []),
                "findings_count": len(citations.get("findings", [])),
            },
            "all_gate_statuses": {k: v.get("status") for k, v in gates.items()},
        }
        all_results.append(result_entry)
        
        print(f"  [OK] Hoàn thành trong {elapsed:.2f}s | Trạng thái: {report.get('status')} | Summary: {summary}")
        print(f"       + Tương đồng Corpus (Total): {ext_sim.get('total_similarity_score', 0.0)}% (Lex: {ext_sim.get('lexical_score', 0.0)}%, Sem: {ext_sim.get('semantic_score', 0.0)}%)")
        print(f"       + Quy mô Corpus đối soát:    {ext_sim.get('corpus_size', 0)} tài liệu")
        print(f"       + Stylometric Profile Gate:  [{stylometry.get('status')}] Decision: {stylometry.get('decision')}")
        print(f"       + Trích dẫn IEEE số/Bib:     [{citations.get('status')}] {len(citations.get('citation_numbers', []))} trích dẫn / {len(citations.get('bibliography_numbers', []))} mục TLTK")
        
    except Exception as exc:
        print(f"  [ERROR] Lỗi khi kiểm tra {name}: {exc}")
        import traceback
        traceback.print_exc()

# Save combined summary report
summary_path = Path(r"D:\Download\WordAssistant\artifacts\three_projects_audit_summary.json")
summary_path.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")
print("\n================================================================================")
print(f"  TỔNG HỢP KIỂM ĐỊNH ĐÃ LƯU TẠI: {summary_path}")
print("================================================================================")
