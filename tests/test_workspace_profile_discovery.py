from __future__ import annotations
import json
from pathlib import Path
from wordassistant.cli import run
from wordassistant.profiles.loader import discover_profiles, resolve_profile

def test_workspace_profile_discovery_and_scaffold(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert run(["init", "."]) == 0
    
    # Write a valid custom profile into .wordassistant/profiles/custom.json
    custom_prof = {
        "id": "custom_profile",
        "name": "Custom Profile for Project",
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
                    "body_size_pt": 11.0,
                    "line_spacing": 1.15
                }
            }
        }
    }
    prof_file = tmp_path / ".wordassistant" / "profiles" / "custom.json"
    prof_file.write_text(json.dumps(custom_prof, indent=2), encoding="utf-8")
    
    # Discovery should find custom_profile
    profs = discover_profiles()
    ids = [p.profile_id for p in profs]
    assert "custom_profile" in ids
    
    # Resolve by ID
    resolved = resolve_profile("custom_profile")
    assert resolved.profile_id == "custom_profile"
    
    # Scaffold document using custom profile
    out_docx = tmp_path / "custom_doc.docx"
    assert run(["scaffold", str(out_docx), "--profile", "custom_profile", "--variant", "default", "--json"]) == 0
    assert out_docx.exists()
