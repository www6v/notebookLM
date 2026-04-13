# Base Prompt Assembly Guide

Use this guide when converting the structured content into the final image-generation prompt.

## Output Goal

Write one polished prompt for generating a single infographic image.

## Prompt Requirements

- The prompt must be immediately usable by an image model.
- Describe the final composition, not the workflow.
- Keep it visually specific and production-oriented.
- Include the requested output language for all visible text.
- Preserve important facts from the structured content.
- Ask for clear hierarchy, readable labels, and balanced spacing.

## Mandatory Prompt Parts

The final prompt should cover:

1. Subject and purpose
2. Overall composition
3. Chosen layout behavior
4. Chosen visual style
5. Major sections or visual blocks
6. Typography and readability constraints
7. Color and mood
8. Explicit negatives, such as clutter, tiny text, distorted labels, photo realism when not desired, and inconsistent icon styles

## Assembly Instructions

- Start with one sentence describing the infographic topic and audience.
- Then describe the page structure from top to bottom or center outward.
- Integrate the selected layout reference and style reference naturally.
- Mention the most important section titles or blocks.
- Mention any critical numbers or labels that must remain legible.
- End with a short negative list that reduces common image-generation failure modes.

## Output Format

- Output plain markdown text only.
- Do not wrap the final prompt in code fences.
- Do not include headings like "Explanation" or "Reasoning".
