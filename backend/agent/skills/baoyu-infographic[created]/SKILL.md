---
description: Create an infographic through staged analysis, structured copy, prompt assembly, and image generation.
---
# Baoyu Infographic

Use this skill to turn one source markdown document into a staged infographic workflow output.

## Supported Inputs

- Source document: one workspace markdown file that contains the material to summarize.
- Output directory: a workspace directory where stage artifacts will be written.
- Common options:
  - `title`
  - `language` or `lang`
  - `aspect`
  - `layout`
  - `style`
  - `detail_level`
  - `custom_prompt`

## Workflow

### Step 1: Analyze the source

- Read the source file and `references/analysis-framework.md`.
- Produce a compact but actionable analysis document.
- Write the result to the stage output path, typically `analysis.md`.

### Step 2: Build structured infographic content

- Read the source file, the analysis output, and `references/structured-content-template.md`.
- Convert the source into a clean infographic brief with section hierarchy, copy blocks, and visual guidance.
- Write the result to the stage output path, typically `structured-content.md`.

### Step 3: Refine for visual communication

- Remove low-value detail.
- Keep only information that improves the final visual.
- Preserve critical facts, terminology, numbers, and named entities.

### Step 4: Lock the visual system

- Normalize the chosen `layout`, `style`, `aspect`, and output language.
- If the task parameters already provide these values, follow them.
- If the analysis recommends a different approach, mention the normalization inside the artifact instead of silently changing it.

### Step 5: Assemble the final image prompt

- Read the structured content plus:
  - `references/base-prompt.md`
  - `references/layouts/<layout>.md`
  - `references/styles/<style>.md`
- Write one final image-generation prompt markdown file to the requested prompt path.
- The final prompt must be directly usable for image generation without extra explanation.

### Step 6: Render the image

- When the workflow asks for the final image, use `generate_image_from_promptfile`.
- Pass the provided prompt file path and output file path.
- Use the requested aspect ratio.
- Do not stop after describing the image; actually generate it.

## Execution Rules

- Use workspace-relative paths exactly as provided by the runtime.
- Prefer writing complete files with `write_file`.
- Load reference files progressively; do not copy them blindly into artifacts.
- Keep stage outputs deterministic, professional, and easy for later stages to consume.
- Do not invent new workflow stages or file names when the task already specifies them.
