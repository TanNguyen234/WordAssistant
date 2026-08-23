from pathlib import Path
from docx import Document
from wordassistant.cli import run

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'use_cases/hcmunre_dacn_2026_2027/assets/huong_dan_trinh_bay_dacn_2026_2027.docx'

def test_doctor_json_is_core_only_and_succeeds(capsys):
    code = run(['doctor', '--json'])
    out = capsys.readouterr().out
    assert code == 0
    assert 'python-docx' in out

def test_status_command(tmp_path, capsys):
    run(['init', str(tmp_path), '--json'])
    capsys.readouterr()
    code = run(['status', '--json'])
    out = capsys.readouterr().out
    assert code == 0
    assert 'is_workspace' in out

def test_context_cli_needs_only_file_and_query(capsys):
    code = run(['context', str(GUIDE), '--query', 'trích dẫn tài liệu gốc', '--max-tokens', '1200', '--json'])
    out = capsys.readouterr().out.casefold()
    assert code == 0
    assert 'trích dẫn' in out

def test_init_creates_small_agent_workspace(tmp_path, capsys):
    target = tmp_path / 'proj'
    code = run(['init', str(target), '--json'])
    assert code == 0
    assert (target / '.wordassistant/project.json').exists()
    assert (target / '.wordassistant/evidence.json').exists()

def test_capabilities_explain_core_and_advanced(capsys):
    assert run(['capabilities', '--json']) == 0
    out = capsys.readouterr().out
    assert 'replace' in out
    assert 'tracked_changes' in out

def test_profiles_command_lists_variants(capsys):
    assert run(['profiles', '--json']) == 0
    out = capsys.readouterr().out
    assert 'hcmunre_dacn_2026_2027' in out
    assert 'report' in out and 'proposal' in out

def test_profile_show_and_validate(capsys):
    code = run(['profile', 'show', 'generic', '--json'])
    out = capsys.readouterr().out
    assert code == 0
    assert 'typography' in out
    
    code = run(['profile', 'validate', str(ROOT / 'profiles/generic.json'), '--json'])
    out = capsys.readouterr().out
    assert code == 0
    assert '"valid": true' in out

def test_inspect_cli(capsys):
    code = run(['inspect', str(GUIDE), '--json'])
    out = capsys.readouterr().out
    assert code == 0
    assert 'paragraphs' in out
    assert 'sections' in out

def test_evidence_cli_crud(tmp_path, capsys):
    reg = tmp_path / 'evidence.json'
    
    # 1. Add
    code = run([
        'evidence', 'add', str(reg),
        '--id', 'ev1',
        '--title', 'Machine Learning Paper',
        '--authors', 'John Doe, Jane Smith',
        '--year', '2023',
        '--url', 'https://doi.org/10.1234/example',
        '--verified-by', 'Alice',
        '--json'
    ])
    assert code == 0
    capsys.readouterr()
    
    # 2. Get
    code = run(['evidence', 'get', str(reg), 'ev1', '--json'])
    out = capsys.readouterr().out
    assert code == 0
    assert 'Machine Learning Paper' in out
    
    # 3. List
    code = run(['evidence', 'list', str(reg), '--json'])
    out = capsys.readouterr().out
    assert code == 0
    assert 'ev1' in out
    
    # 4. Validate
    code = run(['evidence', 'validate', str(reg), '--json'])
    out = capsys.readouterr().out
    assert code == 0
    assert '"valid": true' in out
    
    # 5. Remove
    code = run(['evidence', 'remove', str(reg), 'ev1', '--json'])
    assert code == 0

def test_verify_orchestrator_cli(tmp_path, capsys):
    out = tmp_path / 'test_doc.docx'
    run(['scaffold', str(out), '--profile', 'generic', '--variant', 'default', '--title', 'Final Report', '--json'])
    capsys.readouterr()
    
    d = Document(out)
    for p in d.paragraphs:
        if '[Document content]' in p.text or '[Section content...]' in p.text or '[Front matter content]' in p.text:
            p.text = 'Completed report content without draft placeholders.'
    d.save(out)
    
    code = run(['verify', str(out), '--profile', 'generic', '--variant', 'default', '--json'])
    out_txt = capsys.readouterr().out
    assert code == 0
    assert '"valid": true' in out_txt
    assert 'inventory' in out_txt
