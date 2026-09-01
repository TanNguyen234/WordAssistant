# OOXML backend

The OOXML backend owns features that python-docx cannot express reliably, including numbering definitions, fields, bookmarks, cross-references, notes, content controls, and package-level properties.

Structural success means required parts, relationships, and semantic elements survive save/reopen. It does not prove Word pagination, refreshed field results, or rendered appearance. Those dimensions require separate evidence.

Automatic heading numbering links multilevel levels to Heading styles. Fixed table geometry synchronizes table width, indent, grid columns, effective cell widths, fixed layout, and margins.
