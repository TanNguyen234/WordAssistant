from __future__ import annotations
from dataclasses import dataclass
import math
import re
import unicodedata
from wordassistant.document.model import DocumentSection

_WORD = re.compile(r'\w+', re.UNICODE)
MAX_CONTEXT_TOKENS = 12000

_VI_MAP = {
    'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
    'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
    'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
    'đ': 'd',
    'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
    'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
    'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
    'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
    'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
    'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
    'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
    'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
    'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
    'À': 'A', 'Á': 'A', 'Ả': 'A', 'Ã': 'A', 'Ạ': 'A',
    'Ă': 'A', 'Ằ': 'A', 'Ắ': 'A', 'Ẳ': 'A', 'Ẵ': 'A', 'Ặ': 'A',
    'Â': 'A', 'Ầ': 'A', 'Ấ': 'A', 'Ẩ': 'A', 'Ẫ': 'A', 'Ậ': 'A',
    'Đ': 'D',
    'È': 'E', 'É': 'E', 'Ẻ': 'E', 'Ẽ': 'E', 'Ẹ': 'E',
    'Ê': 'E', 'Ề': 'E', 'Ế': 'E', 'Ể': 'E', 'Ễ': 'E', 'Ệ': 'E',
    'Ì': 'I', 'Í': 'I', 'Ỉ': 'I', 'Ĩ': 'I', 'Ị': 'I',
    'Ò': 'O', 'Ó': 'O', 'Ỏ': 'O', 'Õ': 'O', 'Ọ': 'O',
    'Ô': 'O', 'Ồ': 'O', 'Ố': 'O', 'Ổ': 'O', 'Ỗ': 'O', 'Ộ': 'O',
    'Ơ': 'O', 'Ờ': 'O', 'Ớ': 'O', 'Ở': 'O', 'Ỡ': 'O', 'Ợ': 'O',
    'Ù': 'U', 'Ú': 'U', 'Ủ': 'U', 'Ũ': 'U', 'Ụ': 'U',
    'Ư': 'U', 'Ứ': 'U', 'Ừ': 'U', 'Ử': 'U', 'Ữ': 'U', 'Ự': 'U',
    'Ỳ': 'Y', 'Ý': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y'
}

def remove_diacritics(text: str) -> str:
    res = []
    for ch in unicodedata.normalize('NFC', text):
        res.append(_VI_MAP.get(ch, ch))
    return "".join(res)

@dataclass(frozen=True)
class ContextBundle:
    query: str
    sections: tuple[DocumentSection, ...]
    text: str
    estimated_tokens: int
    max_tokens: int
    truncated: bool = False

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    words = len(_WORD.findall(text))
    chars = len(text)
    return max(1, math.ceil(max(chars / 3.0, words * 1.6)))

def _tokenize(text: str) -> list[str]:
    norm = unicodedata.normalize('NFC', text).casefold()
    return [w for w in _WORD.findall(norm) if len(w) > 1]

def _score_section(query: str, s: DocumentSection, avg_len: float = 200.0) -> float:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 0.0
    q_tokens_nodiacritics = [remove_diacritics(w) for w in q_tokens]
    
    title_norm = unicodedata.normalize('NFC', s.title).casefold()
    title_nodiacritics = remove_diacritics(title_norm)
    title_tokens = set(_tokenize(title_norm))
    title_tokens_no = set(_tokenize(title_nodiacritics))
    
    body_sample = s.text[:15000]
    body_norm = unicodedata.normalize('NFC', body_sample).casefold()
    body_nodiacritics = remove_diacritics(body_norm)
    body_tokens = set(_tokenize(body_norm))
    body_tokens_no = set(_tokenize(body_nodiacritics))
    
    score = 0.0
    
    # Exact phrase boost in title or body
    q_phrase = unicodedata.normalize('NFC', query.strip()).casefold()
    q_phrase_no = remove_diacritics(q_phrase)
    if q_phrase and (q_phrase in title_norm or q_phrase_no in title_nodiacritics):
        score += 8.0
    elif q_phrase and (q_phrase in body_norm or q_phrase_no in body_nodiacritics):
        score += 3.0
        
    # Term overlap with title & body
    for qt, qt_no in zip(q_tokens, q_tokens_nodiacritics):
        if qt in title_tokens or qt_no in title_tokens_no:
            score += 4.0
        if qt in body_tokens or qt_no in body_tokens_no:
            score += 1.0
            
    # Normalize by query length
    return score / len(q_tokens)

