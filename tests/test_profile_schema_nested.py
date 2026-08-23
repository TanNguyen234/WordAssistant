from __future__ import annotations
import pytest
from wordassistant.profiles.loader import validate_profile_dict, ProfileError

def base_profile():
    return {
        "id": "test",
        "name": "Test Profile",
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

def test_reject_invalid_header_footer():
    p = base_profile()
    p["variants"]["default"]["header_footer"] = {"page_number_start": -1}
    with pytest.raises(ProfileError):
        validate_profile_dict(p)

    p2 = base_profile()
    p2["variants"]["default"]["header_footer"] = {"header_left": 123}  # Non-string
    with pytest.raises(ProfileError):
        validate_profile_dict(p2)

def test_reject_invalid_citations():
    p = base_profile()
    p["variants"]["default"]["citations"] = {"minimum_references": -5}
    with pytest.raises(ProfileError):
        validate_profile_dict(p)

    p2 = base_profile()
    p2["variants"]["default"]["citations"] = {"prefer_primary_source": "yes"}  # Non-bool
    with pytest.raises(ProfileError):
        validate_profile_dict(p2)

def test_reject_invalid_template_asset():
    p = base_profile()
    p["variants"]["default"]["template_asset"] = "../secret.docx"
    with pytest.raises(ProfileError):
        validate_profile_dict(p)

    p2 = base_profile()
    p2["variants"]["default"]["template_asset"] = "something.txt"  # Not .docx
    with pytest.raises(ProfileError):
        validate_profile_dict(p2)
