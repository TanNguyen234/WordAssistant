from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from docx import Document

import os

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]

OFFICIAL_ASSETS = {
    ROOT / 'use_cases/hcmunre_dacn_2026_2027/assets/huong_dan_trinh_bay_dacn_2026_2027.docx':
        '0f3622dbcd74009fb0867e0d3fa4a1624a38983af502e55d48868edf33f74e78',
    ROOT / 'use_cases/hcmunre_dacn_2026_2027/assets/mau_de_cuong_do_an_chuyen_nganh.docx':
        'bb291a6de459e33267170c3dd9087903a0d9f1911086bbfc935cb9f7781904e6'
}

def run(cmd: list[str]) -> None:
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    try:
        print('+', ' '.join(str(x) for x in cmd))
    except Exception:
        print('+', str(cmd[0]))
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)

def run_expect_failure(cmd: list[str]) -> None:
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    try:
        print('+ [expect-fail]', ' '.join(str(x) for x in cmd))
    except Exception:
        print('+ [expect-fail]', str(cmd[0]))
    res = subprocess.run(cmd, cwd=ROOT, env=env)
    assert res.returncode != 0, f"Expected non-zero exit code, got {res.returncode}"

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
        "from wordassistant.document.model import DocumentSection; "
        "from pathlib import Path; "
        "r = Path('use_cases/hcmunre_dacn_2026_2027/assets'); "
        "a = index_docx(r / 'huong_dan_trinh_bay_dacn_2026_2027.docx'); "
        "b = index_docx(r / 'mau_de_cuong_do_an_chuyen_nganh.docx'); "
        "assert 10 <= len(a) <= 45 and 8 <= len(b) <= 30, f'Unexpected section counts: {len(a)}, {len(b)}'; "
        "ctx = build_context(a, 'trích dẫn nguồn tài liệu gốc IEEE', max_tokens=1500); "
        "assert ctx.estimated_tokens <= 1500, f'Hard budget exceeded: {ctx.estimated_tokens} > 1500'; "
        "assert any('trích dẫn' in s.title.lower() or 'tài liệu' in s.title.lower() or 'ieee' in s.text.lower() for s in ctx.sections), 'Context missing relevant citation guidance'; "
        "stress_secs = [DocumentSection(f'sec_{i}', f'Section {i} Topic Title', f'Text content of paragraph {i} in stress document.', 1, None, i) for i in range(200)]; "
        "stress_ctx = build_context(stress_secs, 'Topic Title 150', max_tokens=2000); "
        "assert stress_ctx.estimated_tokens <= 2000, 'Stress token budget exceeded'; "
        "assert any(s.section_id == 'sec_150' for s in stress_ctx.sections), 'Stress query missed exact target'; "
        "print({'guidance_sections': len(a), 'proposal_sections': len(b), 'estimated_tokens': ctx.estimated_tokens, 'stress_status': 'PASS'})"
    ]
    run(context_cmd)

    print("\n=== 6. Running CLI End-to-End Workflow Smoke & Verification Gates ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        report_docx = tmp / 'test_report.docx'
        proposal_docx = tmp / 'test_proposal.docx'
        generic_docx = tmp / 'test_generic.docx'
        neg_report_docx = tmp / 'test_neg_report.docx'
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
        
        # A. Draft scaffold smoke & negative verify proof
        run([
            sys.executable, '-m', 'wordassistant.cli', 'scaffold', str(report_docx),
            '--profile', 'hcmunre_dacn_2026_2027', '--variant', 'report',
            '--title', 'XAY DUNG HE THONG RAG',
            '--student', 'NGUYEN VAN A - 2351010001',
            '--supervisor', 'TS. NGUYEN VAN B',
            '--json'
        ])
        # Draft validate on fresh scaffold must succeed
        run([
            sys.executable, '-m', 'wordassistant.cli', 'validate', str(report_docx),
            '--profile', 'hcmunre_dacn_2026_2027', '--variant', 'report', '--json'
        ])
        # Unedited scaffold MUST FAIL final verify because placeholders remain
        run_expect_failure([
            sys.executable, '-m', 'wordassistant.cli', 'verify', str(report_docx),
            '--profile', 'hcmunre_dacn_2026_2027', '--variant', 'report', '--json'
        ])
        print("draft-scaffold-negative-verify: OK (rejected as expected)")

        # B. Completed synthetic report fixture (passes verify)
        d = Document(report_docx)
        for p in d.paragraphs:
            if "[Front matter content]" in p.text:
                p.text = "Lời cảm ơn chi tiết và đầy đủ gửi đến thầy cô và gia đình."
            elif "[Section content...]" in p.text:
                p.text = "Nội dung nghiên cứu chi tiết của đồ án giải quyết trọn vẹn bài toán đặt ra."
            elif "[List of figures]" in p.text:
                p.text = "Hình 1.1: Sơ đồ kiến trúc\nHình 1.2: Lưu đồ xử lý"
            elif "[List of tables]" in p.text:
                p.text = "Bảng 1.1: Danh sách tham số\nBảng 1.2: Kết quả đo đạc"
            elif "[Document content]" in p.text:
                p.text = "Nội dung báo cáo đã hoàn thiện đầy đủ."
                
        # Add 11 references under bibliography
        for idx in range(1, 12):
            d.add_paragraph(f"[{idx}] Tác giả {idx}, Tên tài liệu {idx}, Nhà xuất bản {idx}, 202{idx % 5}.")
        d.save(report_docx)
        
        # Final verify on completed synthetic report MUST PASS
        run([
            sys.executable, '-m', 'wordassistant.cli', 'verify', str(report_docx),
            '--profile', 'hcmunre_dacn_2026_2027', '--variant', 'report', '--json'
        ])
        print("completed-synthetic-report-verify: PASS")

        # C. Negative final-delivery fixture (one placeholder left)
        shutil.copyfile(report_docx, neg_report_docx)
        d_neg = Document(neg_report_docx)
        d_neg.add_paragraph("[Section content...]")
        d_neg.save(neg_report_docx)
        run_expect_failure([
            sys.executable, '-m', 'wordassistant.cli', 'verify', str(neg_report_docx),
            '--profile', 'hcmunre_dacn_2026_2027', '--variant', 'report', '--json'
        ])
        print("negative-delivery-fixture-verify: OK (rejected as expected)")

        # scaffold proposal clone & generic
        run([
            sys.executable, '-m', 'wordassistant.cli', 'scaffold', str(proposal_docx),
            '--profile', 'hcmunre_dacn_2026_2027', '--variant', 'proposal', '--json'
        ])
        run([
            sys.executable, '-m', 'wordassistant.cli', 'scaffold', str(generic_docx),
            '--profile', 'generic', '--variant', 'default', '--title', 'GENERIC DOC', '--json'
        ])
        
        # replace dry-run
        run([
            sys.executable, '-m', 'wordassistant.cli', 'replace', str(report_docx),
            '--old', 'XAY DUNG HE THONG', '--new', 'PHAT TRIEN HE THONG', '--dry-run', '--json'
        ])
        # evidence
        run([
            sys.executable, '-m', 'wordassistant.cli', 'evidence', 'add', str(evidence_file),
            '--id', 'smoke1', '--title', 'Smoke Title', '--authors', 'Author A', '--year', '2024',
            '--url', 'https://example.com/smoke', '--verified-by', 'CI',
            '--json'
        ])
        run([sys.executable, '-m', 'wordassistant.cli', 'evidence', 'validate', str(evidence_file), '--json'])

    print("\n=== 7. Verifying LibreOffice Render Availability & Direct Render CLI ===")
    from wordassistant.doctor import find_libreoffice_executable
    lo_exe = find_libreoffice_executable()
    if lo_exe:
        print(f"libreoffice-render: AVAILABLE ({lo_exe})")
        with tempfile.TemporaryDirectory() as render_tmpdir:
            r_docx = Path(render_tmpdir) / 'render_test.docx'
            r_pdf_dir = Path(render_tmpdir) / 'pdf_out'
            run([
                sys.executable, '-m', 'wordassistant.cli', 'scaffold', str(r_docx),
                '--profile', 'generic', '--variant', 'default', '--title', 'RENDER TEST', '--json'
            ])
            run([
                sys.executable, '-m', 'wordassistant.cli', 'render', str(r_docx),
                '--outdir', str(r_pdf_dir), '--timeout', '180', '--json'
            ])
            expected_pdf = r_pdf_dir / f"{r_docx.stem}.pdf"
            assert expected_pdf.exists() and expected_pdf.stat().st_size > 0, "Direct render CLI did not produce expected non-empty PDF"
            print(f"direct-render-cli: OK ({expected_pdf.name}, {expected_pdf.stat().st_size} bytes)")
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
        run([py_exe, '-m', 'wordassistant.cli', 'profiles', '--json'])
        run([py_exe, '-m', 'wordassistant.cli', 'profile', 'validate', 'generic', '--json'])
        
        clean_gen_docx = Path(clean_env_dir) / 'clean_generic.docx'
        clean_prop_docx = Path(clean_env_dir) / 'clean_proposal.docx'
        run([py_exe, '-m', 'wordassistant.cli', 'scaffold', str(clean_gen_docx), '--profile', 'generic', '--variant', 'default', '--json'])
        run([py_exe, '-m', 'wordassistant.cli', 'inspect', str(clean_gen_docx), '--json'])
        run([py_exe, '-m', 'wordassistant.cli', 'scaffold', str(clean_prop_docx), '--profile', 'hcmunre_dacn_2026_2027', '--variant', 'proposal', '--json'])
        
        # Verify packaged official docx hashes inside installed package
        verify_pkg_code = (
            "import hashlib; from importlib.resources import files; "
            "hd = files('wordassistant').joinpath('data', 'use_cases', 'hcmunre_dacn_2026_2027', 'assets', 'huong_dan_trinh_bay_dacn_2026_2027.docx').read_bytes(); "
            "dc = files('wordassistant').joinpath('data', 'use_cases', 'hcmunre_dacn_2026_2027', 'assets', 'mau_de_cuong_do_an_chuyen_nganh.docx').read_bytes(); "
            "assert hashlib.sha256(hd).hexdigest().lower() == '0f3622dbcd74009fb0867e0d3fa4a1624a38983af502e55d48868edf33f74e78'; "
            "assert hashlib.sha256(dc).hexdigest().lower() == 'bb291a6de459e33267170c3dd9087903a0d9f1911086bbfc935cb9f7781904e6'; "
            "print('installed-package-asset-hashes: VERIFIED')"
        )
        run([py_exe, '-c', verify_pkg_code])
        
        if Path(wa_exe).exists():
            run([wa_exe, 'doctor', '--json'])
        print('clean-venv-smoke: OK')

    print('\n========================================')
    print('release-check: PASS')
    print('========================================')

if __name__ == '__main__':
    main()
