#!/usr/bin/env python3
"""
AI Writing Linter & Pattern Scanner (Bilingual: English & Vietnamese)
Based on Wikipedia:Signs of AI writing (WP:AISIGNS) and contemporary LLM corpus analysis.

Detects:
- Engine & Platform Leakage (ChatGPT, Gemini, Grok, DeepSeek, Perplexity metadata/tracking)
- Unfilled Placeholders & Phrasal Templates
- Chatbot Conversational Preambles & Polite Residue
- High-Density AI Clichés and Vocabulary (EN & VI)
- Syntactic Tells (Negative Parallelisms, Trailing Participial Clauses, Copula Avoidance)
- Formatting Tells (Inline-header lists, Emoji headers/bullets, Em-dash clutter)
"""

import argparse
import json
import re
import sys
from typing import Dict, List, Any


# 1. Unambiguous Engine & Platform Leaks (Severity: CRITICAL - 100% LLM signature)
CRITICAL_LEAKS_PATTERNS = [
    # ChatGPT
    (r':contentReference\[oaicite:\d+\]', 'ChatGPT internal citation reference (oaicite)'),
    (r'\[oai_citation:\d+[^\]]*\]', 'ChatGPT internal citation reference (oai_citation)'),
    (r'\b\w+\+\d+(?:ISO|Wikipedia|Google Cloud|Microsoft Learn)', 'ChatGPT multi-source cluster notation (e.g. Wikipedia+1)'),
    (r'\bturn\d+search\d+\b', 'ChatGPT search turn artifact (turn0search0)'),
    (r'\bturn\d+(?:image|news|file)\d+\b', 'ChatGPT turn media artifact'),
    (r'citeturn\d+search\d+', 'ChatGPT Unicode PUA citation glyph marker'),
    (r'\d+', 'ChatGPT Unicode PUA numbered citation marker'),
    (r'\(\{"attribution":\{"attributableIndex":"[^"]+"\}\}\)', 'ChatGPT internal JSON attribution metadata'),
    # Gemini
    (r'\[cite:\s*\d+(?:,\s*\d+)*\]', 'Gemini citation marker [cite: N]'),
    (r'\[span_\d+\]\((?:start_span|end_span)\)', 'Gemini span markup bug [span_N](start_span)'),
    # Grok
    (r'<grok-card\s+[^>]*data-type="citation_card"[^>]*>', 'Grok citation card XML tag'),
    (r'\[\]\(grok_render_citation_card_json=[^\)]+\)', 'Grok citation card render JSON'),
    # DeepSeek
    (r'【\d+†L\d+(?:-L?\d+)?】', 'DeepSeek lenticular brackets with dagger source line tag (e.g. 【85†L261-269】)'),
    # Perplexity
    (r'\[attached_file:\d+\]', 'Perplexity attached file tag'),
    (r'\[web:\d+\]', 'Perplexity web citation tag'),
    (r'https?://[^\s]*ppl-ai-file-upload[^\s]*', 'Perplexity S3 file upload URL link'),
    # Generic AI writing block artifact
    (r':::writing\{variant="document"\s+id="\d+"\}', 'AI workspace artifact document marker'),
    # URL tracking tags indicating LLM web search output
    (r'[?&]utm_source=(?:chatgpt\.com|openai|copilot\.com)', 'URL contains AI referral tracking tag (utm_source=chatgpt/openai/copilot)'),
    (r'[?&]referrer=grok\.com', 'URL contains Grok referral tracking tag'),
    # Code fence leakage of wikitext
    (r'```wikitext', 'Wikitext wrapped inside Markdown code fence'),
]

