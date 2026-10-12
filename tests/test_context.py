import pytest
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


def test_target_section_is_a_hard_boundary_even_when_budget_remains():
    sections = [
        DocumentSection('target', 'Target section', 'only the requested section', 1),
        DocumentSection('neighbor', 'Related section', 'related query context', 1),
    ]

    bundle = build_context(
        sections,
        query='related query',
        max_tokens=1000,
        target_section_id='target',
    )

    assert [section.section_id for section in bundle.sections] == ['target']
    assert 'only the requested section' in bundle.text
    assert 'related query context' not in bundle.text
    assert bundle.truncated is False


def test_target_section_rejects_unknown_id():
    sections = [DocumentSection('known', 'Known section', 'content', 1)]

    with pytest.raises(ValueError, match='Unknown section id'):
        build_context(
            sections,
            query='content',
            max_tokens=1000,
            target_section_id='missing',
        )


@pytest.mark.parametrize('field', ['target_section_id', 'active_section_id'])
def test_section_constraint_is_validated_before_empty_index_return(field):
    with pytest.raises(ValueError, match='Unknown section id'):
        build_context([], query='content', max_tokens=1000, **{field: 'missing'})


@pytest.mark.parametrize('field', ['target_section_id', 'active_section_id'])
@pytest.mark.parametrize('invalid', ['', '   ', 0])
def test_explicit_invalid_section_constraint_cannot_expand_retrieval(field, invalid):
    sections = [DocumentSection('known', 'Known section', 'content', 1)]
    with pytest.raises(ValueError, match='non-empty string'):
        build_context(sections, query='content', max_tokens=1000, **{field: invalid})
