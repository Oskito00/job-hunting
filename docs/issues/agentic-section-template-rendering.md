# Draft Issue: Let CV templates control repeated section formatting

## Problem

The current CV generation flow is close to the target product shape:

- A source CV is uploaded.
- The agent visually creates a `template.html` from the uploaded CV.
- The agent extracts profile/contact/experience data into the local workspace.
- A tailored `cv-content.json` is generated from the job description and experience bank.
- The renderer inserts that structured content into the template and exports HTML/PDF.

The remaining gap is that the final CV is still partly deterministic. The LLM controls the selected content, but Python still controls the internal HTML structure for repeated sections such as education, work experience, projects, skills, and bullets.

That means details like date placement, bolding, role/company ordering, bullet indentation, and education formatting may not match the uploaded CV template unless they happen to match the hardcoded renderers in `html_render.py`.

## Goal

Make `template.html` responsible for the formatting of repeated CV entries while keeping the actual content structured, validated, escaped, and safe to render.

The user should be able to drop in a CV, get a visually faithful reusable template, add more experience, and have the LLM decide what content belongs in the new CV while the generated template controls how that content is laid out.

## Proposed Approach

Extend the generated `template.html` format so it can include optional section partials using native HTML `<template>` tags.

Example:

```html
<template id="education-entry">
  <div class="education-entry">
    <div class="entry-header">
      <strong>{{institution}}</strong>
      <strong>{{dates}}</strong>
    </div>
    <div>{{degree}}</div>
    <div>{{details}}</div>
  </div>
</template>

<template id="work-entry">
  <article class="work-entry">
    <div class="entry-header">
      <strong>{{role}}</strong>
      <span>{{dates}}</span>
    </div>
    <div>{{company}}</div>
    {{bullets}}
  </article>
</template>

<template id="bullet-item">
  <li>{{text}}</li>
</template>
```

The Python renderer should:

- Parse optional partials from `template.html`.
- Use a partial when one exists for a repeated entry type.
- Fall back to the current deterministic renderer when a partial is missing.
- Escape all scalar content before insertion.
- Only allow known placeholders for each partial type.
- Leave section-level placeholders such as `{{education}}`, `{{work_experience}}`, and `{{skills}}` as the insertion points for rendered repeated content.

## Suggested Partials

- `contact-item`
- `education-entry`
- `skill-item`
- `work-entry`
- `project-entry`
- `additional-experience-entry`
- `bullet-list`
- `bullet-item`

## Template Agent Changes

Update the template-generation agent prompt so it:

- Recreates the visual structure of the uploaded CV from rendered page images.
- Adds section-level placeholders for major CV sections.
- Adds partial templates for repeated entries.
- Mirrors internal formatting from the uploaded CV, including date alignment, bold text, spacing, bullet style, and section hierarchy.
- Avoids hardcoded assumptions such as star ratings for skills.

## Acceptance Criteria

- Given a generated `template.html` with an `education-entry` partial, education entries render using that partial rather than the hardcoded Python education layout.
- Given a generated `template.html` with a `work-entry` and `bullet-item` partial, work experience entries and bullets render using those partials.
- If a partial is missing, rendering still succeeds using the existing fallback layout.
- Rendered HTML has no unresolved `{{placeholder}}` tokens.
- User-provided content is escaped before insertion into partials.
- Existing tests for basic rendering, custom templates, PDF generation, and one-page mode continue to pass.
- New tests cover partial rendering, fallback rendering, placeholder validation, and escaping.

## Non-Goals

- Do not let the LLM output the final complete CV HTML directly.
- Do not remove structured `cv-content.json`.
- Do not make final rendering depend on model calls.
- Do not solve every possible CV layout edge case in one change.

## Implementation Notes

Keep the architecture as:

```text
source CV + images -> template agent -> template.html with placeholders and partials
experience bank + JD -> tailoring agent -> cv-content.json
cv-content.json + template.html -> deterministic safe renderer -> cv.html/pdf
```

This keeps the system agentic where judgement is needed, but deterministic where correctness, escaping, validation, and PDF generation matter.
