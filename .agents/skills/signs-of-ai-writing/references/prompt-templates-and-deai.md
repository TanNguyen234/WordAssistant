# Writing review prompts

These prompts request editorial work. They do not ask a model to imitate a person, conceal tool use, or evade an authorship detector. Replace bracketed instructions with the actual scope and provide only the text and source material needed for the task.

## English copyedit

```text
Edit the passage for [audience and purpose]. Preserve the author's meaning,
uncertainty, technical terms, and voice. Correct only issues that affect
accuracy, clarity, grammar, or flow. Do not add facts or citations. Keep
qualifications that are supported or necessary. Return (1) the edited passage
and (2) a concise list of substantive changes or questions for the author.
```

## Vietnamese copyedit

```text
Biên tập đoạn văn cho [đối tượng đọc và mục đích]. Giữ nguyên ý nghĩa, mức độ
chắc chắn, thuật ngữ chuyên ngành và giọng văn của tác giả. Chỉ sửa điểm ảnh
hưởng đến độ chính xác, rõ ràng, ngữ pháp hoặc mạch văn. Không thêm dữ kiện hay
trích dẫn. Giữ các giới hạn và điều kiện có căn cứ. Trả lại (1) bản đã biên tập
và (2) danh sách ngắn các thay đổi quan trọng hoặc câu hỏi cần tác giả xác nhận.
```

## Claim and citation audit

```text
For each factual claim in the passage, identify the cited source and the exact
page, section, table, or passage that supports it. Compare the claim with the
provided source text. Mark each item as supported, partly supported, unsupported,
or not checked, and explain why. Do not infer support from a title or DOI alone.
Do not invent bibliographic data. Preserve the draft and list proposed changes
separately so the author can review them.
```

## Review a style flag

```text
The attached linter finding is a prompt, not a verdict. Read the surrounding
paragraph and explain whether the wording causes a concrete problem for this
audience. If it does, suggest the smallest correction that preserves meaning
and voice. If it does not, recommend keeping the text. Do not make claims about
who wrote the passage or how a detector would score it.
```
