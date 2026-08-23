import json
from pathlib import Path
import pytest
from wordassistant.profiles.loader import (
    load_profile,
    discover_profiles,
    ProfileError,
    validate_profile_dict,
)

ROOT = Path(__file__).resolve().parents[1]

def make_valid_variant(**kwargs):
    base = {
        'page': {
            'size': 'A4', 'width_cm': 21.0, 'height_cm': 29.7,
            'margins_cm': {'top': 2.0, 'bottom': 2.0, 'left': 3.0, 'right': 2.0},
            'one_sided': True
        },
        'typography': {
            'body_font': 'Times New Roman',
            'body_size_pt': 13.0,
            'line_spacing': 1.5
        }
    }
    base.update(kwargs)
    return base

def test_profile_rejects_unknown_keys(tmp_path):
    var = make_valid_variant()
    var['page']['one_sidded'] = True # TYPO
    bad = {
        'id': 'bad_typo', 'name': 'Bad Typo', 'version': 1,
        'variants': {'default': var}
    }
    f = tmp_path / 'bad.json'
    f.write_text(json.dumps(bad), encoding='utf-8')
    with pytest.raises(ProfileError, match="Unknown key|one_sidded"):
        load_profile(f)

def test_profile_rejects_wrong_types(tmp_path):
    var = make_valid_variant()
    var['page']['size'] = 123
    bad = {
        'id': 'bad_types', 'name': 'Bad Types', 'version': 1,
        'variants': {'default': var}
    }
    f = tmp_path / 'bad.json'
    f.write_text(json.dumps(bad), encoding='utf-8')
    with pytest.raises(ProfileError):
        load_profile(f)

def test_profile_rejects_invalid_enums(tmp_path):
    var = make_valid_variant()
    var['typography']['styles'] = {
        'heading1': {'font': 'Times New Roman', 'size_pt': 14, 'alignment': 'banana'}
    }
    bad = {
        'id': 'bad_enum', 'name': 'Bad Enum', 'version': 1,
        'variants': {'default': var}
    }
    f = tmp_path / 'bad.json'
    f.write_text(json.dumps(bad), encoding='utf-8')
    with pytest.raises(ProfileError, match="alignment|banana"):
        load_profile(f)

def test_profile_rejects_path_traversal(tmp_path):
    var = make_valid_variant(template_asset='../../etc/passwd')
    bad = {
        'id': 'bad_path', 'name': 'Bad Path', 'version': 1,
        'variants': {'default': var}
    }
    f = tmp_path / 'bad.json'
    f.write_text(json.dumps(bad), encoding='utf-8')
    with pytest.raises(ProfileError, match="traversal|path"):
        load_profile(f)

def test_profile_rejects_duplicate_or_empty_blueprint_titles(tmp_path):
    var = make_valid_variant(section_blueprint=[
        {'title': 'Intro', 'level': 1},
        {'title': '', 'level': 1}
    ])
    bad = {
        'id': 'bad_bp', 'name': 'Bad BP', 'version': 1,
        'variants': {'default': var}
    }
    f = tmp_path / 'bad.json'
    f.write_text(json.dumps(bad), encoding='utf-8')
    with pytest.raises(ProfileError, match="title|empty"):
        load_profile(f)

    var_dup = make_valid_variant(section_blueprint=[
        {'title': 'Intro', 'level': 1},
        {'title': 'Intro', 'level': 1}
    ])
    bad_dup = {
        'id': 'bad_bp2', 'name': 'Bad BP2', 'version': 1,
        'variants': {'default': var_dup}
    }
    f2 = tmp_path / 'bad2.json'
    f2.write_text(json.dumps(bad_dup), encoding='utf-8')
    with pytest.raises(ProfileError, match="Duplicate title|title"):
        load_profile(f2)

def test_dynamic_profile_discovery(tmp_path):
    custom_profile = {
        'id': 'custom_discovered_profile',
        'name': 'Custom Discovered',
        'version': 1,
        'variants': {'default': make_valid_variant()}
    }
    p_dir = tmp_path / 'profiles'
    p_dir.mkdir()
    (p_dir / 'custom.json').write_text(json.dumps(custom_profile), encoding='utf-8')
    
    discovered = discover_profiles(extra_dirs=[p_dir])
    ids = [p.profile_id for p in discovered]
    assert 'custom_discovered_profile' in ids
    assert 'generic' in ids
    assert 'hcmunre_dacn_2026_2027' in ids
