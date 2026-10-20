import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]


def _manifest():
    return json.loads((ROOT / "antigravity-workflow.json").read_text(encoding="utf-8"))


def _runner():
    path = ROOT / "scripts" / "run_antigravity_workflow.py"
    spec = importlib.util.spec_from_file_location("antigravity_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_public_cli_subcommand_recognizes_bare_and_absolute_executables():
    runner = _runner()

    assert runner.uses_wordassistant_subcommand("wordassistant compose in.docx", "compose")
    assert runner.uses_wordassistant_subcommand(
        '& "D:\\Download\\WordAssistant\\.venv\\Scripts\\wordassistant.exe" compose in.docx',
        "compose",
    )
    assert runner.uses_wordassistant_subcommand(
        "/opt/wordassistant compose in.docx", "compose"
    )
    assert not runner.uses_wordassistant_subcommand("wordassistant create in.docx", "compose")


def test_recovered_live_result_is_bound_to_runner_owned_plan_hash():
    runner = _runner()
    result = {"test_result": {}}
    frozen_hash = "a" * 64

    runner.bind_recovered_plan_hash(
        "live_create_document",
        result,
        recovered=True,
        frozen_plan_sha256=frozen_hash,
    )

    assert result["test_result"]["plan_sha256"] == frozen_hash


def test_workflow_is_a_small_fail_closed_state_machine():
    manifest = _manifest()

    assert manifest["version"] == 1
    assert manifest["execution"]["max_objectives_per_invocation"] == 1
    assert manifest["execution"]["fresh_session_per_phase"] is True
    assert manifest["execution"]["stop_on_gate_failure"] is True
    assert manifest["execution"]["model"] == "gemini-3.8-flash-high"
    assert manifest["execution"]["effort"] is None

    phases = manifest["phases"]
    assert [phase["id"] for phase in phases] == [
        "intake",
        "discover",
        "plan",
        "implement",
        "focused_test",
        "live_create_document",
        "live_apply_features",
        "live_native_finalize",
        "live_visual_audit",
        "live_negative_tests",
        "constraint_audit",
        "review_architecture",
        "review_word_fidelity",
        "review_test_release",
        "final_gate",
    ]
    assert all(len(phase["objective"].splitlines()) == 1 for phase in phases)
    assert all(phase["max_tasks"] == 1 for phase in phases)


def test_mutating_phase_is_narrow_and_every_transition_has_a_constraint_gate():
    manifest = _manifest()
    phases = {phase["id"]: phase for phase in manifest["phases"]}

    assert phases["implement"]["access"] == "write"
    assert phases["implement"]["requires"] == ["plan"]
    assert phases["implement"]["write_policy"]["plan_allowlist_only"] is True
    assert phases["implement"]["write_policy"]["one_root_cause_change"] is True

    for phase in manifest["phases"]:
        assert "constraint_monitor" in phase["gates"]

    for reviewer in (
        phases["review_architecture"],
        phases["review_word_fidelity"],
        phases["review_test_release"],
    ):
        assert reviewer["access"] == "read"
        assert reviewer["fresh_context"] is True
        assert reviewer["may_edit"] is False

    focuses = {
        tuple(phases[name]["focus"])
        for name in (
            "review_architecture",
            "review_word_fidelity",
            "review_test_release",
        )
    }
    assert len(focuses) == 3


def test_lanes_select_only_needed_phases_and_live_qa_cannot_edit_source():
    manifest = _manifest()
    lanes = manifest["lanes"]

    assert lanes["read_only"] == ["intake", "discover", "constraint_audit"]
    assert "implement" in lanes["change"]
    assert "implement" not in lanes["live_qa"]
    assert "discover" not in lanes["live_qa"]
    assert lanes["live_qa"][2:7] == [
        "live_create_document",
        "live_apply_features",
        "live_native_finalize",
        "live_visual_audit",
        "live_negative_tests",
    ]
    assert lanes["live_qa"][-1] == "final_gate"
    assert manifest["constraints"]["live_qa_write_roots"] == [
        "artifacts/antigravity-live-test/"
    ]


def test_runner_uses_model_variant_without_unsupported_effort_flag():
    runner = _runner()
    manifest = _manifest()
    command = runner.build_agy_command(
        manifest,
        phase_id="discover",
        prompt="bounded discovery",
        executable="agy.exe",
    )

    assert command[0] == "agy.exe"
    assert command[command.index("--model") + 1] == "gemini-3.8-flash-high"
    assert "--effort" not in command
    assert command[command.index("--add-dir") + 1] == str(ROOT)
    assert "--sandbox" in command
    assert "--dangerously-skip-permissions" in command
    assert "--json-schema" in command
    assert command.count("--print") == 1
    assert command[-1] == "bounded discovery"
    assert "--mode" in command
    assert command[command.index("--mode") + 1] == "plan"


def test_antigravity_is_not_an_automatic_skill_or_runner_requirement():
    runner = _runner()
    rule = (ROOT / ".agents" / "rules" / "wordassistant.md").read_text(encoding="utf-8")
    prompt = runner.build_phase_prompt(
        _manifest(),
        phase_id="intake",
        request="bounded request",
        previous_result=None,
        allowed_paths=set(),
    )
    assert "Do not invoke `agy`" in rule
    assert "only when the user explicitly asks" in rule
    assert "antigravity-orchestrator" not in rule
    assert "$antigravity-orchestrator" not in prompt


def test_constraint_monitor_rejects_changes_outside_plan_allowlist():
    runner = _runner()

    assert runner.out_of_scope_paths(
        changed_paths={"src/wordassistant/cli.py", "README.md"},
        allowed_paths={"src/wordassistant/cli.py"},
    ) == {"README.md"}
    assert runner.out_of_scope_paths(
        changed_paths={"tests/agent/test_cli.py"},
        allowed_paths={"tests/agent/"},
    ) == set()
    assert runner.out_of_scope_paths(
        changed_paths={"github/workflows/ci.yml"},
        allowed_paths={".github/workflows/ci.yml"},
    ) == {"github/workflows/ci.yml"}


def test_phase_result_must_satisfy_declared_machine_gate():
    runner = _runner()
    manifest = _manifest()
    phase = next(item for item in manifest["phases"] if item["id"] == "plan")

    ok, reasons = runner.validate_phase_result(
        {
            "status": "PASS",
            "phase": "plan",
            "scope": ["src/wordassistant/cli.py"],
            "evidence": ["capabilities.json"],
            "next_phase": "implement",
            "gate_results": [
                {"gate": gate, "status": "PASS", "evidence": ["observed"]}
                for gate in phase["gates"]
            ],
            "write_allowlist": ["src/wordassistant/cli.py"],
            "focused_test": ".venv/Scripts/python.exe -m pytest tests/test_cli.py -q",
        },
        expected_phase="plan",
        phase_definition=phase,
        lane="change",
    )
    assert ok is True
    assert reasons == []

    ok, reasons = runner.validate_phase_result(
        {"status": "PASS", "phase": "plan", "scope": []},
        expected_phase="plan",
        phase_definition=phase,
        lane="change",
    )
    assert ok is False
    assert "evidence" in " ".join(reasons)


def test_machine_gate_rejects_missing_or_self_failed_gate():
    runner = _runner()
    manifest = _manifest()
    phase = next(item for item in manifest["phases"] if item["id"] == "discover")
    result = {
        "status": "PASS",
        "phase": "discover",
        "scope": ["wordassistant-agent.json"],
        "evidence": ["read manifest"],
        "next_phase": "plan",
        "gate_results": [
            {"gate": "constraint_monitor", "status": "PASS", "evidence": ["clean"]},
            {"gate": "bounded_discovery", "status": "FAIL", "evidence": ["too broad"]},
        ],
    }

    ok, reasons = runner.validate_phase_result(
        result,
        expected_phase="discover",
        phase_definition=phase,
        lane="change",
    )
    assert ok is False
    assert any("evidence_cited" in reason for reason in reasons)
    assert any("bounded_discovery" in reason for reason in reasons)


def test_live_qa_rejects_caller_write_paths_and_run_dir_blind_spots(tmp_path):
    runner = _runner()
    manifest = _manifest()

    assert runner.resolve_allowed_paths(manifest, "live_qa", []) == {
        "artifacts/antigravity-live-test/"
    }
    try:
        runner.resolve_allowed_paths(manifest, "live_qa", ["src/"])
    except ValueError as exc:
        assert "does not accept" in str(exc)
    else:
        raise AssertionError("live_qa accepted a caller source allowlist")

    safe = runner.resolve_run_dir(
        ROOT, ROOT / "artifacts" / "antigravity-workflow" / "run-1", "read_only"
    )
    assert safe.is_relative_to(ROOT / "artifacts" / "antigravity-workflow")
    try:
        runner.resolve_run_dir(ROOT, ROOT / "src" / "wordassistant", "read_only")
    except ValueError as exc:
        assert "must stay below" in str(exc)
    else:
        raise AssertionError("source directory was accepted as a log blind spot")


def test_handoff_fails_instead_of_truncating_reviewer_results():
    runner = _runner()
    manifest = _manifest()
    oversized = {
        "dependency_results": [
            {"phase": f"review-{index}", "evidence": ["x" * 6000]}
            for index in range(3)
        ]
    }

    try:
        runner.build_phase_prompt(
            manifest,
            phase_id="final_gate",
            request="review",
            previous_result=oversized,
            allowed_paths=set(),
        )
    except ValueError as exc:
        assert "exceeds" in str(exc)
    else:
        raise AssertionError("oversized reviewer evidence was silently truncated")


def test_timeout_preserves_partial_logs(tmp_path, monkeypatch):
    runner = _runner()
    manifest = _manifest()
    phase = next(item for item in manifest["phases"] if item["id"] == "intake")
    terminated = []

    class TimedOutProcess:
        pid = 4242
        returncode = None

        def __init__(self, command, **kwargs):
            self.command = command

        def communicate(self, timeout):
            raise subprocess.TimeoutExpired(
                self.command, timeout, output="partial", stderr="slow"
            )

        def poll(self):
            return None

    monkeypatch.setattr(runner.subprocess, "Popen", TimedOutProcess)
    monkeypatch.setattr(
        runner, "_terminate_process_tree", lambda process: terminated.append(process.pid)
    )
    try:
        runner.run_phase(
            command=["agy.exe"],
            phase_id="intake",
            root=ROOT,
            log_dir=tmp_path,
            timeout_seconds=1,
            phase_definition=phase,
            lane="read_only",
        )
    except RuntimeError as exc:
        assert "process tree terminated" in str(exc)
    else:
        raise AssertionError("timeout was accepted")
    assert (tmp_path / "intake.stdout.json").read_text(encoding="utf-8") == "partial"
    assert (tmp_path / "intake.stderr.txt").read_text(encoding="utf-8") == "slow"
    assert terminated == [4242]


def test_windows_timeout_cleanup_traces_descendants_after_parent_exit(monkeypatch):
    runner = _runner()
    if runner.os.name != "nt":
        return
    calls = []

    class ExitedParent:
        pid = 4242

        def poll(self):
            return 0

    monkeypatch.setattr(runner.shutil, "which", lambda _: "pwsh.exe")
    def record_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(runner.subprocess, "run", record_run)

    runner._terminate_process_tree(ExitedParent())

    assert len(calls) == 1
    command, kwargs = calls[0]
    assert kwargs["env"]["WORDASSISTANT_ROOT_PROCESS_ID"] == "4242"
    assert "Get-CimInstance Win32_Process" in command[-1]
    assert "Stop-Process" in command[-1]


def test_live_qa_dry_run_emits_every_phase_without_writing(tmp_path, capsys):
    runner = _runner()
    dry_run_dir = ROOT / "artifacts" / "antigravity-live-test" / "dry-run-regression"

    exit_code = runner.main(
        [
            "--lane",
            "live_qa",
            "--request",
            "exercise the public contract",
            "--run-dir",
            str(dry_run_dir),
            "--dry-run",
        ]
    )

    output = capsys.readouterr().out
    manifest = _manifest()
    assert exit_code == 0
    assert output.count('"command"') == len(manifest["lanes"]["live_qa"])
    assert not dry_run_dir.exists()


def test_live_workspace_exposes_contracts_but_not_source(tmp_path):
    runner = _runner()
    workspace = runner.prepare_live_workspace(ROOT, tmp_path / "live")

    assert (workspace / "GEMINI.md").is_file()
    assert (workspace / "wordassistant-agent.json").is_file()
    assert (workspace / ".agents" / "skills" / "wordassistant" / "SKILL.md").is_file()
    assert not (workspace / "src").exists()
    assert not (workspace / "tests").exists()
    assert not (workspace / ".git").exists()

    (workspace / "src").mkdir()
    try:
        runner.prepare_live_workspace(ROOT, workspace)
    except ValueError as exc:
        assert "new and empty" in str(exc)
    else:
        raise AssertionError("stale live workspace was reused")


def test_review_routing_and_test_access_are_scope_sensitive():
    runner = _runner()
    manifest = _manifest()
    focused = next(item for item in manifest["phases"] if item["id"] == "focused_test")

    assert runner.phase_access(focused, "change") == "read"
    assert runner.phase_access(focused, "live_qa") == "write"
    assert runner.word_review_applicable("Update packaging metadata", {"pyproject.toml"}) is False
    assert runner.word_review_applicable("Update WordAssistant packaging metadata", {"pyproject.toml"}) is False
    assert runner.word_review_applicable("Fix DOCX pagination", {"src/wordassistant/cli.py"}) is True
    assert runner.word_review_applicable(
        "Fix section break insertion", {"src/wordassistant/operations/sections.py"}
    ) is True
    assert runner.word_review_applicable(
        "Correct backend routing", {"src/wordassistant/backends/router.py"}
    ) is True
    command = runner.build_agy_command(
        manifest,
        phase_id="focused_test",
        prompt="test",
        executable="agy.exe",
        lane="change",
    )
    assert command[command.index("--mode") + 1] == "plan"
    live_command = runner.build_agy_command(
        manifest,
        phase_id="focused_test",
        prompt="test",
        executable="agy.exe",
        lane="live_qa",
        isolated_project=True,
        timeout_seconds=61,
    )
    assert "--new-project" in live_command
    assert live_command[live_command.index("--print-timeout") + 1] == "61s"


def test_repository_root_is_not_caller_subdirectory_and_delta_keeps_hashes():
    runner = _runner()

    assert runner.repository_root(ROOT / "scripts") == ROOT
    assert runner.delta_records(
        {"src/a.py": "before", "README.md": "same"},
        {"src/a.py": "after", "README.md": "same"},
    ) == [
        {
            "path": "src/a.py",
            "before_sha256": "before",
            "after_sha256": "after",
        }
    ]


def test_phase_specific_contract_rejects_fabricated_generic_pass():
    runner = _runner()
    manifest = _manifest()
    intake = next(item for item in manifest["phases"] if item["id"] == "intake")
    generic = {
        "status": "PASS",
        "phase": "intake",
        "scope": ["GEMINI.md"],
        "evidence": ["claimed"],
        "next_phase": "discover",
        "gate_results": [
            {"gate": gate, "status": "PASS", "evidence": ["claimed"]}
            for gate in intake["gates"]
        ],
    }

    ok, reasons = runner.validate_phase_result(
        generic,
        expected_phase="intake",
        phase_definition=intake,
        lane="read_only",
    )
    assert ok is False
    assert any("request_contract" in reason for reason in reasons)


def test_successful_change_implementation_cannot_be_noop():
    runner = _runner()
    manifest = _manifest()
    phase = next(item for item in manifest["phases"] if item["id"] == "implement")
    result = {
        "status": "PASS",
        "phase": "implement",
        "scope": ["src/wordassistant/cli.py"],
        "evidence": ["claimed implementation"],
        "next_phase": "focused_test",
        "gate_results": [
            {"gate": gate, "status": "PASS", "evidence": ["claimed"]}
            for gate in phase["gates"]
        ],
        "implementation": {"changed_paths": []},
    }

    ok, reasons = runner.validate_phase_result(
        result,
        expected_phase="implement",
        phase_definition=phase,
        lane="change",
    )
    assert ok is False
    assert any("no-op" in reason for reason in reasons)


def test_live_phase_requires_nonempty_hashed_workspace_artifacts(tmp_path):
    runner = _runner()
    manifest = _manifest()
    phase = next(
        item for item in manifest["phases"] if item["id"] == "live_create_document"
    )
    result = {
        "status": "PASS",
        "phase": "live_create_document",
        "scope": [str(tmp_path)],
        "evidence": ["claimed"],
        "next_phase": "live_apply_features",
        "gate_results": [
            {"gate": gate, "status": "PASS", "evidence": ["claimed"]}
            for gate in phase["gates"]
        ],
        "test_result": {
            "command": "wordassistant create",
            "exit_code": 0,
            "expected_invariant": "document created",
            "observed_invariant": "document created",
            "artifacts": [],
            "plan_sha256": "a" * 64,
        },
    }
    ok, reasons = runner.validate_phase_result(
        result,
        expected_phase="live_create_document",
        phase_definition=phase,
        lane="live_qa",
    )
    assert ok is False
    assert any("artifacts are empty" in reason for reason in reasons)

    artifact = tmp_path / "report.docx"
    artifact.write_bytes(b"docx")
    digest = __import__("hashlib").sha256(artifact.read_bytes()).hexdigest()
    assert runner.verify_artifact_records(
        [{"path": "report.docx", "sha256": digest, "role": "output"}],
        tmp_path,
    ) == [{"path": str(artifact.resolve()), "sha256": digest, "role": "output"}]

    reference = {
        "result_file": str(artifact),
        "sha256": digest,
    }
    runner.verify_result_reference(reference)
    artifact.write_bytes(b"changed")
    try:
        runner.verify_result_reference(reference)
    except RuntimeError as exc:
        assert "hash changed" in str(exc)
    else:
        raise AssertionError("mutable frozen-plan reference was accepted")

    predecessor = {("authored.docx", "a" * 64), ("assets.json", "b" * 64)}
    assert runner.missing_handoff_outputs(
        predecessor, {("authored.docx", "a" * 64)}
    ) == {("assets.json", "b" * 64)}
    assert runner.missing_handoff_outputs(
        {(".wordassistant-handoff/authored.docx", "a" * 64)},
        {("authored.docx", "a" * 64)},
    ) == set()
    assert runner.missing_handoff_outputs(predecessor, predecessor) == set()


def test_native_first_pass_can_truthfully_require_visual_review():
    runner = _runner()
    manifest = _manifest()
    phase = next(
        item for item in manifest["phases"] if item["id"] == "live_native_finalize"
    )
    result = {
        "status": "PASS",
        "phase": "live_native_finalize",
        "scope": ["artifacts/live"],
        "evidence": ["native render completed; visual review remains"],
        "next_phase": "live_visual_audit",
        "gate_results": [
            {"gate": gate, "status": "PASS", "evidence": ["observed"]}
            for gate in phase["gates"]
        ],
        "test_result": {
            "command": "wordassistant verify final.docx --render --json",
            "exit_code": 1,
            "expected_invariant": "REVIEW_REQUIRED before page inspection",
            "observed_invariant": "REVIEW_REQUIRED with challenge token",
            "artifacts": [
                {"path": "final.docx", "sha256": "b" * 64, "role": "output"}
            ],
            "plan_sha256": "a" * 64,
        },
    }

    ok, reasons = runner.validate_phase_result(
        result,
        expected_phase="live_native_finalize",
        phase_definition=phase,
        lane="live_qa",
    )

    assert ok, reasons
