---
name: source-metadata
description: Generate a meaningful filename, five tags, and a concise summary for one uploaded source document.
---

# Source Metadata Generator

Generate metadata for one uploaded source so the UI can show better title and preview information.

## Input

You will receive:
- `original_filename`: original uploaded file name (may include extension)
- `source_type`: source type (pdf, docx, txt, markdown, csv, pptx, image, audio, video, web, youtube, bilibili)
- `content_language_hint`: language hint if available
- `content`: extracted full text or long transcript/description

## Required Output

Return strict JSON only, no markdown fence, no extra text:

```json
{
  "filename": "meaningful filename without extension",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "summary": "one concise paragraph summary"
}
```

## Rules

1. `filename`
   - Must be meaningful and specific to content.
   - Do not include extension.
   - Keep it concise: 6-80 characters.
   - Avoid file-system special characters: `\\ / : * ? \" < > |`.
   - Keep language consistent with content language.

2. `tags`
   - Exactly 5 items.
   - Each tag should be 2-20 characters and content-relevant.
   - No duplicates, no empty strings.
   - Prefer noun phrases.

3. `summary`
   - Single paragraph, informative and factual.
   - Keep within 60-240 words.
   - Cover main topic, key points, and value.
   - Keep language consistent with content language.

4. Robustness
   - If content is noisy or partial, still infer the best possible metadata from available signals.
   - Never output placeholders like `N/A`, `unknown`, `tag1`.

## Validation Checklist

Before output:
- Is the output valid JSON?
- Does `tags` have exactly 5 unique strings?
- Does `filename` exclude extension and illegal characters?
- Is `summary` a single paragraph?
