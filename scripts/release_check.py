from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

OFFICIAL_ASSETS = {
    ROOT / 'use_cases/hcmunre_dacn_2026_2027/assets/huong_dan_trinh_bay_dacn_2026_2027.docx':
        '0f3622dbcd74009fb0867e0d3fa4a1624a38983af502e55d48868edf33f74e78',
    ROOT / 'use_cases/hcmunre_dacn_2026_2027/assets/mau_de_cuong_do_an_chuyen_nganh.docx':
        'bb291a6de459e33267170c3dd9087903a0d9f1911086bbfc935cb9f7781904e6'
}

def run(cmd: list[str]) -> None:
    print('+', ' '.join(str(x) for x in cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)

def verify_source_hashes() -> None:
    for path, expected_hash in OFFICIAL_ASSETS.items():
        if not path.exists():
            raise FileNotFoundError(f"Official asset missing: {path}")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest().lower()
        if actual_hash != expected_hash.lower():
            raise ValueError(f"Asset byte mismatch for {path.name}: expected {expected_hash}, got {actual_hash}")
    print("source-asset-hashes: VERIFIED")

def main() -> None:
    print("=== 1. Checking Package Data Synchronization ===")
    run([sys.executable, 'scripts/sync_package_data.py', '--check'])

    print("\n=== 2. Verifying Official Source Asset Hashes ===")
    verify_source_hashes()

    print("\n=== 3. Running Pytest Suite ===")
    run([sys.executable, '-m', 'pytest', '-v'])

    print("\n=== 4. Verifying Python Compilation ===")
    run([sys.executable, '-m', 'compileall', '-q', 'src', 'tests'])

    print("\n=== 5. Running Document Indexing Smoke Check ===")
    env_cmd = [
        sys.executable, '-c',
        "from wordassistant.document.structure import index_docx; "
        "from pathlib import Path; "
        "r = Path('use_cases/hcmunre_dacn_2026_2027/assets'); "
        "a = index_docx(r / 'huong_dan_trinh_bay_dacn_2026_2027.docx'); "
        "b = index_docx(r / 'mau_de_cuong_do_an_chuyen_nganh.docx'); "
        "assert 10 <= len(a) <= 45 and 8 <= len(b) <= 30, f'Unexpected section counts: {len(a)}, {len(b)}'; "
        "print({'guidance_sections': len(a), 'proposal_sections': len(b)})"
    ]
    run(env_cmd)

    print("\n=== 6. Running CLI End-to-End Workflow Smoke Check ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        report_docx = tmp / 'test_report.docx'
        evidence_file = tmp / 'evidence.json'
        
        # doctor
        run([sys.executable, '-m', 'wordassistant.cli', 'doctor', '--json'])
        # profiles
        run([sys.executable, '-m', 'wordassistant.cli', 'profiles', '--json'])
        # scaffold
        run([
            sys.executable, '-m', 'wordassistant.cli', 'scaffold', str(report_docx),
            '--profile', 'hcmunre_dacn_2026_2027', '--variant', 'report',
            '--title', 'SMOKE TEST REPORT', '--json'
        ])
        # validate
        run([
            sys.executable, '-m', 'wordassistant.cli', 'validate', str(report_docx),
            '--profile', 'hcmunre_dacn_2026_2027', '--variant', 'report', '--json'
        ])
        # verify orchestrator
        run([
            sys.executable, '-m', 'wordassistant.cli', 'verify', str(report_docx),
            '--profile', 'hcmunre_dacn_2026_2027', '--variant', 'report', '--json'
        ])
        # replace dry-run
        run([
            sys.executable, '-m', 'wordassistant.cli', 'replace', str(report_docx),
            '--old', 'SMOKE TEST', '--new', 'HARDENED AUDIT', '--dry-run', '--json'
        ])
        # evidence
        run([
            sys.executable, '-m', 'wordassistant.cli', 'evidence', 'add', str(evidence_file),
            '--id', 'smoke1', '--title', 'Smoke Title', '--authors', 'Author A', '--year', '2024',
            '--url', 'https://example.com/smoke', '--verified-by', 'CI', '--json'
        ])
        run([sys.executable, '-m', 'wordassistant.cli', 'evidence', 'validate', str(evidence_file), '--json'])

    print('\n========================================')
    print('release-check: PASS')
    print('========================================')

if __name__ == '__main__':
    main()
