from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator
import re
import unicodedata
from docx import Document
from docx.document import Document as Doc
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from .model import DocumentSection

_HEADING_STYLE = re.compile(r'^Heading\s*(\d+)$', re.I)
_MAJOR = re.compile(
    r'^(?:'
    r'chương\s+\d+|chapter\s+\d+|'
    r'phần\s*:\s*[A-ZÀ-Ỹ]|'
    r'mở đầu(?:\s*[:.]?.*)?$|lời mở đầu(?:\s*[:.]?.*)?$|'
    r'kết luận(?:\s+và\s+hướng\s+phát\s+triển)?\s*$|'
    r'phụ lục(?:\s*\([^)]*\))?\s*$|'
    r'danh mục tài liệu tham khảo(?:\s+\d+)?\s*$|'
    r'tài liệu tham khảo\.?\s*$|'
    r'quy định về trích dẫn(?:\s*[:.]?.*)?$|'
    r'hướng dẫn\s*$|trình bày đồ án.*|'
    r'nội dung\s*$|nội dung của các chương mục.*|'
    r'dự kiến kế hoạch thực hiện.*|các cơ quan, đơn vị cần liên hệ.*|'
    r'i{1,3}v?\.|v\.'
    r')', re.I)
_TOP_GUIDANCE = re.compile(r'^(?:trang\s+|cách thể hiện báo cáo|nội dung của các chương mục|phụ lục:|tài liệu tham khảo\.?$|quy định về trích dẫn)', re.I)
_MINOR = re.compile(r'^(?:\d+\.\s+|\d+\.\d+\.?\s+|\d+\.\d+\.\d+\.?\s+|\d+\.\s*[A-ZÀ-Ỹ])')

def index_docx(path: str | Path) -> list[DocumentSection]:
    d = Document(path)
    out = []
    counts = defaultdict(int)
    stack = {}
    title = 'Document preamble'
    sid = '__preamble__'
    level = 0
    parent = None
    buf = []
    start_idx = 0
    sample_mode = False
    
    def flush():
        nonlocal buf
        text = '\n\n'.join(x for x in buf if x.strip()).strip()
        if text or sid != '__preamble__':
            out.append(DocumentSection(sid, title, text, level, parent, start_idx))
        buf = []
        
    for idx, block in enumerate(iter_blocks(d)):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            is_sample_marker = bool(text) and text.casefold().startswith('(mẫu')
            if is_sample_marker:
                h = 1
                sample_mode = True
            elif sample_mode:
                h = None
            else:
                h = detect_heading(block)
            if text and h is not None:
                flush()
                title = text
                level = h
                base = slug(text)
                counts[base] += 1
                sid = base if counts[base] == 1 else f"{base}-{counts[base]}"
                parent = next((stack[x] for x in sorted(stack, reverse=True) if x < level), None)
                stack[level] = sid
                for k in list(stack):
                    if k > level:
                        del stack[k]
                start_idx = idx
                continue
            if text:
                buf.append(text)
        else:
            t = table_text(block)
            if t:
                buf.append(t)
    flush()
    return _coalesce(out)

def detect_heading(p: Paragraph) -> int | None:
    text = p.text.strip()
    if not text:
        return None
    style = p.style.name if p.style else ''
    m = _HEADING_STYLE.match(style or '')
    if m:
        return min(9, int(m.group(1)))
    ppr = p._p.pPr
    if ppr is not None and ppr.outlineLvl is not None:
        return int(ppr.outlineLvl.val) + 1
    num_ilvl = None
    if ppr is not None and ppr.numPr is not None and ppr.numPr.ilvl is not None:
        num_ilvl = int(ppr.numPr.ilvl.val)
    meaningful = [r for r in p.runs if r.text.strip()]
    bold = bool(meaningful) and sum(1 for r in meaningful if r.bold is True) >= max(1, len(meaningful) // 2)
    if num_ilvl == 0 and bold and len(text) <= 180 and (_MAJOR.match(text) or _TOP_GUIDANCE.match(text)):
        return 1
    if num_ilvl is not None and num_ilvl > 0 and bold and len(text) <= 180:
        return min(6, num_ilvl + 1)
    if _MAJOR.match(text) and (bold or text.upper() == text or len(text) <= 90):
        return 1
    if _MINOR.match(text) and bold and len(text) <= 160:
        dots = text.split()[0].count('.')
        return min(6, max(2, dots + 1))
    return None

def iter_blocks(d: Doc) -> Iterator[Paragraph | Table]:
    for child in d.element.body.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, d)
        elif child.tag == qn('w:tbl'):
            yield Table(child, d)

