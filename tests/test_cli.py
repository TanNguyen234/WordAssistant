from pathlib import Path
from wordassistant.cli import run

ROOT=Path(__file__).resolve().parents[1]
GUIDE=ROOT/'use_cases/hcmunre_dacn_2026_2027/assets/huong_dan_trinh_bay_dacn_2026_2027.docx'


def test_doctor_json_is_core_only_and_succeeds(capsys):
    code=run(['doctor','--json'])
    out=capsys.readouterr().out
    assert code==0
    assert 'python-docx' in out


def test_context_cli_needs_only_file_and_query(capsys):
    code=run(['context',str(GUIDE),'--query','trích dẫn tài liệu gốc','--max-tokens','1200','--json'])
    out=capsys.readouterr().out.casefold()
    assert code==0
    assert 'trích dẫn' in out

def test_init_creates_small_agent_workspace(tmp_path, capsys):
    target=tmp_path/'proj'
    code=run(['init',str(target),'--json'])
    assert code==0
    assert (target/'.wordassistant/project.json').exists()
    assert (target/'.wordassistant/evidence.json').exists()


def test_capabilities_explain_core_and_advanced(capsys):
    assert run(['capabilities','--json'])==0
    out=capsys.readouterr().out
    assert 'replace' in out
    assert 'tracked_changes' in out

def test_profiles_command_lists_variants(capsys):
    assert run(['profiles','--json'])==0
    out=capsys.readouterr().out
    assert 'hcmunre_dacn_2026_2027' in out
    assert 'report' in out and 'proposal' in out
