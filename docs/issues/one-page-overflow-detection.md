# Draft Issue: Detect one-page CV overflow before PDF export

## Problem

Strict one-page mode currently clips content when the rendered CV is taller than A4.

The one-page CSS sets the page height to `297mm` with `overflow: hidden`, so Chrome correctly exports a single page, but any content below the visible area is silently cut off. The current render limits only check approximate content constraints such as bullet counts and character lengths; they do not measure the actual rendered layout.

## Goal

One-page mode should never silently produce a clipped PDF.

The system should either:

- Fit the CV onto one rendered page.
- Trigger a revision/compression pass with useful overflow context.
- Fail clearly and tell the user the content cannot fit in strict one-page mode.

## Proposed Approach

Add a post-render layout validation step for one-page mode:

1. Render `cv.html`.
2. Use a browser measurement step to inspect the rendered page.
3. Compare the page container's `scrollHeight` with its visible/client height.
4. If the page overflows, run an LLM revision pass with the measured overflow context.
5. Re-render and measure again.
6. If it still overflows, fail clearly rather than exporting a clipped PDF.

## Acceptance Criteria

- One-page mode detects when the rendered `.page.one_page` content exceeds the visible A4 height.
- The CLI does not silently export a clipped one-page PDF.
- Overflow creates a clear render report entry.
- At least one revision pass can be triggered using the overflow result.
- Tests cover both fitting and overflowing one-page HTML.
- Existing multi-page rendering remains unchanged.

## Notes

This is separate from character/count render limits. Content can pass those limits and still overflow visually because template CSS, font size, margins, headings, section order, and spacing all affect final height.
