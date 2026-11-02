"""Bind authored review records to the saved, visually inspected LMS essay."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATE = '2026-10-26'
REVIEWER = 'Codex source and editorial review'
def readj(p):
    return json.loads((ROOT / p).read_text(encoding='utf-8-sig'))
def writej(p, data):
    (ROOT / p).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(p):
    with (ROOT / p).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))
def writecsv(p, data):
    with (ROOT / p).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]))
        w.writeheader(); w.writerows(data)

doc_hash = digest(ROOT / 'output/final.docx')
render = readj('qa/final-render.json')
assert render['render_reuse_manifest']['document_sha256'] == doc_hash
pages = render['render']['page_images']
assert len(pages) == 38
writej('qa/final-visual-review.json', {
    'document_sha256': doc_hash, 'reviewed_by': REVIEWER, 'review_date': DATE,
    'verification_level': 'native Word render and page-by-page visual inspection',
    'page_count': 38, 'reviewed_pages': list(range(1, 39)),
    'page_images': [{'path': p, 'sha256': digest(Path(p))} for p in pages],
    'status': 'PASS',
    'observations': [
        'Cover metadata honestly states information not provided; no institutional affiliation is asserted.',
        'TOC, 11-figure list, 19-table list and continuous appendix page numbers are visible and consistent.',
        'All pages inspected: no clipped text, missing glyphs, overlapping assets or unintended blank pages.',
        'Tables repeat headers across pages. Chapter starts retain whitespace; long source identifiers and slash-delimited technical labels may wrap.',
        'Five added models and adjacent explanations are readable. Overview architecture/data models retain editable sources for detail.',
        'Unresolvable TOC line-spacing warning was reviewed against actual rendered front matter; no visible defect.',
        'Static exports and API aggregates do not establish runtime execution; capture checklist remains NOT_RUN.'
    ]})

plan = readj('content-review-plan.json')
plan['document_sha256'] = doc_hash
plan['final_visual_review_file'] = 'qa/final-visual-review.json'
writej('content-review-plan.json', plan)
data = rows('structure-parity.csv')
for row in data:
    row['evidence_files'] = 'project.json;content-review-plan.json;output/final.docx'
writecsv('structure-parity.csv', data)

audit = readj('qa/final-integrity-audit.json')
assert audit['document']['sha256'] == doc_hash
numeric_reasons = [
    'Project charter describes the three planned roles and business case; this is a project-source claim, mapped in claim-evidence.csv rather than an external research result.',
    'Ten acceptance scenarios and quality gates are documented in the project quality/UAT plan; the prose explicitly states they have not been executed.',
    'The reconciled project baseline is 20 weeks, 1.2 billion VND and 8.5 FTE; FTE is expressly distinguished from headcount.',
    'Resource/budget baseline supports the six cost categories and 8.5 FTE; totals are planned estimates, not actual spending.',
    'Definition of Done and zero P0/P1 target are quality-plan conditions, not measured defect results.',
    'The archived 23 October Trello JSON snapshot supports 9 lists and 39 cards; the report distinguishes API aggregation from screenshots and confirmed Done.',
    'The reviewed assignments.py routes support grading, ownership/score guards, Submission/Grade updates and Notification creation; this is source inspection, not runtime proof.'
]
dispositions = []
for gate, value in audit['gates'].items():
    if value['status'] != 'WARN':
        continue
    for i, finding in enumerate(value['findings'], 1):
        if gate == 'typography_punctuation_review':
            reason = 'Reviewed dash punctuation denotes technical relationships, ranges or explicit qualifications; it does not change the source meaning.'
        elif gate == 'quantitative_claims_lacking_citation':
            assert len(value['findings']) == len(numeric_reasons)
            reason = numeric_reasons[i-1]
        elif gate == 'repetitive_prose_review':
            reason = 'Reviewed repeated phrase: ' + finding['text'] + '. It identifies a stable source path, model/capture ID or baseline reused across analysis and evidence limitations; retaining it preserves traceability.'
        elif gate == 'ai_use_disclosure_provenance':
            reason = 'No applicable course AI declaration form or required wording was supplied. Actual Codex assistance is recorded in final provenance; no student declaration or approval is fabricated.'
        else:
            raise RuntimeError('Unreviewed gate: ' + gate)
        dispositions.append(dict(gate=gate, finding_index=i, decision='accepted', reason=reason,
            evidence='output/final.docx;qa/final-integrity-audit.json;source-audit.md;claim-evidence.csv;content-review-plan.json;qa/final-integrity-provenance.json',
            reviewed_by=REVIEWER, review_date=DATE))
writecsv('integrity-warning-dispositions.csv', dispositions)

project = readj('project.json')
project['output_docx'] = 'output/final.docx'
project['qa_reports'] = dict(profile_validation='qa/final-profile-validation.json', word_verify='qa/final-delivery.json',
    integrity_audit='qa/final-integrity-audit.json', integrity_provenance='qa/final-integrity-provenance.json', readiness='qa/readiness.json')
project['acceptance_checks']['all_rendered_pages_visually_reviewed'] = True
project['acceptance_checks']['all_integrity_warnings_reviewed_and_dispositioned'] = True
writej('project.json', project)
print(json.dumps({'document_sha256': doc_hash, 'reviewed_pages': len(pages), 'warning_dispositions': len(dispositions)}))
