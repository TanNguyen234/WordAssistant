from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from docx import Document

@dataclass(frozen=True)
class ReplaceResult:
    output: Path
    replacements: int


def _replace_para(paragraph, old:str, new:str)->int:
    # Fast path that preserves run formatting when the match is inside a single run.
    n=0
    for run in paragraph.runs:
        c=run.text.count(old)
        if c:
            run.text=run.text.replace(old,new); n+=c
    if n:return n
    # Cross-run fallback: replace paragraph text and preserve the first run's formatting only.
    text=paragraph.text
    c=text.count(old)
    if not c:return 0
    if paragraph.runs:
        first=paragraph.runs[0]; first.text=text.replace(old,new)
        for r in paragraph.runs[1:]: r.text=''
    else: paragraph.add_run(text.replace(old,new))
    return c


def replace_text(input_path:str|Path, old:str, new:str, output_path:str|Path|None=None)->ReplaceResult:
    if not old: raise ValueError('old text must be non-empty')
    src=Path(input_path); out=Path(output_path) if output_path else src.with_name(src.stem+'_edited.docx')
    d=Document(src); total=0
    for p in d.paragraphs: total+=_replace_para(p,old,new)
    for table in d.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs: total+=_replace_para(p,old,new)
    out.parent.mkdir(parents=True,exist_ok=True); d.save(out)
    return ReplaceResult(out,total)
