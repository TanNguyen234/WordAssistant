import sys
import json
import time
from pathlib import Path
from wordassistant.document.integrity import audit_integrity

sys.stdout.reconfigure(encoding='utf-8')

base = Path("artifacts/course-essay/strongwine-revision-20261027")
docx = base / "output/StrongWine_20261102_academic_standardized.docx"
corpus = base / "sources"
ev = base / "evidence.json"
qa_dir = base / "qa"
qa_dir.mkdir(parents=True, exist_ok=True)

print(f"=== RUNNING AUDIT INTEGRITY ON STANDARDIZED STRONGWINE ===")
print(f"DOCX: {docx}")
print(f"Corpus: {corpus}")
print(f"Evidence: {ev}")

start_time = time.time()
report = audit_integrity(
    docx_path=docx,
    evidence_registry_path=ev,
    corpus_dir=corpus,
    output_html=qa_dir / 'text_audit_strongwine_standardized.html',
    auto_evidence_corpus=True
)
elapsed = time.time() - start_time
print(f"\nAudit completed in {elapsed:.2f} seconds.")
print(f"Overall Status: {report.get('status')}")
print(f"Summary Counts: {report.get('summary')}")

print("\n--- GATES DETAIL ---")
for k, v in report.get('gates', {}).items():
    st = v.get('status')
    cnt = len(v.get('findings', []))
    print(f"  [{st:4s}] {k:44s} (Findings: {cnt})")

cit_gate = report['gates'].get('numeric_citation_bibliography_consistency', {})
print(f"\nCitation & Bibliography Consistency:")
print(f"  Status: {cit_gate.get('status')}")
print(f"  Cited numbers in text: {cit_gate.get('citation_numbers')}")
print(f"  Bibliography numbers : {cit_gate.get('bibliography_numbers')}")
print(f"  Findings: {cit_gate.get('findings')}")

src_gate = report['gates'].get('source_evidence', {})
print(f"\nSource Evidence Gate:")
print(f"  Status: {src_gate.get('status')}")
print(f"  Verified records: {src_gate.get('verified_record_count')}")
print(f"  Primary records: {src_gate.get('primary_record_count')}")
print(f"  Findings: {src_gate.get('findings')}")

rep_gate = report['gates'].get('repetitive_prose_review', {})
print(f"\nRepetitive Prose Gate:")
print(f"  Status: {rep_gate.get('status')}")
print(f"  Findings count: {len(rep_gate.get('findings', []))}")

# Save report
out_json = qa_dir / 'integrity-audit-standardized.json'
out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"\nSaved standardized audit report to: {out_json}")