def table_text(t: Table) -> str:
    rows = []
    for row in t.rows:
        cells = [' '.join(p.text.strip() for p in c.paragraphs if p.text.strip()) for c in row.cells]
        if any(cells):
            rows.append(' | '.join(cells))
    return '\n'.join(rows)

def slug(s: str) -> str:
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:64]
    return s or 'section'

def _coalesce(sections: list[DocumentSection]) -> list[DocumentSection]:
    if len(sections) < 2:
        return sections
    result = []
    i = 0
    while i < len(sections):
        s = sections[i]
        if s.section_id != '__preamble__' and len(s.text) < 20 and len(s.title) < 35 and i + 1 < len(sections) and s.level >= 2:
            n = sections[i + 1]
            merged = DocumentSection(n.section_id, n.title, (s.title + '\n' + s.text + '\n' + n.text).strip(), n.level, n.parent_id, s.source_index, n.metadata)
            sections = sections[:i] + [merged] + sections[i + 2:]
            continue
        result.append(s)
        i += 1
    return result

def inspect_document(path: str | Path) -> dict[str, Any]:
    src = Path(path).resolve()
    d = Document(src)
    doc_xml = d._element.xml
    
    sections = index_docx(src)
    
    # Inventory counts
    p_count = len(d.paragraphs)
    tbl_count = len(d.tables)
    sec_count = len(d.sections)
    
    img_count = doc_xml.count('<w:drawing') + doc_xml.count('<w:pict')
    hyperlink_count = doc_xml.count('<w:hyperlink')
    field_count = doc_xml.count('<w:fldSimple') + doc_xml.count('<w:fldChar')
    bookmark_count = doc_xml.count('<w:bookmarkStart')
    comment_count = doc_xml.count('<w:commentReference')
    footnote_count = doc_xml.count('<w:footnoteReference')
    endnote_count = doc_xml.count('<w:endnoteReference')
    sdt_count = doc_xml.count('<w:sdt')
    ins_count = doc_xml.count('<w:ins')
    del_count = doc_xml.count('<w:del')
    
    has_toc = 'TOC' in doc_xml
    has_page = 'w:instr="PAGE"' in doc_xml or 'PAGE' in doc_xml
    
    adv_rec = (ins_count + del_count + comment_count + sdt_count > 0)
    
    return {
        'file': str(src),
        'file_name': src.name,
        'size_bytes': src.stat().st_size if src.exists() else 0,
        'paragraphs': p_count,
        'tables': tbl_count,
        'sections': sec_count,
        'images': img_count,
        'hyperlinks': hyperlink_count,
        'bookmarks': bookmark_count,
        'comments': comment_count,
        'footnotes': footnote_count,
        'endnotes': endnote_count,
        'content_controls': sdt_count,
        'revisions': {
            'insertions': ins_count,
            'deletions': del_count
        },
        'fields': {
            'total_field_tags': field_count,
            'toc_field': has_toc,
            'page_field': has_page
        },
        'advanced_backend_recommended': adv_rec,
        'outline': [
            {'id': s.section_id, 'title': s.title, 'level': s.level}
            for s in sections
        ]
    }
