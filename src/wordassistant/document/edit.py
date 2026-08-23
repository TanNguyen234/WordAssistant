from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import tempfile
from docx import Document

@dataclass(frozen=True)
class ReplaceResult:
    output: Path
    replacements: int
    status: str = "SUCCESS"  # SUCCESS, UNSAFE_EDIT_BLOCKED, NO_MATCH, DRY_RUN
    dry_run: bool = False
    complex_structures_detected: tuple[str, ...] = ()
    advanced_backend_required: bool = False
    error: str | None = None

def _detect_complex_elements(element) -> list[str]:
    detected = []
    xml = element.xml if hasattr(element, 'xml') else ''
    if '<w:hyperlink' in xml:
        detected.append('hyperlink')
    if '<w:fldSimple' in xml or '<w:fldChar' in xml or '<w:instrText' in xml:
        detected.append('field')
    if '<w:sdt' in xml:
        detected.append('content_control')
    if '<w:ins' in xml or '<w:del' in xml:
        detected.append('tracked_change')
    if '<w:footnoteReference' in xml:
        detected.append('footnote')
    if '<w:endnoteReference' in xml:
        detected.append('endnote')
    if '<w:commentReference' in xml:
        detected.append('comment')
    if '<w:drawing' in xml or '<w:pict' in xml:
        detected.append('drawing')
    return detected

def _replace_paragraph_runs_safe(paragraph, old: str, new: str) -> int:
    # 1. Fast path: check if any run contains the entire match
    single_run_count = 0
    for run in paragraph.runs:
        c = run.text.count(old)
        if c:
            run.text = run.text.replace(old, new)
            single_run_count += c
    if single_run_count > 0:
        return single_run_count
        
    # 2. Cross-run match: find occurrences across runs
    full_text = paragraph.text
    if old not in full_text:
        return 0
        
    runs = paragraph.runs
    if not runs:
        paragraph.add_run(full_text.replace(old, new))
        return full_text.count(old)
        
    # Build run character offset intervals
    run_spans = []
    curr_offset = 0
    for r in runs:
        r_len = len(r.text)
        run_spans.append((curr_offset, curr_offset + r_len, r))
        curr_offset += r_len
        
    match_indices = []
    start = 0
    while True:
        idx = full_text.find(old, start)
        if idx == -1:
            break
        match_indices.append((idx, idx + len(old)))
        start = idx + len(old)
        
    if not match_indices:
        return 0
        
    for m_start, m_end in reversed(match_indices):
        start_run_idx = None
        end_run_idx = None
        
        for i, (r_start, r_end, r) in enumerate(run_spans):
            if r_start <= m_start < r_end:
                start_run_idx = i
            if r_start < m_end <= r_end:
                end_run_idx = i
                
        if start_run_idx is not None and end_run_idx is not None:
            r_start_obj = runs[start_run_idx]
            r_end_obj = runs[end_run_idx]
            
            offset_in_start = m_start - run_spans[start_run_idx][0]
            offset_in_end = m_end - run_spans[end_run_idx][0]
            
            prefix = r_start_obj.text[:offset_in_start]
            suffix = r_end_obj.text[offset_in_end:]
            
            if start_run_idx == end_run_idx:
                r_start_obj.text = prefix + new + suffix
            else:
                r_start_obj.text = prefix + new
                for mid_idx in range(start_run_idx + 1, end_run_idx):
                    runs[mid_idx].text = ""
                r_end_obj.text = suffix
        else:
            # Fallback across boundary - replace in first run and clear others
            first = runs[0]
            first.text = full_text.replace(old, new)
            for r in runs[1:]:
                r.text = ""
            break
            
    return len(match_indices)

def _collect_all_paragraphs(doc: Document) -> list:
    paragraphs = []
    paragraphs.extend(doc.paragraphs)
    
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                paragraphs.extend(cell.paragraphs)
                
    for section in doc.sections:
        paragraphs.extend(section.header.paragraphs)
        for table in section.header.tables:
            for row in table.rows:
                for cell in row.cells:
                    paragraphs.extend(cell.paragraphs)
                    
        paragraphs.extend(section.footer.paragraphs)
        for table in section.footer.tables:
            for row in table.rows:
                for cell in row.cells:
                    paragraphs.extend(cell.paragraphs)
                    
    return paragraphs

def replace_text(
    input_path: str | Path,
    old: str,
    new: str,
    output_path: str | Path | None = None,
    count: int | None = None,
    dry_run: bool = False
) -> ReplaceResult:
    if not old:
        raise ValueError("old text must be non-empty")
        
    src = Path(input_path)
    out = Path(output_path) if output_path else src.with_name(f"{src.stem}_edited.docx")
    
    d = Document(src)
    all_paragraphs = _collect_all_paragraphs(d)
    
    # 1. Preflight Phase: Scan all target paragraphs for complex structures
    complex_detected: set[str] = set()
    matching_paragraphs = []
    
    for p in all_paragraphs:
        if old in p.text:
            matching_paragraphs.append(p)
            detected_in_p = _detect_complex_elements(p._p)
            complex_detected.update(detected_in_p)
            
    if not matching_paragraphs:
        return ReplaceResult(
            output=out,
            replacements=0,
            status="NO_MATCH",
            dry_run=dry_run,
            complex_structures_detected=(),
            advanced_backend_required=False
        )
        
    # If any matched container has complex elements (fields, content controls, revisions, etc.), BLOCK mutation
    if complex_detected:
        return ReplaceResult(
            output=out,
            replacements=0,
            status="UNSAFE_EDIT_BLOCKED",
            dry_run=dry_run,
            complex_structures_detected=tuple(sorted(complex_detected)),
            advanced_backend_required=True,
            error=f"Target occurrence is inside or shares container with complex structures: {sorted(complex_detected)}; mutation blocked for safety."
        )
        
    # 2. Execution Phase: Perform safe replacement
    total_replacements = 0
    for p in matching_paragraphs:
        if count is not None and total_replacements >= count:
            break
        made = _replace_paragraph_runs_safe(p, old, new)
        total_replacements += made
        
    if dry_run:
        return ReplaceResult(
            output=out,
            replacements=total_replacements,
            status="DRY_RUN",
            dry_run=True,
            complex_structures_detected=(),
            advanced_backend_required=False
        )
        
    if total_replacements > 0:
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=out.parent, prefix=".tmp_wa_", suffix=".docx")
        os.close(tmp_fd)
        try:
            d.save(tmp_path)
            os.replace(tmp_path, out)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            raise
            
    return ReplaceResult(
        output=out,
        replacements=total_replacements,
        status="SUCCESS",
        dry_run=False,
        complex_structures_detected=(),
        advanced_backend_required=False
    )
