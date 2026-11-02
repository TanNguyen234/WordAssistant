import sys
import json
from pathlib import Path
from wordassistant.document.integrity import audit_integrity

sys.stdout.reconfigure(encoding='utf-8')

base = Path("artifacts/course-essay/strongwine-revision-20261027")
docx = base / "output/StrongWine_20261102_standardized.docx"
ev = base / "evidence.json"
sources = base / "sources"

print("Auditing StrongWine current status...")
report = audit_integrity(
    docx_path=docx,
    evidence_registry_path=ev,
    corpus_dir=sources,
    auto_evidence_corpus=True
)

print(f"Overall status: {report.get('status')}")
for k, v in report.get("gates", {}).items():
    st = v.get("status")
    cnt = len(v.get("findings", []))
    print(f"  [{st:4s}] {k:44s} (Findings: {cnt})")

cit_gate = report['gates'].get('numeric_citation_bibliography_consistency', {})
print(f"Citations: cited={cit_gate.get('citation_numbers')}, bib={cit_gate.get('bibliography_numbers')}")
print(f"Citation findings: {cit_gate.get('findings')}")

src_gate = report['gates'].get('source_evidence', {})
print(f"Source evidence: status={src_gate.get('status')}, verified={src_gate.get('verified_record_count')}, primary={src_gate.get('primary_record_count')}")
print(f"Source findings: {src_gate.get('findings')}")

rep_gate = report['gates'].get('repetitive_prose_review', {})
print(f"Repetitive prose: status={rep_gate.get('status')}, findings={rep_gate.get('findings')}")
