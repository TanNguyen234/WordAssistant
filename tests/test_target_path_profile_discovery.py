from __future__ import annotations
import json
from pathlib import Path
from wordassistant.cli import run
from wordassistant.profiles.loader import resolve_profile

def test_resolve_profile_relative_to_target_path(tmp_path: Path, monkeypatch):
    # CWD is inside an unrelated folder
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    monkeypatch.chdir(other_dir)
    
    # Project directory is somewhere else
    proj_dir = tmp_path / "my_project"
    proj_dir.mkdir()
    (proj_dir / ".wordassistant" / "profiles").mkdir(parents=True)
    
    custom_prof = {
        "id": "target_specific_profile",
        "name": "Target Specific Profile",
        "version": 1,
        "variants": {
            "default": {
                "page": {
                    "size": "A4",
                    "width_cm": 21.0,
                    "height_cm": 29.7,
                    "margins_cm": {"top": 2.0, "bottom": 2.0, "left": 2.0, "right": 2.0},
                    "one_sided": True
                },
                "typography": {
                    "body_font": "Arial",
                    "body_size_pt": 11.0
                }
            }
        }
    }
    prof_file = proj_dir / ".wordassistant" / "profiles" / "custom.json"
    prof_file.write_text(json.dumps(custom_prof), encoding="utf-8")
    
    # Resolve profile with target start path
    prof = resolve_profile("target_specific_profile", start_path=proj_dir)
    assert prof.profile_id == "target_specific_profile"
    
    # Scaffold using CLI with target output path inside proj_dir
    target_docx = proj_dir / "output.docx"
    assert run(["scaffold", str(target_docx), "--profile", "target_specific_profile", "--variant", "default", "--json"]) == 0
    assert target_docx.exists()
