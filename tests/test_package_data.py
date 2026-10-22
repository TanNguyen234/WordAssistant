from pathlib import Path

def test_agent_entrypoints_present():
    root=Path(__file__).resolve().parents[1]
    assert (root/'wordassistant-agent.json').exists()
    assert (root/'src/wordassistant/data/agent/wordassistant-agent.json').read_bytes() == (root/'wordassistant-agent.json').read_bytes()
    assert (root/'.agents/skills/wordassistant/SKILL.md').exists()
    assert (root/'.agents/rules/wordassistant.md').exists()
    assert (root/'scripts/bootstrap.ps1').exists()
    assert not (root/'antigravity-workflow.json').exists()
    assert not (root/'scripts/run_antigravity_workflow.py').exists()
    assert not (root/'src/wordassistant/agent_runner.py').exists()

def test_packaged_profiles_and_hcmunre_sources_present():
    root=Path(__file__).resolve().parents[1]
    data=root/'src/wordassistant/data'
    assert (data/'profiles/generic.json').exists()
    assert (data/'profiles/hcmunre_dacn_2026_2027.json').exists()
    assert (data/'use_cases/hcmunre_dacn_2026_2027/assets/huong_dan_trinh_bay_dacn_2026_2027.docx').exists()
    assert (data/'use_cases/hcmunre_dacn_2026_2027/assets/mau_de_cuong_do_an_chuyen_nganh.docx').exists()
