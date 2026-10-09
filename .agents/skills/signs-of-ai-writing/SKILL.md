---
name: signs-of-ai-writing
description: Comprehensive bilingual (English & Vietnamese) ruleset and detection guide for identifying, auditing, and eliminating signs of AI writing based on the Wikipedia:Signs_of_AI_writing standard. Make sure to use this skill whenever the user asks to review text for AI writing, check or detect AI patterns, humanize or de-AI content, clean robotic or puffed-up drafts, eliminate AI clichés/vocabulary in English or Vietnamese, fix formatting artifacts (inline lists, emoji headings, em-dash clutter), or audit citations for hallucinated references.
---

# Signs of AI Writing (Bilingual EN / VI)

A comprehensive field guide, ruleset, and verification skill for detecting, auditing, and eliminating signs of machine-generated text in both **English** and **Vietnamese**, built on the authoritative [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) guidelines.

---

## 1. Core Philosophy & Working Contract

1. **Descriptive, Not Prescriptive:**
   Signs are diagnostic *symptoms*, not the disease itself. Fixing only the superficial surface markers (e.g. replacing *delve* or deleting bolding) without addressing deeper issues (hallucinated sources, puffery, weasel claims, lack of evidence) does not solve the underlying quality defect.
2. **Anti-Evasion Principle (Academic & Real-World Integrity):**
   This skill is designed to produce **authentic, verifiable, rigorous human-standard prose**—**never** to cheat or evade AI detectors using gimmickry or syntactic obfuscation.
3. **False-Positive Prevention:**
   Never accuse a writer of using AI based on a single factor (e.g. formal vocabulary, flawless grammar, or one transition word). Definite proof requires engine leaks, unedited placeholders, or a high-density cluster of multiple structural tropes. Consult [references/false-positives-and-human-signs.md](references/false-positives-and-human-signs.md).

---

## 2. The 7 Pillars of AI Writing Detection

| Pillar | English Key Hallmarks | Vietnamese Parallels (Tiếng Việt) | Primary Remedy |
|---|---|---|---|
| **1. Significance & Legacy Inflation** | "stands as a testament", "pivotal moment", "reflects broader trends", "enduring legacy" | "đóng vai trò then chốt", "là minh chứng rõ nét", "đánh dấu bước ngoặt", "mang đậm dấu ấn" | Cut philosophical boosterism; state plain chronological facts. |
| **2. Trailing Superficial Participles** | Sentence-ending: `, highlighting...`, `, underscoring...`, `, fostering...` | Câu nối đuôi: `, qua đó khẳng định...`, `, góp phần nâng cao...`, `, từ đó tạo tiền đề...` | Sever the trailing participle clause; end sentence cleanly. |
| **3. Canned Attribution & Weasel Words** | "profiled in prominent media", "observers argue", "active social media presence" | "được đưa tin rộng rãi trên báo đài", "giới quan sát nhận định", "nhiều chuyên gia cho rằng" | Cite substantive facts and specific named experts directly. |
| **4. Negative Parallelisms** | "Not only X, but also Y", "Not X, but Y", "Y rather than X", "No X, no Y, just Z" | "Không chỉ là X mà còn là Y", "Không phải X mà chính là Y", "X thay vì Y", "Không hoa mỹ, chỉ là..." | State assertions directly without artificial contrastive debate. |
| **5. AI Vocabulary Saturation** | *delve, tapestry, pivotal, crucial, vibrant, intricate, interplay, landscape, testament, bolster* | *bức tranh toàn cảnh, đa sắc màu, nép mình bên, tọa lạc đắc địa, bề dày lịch sử, đi sâu vào* | Ban the cliché glossary; replace with precise, grounded verbs. |
| **6. Copula Avoidance** | Replacing "is/are" with "serves as", "stands as", "functions as", "marks" | Thay "là / có" bằng "được xem như là", "đóng vai trò là", "nắm giữ kỷ lục là", "sở hữu một..." | Restore direct copulas (*is*, *are*, *là*, *có*). |
| **7. Structural & Formatting Tells** | Inline-header lists (`* **Title:**`), emoji headers, title-cased subheadings, leaked `---` | Bullet point chẻ nhỏ văn xuôi, emoji trang trí (`🚀`, `💡`), in đậm từ khóa cơ học | Restore continuous prose paragraphs; strip emojis and excess bold. |

---

## 3. Leaked Engine Artifacts & System Glitches (Critical Tells)

If any of these markers appear, the text is **100% machine-generated** and was unedited from an LLM interface:

- **ChatGPT:** `:contentReference[oaicite:0]`, `[oai_citation:0‡domain]`, `turn0search0`, `citeturn0search0`, `0`, `({"attribution":{"attributableIndex":"..."}})`.
- **Gemini:** `[cite: 1]`, `[span_1](start_span)`, `[span_1](end_span)`.
- **Grok:** `<grok-card data-id="...">`, `grok_render_citation_card_json`.
- **DeepSeek:** `【85†L261-269】` (lenticular brackets with dagger source lines).
- **Perplexity:** `[attached_file:1]`, `[web:1]`, `ppl-ai-file-upload`.
- **URL Tracking:** `?utm_source=chatgpt.com`, `?utm_source=openai`, `?referrer=grok.com`.
- **Unfilled Placeholders:** `[Insert Name]`, `[link to source]`, `2025-XX-XX`, `[Chèn liên kết]`, `[Điền tên]`.
- **Conversational Banter:** "Certainly!", "Here is a...", "I hope this helps!", "Chắc chắn rồi!", "Dưới đây là bản thảo...".

---

## 4. Operational De-AI & Audit Workflow

When auditing or rewriting any document, follow this 4-stage pipeline:

```
Step 1: Automated Linting
   │    Run: python scripts/ai_writing_linter.py <file>
   ▼
Step 2: Strip Leaks & Preambles
   │    Remove chat pleasantries, system tags, and unfilled brackets.
   ▼
Step 3: Structural De-Biasing & Fact-Checking
   │    - Dissolve bulleted lists back into flowing paragraphs.
   │    - Verify every external link, DOI, ISBN, and page citation.
   ▼
Step 4: Prose Humanization
        - Restore "is/are" and "là/có".
        - Delete trailing participial clauses.
        - Purge vocabulary clichés using reference tables.
        - Vary sentence cadence (mix 6-word and 25-word sentences).
```

### Quick Command: Run the Bundled Linter
```powershell
# Scan a file for both English and Vietnamese AI signs:
python scripts/ai_writing_linter.py path/to/document.md

# Scan for Vietnamese only:
python scripts/ai_writing_linter.py path/to/document.md --lang vi

# Output structured JSON:
python scripts/ai_writing_linter.py path/to/document.md --json
```

---

## 5. Reference Library

Load these detailed references into context as needed:
- **[references/rules-en.md](references/rules-en.md)**: Exhaustive English catalog, chronological LLM vocabulary breakdown (GPT-4 through GPT-6), and before/after rewrites.
- **[references/rules-vi.md](references/rules-vi.md)**: Comprehensive Vietnamese catalog, machine-translation tropes, Vietnamese cliché glossary, and localized before/after pairs.
- **[references/false-positives-and-human-signs.md](references/false-positives-and-human-signs.md)**: Evidentiary thresholds, temporal cutoff (Nov 30, 2022), authentic human markers, and avoiding false accusations.
- **[references/prompt-templates-and-deai.md](references/prompt-templates-and-deai.md)**: Reusable prompt templates and instruction blocks for delegating humanizing rewrites.