# 2. Placeholders & Incomplete Templates (Severity: HIGH)
PLACEHOLDER_PATTERNS = [
    (r'\[(?:Insert|Add|Paste)\s+[^\]]+\]', 'Unfilled bracket placeholder (e.g. [Insert Name/URL])', 'en'),
    (r'\[(?:Chèn|Điền|Thêm|Nhập)\s+[^\]]+\]', 'Unfilled Vietnamese bracket placeholder (e.g. [Chèn liên kết/tên])', 'vi'),
    (r'\b202\d-[Xx]{2}-[Xx]{2}\b', 'Placeholder date (e.g. 2025-XX-XX)', 'both'),
    (r'\b(?:PASTE_URL_HERE|INSERT_SOURCE_URL|PASTE_SPOTIFY_TRACK_URL_HERE|PASTE_YOUTUBE_VIDEO_URL_HERE)\b', 'Explicit code placeholder token', 'en'),
    (r'\(\s*(?:Add your channel URL here|If available)\s*\)', 'Unfilled parenthesis instruction', 'en'),
    (r'\(\s*(?:Chèn liên kết tại đây|Nếu có)\s*\)', 'Unfilled Vietnamese parenthesis instruction', 'vi'),
]

# 3. Conversational Preambles & Assistant Chatter (Severity: HIGH)
CONVERSATIONAL_PATTERNS = [
    # English
    (r'^(?:Certainly!|Of course!|Sure!|Here is (?:a|the)|I hope this helps|Here\'s a breakdown|As requested,)\b', 'AI conversational preamble', 'en'),
    (r'\b(?:Would you like (?:me to|further)|Let me know if you (?:need|would like)|Feel free to ask|I am an AI language model|As a large language model)\b', 'AI conversational sign-off or disclaimer', 'en'),
    (r'\b(?:Delete this section before submission|Here is a Wikipedia-style|professional encyclopedia-style draft)\b', 'AI meta-instruction leaked into text', 'en'),
    # Vietnamese
    (r'^(?:Chắc chắn rồi!|Dưới đây là|Hy vọng (?:thông tin này|bài viết này) (?:hữu ích|giúp ích)|Như bạn đã yêu cầu,)\b', 'Vietnamese AI conversational preamble', 'vi'),
    (r'\b(?:Bạn có muốn tôi (?:bổ sung|điều chỉnh|làm rõ)|Hãy cho tôi biết nếu bạn|Đừng ngần ngại đặt câu hỏi|Với tư cách là một (?:mô hình ngôn ngữ|trợ lý AI))\b', 'Vietnamese AI conversational sign-off or disclaimer', 'vi'),
    (r'\b(?:Xóa phần này trước khi gửi|Dưới đây là bản thảo theo phong cách bách khoa)\b', 'Vietnamese AI meta-instruction leaked into text', 'vi'),
]

# 4. Hedging & Epistemic Disclaimers (Severity: MEDIUM-HIGH)
HEDGING_PATTERNS = [
    # English
    (r'\b(?:While (?:specific|detailed) (?:details|information|records) are (?:limited|scarce|not widely documented))\b', 'Hedging disclaimer about scarce sources', 'en'),
    (r'\b(?:not widely (?:documented|available|transcribed|disclosed))\b', 'Generic lack-of-documentation claim', 'en'),
    (r'\b(?:based on available (?:information|sources|records))\b', 'Canned "based on available info" qualifier', 'en'),
    (r'\b(?:should be (?:treated|interpreted) as [^,\.]+ rather than (?:as )?[^,\.]+)\b', 'Didactic source interpretation disclaimer', 'en'),
    (r'\b(?:does not by itself establish|does not necessarily mean)\b', 'Procedural boundary hedging', 'en'),
    # Vietnamese
    (r'\b(?:Mặc dù (?:thông tin|chi tiết) cụ thể (?:còn hạn chế|chưa được ghi chép rộng rãi|khá khan hiếm))\b', 'Vietnamese hedging disclaimer about scarce sources', 'vi'),
    (r'\b(?:chưa được (?:công bố|ghi chép|tài liệu hóa) rộng rãi)\b', 'Vietnamese lack-of-documentation claim', 'vi'),
    (r'\b(?:dựa trên (?:thông tin|nguồn tư liệu) hiện có)\b', 'Vietnamese canned "based on available info" qualifier', 'vi'),
    (r'\b(?:nên được (?:hiểu|xem) như là [^,\.]+ thay vì [^,\.]+)\b', 'Vietnamese didactic source interpretation disclaimer', 'vi'),
    (r'\b(?:không đồng nghĩa với việc|tự thân nó không chứng minh)\b', 'Vietnamese procedural boundary hedging', 'vi'),
]

