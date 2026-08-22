from wordassistant.context.retrieve import build_context
from wordassistant.document.model import DocumentSection


def make_sections(n=200):
    return [DocumentSection(section_id=f's{i}', title=f'Section {i}', text=(f'content {i} ' * 80), level=1) for i in range(n)]


def test_context_obeys_budget_and_keeps_query_relevant_section():
    ss=make_sections(); ss[137]=DocumentSection('s137','Evaluation and error analysis','evaluation metrics false positives error analysis '*100,1)
    bundle=build_context(ss, query='error analysis evaluation metrics', max_tokens=1200)
    assert bundle.estimated_tokens <= 1200
    assert any(x.section_id=='s137' for x in bundle.sections)
    assert len(bundle.sections) < 30


def test_context_does_not_require_active_section_id():
    ss=[DocumentSection('a','Intro','alpha beta',1), DocumentSection('b','Citation rules','primary source citation ieee bibliography',1)]
    b=build_context(ss, query='citation bibliography', max_tokens=500)
    assert b.sections[0].section_id=='b'
