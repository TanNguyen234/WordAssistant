from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from docx import Document
from wordassistant.profiles.loader import DocumentProfile

@dataclass(frozen=True)
class Issue:
    severity:str; code:str; message:str
@dataclass(frozen=True)
class ValidationResult:
    valid:bool; issues:tuple[Issue,...]

def validate_document(path:str|Path,profile:DocumentProfile,variant_name:str,tolerance_cm:float=.08)->ValidationResult:
    v=profile.variant(variant_name); d=Document(path); issues=[]
    if not d.sections: issues.append(Issue('error','no_sections','Document has no sections'))
    for i,s in enumerate(d.sections):
        for label,actual,expected in [('width',s.page_width.cm,v.page.width_cm),('height',s.page_height.cm,v.page.height_cm),('top_margin',s.top_margin.cm,v.page.margins.top_cm),('bottom_margin',s.bottom_margin.cm,v.page.margins.bottom_cm),('left_margin',s.left_margin.cm,v.page.margins.left_cm),('right_margin',s.right_margin.cm,v.page.margins.right_cm)]:
            if abs(actual-expected)>tolerance_cm: issues.append(Issue('error','page_geometry',f'Section {i+1} {label}: {actual:.2f} cm, expected {expected:.2f} cm'))
    # advisory checks only; missing refs should not make an empty scaffold structurally invalid
    minrefs=v.citations.get('minimum_references')
    if isinstance(minrefs,int):
        text='\n'.join(p.text for p in d.paragraphs); count=sum(1 for ln in text.splitlines() if ln.strip().startswith('[') and ']' in ln)
        if count and count<minrefs: issues.append(Issue('warning','reference_count',f'Found about {count} references; profile asks for at least {minrefs}.'))
    return ValidationResult(not any(i.severity=='error' for i in issues),tuple(issues))
