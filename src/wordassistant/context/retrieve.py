from __future__ import annotations
from dataclasses import dataclass
import math,re
from wordassistant.document.model import DocumentSection
_WORD=re.compile(r'\w+',re.UNICODE)
@dataclass(frozen=True)
class ContextBundle:
    query:str; sections:tuple[DocumentSection,...]; text:str; estimated_tokens:int; max_tokens:int

def estimate_tokens(text:str)->int:
    if not text:return 0
    words=len(_WORD.findall(text)); chars=len(text)
    return max(1,math.ceil(max(chars/3.0,words*1.6)))

def _score(q:str,s:DocumentSection)->float:
    qs={x.casefold() for x in _WORD.findall(q) if len(x)>1};
    if not qs:return 0
    title={x.casefold() for x in _WORD.findall(s.title)}; body={x.casefold() for x in _WORD.findall(s.text[:12000])}
    return 4*len(qs&title)/len(qs)+len(qs&body)/len(qs)

def build_context(sections:list[DocumentSection],query:str,max_tokens:int=12000,active_section_id:str|None=None)->ContextBundle:
    if max_tokens<100: raise ValueError('max_tokens must be >= 100')
    byid={s.section_id:s for s in sections}; ranked=sorted(sections,key=lambda s:(_score(query,s),-s.level),reverse=True)
    chosen=[]
    if active_section_id:
        if active_section_id not in byid: raise ValueError(f'Unknown section id: {active_section_id}')
        chosen.append(byid[active_section_id])
    for s in ranked:
        if s not in chosen: chosen.append(s)
    blocks=[]; used=[]; budget=max_tokens
    for s in chosen:
        block=f"## {s.title}\n{s.text}".strip(); cost=estimate_tokens(block)
        if cost<=budget:
            blocks.append(block); used.append(s); budget-=cost
        elif not used and budget>100:
            # retain most relevant section even if it needs truncation
            max_chars=max(200,int(budget*2.6)); block=block[:max_chars].rstrip()+"\n[…truncated…]"
            blocks.append(block); used.append(DocumentSection(s.section_id,s.title,block,s.level,s.parent_id,s.source_index,s.metadata)); budget=0
        if budget<80: break
    text='\n\n'.join(blocks)
    return ContextBundle(query,tuple(used),text,min(max_tokens,estimate_tokens(text)),max_tokens)