def _truncate_to_budget(heading: str, body: str, budget: int) -> str | None:
    marker = "\n[… truncated to budget …]"
    base_prefix = f"{heading}\n"
    if estimate_tokens(base_prefix.strip()) > budget:
        head_text = heading
        low, high = 1, len(head_text)
        best_head = None
        while low <= high:
            mid = (low + high) // 2
            cand = head_text[:mid].rstrip()
            if estimate_tokens(cand) <= budget:
                best_head = cand
                low = mid + 1
            else:
                high = mid - 1
        return best_head
        
    target_budget = budget
    low, high = 0, len(body)
    best_text = None
    
    while low <= high:
        mid = (low + high) // 2
        cand_body = body[:mid].rstrip()
        cand = f"{base_prefix}{cand_body}{marker}".strip()
        if estimate_tokens(cand) <= target_budget:
            best_text = cand
            low = mid + 1
        else:
            high = mid - 1
            
    if best_text is None:
        cand = f"{base_prefix}".strip()
        if estimate_tokens(cand) <= budget:
            return cand
            
    return best_text

def build_context(
    sections: list[DocumentSection],
    query: str,
    max_tokens: int = 12000,
    active_section_id: str | None = None,
    target_section_id: str | None = None
) -> ContextBundle:
    if type(max_tokens) is not int or type(max_tokens) is bool:
        raise TypeError(f"max_tokens must be an integer, got {type(max_tokens).__name__}: {max_tokens!r}")
    if max_tokens < 100:
        raise ValueError(f"max_tokens must be >= 100, got {max_tokens}")
    if max_tokens > MAX_CONTEXT_TOKENS:
        raise ValueError(
            f"max_tokens exceeds the configured hard maximum of {MAX_CONTEXT_TOKENS}"
        )
        
    by_id = {s.section_id: s for s in sections}
    for name, section_id in (
        ('target_section_id', target_section_id),
        ('active_section_id', active_section_id),
    ):
        if section_id is not None:
            if not isinstance(section_id, str) or not section_id.strip():
                raise ValueError(f"{name} must be a non-empty string")
            if section_id not in by_id:
                raise ValueError(f"Unknown section id: {section_id}")
    if (target_section_id is not None and active_section_id is not None
            and active_section_id != target_section_id):
        raise ValueError("target_section_id conflicts with active_section_id")

    if not sections:
        return ContextBundle(query=query, sections=(), text="", estimated_tokens=0, max_tokens=max_tokens, truncated=False)
        
    avg_len = sum(len(s.text) for s in sections) / max(1, len(sections))
    
    ranked = sorted(sections, key=lambda s: (_score_section(query, s, avg_len), -s.level), reverse=True)
    
    chosen: list[DocumentSection] = []
    if target_section_id is not None:
        # A target is a hard retrieval boundary: do not add neighboring sections.
        chosen = [by_id[target_section_id]]
    else:
        if active_section_id is not None:
            chosen.append(by_id[active_section_id])

        for section in ranked:
            if section not in chosen:
                chosen.append(section)
            
    blocks: list[str] = []
    used_sections: list[DocumentSection] = []
    budget = max_tokens
    was_truncated = False
    
    for s in chosen:
        heading = f"## {s.title}"
        if s.parent_id and s.parent_id in by_id:
            parent = by_id[s.parent_id]
            heading = f"## {parent.title} > {s.title}"
            
        full_block = f"{heading}\n{s.text}".strip()
        cost = estimate_tokens(full_block)
        
        if cost <= budget:
            blocks.append(full_block)
            used_sections.append(s)
            budget -= cost
        else:
            was_truncated = True
            if budget >= 50:
                truncated = _truncate_to_budget(heading, s.text, budget)
                if truncated and estimate_tokens(truncated) <= budget:
                    blocks.append(truncated)
                    used_sections.append(
                        DocumentSection(
                            s.section_id,
                            s.title,
                            truncated,
                            s.level,
                            s.parent_id,
                            s.source_index,
                            s.metadata
                        )
                    )
                    budget -= estimate_tokens(truncated)
            break
            
    text = "\n\n".join(blocks)
    actual_tokens = estimate_tokens(text)
    
    if actual_tokens > max_tokens:
        was_truncated = True
        while actual_tokens > max_tokens and len(text) > 0:
            text = text[:int(len(text) * (max_tokens / max(1, actual_tokens)))].rstrip()
            actual_tokens = estimate_tokens(text)
            
    return ContextBundle(
        query=query,
        sections=tuple(used_sections),
        text=text,
        estimated_tokens=actual_tokens,
        max_tokens=max_tokens,
        truncated=(
            was_truncated
            or (target_section_id is None and len(used_sections) < len(sections))
        )
    )
