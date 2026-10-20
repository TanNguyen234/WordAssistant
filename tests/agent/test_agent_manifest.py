import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_agent_manifest_is_compact_and_actionable():
    manifest = json.loads((ROOT / "wordassistant-agent.json").read_text(encoding="utf-8"))
    assert manifest["version"] == 1
    # The two academic-source families extend the compact 30-family surface.
    assert len(manifest["commands"]) <= 32
    assert {"evidence", "research"} <= set(manifest["commands"])
    assert len(manifest["commands"]) == len(set(manifest["commands"]))
    assert {"inspect", "context", "create", "edit", "verify", "render"} <= set(manifest["commands"])
    assert manifest["capability_discovery_command"] == "wordassistant capabilities --json"
    assert "long_document_edit" in manifest["recommended_workflows"]
    assert {"protect", "properties", "mail-merge"} <= set(manifest["commands"])
    assert manifest["orchestration"]["manifest"] == "antigravity-workflow.json"
    assert manifest["orchestration"]["runner"] == "wordassistant-antigravity"
    assert "run_antigravity_workflow.py" in manifest["orchestration"]["repository_runner"]
    assert "only when the user explicitly requests it" in manifest["orchestration"]["repository_runner"]
    assert "Do not invoke the runner automatically" in manifest["orchestration"]["policy"]


def test_agent_manifest_has_fail_closed_delivery_gates():
    manifest = json.loads((ROOT / "wordassistant-agent.json").read_text(encoding="utf-8"))
    gates = manifest["delivery_gates"]

    assert gates["validation"] == "validate.valid == true"
    assert gates["verification"] == "verify.delivery_status == PASS"
    assert "content" in gates["visual_page_audit"].casefold()
    assert "dimensions" in gates["visual_page_audit"].casefold()
    assert "exact requested invariant" in gates["negative_tests"].casefold()
    assert gates["contradiction_policy"].startswith("FAIL")

    packaged = json.loads(
        (ROOT / "src" / "wordassistant" / "data" / "agent" / "wordassistant-agent.json").read_text(encoding="utf-8")
    )
    assert packaged["delivery_gates"] == gates
    assert packaged["delivery_completion_sequence"] == manifest["delivery_completion_sequence"]
    assert "visual-review-token" in gates["verification"] or "visual-review-token" in manifest["delivery_completion_sequence"]["final_pass"]


def test_agent_manifest_requires_course_essay_evidence_matrix():
    manifest = json.loads((ROOT / "wordassistant-agent.json").read_text(encoding="utf-8"))
    gate = manifest["delivery_gates"]["course_essay_evidence_matrix"].casefold()

    for required_evidence in (
        "every database table",
        "sample rows",
        "every function",
        "1366 px",
        "embedded",
        "12 mm",
        "multilevel numbering",
        "hình x.x",
    ):
        assert required_evidence in gate
