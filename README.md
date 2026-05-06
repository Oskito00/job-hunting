# Job Hunting CV Agent

CLI tool for importing a CV into a local evidence bank, generating job-tailored CV content, rendering it through a reusable HTML template, and exporting a clickable-link PDF.

## Usage

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Add your OpenAI API key to `.env`:

```bash
OPENAI_API_KEY=...
```

Run the guided flow:

```bash
cv-agent wizard
```

Or use the commands directly.

Create a local workspace from an existing CV:

```bash
cv-agent setup --cv path/to/current-cv.pdf
```

`init` is also supported as an alias for `setup`. For PDFs, the CLI stores the source CV, renders the CV pages to local images, and uses those images to create the reusable HTML template. Extracted text is still used for the profile and experience bank.

Add rough experience notes:

```bash
cv-agent add-experience --text "Built an internal dashboard with FastAPI and React..."
```

You do not need to write YAML by hand. The experience writer agent classifies rough notes into local Markdown evidence files under `.cv-agent/experience-bank/` and adds frontmatter automatically. Manual Markdown editing is still possible for power users.

Create a tailored CV from a job URL:

```bash
cv-agent create --url "<job-url>" --company "<company>" --role "<role>"
```

`create` fetches and extracts the job description from the URL. If extraction is not confident, it asks you to paste the job description. It writes `cv-content.json`, `cv.html`, `cv.pdf`, and reports to an application folder.

Use a saved job description file instead of a URL:

```bash
cv-agent create --jd-file job.md --company "<company>" --role "<role>"
```

Skip PDF export while debugging:

```bash
cv-agent create --jd-file job.md --company "<company>" --role "<role>" --no-pdf
```

Rerender HTML:

```bash
cv-agent render applications/<application-folder>
```

Rerender PDF:

```bash
cv-agent pdf applications/<application-folder>
```

Use `--one-page` with `create` or `render` to request strict one-page output. Without it, the agent preserves work history by default and the renderer allows a flowing multi-page CV.

Generated application outputs are ignored by git. The local `.env` file is also ignored and should contain `OPENAI_API_KEY`.

The `.cv-agent/`, `experience-bank/`, and `experience-transcripts/` directories are local-only inputs and are ignored by git.
