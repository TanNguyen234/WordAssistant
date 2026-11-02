import hashlib
import json

from docx import Document

from wordassistant.document.report_review import SOFTWARE_DECISIONS, assess_content_review


def case(tmp_path, domain='software'):
    doc = Document()
    doc.add_heading('Analysis', 1)
    doc.add_paragraph('A source-backed argument and its consequences.')
    output = tmp_path / 'report.docx'
    doc.save(output)
    plan = {'schema_version': 1, 'domain': domain,
            'document_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'model_scope_reason': 'The assignment requires an analytical essay.',
            'model_decisions': [{'dimension': dim, 'disposition': 'NOT_APPLICABLE',
                'reason': 'The inspected assignment excludes this model.', 'authority': 'assignment section 2',
                'status': 'REVIEWED', 'reviewer': 'Reviewer', 'review_date': '2026-10-25'} for dim in SOFTWARE_DECISIONS],
            'section_reviews': [{'heading': 'Analysis', 'status': 'REVIEWED', 'reviewer': 'Reviewer',
                'review_date': '2026-10-25', 'argument': 'Explains the choice and consequence.',
                'evidence': 'Compared the claim with source section 2.',
                'terminology': 'Terms are defined for the intended reader.',
                'sufficiency': 'Answers the assignment question without an arbitrary word quota.'}]}
    project = {'output_docx': 'report.docx', 'content_review_plan_file': 'review.json'}
    return plan, project


def save(tmp_path, plan):
    (tmp_path / 'review.json').write_text(json.dumps(plan), encoding='utf-8')


def test_software_report_cannot_silently_omit_data_model_decision(tmp_path):
    plan, project = case(tmp_path)
    plan['model_decisions'] = [x for x in plan['model_decisions'] if x['dimension'] != 'data']
    save(tmp_path, plan)
    result = assess_content_review(tmp_path, project)
    assert result['status'] == 'INCOMPLETE'
    assert any(x['check'] == 'software_model_scope' and 'data' in x['detail'] for x in result['checks'])


def test_other_subject_does_not_require_uml(tmp_path):
    plan, project = case(tmp_path, 'literature')
    plan['model_decisions'] = []
    save(tmp_path, plan)
    assert assess_content_review(tmp_path, project)['status'] == 'PASS'


def test_stale_document_and_unembedded_figure_cannot_pass(tmp_path):
    plan, project = case(tmp_path)
    plan['document_sha256'] = '0' * 64
    item = plan['model_decisions'][0]
    item['disposition'] = 'REQUIRED'
    item['assets'] = [{'editable_file': 'absent.puml', 'rendered_file': 'absent.png',
                       'caption_title': 'Imaginary model', 'sources': []}]
    save(tmp_path, plan)
    result = assess_content_review(tmp_path, project)
    assert result['status'] == 'FAIL'
    assert any('not embedded' in x['detail'] for x in result['checks'])


def test_review_records_need_argument_and_evidence_not_just_status(tmp_path):
    plan, project = case(tmp_path)
    plan['section_reviews'][0].pop('argument')
    save(tmp_path, plan)
    assert assess_content_review(tmp_path, project)['status'] == 'INCOMPLETE'


def test_malformed_model_plan_fails_without_crashing_readiness(tmp_path):
    plan, project = case(tmp_path)
    plan['model_decisions'] = ['not a model record']
    save(tmp_path, plan)
    assert assess_content_review(tmp_path, project)['status'] == 'FAIL'


def test_recorded_review_cannot_hide_a_skipped_heading_level(tmp_path):
    plan, project = case(tmp_path)
    doc = Document(tmp_path / 'report.docx')
    doc.add_heading('Missing intermediate parent', 3)
    doc.save(tmp_path / 'report.docx')
    plan['document_sha256'] = hashlib.sha256((tmp_path / 'report.docx').read_bytes()).hexdigest()
    save(tmp_path, plan)
    assert assess_content_review(tmp_path, project)['status'] == 'FAIL'
