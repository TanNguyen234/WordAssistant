import json
import hashlib
from pathlib import Path

from wordassistant.capabilities import export_feature_matrix
from wordassistant.runtime import build_default_registry, build_default_router


ROOT = Path(__file__).resolve().parents[2]


def test_documented_feature_matrix_matches_runtime_registry():
    registry = build_default_registry()
    expected = export_feature_matrix(registry, build_default_router(registry))
    documented = json.loads(
        (ROOT / "docs" / "word_feature_matrix.json").read_text(encoding="utf-8")
    )
    assert documented == expected


def test_unverified_native_operations_are_not_marked_verified():
    registry = build_default_registry()
    matrix = export_feature_matrix(registry, build_default_router(registry))
    operations = {item["name"]: item for item in matrix["operations"]}
    assert operations["comment.reply"]["evidence"]["native_roundtrip"] == "UNVERIFIED"
    assert operations["field.update_all"]["evidence"]["dynamic_result"] == "VERIFIED"


def test_every_verified_evidence_source_exists():
    registry = build_default_registry()
    matrix = export_feature_matrix(registry, build_default_router(registry))
    for operation in matrix["operations"]:
        for dimension, status in operation["evidence"].items():
            if status == "VERIFIED":
                sources = operation["evidence_sources"][dimension]
                assert sources, (operation["name"], dimension)
                for source in sources:
                    assert (ROOT / source.split("::", 1)[0]).is_file(), source


def test_native_live_evidence_is_zero_skip_and_bound_to_current_sources():
    evidence_path = ROOT / "docs/reviews/native-word-live-evidence-2026-08-30.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    run = evidence["run"]
    assert run["status"] == "PASS"
    assert run["exit_code"] == 0
    assert len(run["tests"]) >= 6
    assert run["consecutive_repetitions"] >= 3
    assert run["passed"] == len(run["tests"]) * run["consecutive_repetitions"]
    assert run["failed"] == run["skipped"] == 0

    for relative_path, expected_hash in evidence["source_sha256"].items():
        actual_hash = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        assert actual_hash.upper() == expected_hash.upper(), relative_path


def test_every_verified_native_claim_links_to_live_run_evidence():
    registry = build_default_registry()
    matrix = export_feature_matrix(registry, build_default_router(registry))
    for operation in matrix["operations"]:
        for dimension in ("native_roundtrip", "dynamic_result"):
            if operation["evidence"][dimension] == "VERIFIED":
                runs = operation["evidence_runs"][dimension]
                assert runs, (operation["name"], dimension)
                for run in runs:
                    assert (ROOT / run).is_file(), run
