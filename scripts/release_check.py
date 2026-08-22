from __future__ import annotations
from pathlib import Path
import json, subprocess, sys, tempfile

ROOT=Path(__file__).resolve().parents[1]

def run(cmd):
    print('+',' '.join(str(x) for x in cmd))
    subprocess.run(cmd,cwd=ROOT,check=True)

def main():
    run([sys.executable,'scripts/sync_package_data.py','--check'])
    run([sys.executable,'-m','pytest'])
    run([sys.executable,'-m','compileall','-q','src'])
    env_cmd=[sys.executable,'-c',
      "from wordassistant.document.structure import index_docx; "
      "from pathlib import Path; "
      "r=Path('use_cases/hcmunre_dacn_2026_2027/assets'); "
      "a=index_docx(r/'huong_dan_trinh_bay_dacn_2026_2027.docx'); "
      "b=index_docx(r/'mau_de_cuong_do_an_chuyen_nganh.docx'); "
      "assert 10<=len(a)<=45 and 8<=len(b)<=30; print({'guidance_sections':len(a),'proposal_sections':len(b)})"]
    run(env_cmd)
    print('release-check: PASS')
if __name__=='__main__':main()
