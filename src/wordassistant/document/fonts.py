from __future__ import annotations

from docx.oxml.ns import qn


_FONT_SLOTS = ("ascii", "hAnsi", "eastAsia", "cs")
_THEME_SLOTS = ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme")


def set_word_font(font, name: str) -> None:
    """Set a fixed Word font for Latin, East Asian, and complex-script text."""
    font.name = name
    owner = font._element
    r_pr = owner.get_or_add_rPr()
    r_fonts = r_pr.get_or_add_rFonts()
    for slot in _FONT_SLOTS:
        r_fonts.set(qn(f"w:{slot}"), name)
    for slot in _THEME_SLOTS:
        key = qn(f"w:{slot}")
        if key in r_fonts.attrib:
            del r_fonts.attrib[key]
