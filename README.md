# Job Hunting CV Agent

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Interface](https://img.shields.io/badge/Interface-CLI-lightgrey)
![Powered by OpenAI](https://img.shields.io/badge/Powered%20by-OpenAI-black)
![Status](https://img.shields.io/badge/Status-V1-orange)

A local CLI tool for tailoring CVs to job descriptions.

The tool imports an existing CV, builds a reusable HTML template from it, stores your experience as local evidence files, and generates a tailored CV for a job role as HTML and PDF.

This is a V1 project: the full CLI flow works, but it is still intended for careful local use rather than as a polished hosted product.

## What It Does

- Stores your source CV locally for reuse.
- Creates a reusable `template.html` from the uploaded CV.
- Turns rough experience notes into structured local Markdown evidence files.
- Fetches job descriptions from URLs, with paste/file fallback.
- Uses an OpenAI agent to select and tailor relevant content.
- Renders a tailored `cv.html` and clickable-link `cv.pdf`.
- Keeps generated CVs and personal evidence out of git.

## Requirements

- Python 3.11+
- Google Chrome, Chromium, or Microsoft Edge for PDF export
- An OpenAI API key

## Setup

Clone the repo and install it locally:

```bash
git clone https://github.com/Oskito00/job-hunting.git
cd job-hunting
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Create a `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
```

You can optionally set a model:

```bash
OPENAI_MODEL=gpt-5.5
```

## Quick Start

Run the guided flow:

```bash
cv-agent wizard
```

The wizard will guide you through importing your CV, adding experience notes, providing a job description, and generating the tailored CV outputs.

## Normal CLI Flow

Create a local workspace from your current CV:

```bash
cv-agent setup --cv path/to/current-cv.pdf
```

For PDFs, the CLI stores the source CV, renders page images, and uses those images to create the reusable HTML template. Extracted text is also used to initialise the local profile and experience bank.

Add rough experience notes:

```bash
cv-agent add-experience --text "Built an internal dashboard with FastAPI and React..."
```

You do not need to write YAML by hand. The experience writer agent classifies rough notes into local Markdown evidence files under `.cv-agent/experience-bank/` and adds frontmatter automatically.

Create a tailored CV from a job URL:

```bash
cv-agent create --url "<job-url>" --company "<company>" --role "<role>"
```

`create` fetches and extracts the job description from the URL. If extraction is not confident, it asks you to paste the job description.

Use a saved job description file instead:

```bash
cv-agent create --jd-file job.md --company "<company>" --role "<role>"
```

The tool is reusable across multiple roles. Run setup once:

```bash
cv-agent setup --cv path/to/current-cv.pdf
```

That creates the local `.cv-agent/` workspace. Then create a new application pack for each role:

```bash
cv-agent create --url "<job-url>" --company "Company A" --role "Role A"
cv-agent create --url "<job-url-2>" --company "Company B" --role "Role B"
cv-agent create --jd-file another-job.md --company "Company C" --role "Role C"
```

Each application folder contains:

- `cv-content.json`
- `cv.html`
- `cv.pdf`
- `jd.md`
- `coverage-report.md`
- `render-report.md`

Rerender HTML or PDF from an existing application:

```bash
cv-agent render applications/<application-folder>
cv-agent pdf applications/<application-folder>
```

Request strict one-page output:

```bash
cv-agent create --url "<job-url>" --company "<company>" --role "<role>" --one-page
```

Skip PDF export while debugging:

```bash
cv-agent create --jd-file job.md --company "<company>" --role "<role>" --no-pdf
```

## Local Files

The tool writes personal and generated files locally:

- `.cv-agent/` stores your source CV, profile, template, and evidence bank.
- `applications/` stores generated CV outputs.
- `.env` stores local environment variables.

These paths are ignored by git. Do not commit personal CVs, API keys, or generated application folders.

## Current Limitations

- One-page mode is strict and may need further overflow detection work.
- The generated template controls the overall CV layout, but repeated section internals are still partly rendered by Python.
- Voice-note ingestion is not part of V1.
- Job URL extraction works for normal readable pages, but some sites may require paste/file fallback.

## Developer Notes

Contributors are welcome. This is an early project, so small, focused pull requests are preferred.

Run tests with:

```bash
python -m unittest discover tests
```

Useful checks before opening a PR:

```bash
python -m compileall -q src tests
git diff --check
```

Contribution workflow:

- Create a branch from `main`.
- Keep personal data out of commits.
- Add or update focused tests for behavior changes.
- Open a pull request back into `main` with a clear summary and test notes.

Main is protected by repository rules, so changes should go through PRs rather than direct pushes.
