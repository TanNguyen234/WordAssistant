# English Ruleset: Catalog of AI Writing Signs & Rectification

This document provides the exhaustive catalog of English-language AI writing signs, categorized into 7 operational dimensions derived from the official Wikipedia field guide ([Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)).

---

## 1. Content & Argumentation Flaws

### 1.1 Undue Emphasis on Significance, Legacy, and Broader Trends (WP:AILEGACY, WP:AITREND)
- **The Pattern:** LLMs artificially puff up the importance of even the most mundane subjects (population data, minor tools, local venues, obscure biological species) by claiming they "mark a pivotal moment", "serve as a testament", or "reflect broader historical/social shifts".
- **Banned / Red-Flag Words:**
  `stands as a testament`, `serves as a reminder`, `a pivotal/crucial/vital/key moment/role`, `underscores its importance`, `reflects broader`, `symbolizing its enduring/lasting`, `contributing to the`, `setting the stage for`, `marking/shaping the`, `represents a shift`, `focal point`, `indelible mark`, `deeply rooted`.
- **Bad Example:**
  > "The founding of the local municipal clinic in 1994 marked a pivotal moment in the healthcare landscape of the district, serving as a testament to the community's enduring commitment to public well-being and reflecting broader national shifts toward decentralized medical care."
- **Remediation / Corrected:** State objective, verifiable facts without philosophical fluff:
  > "The municipal clinic was established in 1994 to provide outpatient care in the district."

---

### 1.2 Canned Emphasis on Notability, Attribution, and Media Coverage (WP:AIATTR)
- **The Pattern:** Rather than summarizing what reliable sources report, the LLM hits the reader over the head with statements about *the nature of the sources themselves* (e.g. "documented in regional press", "profiled in multiple prominent media outlets", "maintains an active social media presence").
- **Banned / Red-Flag Words:**
  `independent coverage`, `prominent/major media outlets`, `trade publications`, `cited/featured/profiled in`, `written by a leading expert`, `active social media presence`, `maintains a strong digital presence`.
- **Bad Example:**
  > "Dr. Smith maintains an active social media presence and has been profiled in multiple high-quality, independent media outlets including Wired and Forbes, demonstrating significant and sustained coverage."
- **Remediation / Corrected:** Cite the sources directly in footnotes or summarize the substantive information they reported:
  > "Smith researched distributed database consistency at MIT and co-authored the Raft protocol analysis in 2018."

---

### 1.3 Superficial Analyses with Dangling Trailing Participles (WP:SUPERFICIAL)
- **The Pattern:** Sentences that mechanically append a present participle phrase (`-ing`) at the end to force an ungrounded conclusion, moral lesson, or sociological synthesis.
- **Banned / Red-Flag Endings:**
  `, highlighting the importance of...`, `, underscoring its significance...`, `, fostering collaboration...`, `, enhancing community engagement...`, `, contributing to socioeconomic development...`, `, reflecting its continued relevance in the landscape.`
- **Bad Example:**
  > "The transit authority replaced 40 diesel buses with hybrid models in 2023, highlighting its ongoing commitment to sustainability and underscoring its role as a forward-thinking urban center."
- **Remediation / Corrected:** Cut the trailing participial clause completely:
  > "In 2023, the transit authority replaced 40 diesel buses with hybrid models."

---

### 1.4 Promotional & Travelogue Buzzwords (WP:AIPUFFERY)
- **The Pattern:** Adopting the tone of a tourism brochure, corporate marketing deck, or press release, even in encyclopedic or technical summaries.
- **Banned / Red-Flag Words:**
  `boasts a`, `vibrant`, `rich tapestry`, `nestled in the heart of`, `breathtaking`, `seamlessly`, `groundbreaking`, `natural beauty`, `diverse array`, `exemplifies dedication to`, `state-of-the-art`.
- **Bad Example:**
  > "Nestled in the heart of the valley, the town boasts a vibrant tapestry of cultural heritage and breathtaking landscapes, offering visitors a unique glimpse into the region's rich history."
- **Remediation / Corrected:**
  > "The town is located in the central valley and was founded as a railway depot in 1882."

---

### 1.5 Vague Expressions of Connection or Association (WP:AICONNECT)
- **The Pattern:** Instead of using precise relational verbs ("was CEO of", "taught physics at", "patented"), LLMs use squishy relational hedges.
- **Banned / Red-Flag Words:**
  `associated with`, `in connection with/to`, `connected with`, `became associated with`.
- **Bad Example:**
  > "In 2018, she became associated with executive leadership at Acme Corp, where sources connect her with product development initiatives."
- **Remediation / Corrected:**
  > "In 2018, she was hired as Vice President of Product Development at Acme Corp."

---

### 1.6 Vague Attributions & Overgeneralized Opinions (WP:AIWEASEL)
- **The Pattern:** Presenting a single author's critique as a consensus among "industry observers" or "scholars", or fabricating an anonymous collective.
- **Banned / Red-Flag Words:**
  `Industry reports suggest`, `Observers have noted`, `Experts argue`, `Critics point out`, `Multiple scholars agree` (when only one citation exists).
- **Remediation:** Name the exact person, date, and publication:
  > "According to a 2024 survey by Gartner..." or "Economist Jane Doe argued in 2023 that..."

---

### 1.7 Rigid "Challenges and Future Outlook" Formulas (WP:FACESCHALLENGES)
- **The Pattern:** Articles ending with a robotic two-part outline formula: "Despite its [positive qualities], [Subject] faces challenges... looking ahead, [Subject] is well-positioned to navigate the evolving landscape."
- **Bad Example:**
  > "Despite its rapid adoption and industrial success, the facility faces challenges including supply-chain constraints. Looking ahead, ongoing investments position it as a key contributor for decades to come."
