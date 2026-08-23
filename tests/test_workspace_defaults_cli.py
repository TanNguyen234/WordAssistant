import json
from pathlib import Path
from wordassistant.cli import run

ROOT = Path(__file__).resolve().parents[1]

def test_cli_advanced_status(capsys):
    code = run(['advanced', 'status', '--json'])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert code == 0
    assert 'installed' in data
    assert 'operational' in data
    assert 'reason' in data
    assert 'core_capabilities' in data
    assert 'advanced_capabilities' in data

def test_cli_config_show_and_set(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run(['init', str(tmp_path), '--json'])
    capsys.readouterr()
    
    # Show
    code_show = run(['config', 'show', '--json'])
    out_show = capsys.readouterr().out
    data_show = json.loads(out_show)
    assert code_show == 0
    assert data_show['profile'] == 'generic'
    
    # Set
    code_set = run(['config', 'set', 'profile', 'hcmunre_dacn_2026_2027', '--json'])
    out_set = capsys.readouterr().out
    data_set = json.loads(out_set)
    assert code_set == 0
    assert data_set['profile'] == 'hcmunre_dacn_2026_2027'
    
    # Verify set persisted
    code_show2 = run(['config', 'show', '--json'])
    out_show2 = capsys.readouterr().out
    data_show2 = json.loads(out_show2)
    assert data_show2['profile'] == 'hcmunre_dacn_2026_2027'

def test_cli_scaffold_falls_back_to_workspace_defaults(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run(['init', str(tmp_path), '--json'])
    run(['config', 'set', 'title', 'CUSTOM WORKSPACE TITLE', '--json'])
    capsys.readouterr()
    
    doc_out = tmp_path / 'default_scaffold.docx'
    # Do not pass --title or --profile
    code = run(['scaffold', str(doc_out), '--json'])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert code == 0
    assert data['profile'] == 'generic'
    assert doc_out.exists()
