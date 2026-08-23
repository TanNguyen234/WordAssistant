from pathlib import Path
import json
from wordassistant.workspace import (
    init_workspace,
    find_workspace,
    load_project_config,
    save_project_config,
    get_workspace_status,
    get_cached_document_index,
    put_cached_document_index,
)
from wordassistant.document.model import DocumentSection

def test_workspace_init_and_detection(tmp_path):
    sub = tmp_path / 'a' / 'b' / 'c'
    sub.mkdir(parents=True)
    
    # Not found before init
    assert find_workspace(sub) is None
    
    wa_dir = init_workspace(tmp_path)
    assert wa_dir.exists()
    assert (wa_dir / 'project.json').exists()
    assert (wa_dir / 'evidence.json').exists()
    assert (wa_dir / 'cache').is_dir()
    
    # Found from sub folder
    found = find_workspace(sub)
    assert found == wa_dir

def test_workspace_project_config(tmp_path):
    init_workspace(tmp_path)
    cfg = load_project_config(tmp_path)
    assert cfg.get('profile') == 'generic'
    
    cfg['profile'] = 'hcmunre_dacn_2026_2027'
    cfg['variant'] = 'report'
    save_project_config(tmp_path, cfg)
    
    reloaded = load_project_config(tmp_path)
    assert reloaded.get('profile') == 'hcmunre_dacn_2026_2027'
    assert reloaded.get('variant') == 'report'

def test_workspace_status(tmp_path):
    init_workspace(tmp_path)
    st = get_workspace_status(tmp_path)
    assert st['is_workspace'] is True
    assert 'profile' in st
    assert 'cache_entries' in st

def test_cached_document_index_by_sha256(tmp_path):
    init_workspace(tmp_path)
    sections = [
        DocumentSection(section_id='s1', title='Heading 1', text='Some body text', level=1)
    ]
    dummy_sha = 'a1b2c3d4e5f6' * 5
    
    put_cached_document_index(tmp_path, dummy_sha, sections)
    cached = get_cached_document_index(tmp_path, dummy_sha)
    
    assert cached is not None
    assert len(cached) == 1
    assert cached[0].title == 'Heading 1'
    assert cached[0].text == 'Some body text'