# 5. Syntactic Tells: Negative Parallelisms (Severity: MEDIUM)
NEGATIVE_PARALLELISM_PATTERNS = [
    # English
    (r'\b(?:not (?:only|just)\s+[^,;]+,\s*but\s+(?:also\s+)?[^,;\.]+)', 'Negative parallelism: "Not only X, but also Y"', 'en'),
    (r'\b(?:isn\'t just\s+[^—–-]+[—–-]\s*it\'s\s+[^,;\.]+)', 'Negative parallelism: "Isn\'t just X — it\'s Y"', 'en'),
    (r'\b(?:not\s+[^,;]+,\s*but\s+[^,;\.]+)', 'Negative parallelism: "Not X, but Y"', 'en'),
    (r'\b(?:rather than\s+[^,;\.]+,\s*[^,;\.]+)', 'Contrastive inversion: "Rather than X, Y"', 'en'),
    (r'\b(?:no\s+[^,;]+,\s*no\s+[^,;]+,\s*just\s+[^,;\.]+)', 'Staccato negation: "No X, no Y, just Z"', 'en'),
    # Vietnamese
    (r'\b(?:không chỉ\s+[^,;]+mà\s+(?:còn\s+)?[^,;\.]+)', 'Vietnamese negative parallelism: "Không chỉ X mà còn Y"', 'vi'),
    (r'\b(?:không đơn thuần là\s+[^,;]+mà\s+(?:chính )?là\s+[^,;\.]+)', 'Vietnamese negative parallelism: "Không đơn thuần là X mà là Y"', 'vi'),
    (r'\b(?:không phải\s+[^,;]+mà\s+là\s+[^,;\.]+)', 'Vietnamese negative parallelism: "Không phải X mà là Y"', 'vi'),
    (r'\b(?:thay vì\s+[^,;]+,\s*[^,;\.]+)', 'Vietnamese contrastive inversion: "Thay vì X, Y"', 'vi'),
]

# 6. Trailing Participial Clauses / Superficial Analysis (Severity: MEDIUM)
TRAILING_PARTICIPLE_PATTERNS = [
    # English
    (r',\s*(?:highlighting|underscoring|emphasizing|fostering|enhancing|contributing to|solidifying|symbolizing|marking a|serving as|showcasing|reflecting)\s+[^,\.]{15,}\.', 'Superficial trailing participial clause', 'en'),
    # Vietnamese
    (r',\s*(?:qua đó (?:khẳng định|thể hiện|nâng cao|đóng góp)|góp phần (?:thúc đẩy|nâng cao|hoàn thiện)|từ đó (?:mở ra|tạo tiền đề|đặt nền móng)|minh chứng cho)\s+[^,\.]{15,}\.', 'Vietnamese superficial trailing clause', 'vi'),
]

# 7. Formulaic Challenges & Outlook Section Formula (Severity: MEDIUM)
CHALLENGE_FORMULA_PATTERNS = [
    # English
    (r'\bDespite (?:its|these|their)\s+[^,]+,\s+[^,\.]+faces\s+(?:several\s+)?challenges\b', 'Canned challenge formula: "Despite X, Y faces challenges"', 'en'),
    (r'\b(?:Future Outlook|Challenges and Legacy|Challenges and Future Directions)\b', 'Formulaic challenge/future header', 'en'),
    # Vietnamese
    (r'\bMặc dù (?:đã đạt được|có nhiều)\s+[^,]+,\s+[^,\.]+vẫn\s+(?:đang\s+)?đối mặt với\s+(?:nhiều\s+)?thách thức\b', 'Vietnamese canned challenge formula: "Mặc dù X, Y vẫn đối mặt thách thức"', 'vi'),
    (r'\b(?:Triển vọng tương lai|Thách thức và hướng đi tương lai|Thách thức và Di sản)\b', 'Vietnamese formulaic challenge/future header', 'vi'),
]

