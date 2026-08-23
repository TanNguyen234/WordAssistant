from __future__ import annotations
import pytest
from wordassistant.profiles.loader import validate_profile_dict, ProfileError

def test_invalid_header_footer_role_raises_profile_error():
    prof_dict = {
        "id": "bad_role_prof",
        "name": "Bad Role",
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
                },
                "header_footer": {
                    "header_left": "unsupported_invalid_role_xyz"
                }
            }
        }
    }
    with pytest.raises(ProfileError, match="supported role"):
        validate_profile_dict(prof_dict)

def test_invalid_metadata_field_value_key_raises_profile_error():
    prof_dict = {
        "id": "bad_key_prof",
        "name": "Bad Key",
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
                },
                "cover": {
                    "metadata_fields": [
                        {"label": "Invalid:", "value_key": "invalid/slashes#bad", "required": True}
                    ]
                }
            }
        }
    }
    with pytest.raises(ProfileError):
        validate_profile_dict(prof_dict)
