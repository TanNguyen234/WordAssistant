from pathlib import Path
import argparse, hashlib, shutil, sys

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
    for line in init_py.read_text(encoding='utf-8').splitlines():
        if line.startswith('__version__'):
            ver_code = line.split('=')[1].strip().strip('"\'')
            if ver_txt != ver_code:
                return False, f"Version mismatch: VERSION={ver_txt} vs __init__.py={ver_code}"
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
    bad = []
    for src, dst in pairs:
        if a.check:
            if not dst.exists() or digest(src) != digest(dst):
                bad.append((src, dst))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            
    if bad:
        for s, d in bad:
            print(f'OUT-OF-SYNC: {s.relative_to(ROOT)} -> {d.relative_to(ROOT)}', file=sys.stderr)
        raise SystemExit(2)
    print("package-data-sync: OK")

if __name__ == '__main__':
    main()

