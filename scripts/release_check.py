from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from docx import Document

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
    run([sys.executable, '-m', 'compileall', '-q', 'src', 'tests', 'scripts'])

    print("\n=== 5. Running Document Indexing & Context Hard Budget Check ===")
    context_cmd = [
        sys.executable, '-c',
        "from wordassistant.document.structure import index_docx; "
        "from wordassistant.context.retrieve import build_context; "
        "from pathlib import Path; "
        "r = Path('use_cases/hcmunre_dacn_2026_2027/assets'); "
        "a = index_docx(r / 'huong_dan_trinh_bay_dacn_2026_2027.docx'); "
        "b = index_docx(r / 'mau_de_cuong_do_an_chuyen_nganh.docx'); "
        "assert 10 <= len(a) <= 45 and 8 <= len(b) <= 30, f'Unexpected section counts: {len(a)}, {len(b)}'; "
        "ctx = build_context(a, 'IEEE font size and format', max_tokens=1500); "
        "assert ctx.estimated_tokens <= 1500, f'Hard budget exceeded: {ctx.estimated_tokens} > 1500'; "
        "print({'guidance_sections': len(a), 'proposal_sections': len(b), 'estimated_tokens': ctx.estimated_tokens})"
    ]
    run(context_cmd)

    print("\n=== 6. Running CLI End-to-End Workflow Smoke Check ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        report_docx = tmp / 'test_report.docx'
        proposal_docx = tmp / 'test_proposal.docx'
        generic_docx = tmp / 'test_generic.docx'
        evidence_file = tmp / 'evidence.json'
        
        # doctor
        run([sys.executable, '-m', 'wordassistant.cli', 'doctor', '--json'])
        # capabilities & advanced
        run([sys.executable, '-m', 'wordassistant.cli', 'capabilities', '--json'])
        run([sys.executable, '-m', 'wordassistant.cli', 'advanced', 'status', '--json'])
        # profiles
        run([sys.executable, '-m', 'wordassistant.cli', 'profiles', '--json'])
        run([sys.executable, '-m', 'wordassistant.cli', 'profile', 'validate', 'generic', '--json'])
        run([sys.executable, '-m', 'wordassistant.cli', 'profile', 'validate', 'hcmunre_dacn_2026_2027', '--json'])
        # scaffold generic & verify
        run([
            sys.executable, '-m', 'wordassistant.cli', 'scaffold', str(generic_docx),
            '--profile', 'generic', '--variant', 'default', '--title', 'GENERIC DOC', '--json'
        ])
        run([
            sys.executable, '-m', 'wordassistant.cli', 'verify', str(generic_docx),
            '--profile', 'generic', '--variant', 'default', '--json'
        ])
        # scaffold proposal clone
        run([
            sys.executable, '-m', 'wordassistant.cli', 'scaffold', str(proposal_docx),
            '--profile', 'hcmunre_dacn_2026_2027', '--variant', 'proposal', '--json'
        ])
        # scaffold report
        run([
            sys.executable, '-m', 'wordassistant.cli', 'scaffold', str(report_docx),
            '--profile', 'hcmunre_dacn_2026_2027', '--variant', 'report',
            '--title', 'SMOKE TEST REPORT', '--json'
        ])
        # draft validate on fresh scaffold
        run([
            sys.executable, '-m', 'wordassistant.cli', 'validate', str(report_docx),
            '--profile', 'hcmunre_dacn_2026_2027', '--variant', 'report', '--json'
        ])
        # Populate references in report and verify
        d = Document(report_docx)
        for idx in range(1, 12):
            d.add_paragraph(f"[{idx}] Tác giả {idx}, Tên tài liệu {idx}, Nhà xuất bản {idx}, 202{idx % 5}.")
        d.save(report_docx)
        
        # verify orchestrator (without render)
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
            sys.executable, '-m', 'wordassistant.cli', 'evidence', 'add',
            '--id', 'smoke1', '--title', 'Smoke Title', '--authors', 'Author A', '--year', '2024',
            '--url', 'https://example.com/smoke', '--verified-by', 'CI',
            str(evidence_file), '--json'
        ])
        run([sys.executable, '-m', 'wordassistant.cli', 'evidence', 'validate', str(evidence_file), '--json'])

    print("\n=== 7. Verifying LibreOffice Render Availability ===")
    from wordassistant.doctor import status
    st = status()
    if st['libreoffice']:
        print("libreoffice-render: AVAILABLE")
    else:
        print("libreoffice-render: SKIPPED_WITH_REASON (LibreOffice binary not on PATH/default locations)")

    print("\n=== 8. Wheel Build and Clean Venv Smoke Test ===")
    dist_dir = ROOT / 'dist'
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    run([sys.executable, '-m', 'build', '--wheel'])
    wheel_files = list(dist_dir.glob('*.whl'))
    assert len(wheel_files) == 1, f"Expected 1 wheel file in dist/, found {len(wheel_files)}"
    wheel_file = wheel_files[0]
    print(f"wheel-built: {wheel_file.name}")

    with tempfile.TemporaryDirectory() as clean_env_dir:
        venv_path = Path(clean_env_dir) / 'test_env'
        run([sys.executable, '-m', 'venv', str(venv_path)])
        pip_exe = str(venv_path / ('Scripts/pip.exe' if sys.platform == 'win32' else 'bin/pip'))
        py_exe = str(venv_path / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python'))
        wa_exe = str(venv_path / ('Scripts/wordassistant.exe' if sys.platform == 'win32' else 'bin/wordassistant'))
        run([pip_exe, 'install', '--quiet', str(wheel_file)])
        
        # Test CLI invocation via python -m and entrypoint executable
        run([py_exe, '-m', 'wordassistant.cli', 'doctor', '--json'])
        if Path(wa_exe).exists():
            run([wa_exe, 'doctor', '--json'])
        print('clean-venv-smoke: OK')

    print('\n========================================')
    print('release-check: PASS')
    print('========================================')

if __name__ == '__main__':
    main()
