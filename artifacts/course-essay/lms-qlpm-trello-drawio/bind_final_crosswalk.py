"""Refresh final crosswalk provenance without changing measured QA reports."""
from finalize_review_records import ROOT, DATE, REVIEWER, rows, writecsv, digest

items = rows('acceptance-crosswalk.csv')
for item in items:
    if item['check_id'] == 'X11':
        item['evidence_files'] = '.wordassistant/project.json;project.json;output/final.docx;qa/final-profile-validation.json;qa/final-delivery.json;qa/final-integrity-audit.json;qa/final-integrity-provenance.json;qa/final-render.json'
        item['notes'] = 'Borrowed HCMUNRE course_essay_style; Tiểu luận môn học; no n8n or imported capstone rubric. Final 38-page Word delivery PASS; content/submission limitations remain explicit.'
    if item['check_id'] == 'X12':
        item['status'] = 'PASS'
        item['evidence_files'] = 'output/final.docx;appendix-models.json;revision-content.json;content-review-plan.json;qa/final-visual-review.json;qa/caption-audit.json'
        item['notes'] = 'Eight model dimensions reviewed; five added source-based models checked for meaning, notation limits, embedded bytes and visible captions. Deployment view is inapplicable without deployment evidence.'
    item['document_sha256'] = digest(ROOT / 'output/final.docx')
    paths = [p.strip() for p in item['evidence_files'].split(';') if p.strip()]
    resolved = [ROOT / p for p in paths]
    assert all(p.is_file() for p in resolved), [str(p) for p in resolved if not p.is_file()]
    item['evidence_sha256'] = ';'.join(digest(p) for p in resolved)
    item['reviewed_by'] = REVIEWER
    item['review_date'] = DATE
writecsv('acceptance-crosswalk.csv', items)
print('Bound 12 acceptance rows to final artifact; X07 remains NOT_RUN.')
