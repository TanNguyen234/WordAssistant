# Academic integrity and natural-writing contract

WordAssistant supports ethical originality checks. It does not promise to make generated text "undetectable" and does not classify a writer as human or AI.

## Why detector-evasion is not a product gate

- Turnitin currently limits its AI Writing Report to English, Spanish, Japanese, and Arabic, not Vietnamese. It also hides scores below 20% because false positives are more likely, and says the score must not be the sole basis for adverse action: <https://guides.turnitin.com/hc/en-us/articles/22774058814093-Using-the-AI-Writing-Report>
- Turnitin's model release notes show that detection behavior changes over time: <https://guides.turnitin.com/hc/en-us/articles/28294949544717-AI-writing-detection-model>
- A 2025 NAACL study found that detector sensitivity can collapse at strict false-positive rates and that moderate transformations can evade detection: <https://aclanthology.org/2025.findings-naacl.271/>
- A 2026 peer-reviewed educational-integrity study recommends using detectors only as initial flags, never sole evidence: <https://doi.org/10.1007/s40979-026-00226-w>
- UNESCO's human-centered guidance emphasizes transparent, ethical human validation: <https://www.unesco.org/en/articles/guidance-generative-ai-education-and-research?hub=67098>

The stronger approach is to retain evidence of how the work was produced. Turnitin's Writing Report similarly emphasizes process evidence such as playback and pasted-text history: <https://guides.turnitin.com/hc/en-us/articles/36916426919949-Reviewing-the-Writing-Report>

## Enforced checks

`wordassistant integrity audit FINAL.docx --evidence evidence.json --profile PROFILE --variant VARIANT --json` performs deterministic checks for:

- exact DOCX and evidence-registry hashes;
- numeric citation and bibliography consistency;
- profile minimum-reference policy and explicit primary-source tags;
- synthetic evidence, missing/invalid registries, unresolved placeholders, and invisible Unicode with spoofing risk;
- quotes without nearby citations and quantitative claims without citation markers;
- an explicit AI-use disclosure;
- repetitive sentence openings, repeated n-grams, and configured punctuation as WARN-only human-review heuristics.

The audit does not compare text against a publication corpus. A similarity provider can be added later only as an explicit optional backend with observed provider evidence and clear licensing/privacy boundaries.

## Provenance

`wordassistant integrity provenance FINAL.docx --evidence evidence.json --output FINAL.provenance.json --json` atomically writes a manifest bound to the current DOCX and registry SHA-256 values. A prior audit cannot be reused after either file changes.

For academic delivery, keep drafts/version history, source notes, the evidence registry, the integrity report, the provenance manifest, and the final rendered pages together. Disclose AI assistance according to the institution's policy; do not fabricate a declaration.