# 8. High-Density AI Clichés & Buzzwords
AI_VOCAB_EN = {
    'stands as a testament': 3,
    'testament to': 2,
    'pivotal moment': 3,
    'pivotal role': 2,
    'crucial role': 2,
    'rich tapestry': 3,
    'cultural tapestry': 3,
    'tapestry': 1,
    'delve': 3,
    'delving': 3,
    'deep dive': 2,
    'nestled in': 2,
    'nestled amidst': 3,
    'vibrant hub': 2,
    'vibrant': 1,
    'evolving landscape': 2,
    'landscape': 1,
    'intricate interplay': 3,
    'intricate': 1,
    'interplay': 2,
    'beacon of': 2,
    'focal point': 2,
    'indelible mark': 3,
    'deeply rooted': 2,
    'fostering': 2,
    'bolstered': 2,
    'garner': 2,
    'garnered': 2,
    'underscores': 2,
    'underscoring': 2,
    'boasts a': 2,
    'boasts': 1,
    'meticulously': 2,
    'multifaceted': 2,
    'enduring legacy': 3,
    'valuable insights': 2,
    'resonates with': 2,
    'active social media presence': 3,
    'independent coverage': 2,
    'prominent media outlets': 2,
}

AI_VOCAB_VI = {
    'đóng vai trò then chốt': 3,
    'vai trò then chốt': 2,
    'đóng vai trò quan trọng': 1,
    'là minh chứng rõ nét': 3,
    'minh chứng sống động': 3,
    'minh chứng cho': 2,
    'bức tranh toàn cảnh': 3,
    'bức tranh đa sắc màu': 3,
    'bức tranh': 1,
    'đi sâu vào': 2,
    'tìm hiểu sâu': 1,
    'nép mình bên': 3,
    'nép mình giữa': 3,
    'tọa lạc tại vị trí đắc địa': 3,
    'mang đậm dấu ấn': 2,
    'bề dày lịch sử': 2,
    'di sản phong phú': 2,
    'góp phần định hình': 2,
    'tạo tiền đề cho': 2,
    'mở ra kỷ nguyên': 2,
    'khẳng định vị thế': 2,
    'đánh dấu bước ngoặt': 2,
    'bước ngoặt quan trọng': 2,
    'tăng cường gắn kết': 2,
    'thúc đẩy mạnh mẽ': 2,
    'nâng cao nhận thức': 1,
    'sở hữu vị thế': 2,
    'sở hữu tiềm năng': 2,
    'hòa mình vào': 2,
    'cam kết mang lại': 2,
    'đa chiều': 1,
    'tỉ mỉ': 1,
    'kết nối chặt chẽ': 1,
    'duy trì sự hiện diện tích cực': 3,
    'được đưa tin rộng rãi': 2,
    'các cơ quan báo đài uy tín': 2,
}

# 9. Formatting & Style Tells (Severity: LOW-MEDIUM)
FORMATTING_PATTERNS = [
    # Inline-header vertical list: e.g. "* **Title:** description" or "1. **Title:** description"
    (r'^\s*(?:[\*\-\•]|\d+\.)\s+\*\*[^\*:]+\*\*:\s+', 'Inline-header vertical list item (* **Header:** ...)', 'both'),
    # Emoji decorating heading or list marker
    (r'^\s*(?:#+\s*|[=\-]{2,}\s*|[\*\-\•]\s*)[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]', 'Emoji used as heading or list decorator', 'both'),
    # Excessive em-dashes with spaces: " — "
    (r'\s+—\s+', 'Em-dash surrounded by spaces (classic LLM typographic quirk)', 'both'),
]


