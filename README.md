# Job Hunting CV Agent

CLI tool for generating evidence-backed CV content from a job description, rendering it to a one-page HTML CV, and exporting a clickable-link PDF.

## Usage

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Create tailored CV content from a job URL:

```bash
cv-agent create --url "<job-url>" --company "<company>" --role "<role>"
```

Render HTML:

```bash
cv-agent render applications/<application-folder>/cv-content.json
```

Render PDF:

```bash
cv-agent pdf applications/<application-folder>/cv.html
```

Generated application outputs are ignored by git. The local `.env` file is also ignored and should contain `OPENAI_API_KEY`.
