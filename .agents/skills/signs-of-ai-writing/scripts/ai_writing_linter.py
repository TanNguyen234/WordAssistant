#!/usr/bin/env python3
"""Report optional editorial checks for English and Vietnamese plain text.

This utility does not identify authorship, estimate AI use, assess plagiarism,
or decide whether a passage is acceptable. Findings are review prompts only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


NOTICE = (
    "Findings describe text patterns only. They cannot establish authorship, "
    "intent, factual accuracy, or plagiarism. Review each item in context."
)

_PLATFORM_ARTIFACTS = [
    (r":contentReference\[oaicite:\d+\]", "Possible internal citation marker"),
    (r"\[oai_citation:\d+[^\]]*\]", "Possible internal citation marker"),
    (r"\bturn\d+(?:search|image|news|file)\d+\b", "Possible internal search or media marker"),
    (r"citeturn\d+search\d+", "Possible internal citation marker"),
    (r"\d+", "Possible internal citation marker"),
    (r"\[cite:\s*\d+(?:,\s*\d+)*\]", "Possible unconverted citation marker"),
    (r"\[span_\d+\]\((?:start_span|end_span)\)", "Possible internal span marker"),
    (r"\[attached_file:\d+\]|\[web:\d+\]", "Possible unconverted file or web marker"),
    (r"\[\]\(grok_render_citation_card_json=[^)]+\)", "Possible unconverted citation card"),
    (r"https?://[^\s)]*ppl-ai-file-upload[^\s)]*", "Possible temporary file-sharing link"),
    (r":::writing\{variant=\"document\"\s+id=\"\d+\"\}", "Possible unconverted document wrapper"),
]

_PLACEHOLDERS = [
    (r"\[(?:insert|add|paste|replace|fill in)\s+[^\]]+\]", "English bracketed placeholder"),
    (r"\[(?:chèn|điền|thêm|nhập|bổ sung)\s+[^\]]+\]", "Vietnamese bracketed placeholder"),
    (r"\b20\d\d-[xX]{2}-[xX]{2}\b", "Placeholder date"),
    (r"\b(?:PASTE_URL_HERE|INSERT_SOURCE_URL|TODO|TBD)\b", "Unresolved template token"),
]

_CHAT_RESIDUE = [
    (r"^(?:certainly!?|of course!?|sure!?|here is (?:a|the)\b|i hope this helps\b)", "Possible conversational preamble or sign-off"),
    (r"^(?:chắc chắn rồi!?|dưới đây là\b|hy vọng (?:thông tin|bài viết) này (?:hữu ích|giúp ích)\b)", "Possible conversational preamble or sign-off"),
    (r"\b(?:let me know if you (?:need|would like)|feel free to ask|i am an ai language model)\b", "Possible conversational sign-off or aside"),
    (r"\b(?:hãy cho tôi biết nếu bạn|đừng ngần ngại đặt câu hỏi|với tư cách là một (?:mô hình ngôn ngữ|trợ lý AI))\b", "Possible conversational sign-off or aside"),
]

# These are examples to prompt an editorial decision. They are not banned words.
_EDITORIAL_CANDIDATES = {
    "en": [
        (r"\b(?:stands as a testament|serves as a reminder|marks a pivotal moment|underscores its importance)\b", "Check whether this emphasis adds a specific, supported fact."),
        (r"\b(?:rich tapestry|vibrant landscape|multifaceted|delve into|plays a crucial role)\b", "Check whether a more precise description would serve the point."),
        (r"\b(?:experts agree|observers say|critics argue|industry sources suggest)\b", "Identify the source or name the person behind this attribution."),
        (r"\bnot only\b.{0,180}\bbut also\b", "Check whether this contrast is needed and accurately framed."),
        (r"\blooking ahead\b.{0,160}\b(?:poised|well-positioned|set to)\b", "Check whether this forecast has evidence and belongs here."),
    ],
    "vi": [
        (r"\b(?:đóng vai trò then chốt|là minh chứng rõ nét|đánh dấu bước ngoặt|khẳng định vị thế)\b", "Kiểm tra xem cụm nhấn mạnh này có thêm thông tin cụ thể, có nguồn hay không."),
        (r"\b(?:bức tranh toàn cảnh|bức tranh đa sắc màu|mang đậm dấu ấn|đi sâu vào)\b", "Cân nhắc cách mô tả cụ thể hơn nếu phù hợp với ý tác giả."),
        (r"\b(?:nhiều chuyên gia cho rằng|giới quan sát nhận định|các báo cáo gần đây chỉ ra)\b", "Nêu nguồn cụ thể hoặc xác định người đưa ra nhận định."),
        (r"\bkhông chỉ\b.{0,180}\bmà còn\b", "Kiểm tra xem cấu trúc đối chiếu này có cần thiết và chính xác không."),
        (r"\bnhìn về tương lai\b.{0,160}\b(?:hứa hẹn|được kỳ vọng|sẽ tiếp tục)\b", "Kiểm tra căn cứ của dự báo và sự cần thiết của câu này."),
    ],
}


def _matches(lines: list[str], patterns: list[tuple[str, str]], category: str, *, insensitive: bool = True) -> list[dict[str, Any]]:
    flags = re.IGNORECASE if insensitive else 0
    findings: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        for pattern, message in patterns:
            match = re.search(pattern, line, flags)
            if match:
                findings.append({
                    "line": line_number,
                    "column": match.start() + 1,
                    "category": category,
                    "message": message,
                    "excerpt": line.strip()[:180],
                })
    return findings


def scan_text(text: str, lang: str = "both") -> dict[str, Any]:
    if lang not in {"en", "vi", "both"}:
        raise ValueError("lang must be 'en', 'vi', or 'both'")
    lines = text.splitlines()
    findings: list[dict[str, Any]] = []
    findings.extend(_matches(lines, _PLATFORM_ARTIFACTS, "possible_artifact"))
    findings.extend(_matches(lines, _PLACEHOLDERS, "placeholder"))
    findings.extend(_matches(lines, _CHAT_RESIDUE, "possible_chat_residue"))
    findings.extend(_matches(lines, [(r"\s+—\s+", "Check whether this dash is the intended punctuation."), (r"\[\^\d+\]", "Check that this footnote marker has a matching note.")], "format_or_note_check"))
    for language in (("en", "vi") if lang == "both" else (lang,)):
        findings.extend(_matches(lines, _EDITORIAL_CANDIDATES[language], "editorial_candidate"))

    unique: list[dict[str, Any]] = []
    seen = set()
    for finding in sorted(findings, key=lambda item: (item["line"], item["column"], item["category"])):
        key = (finding["line"], finding["column"], finding["category"], finding["message"])
        if key not in seen:
            seen.add(key)
            unique.append(finding)
    return {
        "schema_version": "editorial-review.v1",
        "notice": NOTICE,
        "language_scope": lang,
        "total_findings": len(unique),
        "findings": unique,
    }


def format_report(result: dict[str, Any]) -> str:
    lines = ["Editorial review prompts", result["notice"], f"Findings: {result['total_findings']}"]
    if not result["findings"]:
        lines.append("No review prompts were triggered. This is not a quality, accuracy, originality, or authorship certification.")
    for index, finding in enumerate(result["findings"], 1):
        lines.extend([
            f"{index}. Line {finding['line']}, column {finding['column']} [{finding['category']}]: {finding['message']}",
            f"   {finding['excerpt']}",
        ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Show optional editorial review prompts for English or Vietnamese plain text.")
    parser.add_argument("file", nargs="?", help="UTF-8 text or Markdown file. Reads stdin when omitted.")
    parser.add_argument("--lang", choices=("en", "vi", "both"), default="both")
    parser.add_argument("--json", action="store_true", help="Write the editorial-review.v1 JSON result.")
    args = parser.parse_args(argv)
    try:
        if args.file:
            content = Path(args.file).read_text(encoding="utf-8")
        else:
            if hasattr(sys.stdin, "reconfigure"):
                sys.stdin.reconfigure(encoding="utf-8")
            content = sys.stdin.read()
        result = scan_text(content, args.lang)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Could not review input: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else format_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
