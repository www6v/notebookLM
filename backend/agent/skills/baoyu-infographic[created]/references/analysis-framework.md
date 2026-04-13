# Analysis Framework

Use this framework to produce the stage-one analysis artifact for an infographic workflow.

## Goals

- Understand the source well enough to compress it into a visual story.
- Separate essential information from supporting detail.
- Recommend a presentation strategy that fits a single infographic image.

## Output Structure

Produce markdown with these sections:

1. `## Main Topic`
2. `## Audience And Intent`
3. `## Key Messages`
4. `## Evidence To Preserve`
5. `## Visual Opportunities`
6. `## Layout And Style Recommendation`
7. `## Copy Risks`

## What To Extract

- The single clearest topic of the source.
- The intended audience if it can be inferred.
- Three to six key messages that deserve visual emphasis.
- Critical numbers, proper nouns, definitions, or contrasts that must survive compression.
- The most useful visual patterns, such as comparison, hierarchy, process, timeline, map, or grouped cards.

## Layout And Style Recommendation

When writing `## Layout And Style Recommendation`:

- Mention the normalized `layout`, `style`, `aspect`, and language if they are supplied as parameters.
- If the source suggests a different option, mention that as an alternative, but keep the normalized value explicit.
- Explain the recommendation in one short paragraph and one short bullet list.

## Copy Risks

Call out anything likely to break the final image quality:

- Overly dense wording
- Long quotations
- Too many sections
- Tiny labels
- Ambiguous terminology
- Conflicting numbers

## Tone

- Analytical
- Concise
- Ready for downstream execution