- **Remediation:** Present specific, sourced obstacles without the dramatic preamble or speculative boosterism.

---

## 2. Vocabulary & Cliché Density (WP:AIVOCAB)

LLM generation exhibits heavy clustering of specific over-represented vocabulary. Treat edits containing 3 or more of these within 200 words as high-probability AI text:

### Chronological LLM Lexical Clustering:
- **2023 – Mid-2024 (GPT-4 era):**
  `additionally`, `boasts`, `bolstered`, `crucial`, `delve`, `delving`, `deep dive`, `emphasizing`, `enduring`, `focal point`, `garner`, `intricate / intricacies`, `interplay`, `key` (adj), `landscape` (abstract), `meticulously`, `pivotal`, `tapestry`, `testament`, `underscore`, `valuable`, `vibrant`.
- **Mid-2024 – Mid-2025 (GPT-4o era):**
  `align with`, `bolstered`, `crucial`, `emphasizing`, `enhance`, `enduring`, `fostering`, `highlighting`, `pivotal`, `showcasing`, `underscore`, `vibrant`.
- **Mid-2025 – Mid-2026 (GPT-5 era):**
  `emphasizing`, `enhance`, `highlighting`, `showcasing` + canned media attribution terminology.
- **Mid-2026+ (GPT-6 era):**
  `challenge`, `clearer`, `dependable`, `echoed`, `foster`, `leverage`, `matters`, `multifaceted`, `practical`, `prioritize`, `quietly`, `steady`, `universally` (often combined with unnaturally short 8–20 word sentences).
- **Grok Specific Idiolect:**
  `causal`, `empirical`, `correlate`, `underscore` (persisting into 2026).

---

## 3. Syntactic & Grammatical Constructs

### 3.1 Copula Avoidance ("is/are" avoidance) (WP:AINOCOPULA)
- **The Pattern:** LLMs systematically replace direct forms of "to be" (`is`, `are`, `was`) with pompous substitutes (`serves as`, `stands as`, `marks`, `functions as`, `operates as`, `holds the distinction of being`).
- **Correction:** Restore clean copulas:
  - *Bad:* "The library serves as a repository for regional manuscripts."
  - *Good:* "The library houses regional manuscripts." or "The library is a repository for..."

---

### 3.2 Negative Parallelisms (WP:AIPARALLEL)
- **The Pattern:** Synthetic debate formulas where the LLM argues against an imagined misunderstanding:
  - `Not only X, but also Y`
  - `It isn't just X — it's Y`
  - `Not X, but Y` (e.g. "Not a mirror, but a portal")
  - `Y rather than X`
  - `No X, no Y, just Z`
- **Correction:** State positive facts directly without rhetorical theatrics.

---

### 3.3 Rule of Three Overuse (WP:RO3)
- **The Pattern:** Mechanical triads of adjectives or short clauses appended to sound comprehensive:
  - "The project embodies *innovation, resilience, and sustainability*."
  - "He teaches *technique, theory, and performance*."
- **Correction:** List only what is genuinely relevant and sourced, whether 1, 2, or 4 items.

---

## 4. Formatting & Visual Layout Flaws

1. **Title Case in Section Headings:** Capitalizing all words in subheadings (`== Early Life And Musical Career ==` instead of `== Early life and musical career ==`).
2. **Inline-Header Vertical Lists (WP:AILIST):** Converting continuous prose into bullet points where every item starts with bold text followed by a colon (`* **Early Phase:** description`).
3. **Overuse of Boldface (WP:AIBOLD):** Scattering bold text across the paragraph like sales presentation bullet highlights.
4. **Emoji as Formatting (WP:AIEMOJI):** Decorating headings or bullet points with icons (`🚀 Launch`, `💡 Key Takeaway`, `📌 Overview`).
5. **Thematic Breaks (`---`):** Inserting markdown horizontal rules between consecutive sections.

---

## 5. Conversational Leakage & System Artifacts

### 5.1 Chatbot Preambles & Polite Residue
- Remove any remnant of conversational interaction:
  `Certainly!`, `Here is the revised article:`, `I hope this helps!`, `Let me know if you would like me to...`, `As an AI language model...`

### 5.2 Unfilled Placeholders
- Sweep and eliminate unfilled brackets:
  `[Insert Name]`, `[link to source]`, `2025-XX-XX`, `INSERT_URL_HERE`, `PASTE_SPOTIFY_TRACK_URL_HERE`.

### 5.3 Engine Metadata Artifacts (WP:OAICITE, WP:STARTSPAN, WP:GROKCARD)
- Clean out engine citation bugs:
  - `:contentReference[oaicite:N]`
  - `[oai_citation:N‡domain]`
  - `citeturn0search0` or `0`
  - `({"attribution":{"attributableIndex":"..."}})`
  - `[cite: 1]`, `[span_1](start_span)`
  - `<grok-card data-id="...">`
  - `【85†L261-269】` (DeepSeek daggers)
  - `[attached_file:1]`, `[web:1]`, `ppl-ai-file-upload`
  - URL tracking parameters: `?utm_source=chatgpt.com`, `?utm_source=openai`, `?referrer=grok.com`.

---

## 6. Citation & Reference Verification

1. **Check for Link Rot vs Phantom Links:** Hallucinated links were never archived on the Wayback Machine.
2. **Verify DOI / ISBN Checksums:** LLMs generate plausible-looking 13-digit numbers with invalid check digits.
3. **Detect Unrelated Citations:** An LLM may pair a real DOI with a completely fabricated paper title or unrelated discipline.
4. **Demand Page Numbers for Books:** Citations to 800-page textbooks without specific chapters/pages are often LLM guesses that do not verify the text.
