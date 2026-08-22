from pathlib import Path
import argparse,hashlib,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
PAIRS=[
 (ROOT/'profiles/generic.json',ROOT/'src/wordassistant/data/profiles/generic.json'),
 (ROOT/'profiles/hcmunre_dacn_2026_2027.json',ROOT/'src/wordassistant/data/profiles/hcmunre_dacn_2026_2027.json'),
 (ROOT/'use_cases/hcmunre_dacn_2026_2027/assets/huong_dan_trinh_bay_dacn_2026_2027.docx',ROOT/'src/wordassistant/data/use_cases/hcmunre_dacn_2026_2027/assets/huong_dan_trinh_bay_dacn_2026_2027.docx'),
 (ROOT/'use_cases/hcmunre_dacn_2026_2027/assets/mau_de_cuong_do_an_chuyen_nganh.docx',ROOT/'src/wordassistant/data/use_cases/hcmunre_dacn_2026_2027/assets/mau_de_cuong_do_an_chuyen_nganh.docx'),
]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--check',action='store_true'); a=ap.parse_args()
 bad=[]
 for src,dst in PAIRS:
  if a.check:
   if not dst.exists() or digest(src)!=digest(dst):bad.append((src,dst))
  else:
   dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
 if bad:
  for s,d in bad:print(f'OUT-OF-SYNC: {s.relative_to(ROOT)} -> {d.relative_to(ROOT)}',file=sys.stderr)
  raise SystemExit(2)
if __name__=='__main__':main()
