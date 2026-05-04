---
type: index
purpose: cv_experience_bank
---

# Experience Bank

This folder contains curated experience notes for generating tailored CV content from a job description.

Use `experience-transcripts/` as the raw source material. Use this folder as the cleaner, canonical bank of claims, projects, skills, and role context that a CV agent can safely draw from.

## Suggested Agent Flow

1. Read the target job description.
2. Extract the employer's required skills, responsibilities, domain, seniority, and keywords.
3. Search these files by `skills`, `domains`, `role_ids`, and `evidence`.
4. Load only the most relevant role and project files.
5. Generate CV bullets using claims from loaded files.
6. Prefer bullets with clear ownership, impact, technical depth, and domain relevance.
7. Flag anything marked `needs_clarification` rather than presenting it as confirmed fact.

## File Types

- `contact.md`: contact details and profile links.
- `education.md`: degree and academic background.
- `roles/`: employment or client context.
- `projects/`: reusable project stories and CV bullet source material.
- `skills.md`: consolidated skills index for quick matching against job descriptions.

## Evidence Policy

Every strong CV claim should ideally point back to one or more source transcript files, an existing CV, or a later-added portfolio/project file.
