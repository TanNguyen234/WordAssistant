from pathlib import Path
import hashlib
import json
import subprocess
import sys
import wordassistant

ROOT = Path(__file__).resolve().parents[1]

def test_version_single_source_of_truth():
    version_file = ROOT / "VERSION"
    assert version_file.exists()
    assert version_file.read_text(encoding="utf-8").strip() == wordassistant.__version__

def test_all_profiles_and_use_cases_mirrored():
    # Every json in profiles/ must match src/wordassistant/data/profiles/
    for p in (ROOT / "profiles").glob("*.json"):
        target = ROOT / "src/wordassistant/data/profiles" / p.name
        assert target.exists(), f"Missing mirrored profile: {p.name}"
        assert hashlib.sha256(p.read_bytes()).hexdigest() == hashlib.sha256(target.read_bytes()).hexdigest()

    # Every asset in use_cases must match src/wordassistant/data/use_cases
    for uc in (ROOT / "use_cases").iterdir():
        if uc.is_dir():
            for f in uc.rglob("*"):
                if f.is_file() and not f.name.endswith(".md"):
                    rel = f.relative_to(ROOT / "use_cases")
                    target = ROOT / "src/wordassistant/data/use_cases" / rel
                    assert target.exists(), f"Missing mirrored use case asset: {rel}"
                    assert hashlib.sha256(f.read_bytes()).hexdigest() == hashlib.sha256(target.read_bytes()).hexdigest()


def test_sync_check_ignores_python_bytecode_cache():
    cache = ROOT / "src/wordassistant/data/agent/__pycache__"
    cache.mkdir(parents=True, exist_ok=True)
    bytecode = cache / "sync-check-test.pyc"
    bytecode.write_bytes(b"cache")
    try:
        completed = subprocess.run(
            [sys.executable, "scripts/sync_package_data.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr
    finally:
        bytecode.unlink(missing_ok=True)