class Violation:
    def __init__(self, line_num: int, snippet: str, category: str, description: str, severity: str, weight: int):
        self.line_num = line_num
        self.snippet = snippet.strip()
        self.category = category
        self.description = description
        self.severity = severity
        self.weight = weight

    def to_dict(self) -> Dict[str, Any]:
        return {
            'line': self.line_num,
            'snippet': self.snippet[:120] + ('...' if len(self.snippet) > 120 else ''),
            'category': self.category,
            'description': self.description,
            'severity': self.severity,
            'weight': self.weight
        }


def scan_text(text: str, lang: str = 'both') -> Dict[str, Any]:
    lines = text.splitlines()
    violations: List[Violation] = []
    total_score = 0

    # 1. Check line-by-line regex patterns
    for idx, line in enumerate(lines, 1):
        # A. Critical Leaks
        for pattern, desc in CRITICAL_LEAKS_PATTERNS:
            if re.search(pattern, line):
                v = Violation(idx, line, 'ENGINE_LEAK', desc, 'CRITICAL', 25)
                violations.append(v)
                total_score += 25

        # B. Placeholders
        for item in PLACEHOLDER_PATTERNS:
            pattern, desc, p_lang = item
            if p_lang in (lang, 'both'):
                if re.search(pattern, line):
                    v = Violation(idx, line, 'PLACEHOLDER', desc, 'HIGH', 15)
                    violations.append(v)
                    total_score += 15

        # C. Conversational residue
        for item in CONVERSATIONAL_PATTERNS:
            pattern, desc, p_lang = item
            if p_lang in (lang, 'both'):
                if re.search(pattern, line.strip(), re.IGNORECASE):
                    v = Violation(idx, line, 'CONVERSATIONAL_LEAK', desc, 'HIGH', 15)
                    violations.append(v)
                    total_score += 15

        # D. Hedging
        for item in HEDGING_PATTERNS:
            pattern, desc, p_lang = item
            if p_lang in (lang, 'both'):
                if re.search(pattern, line, re.IGNORECASE):
                    v = Violation(idx, line, 'HEDGING_DISCLAIMER', desc, 'MEDIUM_HIGH', 10)
                    violations.append(v)
                    total_score += 10

        # E. Negative Parallelisms
        for item in NEGATIVE_PARALLELISM_PATTERNS:
            pattern, desc, p_lang = item
            if p_lang in (lang, 'both'):
                if re.search(pattern, line, re.IGNORECASE):
                    v = Violation(idx, line, 'NEGATIVE_PARALLELISM', desc, 'MEDIUM', 8)
                    violations.append(v)
                    total_score += 8

        # F. Trailing Participle
        for item in TRAILING_PARTICIPLE_PATTERNS:
            pattern, desc, p_lang = item
            if p_lang in (lang, 'both'):
                if re.search(pattern, line, re.IGNORECASE):
                    v = Violation(idx, line, 'TRAILING_PARTICIPLE', desc, 'MEDIUM', 7)
                    violations.append(v)
                    total_score += 7

        # G. Challenge Formula
        for item in CHALLENGE_FORMULA_PATTERNS:
            pattern, desc, p_lang = item
            if p_lang in (lang, 'both'):
                if re.search(pattern, line, re.IGNORECASE):
                    v = Violation(idx, line, 'CHALLENGE_FORMULA', desc, 'MEDIUM', 8)
                    violations.append(v)
                    total_score += 8

        # H. Formatting Tells
        for item in FORMATTING_PATTERNS:
            pattern, desc, p_lang = item
            if p_lang in (lang, 'both'):
                if re.search(pattern, line):
                    v = Violation(idx, line, 'FORMATTING_TELL', desc, 'LOW_MEDIUM', 5)
                    violations.append(v)
                    total_score += 5

    # 2. Vocabulary & Cliché Density Scan
    lower_text = text.lower()
    
    # English Clichés
    if lang in ('en', 'both'):
        for phrase, weight in AI_VOCAB_EN.items():
            matches = list(re.finditer(r'\b' + re.escape(phrase) + r'\b', lower_text))
            if matches:
                # Find line numbers
                for m in matches:
                    start_char = m.start()
                    line_no = text[:start_char].count('\n') + 1
                    snippet = lines[line_no - 1] if line_no - 1 < len(lines) else phrase
                    v = Violation(line_no, snippet, 'AI_VOCAB_EN', f'AI cliché term: "{phrase}"', 'MEDIUM', weight * 2)
                    violations.append(v)
                    total_score += weight * 2

    # Vietnamese Clichés
    if lang in ('vi', 'both'):
        for phrase, weight in AI_VOCAB_VI.items():
            matches = list(re.finditer(r'\b' + re.escape(phrase) + r'\b', lower_text))
            if matches:
                for m in matches:
                    start_char = m.start()
                    line_no = text[:start_char].count('\n') + 1
                    snippet = lines[line_no - 1] if line_no - 1 < len(lines) else phrase
                    v = Violation(line_no, snippet, 'AI_VOCAB_VI', f'Vietnamese AI cliché term: "{phrase}"', 'MEDIUM', weight * 2)
                    violations.append(v)
                    total_score += weight * 2

    # 3. Overall Risk Assessment
    if total_score >= 50 or any(v.severity == 'CRITICAL' for v in violations):
        risk_level = 'DEFINITE_AI'
        verdict = 'Unambiguous / Very High AI writing probability'
    elif total_score >= 30:
        risk_level = 'HIGH'
        verdict = 'High AI probability (multiple severe tropes or dense clichés)'
    elif total_score >= 15:
        risk_level = 'MODERATE'
        verdict = 'Moderate AI indicators present (review context for false positives)'
    elif total_score > 0:
        risk_level = 'LOW'
        verdict = 'Low AI indicator density (likely benign or stylistic coincidence)'
    else:
        risk_level = 'CLEAN'
        verdict = 'No detectable AI writing signs found'

    # Deduplicate violations on same line and same description
    unique_violations: List[Violation] = []
    seen = set()
    for v in violations:
        key = (v.line_num, v.category, v.description)
        if key not in seen:
            seen.add(key)
            unique_violations.append(v)

    # Sort by line number
    unique_violations.sort(key=lambda x: x.line_num)

    return {
        'total_score': total_score,
        'risk_level': risk_level,
        'verdict': verdict,
        'total_violations': len(unique_violations),
        'violations': [v.to_dict() for v in unique_violations]
    }


