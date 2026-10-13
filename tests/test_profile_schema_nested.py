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


def test_accept_style_color_and_heading_indentation():
    profile = base_profile()
    profile["variants"]["default"]["typography"]["styles"] = {
        "heading2": {
            "font_color": "000000",
            "left_indent_pt": 18,
            "first_line_indent_pt": -9,
        }
    }

    parsed = validate_profile_dict(profile)

    assert parsed.variant("default").typography.styles["heading2"]["font_color"] == "000000"


@pytest.mark.parametrize("value", ["00000", "0000000", "GGGGGG", 123])
def test_reject_invalid_style_font_color(value):
    profile = base_profile()
    profile["variants"]["default"]["typography"]["styles"] = {
        "Caption": {"font_color": value}
    }

    with pytest.raises(ProfileError):
        validate_profile_dict(profile)


def test_reject_negative_style_left_indent():
    profile = base_profile()
    profile["variants"]["default"]["typography"]["styles"] = {
        "Heading 2": {"left_indent_pt": -1}
    }

    with pytest.raises(ProfileError):
        validate_profile_dict(profile)
