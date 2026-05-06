# Draft Issue: Make CV generation template-aware and agentic

## Problem

The tailoring agent currently generates structured `cv-content.json`, and the renderer deterministically inserts that content into the selected template.

That is good for validation and safety, but the generation step is not yet aware enough of the actual template layout. The LLM decides what content is relevant, but it does not have a strong feedback loop around how much content the chosen template can support, which sections are visually prominent, or whether the CV should be one page or multi-page for a specific application.

## Goal

Make the LLM generation step more template-aware while keeping final rendering deterministic and safe.

The agent should decide:

- Which experience-bank evidence is most relevant to the job.
- Which sections should be included.
- How much detail each role/project deserves.
- Whether one-page or multi-page output is appropriate.
- What should be compressed, moved, or omitted when space is limited.

The renderer should still be responsible for escaping, placeholder replacement, HTML validity, and PDF generation.

## Proposed Approach

Introduce a generation planning step before final `cv-content.json` output.

The plan could include:

- Target page mode: `one_page` or `multi_page`.
- Required sections.
- Optional sections.
- Work roles to include, usually all roles.
- Bullet budget per role.
- Project inclusion decisions.
- Skills emphasis.
- Notes about evidence that should be preserved.
- Notes about content that was intentionally omitted.

The final CV content agent can then produce `cv-content.json` from that plan.

## Inputs To Include

- Job description.
- Experience bank search/read results.
- Static profile and education.
- Template metadata, including available placeholders and section partials.
- Optional render feedback, such as overflow measurements or PDF page count.

## Acceptance Criteria

- The generation step produces an explicit content plan before final CV JSON.
- The plan explains section inclusion, role inclusion, project inclusion, and page-mode choice.
- Work experience roles are included by default unless there is a clear reason to omit one.
- One-page mode uses a content budget before rendering.
- Multi-page mode allows richer detail without artificial one-page compression.
- The generated `cv-content.json` remains schema-validated.
- Evidence paths are still required for generated profile, work, project, and additional-experience content.

## Non-Goals

- Do not let the LLM write the final complete HTML CV directly.
- Do not remove structured JSON validation.
- Do not make PDF export dependent on a model call.

## Notes

This complements template partial rendering. Partial rendering controls how repeated entries look; template-aware generation controls what content is selected and how dense the CV should be.
