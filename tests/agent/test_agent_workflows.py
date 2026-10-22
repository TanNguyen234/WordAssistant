import json
from pathlib import Path
import shlex

ROOT = Path(__file__).resolve().parents[2]


def test_manifest_workflows_never_require_source_or_ooxml_knowledge():
    manifest = json.loads((ROOT / "wordassistant-agent.json").read_text(encoding="utf-8"))
    serialized = json.dumps(manifest, ensure_ascii=False).casefold()
    assert "src/wordassistant" not in serialized
    assert "xpath" not in serialized
    for workflow_definition in manifest["recommended_workflows"].values():
        workflow = (
            workflow_definition["steps"]
            if isinstance(workflow_definition, dict)
            else workflow_definition
        )
        assert workflow[:2] == [
            "wordassistant doctor --json",
            "wordassistant capabilities --json",
        ]
        assert workflow[2].startswith("wordassistant inspect") or workflow[2].startswith("wordassistant create")
        assert any("verify" in step for step in workflow)


def test_native_workflow_has_machine_readable_capability_preconditions():
    manifest = json.loads((ROOT / "wordassistant-agent.json").read_text(encoding="utf-8"))
    workflow = manifest["recommended_workflows"]["layout_change"]
    assert workflow["requires_operation_statuses"] == {
        "field.update_all": "SUPPORTED_NATIVE",
        "render.pdf": "SUPPORTED_NATIVE",
    }
    assert "Stop" in workflow["on_unavailable"]


def test_long_edit_workflow_uses_real_option_names_and_real_mutation():
    manifest = json.loads((ROOT / "wordassistant-agent.json").read_text(encoding="utf-8"))
    workflow = manifest["recommended_workflows"]["long_document_edit"]
    edit_steps = [shlex.split(step) for step in workflow if " edit " in step]

    assert len(edit_steps) == 2
    assert "--dry-run" in edit_steps[0]
    assert "--dry-run" not in edit_steps[1]
    assert all("--selector" in step for step in edit_steps)
    section_selector = edit_steps[0][edit_steps[0].index("--selector") + 1]
    assert json.loads(section_selector) == {
        "type": "heading",
        "text": "EXACT_SECTION_HEADING",
    }
    assert '"pattern"' in edit_steps[0][edit_steps[0].index("--options") + 1]
    assert '"replacement"' in edit_steps[0][edit_steps[0].index("--options") + 1]
    assert workflow[-1].startswith("wordassistant verify revised.docx")
    assert "inspect thesis.docx --summary" in workflow[2]
    bounded_context_steps = [step for step in workflow if "wordassistant context" in step]
    assert len(bounded_context_steps) == 2
    assert all("--max-tokens 4000" in step for step in bounded_context_steps)
    assert "--only-section" in bounded_context_steps[1]


def test_create_report_workflow_encodes_complete_delivery_sequence():
    manifest = json.loads((ROOT / "wordassistant-agent.json").read_text(encoding="utf-8"))
    workflow = manifest["recommended_workflows"]["create_report"]
    steps = workflow["steps"]
    serialized = "\n".join(steps)

    assert workflow["requires_operation_statuses"] == {
        "field.update_all": "SUPPORTED_NATIVE",
        "render.pdf": "SUPPORTED_NATIVE",
    }
    assert "compose report.docx --output authored.docx" in serialized
    assert "validate formatted.docx" in serialized
    assert "field update-all formatted.docx --output refreshed.docx" in serialized
    assert "--native-fields --render --engine word" in serialized
    assert "INSPECT_EVERY_PATH_FROM_render.page_images" in steps
    assert "--visual-reviewed" in steps[-1]
    assert "--visual-review-token TOKEN_FROM_CHALLENGE" in steps[-1]
    assert "--delivery" in steps[-1]
