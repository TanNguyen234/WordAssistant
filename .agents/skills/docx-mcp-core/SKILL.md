---
name: docx-mcp-core
description: "Core skill for editing Word (.docx) documents. Use when doing low-level OOXML manipulation, track changes, comments, footnotes, bookmarks, and structural audits. Requires the docx-mcp MCP server to be running."
---

# Core Word Editing with docx-mcp

## Low-Level OOXML Rules & Constraints

When editing Word documents directly via XML elements, the following constraints must be strictly followed to prevent document corruption:

### 1. Element Order in `<w:pPr>` (Paragraph Properties)
OOXML requires child elements in `<w:pPr>` to be in this exact order:
```
w:pStyle → w:numPr → w:spacing → w:ind → w:jc → w:rPr
```
*Putting these elements out of order will cause Word to raise schema validation warnings.*

### 2. Element Order in `<w:rPr>` (Run Properties)
OOXML requires child elements in `<w:rPr>` to follow this order:
```
w:rStyle → w:rFonts → w:b/w:bCs → w:i/w:iCs → w:color → w:sz/w:szCs → w:u → w:vertAlign
```
*Wrong order (e.g. placing `w:u` before `w:sz`) leads to 'unreadable content' in Microsoft Word.*

### 3. w14:paraId Uniqueness
- Each paragraph (`<w:p>`) and table row (`<w:tr>`) must have a unique `w14:paraId` (an 8-digit uppercase hex string, e.g., `1A2B3C4D`).
- The value must be **less than `0x80000000`** (Microsoft reserves the high bit).
- When duplicating content (copy-paste), generate a new unique `paraId` for the copy.
- Run `validate_paraids` or `audit_document` to check.

### 4. Footnote Rules
- **1:1 Mapping**: Each footnote ID must be referenced exactly once in `document.xml`.
- **Sequential IDs**: Footnote IDs must start at `1` and be sequential. `id="-1"` and `id="0"` are reserved for separator lines.
- **paraId inside footnote**: Every paragraph inside `footnotes.xml` needs a unique `paraId`.
- **No reuse**: Never reuse a footnote ID in multiple places in the document body.

### 5. PNG Image / Relationships Ordering (Word for Mac)
If a PNG image relationship appears **before** header/footer relationships in `word/_rels/document.xml.rels`, Word for Mac will fail to open the file.
- **Rule**: Create/access header and footer objects in the script *before* adding any images or pictures.

---

## Tool Reference

Use the tools provided by `docx-mcp` to manipulate the document:
- `open_document(path)`: Open document.
- `search_text(query)`: Search text in body, footnotes, and comments.
- `get_paragraph(para_id)`: Read paragraph contents.
- `insert_text(para_id, text, position)`: Insert text (tracked or untracked).
- `delete_text(para_id, text)`: Delete text (tracked or untracked).
- `replace_text(para_id, old_text, new_text)`: Replace text.
- `audit_document()`: Perform a full structural sanity check.
- `save_document(output_path)`: Save file.
