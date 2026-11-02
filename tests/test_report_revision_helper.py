import importlib.util
from pathlib import Path

from docx import Document
import pytest

spec = importlib.util.spec_from_file_location('report_revision', Path(__file__).parents[1] / 'scripts/revise_course_report.py')
revision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revision)


def case(tmp_path):
    source = tmp_path / 'source.docx'
    doc = Document()
    doc.add_heading('Methods', 1)
    p = doc.add_paragraph('A supported claim [1].')
    p.runs[0].italic = True
    doc.add_heading('Results', 1)
    doc.save(source)
    plan = {'schema_version': 1, 'input_sha256': revision.sha256(source), 'edits': [
        {'section': 'Methods', 'paragraph_index': 0,
         'expected_text_sha256': revision.text_hash(p.text), 'text': 'A clearer supported claim [1].'}]}
    return source, tmp_path / 'output.docx', plan


def test_revision_preserves_citations_style_and_source(tmp_path):
    source, output, plan = case(tmp_path)
    original = source.read_bytes()
    revision.revise(source, output, plan)
    changed = Document(output)
    assert changed.paragraphs[1].text == 'A clearer supported claim [1].'
    assert changed.paragraphs[1].runs[0].italic
    assert source.read_bytes() == original


def test_revision_rejects_citation_loss_without_partial_output(tmp_path):
    source, output, plan = case(tmp_path)
    plan['edits'][0]['text'] = 'Unsupported rewrite.'
    with pytest.raises(ValueError, match='citation'):
        revision.revise(source, output, plan)
    assert not output.exists()


def test_inline_plan_cannot_drop_a_citation(tmp_path):
    source, output, plan = case(tmp_path)
    plan['edits'] = []
    plan['run_edits'] = [{'section': 'Methods', 'paragraph_index': 0, 'run_index': 0,
        'expected_text_sha256': revision.text_hash('A supported claim [1].'),
        'expected_run_sha256': revision.text_hash('A supported claim [1].'), 'text': 'Dropped citation.'}]
    with pytest.raises(ValueError, match='citation'):
        revision.revise(source, output, plan)
    assert not output.exists()


def test_revision_rejects_skipped_parent_heading_before_saving(tmp_path):
    source, output, plan = case(tmp_path)
    plan['headings'] = [{'text': 'Results', 'level': 3}]
    with pytest.raises(ValueError, match='skips a level'):
        revision.revise(source, output, plan)
    assert not output.exists()


def test_revision_rejects_stale_source_and_ambiguous_section(tmp_path):
    source, output, plan = case(tmp_path)
    doc = Document(source)
    doc.add_heading('Methods', 1)
    doc.save(source)
    with pytest.raises(ValueError, match='stale input'):
        revision.revise(source, output, plan)
    plan['input_sha256'] = revision.sha256(source)
    with pytest.raises(ValueError, match='unique'):
        revision.revise(source, output, plan)
    assert not output.exists()


def test_editorial_glossary_keeps_paths_and_does_not_cascade(tmp_path):
    source, _output, plan = case(tmp_path)
    doc = Document(source)
    doc.paragraphs[1].text = 'retrieval in app/services/retrieval.py [1]'
    doc.save(source)
    spec = {'input_sha256': revision.sha256(source), 'scope_start': 'Methods',
            'scope_end': 'Results', 'glossary': [
                {'find': 'retrieval', 'replace': 'source retrieval'},
                {'find': 'source', 'replace': 'changed'}]}
    prepared = revision.prepare(source, spec)
    assert prepared['edits'][0]['text'] == 'source retrieval in app/services/retrieval.py [1]'


def test_glossary_edits_prose_beside_field_without_rewriting_field(tmp_path):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    source, output, _plan = case(tmp_path)
    doc = Document(source)
    p = doc.paragraphs[1]
    p.text = 'retrieval '
    for kind in ('begin', 'separate', 'end'):
        run = p.add_run()
        element = OxmlElement('w:fldChar')
        element.set(qn('w:fldCharType'), kind)
        run._r.append(element)
        if kind == 'begin':
            instruction = OxmlElement('w:instrText')
            instruction.text = ' REF retrieval '
            p.add_run()._r.append(instruction)
        elif kind == 'separate':
            p.add_run('retrieval')
    p.add_run(' retrieval')
    doc.save(source)
    spec = {'input_sha256': revision.sha256(source), 'scope_start': 'Methods', 'scope_end': 'Results',
            'glossary': [{'find': 'retrieval', 'replace': 'truy xuất'}]}
    plan = revision.prepare(source, spec)
    revision.revise(source, output, plan)
    p = Document(output).paragraphs[1]
    assert p.text == 'truy xuất retrieval truy xuất'
    assert p._p.xpath('.//w:instrText')[0].text == ' REF retrieval '
