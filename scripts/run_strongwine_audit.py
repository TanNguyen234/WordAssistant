import sys
import json
import time
from pathlib import Path
from wordassistant.document.integrity import audit_integrity

sys.stdout.reconfigure(encoding='utf-8')

docx = Path('artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_standardized.docx')
corpus = Path('D:/Projects/strongwine_2/Wine-website/docs')
qa_dir = Path('artifacts/course-essay/strongwine-revision-20261027/qa')

print(f'>>> RUNNING REAL AUDIT FOR StrongWine')
print(f'    DOCX: {docx}')
print(f'    Corpus: {corpus}')

start_time = time.time()
report = audit_integrity(
    docx_path=docx,
    evidence_registry_path=None,
    corpus_dir=corpus if corpus.is_dir() else None,
    output_html=qa_dir / 'text_audit_strongwine.html',
    auto_evidence_corpus=True
)
elapsed = time.time() - start_time
print(f'Audit completed in {elapsed:.2f} seconds.')
print(f'Overall Status: {report.get("status")}')
print(f'Summary Counts: {report.get("summary")}')

gates = report.get('gates', {})
print('\n--- GATE RESULTS ---')
for g_name, g_val in gates.items():
    status = g_val.get('status')
    findings = len(g_val.get('findings', []))
    print(f'  [{status:4s}] {g_name:42s} (Findings: {findings})')

# Detail on viet-text-audit specific gates
print('\n--- VIET-TEXT-AUDIT NLP METRICS ---')
ext_sim = gates.get('external_corpus_similarity', {})
print(f'  External Corpus Similarity Gate Status: {ext_sim.get("status")}')
print(f'    Corpus size: {ext_sim.get("corpus_size", 0)}')
print(f'    Total Similarity Score: {ext_sim.get("total_similarity_score", 0.0)}%')
print(f'    Lexical Overlap Score: {ext_sim.get("lexical_overlap_score", 0.0)}%')
print(f'    Semantic Paraphrase Score: {ext_sim.get("semantic_paraphrase_score", 0.0)}%')
if ext_sim.get('findings'):
    print(f'    Top Similarity Findings (first 3):')
    for f in ext_sim.get('findings')[:3]:
        print(f'      - Source: {f.get("source_id")}, Score: {f.get("score")}% ({f.get("match_type")})')

sty_gate = gates.get('stylometric_profile_review', {})
print(f'\n  Stylometric Profile Review Gate Status: {sty_gate.get("status")}')
print(f'    Decision: {sty_gate.get("decision")}')
print(f'    Metrics: {sty_gate.get("metrics")}')

rep_gate = gates.get('repetitive_prose_review', {})
print(f'\n  Repetitive Prose Review Gate Status: {rep_gate.get("status")}')
print(f'    Total Repetition Findings: {rep_gate.get("finding_count_total", len(rep_gate.get("findings", [])))}')
for f in rep_gate.get('findings', [])[:3]:
    print(f'      - Kind: {f.get("kind")}, Text: "{f.get("text")}", Occurrences: {f.get("occurrences")}')

cit_gate = gates.get('numeric_citation_bibliography_consistency', {})
print(f'\n  Citation & Bibliography Consistency Gate Status: {cit_gate.get("status")}')
print(f'    Citation numbers cited in text: {cit_gate.get("citation_numbers")}')
print(f'    Bibliography numbers in bib: {cit_gate.get("bibliography_numbers")}')
for f in cit_gate.get('findings', []):
    print(f'      - Finding: {f.get("kind")} -> Number: {f.get("number")}')

quant_gate = gates.get('quantitative_claims_lacking_citation', {})
print(f'\n  Quantitative Claims Lacking Citation Gate Status: {quant_gate.get("status")}')
print(f'    Uncited Quantitative Claims Count: {len(quant_gate.get("findings", []))}')

# Save QA report
qa_dir.mkdir(parents=True, exist_ok=True)
out_json = qa_dir / 'integrity-audit-live.json'
out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\nFull QA report saved to: {out_json}')