def format_report(result: Dict[str, Any]) -> str:
    lines = []
    lines.append('=' * 78)
    lines.append(' AI WRITING AUDIT REPORT (Wikipedia WP:AISIGNS Standard)')
    lines.append('=' * 78)
    lines.append(f' Risk Level: {result["risk_level"]} (Score: {result["total_score"]})')
    lines.append(f' Verdict:    {result["verdict"]}')
    lines.append(f' Total Violations Found: {result["total_violations"]}')
    lines.append('-' * 78)

    if not result['violations']:
        lines.append(' [PASS] No signs of AI writing detected.')
    else:
        for idx, v in enumerate(result['violations'], 1):
            lines.append(f' #{idx} [Line {v["line"]}] [{v["severity"]}] {v["category"]}')
            lines.append(f'    Issue:   {v["description"]}')
            lines.append(f'    Snippet: {v["snippet"]}')
            lines.append('')
    lines.append('=' * 78)
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Scan text files for signs of AI writing (Bilingual EN/VI).')
    parser.add_argument('file', nargs='?', help='Path to text/markdown file to analyze. Reads stdin if omitted.')
    parser.add_argument('--lang', choices=['en', 'vi', 'both'], default='both', help='Target language dictionary (en, vi, both).')
    parser.add_argument('--json', action='store_true', help='Output results as structured JSON.')
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f'Error reading file {args.file}: {e}', file=sys.stderr)
            sys.exit(1)
    else:
        content = sys.stdin.read()

    results = scan_text(content, lang=args.lang)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(format_report(results))

    if results['risk_level'] in ('DEFINITE_AI', 'HIGH'):
        sys.exit(2)
    elif results['risk_level'] == 'MODERATE':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
