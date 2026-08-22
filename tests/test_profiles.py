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
