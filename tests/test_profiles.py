import json
from pathlib import Path
import pytest
from wordassistant.profiles.loader import load_profile, ProfileError

ROOT = Path(__file__).resolve().parents[1]


def test_hcmunre_has_distinct_report_and_proposal_variants():
    p = load_profile(ROOT / 'profiles/hcmunre_dacn_2026_2027.json')
    assert set(p.variants) >= {'report', 'proposal'}
    assert p.variant('report').page.margins.left_cm == 3.0
    assert p.variant('report').citations['minimum_references'] == 10
    assert p.variant('proposal').citations.get('minimum_references') is None


def test_hcmunre_profile_points_to_bundled_official_assessment_criteria():
    profile_path = ROOT / 'profiles/hcmunre_dacn_2026_2027.json'
    profile = json.loads(profile_path.read_text(encoding='utf-8'))

    criteria = profile['assessment_criteria']
    guide = 'use_cases/hcmunre_dacn_2026_2027/assets/huong_dan_trinh_bay_dacn_2026_2027.docx'
    assert guide in profile['source_assets']
    assert criteria['source_asset'] == guide
    assert criteria['source_sha256'] == '0f3622dbcd74009fb0867e0d3fa4a1624a38983af502e55d48868edf33f74e78'
    assert criteria['scoring_levels_present'] is False
    assert criteria['scoring_weights_present'] is False
    assert {item['report_section'] for item in criteria['sections']} == {
        'supervisor_review', 'reviewer_review'
    }

    loaded = load_profile(profile_path).assessment_criteria
    assert loaded is not None
    assert loaded.source_asset == guide
    assert loaded.scoring_levels_present is False
    assert [section.report_section for section in loaded.sections] == [
        'supervisor_review', 'reviewer_review'
    ]


def test_document_completeness_review_defaults_and_hcmunre_report_override():
    generic = load_profile(ROOT / 'src/wordassistant/data/profiles/generic.json')
    hcmunre = load_profile(ROOT / 'profiles/hcmunre_dacn_2026_2027.json')

    assert generic.variant('default').content_review == {
        'chapter_heading_numbering': 'review',
        'unresolved_placeholders': 'strict_on_verify',
    }
    assert hcmunre.variant('report').content_review == {
        'chapter_heading_numbering': 'required',
        'unresolved_placeholders': 'strict_on_verify',
    }
    assert hcmunre.variant('proposal').content_review.get('chapter_heading_numbering', 'review') == 'review'


def test_profile_rejects_unknown_content_review_policy(tmp_path):
    profile = json.loads((ROOT / 'src/wordassistant/data/profiles/generic.json').read_text(encoding='utf-8'))
    profile['variants']['default']['content_review']['chapter_heading_numbering'] = 'auto_fix'
    path = tmp_path / 'invalid-review-policy.json'
    path.write_text(json.dumps(profile), encoding='utf-8')

    with pytest.raises(ProfileError, match='content_review.chapter_heading_numbering'):
        load_profile(path)


def test_profile_validation_is_strict_for_boolean_tuple_and_margin(tmp_path):
    bad = {
        'id':'bad','name':'Bad','version':1,
        'variants': {'default': {
            'page': {'size':'A4','width_cm':21.0,'height_cm':29.7,
                     'margins_cm':{'top':2,'bottom':2,'left':20,'right':2},
                     'one_sided':'false'},
            'typography': {'body_font':'Times New Roman','body_size_pt':13},
            'front_matter':'cover'
        }}
    }
    f=tmp_path/'bad.json'; f.write_text(json.dumps(bad), encoding='utf-8')
    with pytest.raises(ProfileError): load_profile(f)


def test_profile_rejects_zero_version(tmp_path):
    f=tmp_path/'bad.json'; f.write_text(json.dumps({'id':'x','name':'x','version':0,'variants':{}}))
    with pytest.raises(ProfileError): load_profile(f)


def test_hcmunre_course_essay_style_is_style_only():
    profile = load_profile(ROOT / 'profiles/hcmunre_dacn_2026_2027.json')
    variant = profile.variant('course_essay_style')
    packaged = load_profile(ROOT / 'src/wordassistant/data/profiles/hcmunre_dacn_2026_2027.json')
    assert packaged.variant('course_essay_style') == variant

    assert variant.page.size == 'A4'
    assert (
        variant.page.margins.top_cm,
        variant.page.margins.bottom_cm,
        variant.page.margins.left_cm,
        variant.page.margins.right_cm,
    ) == (2.0, 2.0, 3.0, 2.0)
    assert variant.typography.body_font == 'Times New Roman'
    assert variant.typography.body_size_pt == 13
    assert variant.typography.line_spacing == 1.5
    assert not variant.cover
    assert not variant.front_matter
    assert not variant.section_blueprint
    assert not variant.citations
