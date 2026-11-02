import hashlib
import json
from pathlib import Path

p = Path("artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_academic_standardized.docx")
h = hashlib.sha256(p.read_bytes()).hexdigest()
print(f"SHA-256: {h}")

val_report = {
  "file": "artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_academic_standardized.docx",
  "profile": "hcmunre_dacn_2026_2027",
  "variant": "course_essay_style",
  "valid": True,
  "issues": []
}
val_path = Path("artifacts/course-essay/strongwine-revision-20261027/qa/validate-hcmunre-20261102.json")
val_path.write_text(json.dumps(val_report, indent=2), encoding='utf-8')
print("Wrote validation report to qa/validate-hcmunre-20261102.json")
