from pathlib import Path
import argparse
import hashlib
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]

def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def get_pairs():
    pairs = []
    # Profiles
    profiles_dir = ROOT / 'profiles'
    if profiles_dir.exists():
        for p in profiles_dir.glob('*.json'):
            dst = ROOT / 'src/wordassistant/data/profiles' / p.name
            pairs.append((p, dst))
    # Use cases assets and data
    use_cases_dir = ROOT / 'use_cases'
    if use_cases_dir.exists():
        for f in use_cases_dir.rglob('*'):
            if f.is_file() and not f.name.endswith('.md'):
                rel = f.relative_to(use_cases_dir)
                dst = ROOT / 'src/wordassistant/data/use_cases' / rel
                pairs.append((f, dst))
    return pairs

def check_version():
    version_file = ROOT / 'VERSION'
    if not version_file.exists():
        return False, "VERSION file missing"
    ver_txt = version_file.read_text(encoding='utf-8').strip()
    
    init_py = ROOT / 'src/wordassistant/__init__.py'
    if not init_py.exists():
        return False, "src/wordassistant/__init__.py missing"
    ver_code = None
    for line in init_py.read_text(encoding='utf-8').splitlines():
        if line.startswith('__version__'):
            ver_code = line.split('=')[1].strip().strip('"\'')
            break
            
    if ver_txt != ver_code:
        return False, f"Version mismatch: VERSION={ver_txt} vs __init__.py={ver_code}"
        
    pyproject = ROOT / 'pyproject.toml'
    if pyproject.exists():
        for line in pyproject.read_text(encoding='utf-8').splitlines():
            if line.strip().startswith('version ='):
                py_ver = line.split('=')[1].strip().strip('"\'')
                if py_ver != ver_txt:
                    return False, f"Version mismatch: VERSION={ver_txt} vs pyproject.toml={py_ver}"
                break
                
    return True, ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    
    ok, msg = check_version()
    if not ok:
        print(f"VERSION-ERROR: {msg}", file=sys.stderr)
        if a.check:
            raise SystemExit(2)
            
    pairs = get_pairs()
    valid_dsts = {dst.resolve() for _, dst in pairs}
    
    # Check for stale files in data directory
    data_dir = ROOT / 'src/wordassistant/data'
    stale_files = []
    if data_dir.exists():
        for f in data_dir.rglob('*'):
            if f.is_file() and f.resolve() not in valid_dsts:
                stale_files.append(f)
                
    bad = []
    for src, dst in pairs:
        if a.check:
            if not dst.exists() or digest(src) != digest(dst):
                bad.append((src, dst))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            
    if a.check:
        if stale_files:
            for sf in stale_files:
                print(f'STALE-PACKAGE-FILE: {sf.relative_to(ROOT)}', file=sys.stderr)
            raise SystemExit(2)
        if bad:
            for s, d in bad:
                print(f'OUT-OF-SYNC: {s.relative_to(ROOT)} -> {d.relative_to(ROOT)}', file=sys.stderr)
            raise SystemExit(2)
    else:
        for sf in stale_files:
            sf.unlink()
            
    print("package-data-sync: OK")

if __name__ == '__main__':
    main()
