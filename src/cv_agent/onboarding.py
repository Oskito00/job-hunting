from __future__ import annotations

import base64
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cv_agent.agent import DEFAULT_MODEL, run_agent_sync
from cv_agent.html_render import default_template_html, validate_template_html
from cv_agent.logging import CliLogger, null_logger
from cv_agent.paths import slugify
from cv_agent.pdf_images import render_pdf_pages_to_images
from cv_agent.workspace import CvWorkspace, ensure_workspace, resolve_workspace


SUPPORTED_TEXT_EXTENSIONS = {".md", ".markdown", ".txt"}
SUPPORTED_CV_EXTENSIONS = {*SUPPORTED_TEXT_EXTENSIONS, ".pdf"}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImportedRole(StrictModel):
    company: str = ""
    title: str = ""
    dates: str = ""
    bullets: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    needs_review: bool = False


class ImportedProject(StrictModel):
    name: str = ""
    bullets: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    needs_review: bool = False


class ImportedEducation(StrictModel):
    institution: str = ""
    degree: str = ""
    classification: str = ""
    dates: str = ""
    needs_review: bool = False


class ImportedContact(StrictModel):
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    website: str = ""
    github: str = ""
    location: str = ""


class ImportedCV(StrictModel):
    name: str = ""
    contact: ImportedContact = Field(default_factory=ImportedContact)
    education: list[ImportedEducation] = Field(default_factory=list)
    work_experience: list[ImportedRole] = Field(default_factory=list)
    projects: list[ImportedProject] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)


class TemplateOutput(StrictModel):
    html: str
    notes: list[str] = Field(default_factory=list)


class EvidenceFileDraft(StrictModel):
    relative_path: str
    content: str


class ExperienceDraft(StrictModel):
    files: list[EvidenceFileDraft] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class InitResult:
    workspace: CvWorkspace
    source_path: Path
    profile_path: Path
    template_path: Path
    import_report_path: Path
    page_image_paths: list[Path]


@dataclass(frozen=True)
class ExperienceAddResult:
    workspace: CvWorkspace
    written_files: list[Path]
    questions: list[str]


def initialise_from_cv(cv_path: Path, root: Path | None = None, model: str | None = None, logger: CliLogger | None = None) -> InitResult:
    active_logger = logger or null_logger()
    workspace = resolve_workspace(root)
    ensure_workspace(workspace)
    active_logger.step(f"Reading source CV from {cv_path}")
    cv_text = extract_cv_text(cv_path)
    source_path = copy_source_cv(cv_path, workspace)
    active_logger.step("Rendering visual CV pages when available")
    page_image_paths = render_source_page_images(source_path, workspace)
    active_logger.step("Running CV import agent")
    imported = run_cv_import_agent(cv_text=cv_text, source_name=cv_path.name, model=model)
    active_logger.step("Writing profile and experience evidence")
    write_imported_profile(workspace, imported)
    write_imported_evidence(workspace, imported)
    active_logger.step("Running template agent")
    template = run_template_agent(cv_text=cv_text, imported=imported, page_image_paths=page_image_paths, model=model)
    write_template(workspace, template)
    write_import_report(workspace, imported, template, page_image_paths)
    return InitResult(
        workspace=workspace,
        source_path=source_path,
        profile_path=workspace.profile_json,
        template_path=workspace.template,
        import_report_path=workspace.import_report,
        page_image_paths=page_image_paths,
    )


def add_experience_from_text(text: str, root: Path | None = None, kind: str | None = None, model: str | None = None, logger: CliLogger | None = None) -> ExperienceAddResult:
    active_logger = logger or null_logger()
    workspace = resolve_workspace(root)
    ensure_workspace(workspace)
    active_logger.step("Running experience writer agent")
    draft = run_experience_writer_agent(text=text, kind=kind, model=model)
    written = write_experience_draft(workspace, draft)
    return ExperienceAddResult(workspace=workspace, written_files=written, questions=draft.questions)


def add_experience_from_file(path: Path, root: Path | None = None, kind: str | None = None, model: str | None = None, logger: CliLogger | None = None) -> ExperienceAddResult:
    text = path.read_text(encoding="utf-8")
    return add_experience_from_text(text=text, root=root, kind=kind, model=model, logger=logger)


def extract_cv_text(path: Path) -> str:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"CV file does not exist: {path}")
    suffix = resolved.suffix.lower()
    if suffix in SUPPORTED_TEXT_EXTENSIONS:
        return resolved.read_text(encoding="utf-8")
    if suffix == ".pdf":
        return extract_pdf_text(resolved)
    raise ValueError(f"Unsupported CV file type: {path.suffix}. Supported: PDF, Markdown, text.")


def extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF import requires the pypdf package. Install project dependencies and retry.") from exc
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(page.strip() for page in pages if page.strip()).strip()
    if not text:
        raise ValueError(f"No selectable text could be extracted from PDF: {path}")
    return text


def copy_source_cv(path: Path, workspace: CvWorkspace) -> Path:
    destination = unique_path(workspace.source / path.name)
    shutil.copy2(path.expanduser().resolve(), destination)
    return destination


def render_source_page_images(source_path: Path, workspace: CvWorkspace) -> list[Path]:
    if source_path.suffix.lower() != ".pdf":
        return []
    return render_pdf_pages_to_images(source_path, workspace.source / "pages")


def run_cv_import_agent(cv_text: str, source_name: str, model: str | None = None) -> ImportedCV:
    from agents import Agent

    agent = Agent(
        name="CV Import Agent",
        instructions=cv_import_instructions(),
        model=model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        output_type=ImportedCV,
    )
    result = run_agent_sync(agent, f"Source CV filename: {source_name}\n\nCV text:\n{cv_text}")
    return normalise_agent_output(result.final_output, ImportedCV)


def run_template_agent(cv_text: str, imported: ImportedCV, page_image_paths: list[Path] | None = None, model: str | None = None) -> TemplateOutput:
    from agents import Agent

    agent = Agent(
        name="CV Template Agent",
        instructions=template_agent_instructions(),
        model=model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        output_type=TemplateOutput,
    )
    result = run_agent_sync(agent, build_template_agent_input(cv_text, imported, page_image_paths or []))
    output = normalise_agent_output(result.final_output, TemplateOutput)
    errors = validate_template_html(output.html)
    if errors:
        fallback = default_template_html()
        return TemplateOutput(html=fallback, notes=[*output.notes, "Generated template failed validation; default template was used.", *errors])
    return output


def build_template_agent_input(cv_text: str, imported: ImportedCV, page_image_paths: list[Path]) -> str | list[dict[str, object]]:
    prompt = build_template_agent_prompt(cv_text, imported, bool(page_image_paths))
    if not page_image_paths:
        return prompt
    content: list[dict[str, object]] = [{"type": "input_text", "text": prompt}]
    content.extend(build_image_content(path) for path in page_image_paths)
    return [{"role": "user", "content": content}]


def build_template_agent_prompt(cv_text: str, imported: ImportedCV, has_images: bool) -> str:
    visual_guidance = "Use the page images as the primary source for visual layout, spacing, typography, section placement, and page structure." if has_images else "No page images are available; infer a conservative template from the extracted text."
    return f"""Create a reusable template.html from this CV.

{visual_guidance}

Imported profile JSON:
{json.dumps(imported.model_dump(), indent=2, ensure_ascii=False)}

Source CV text:
{cv_text}
"""


def build_image_content(image_path: Path) -> dict[str, object]:
    return {
        "type": "input_image",
        "image_url": image_data_url(image_path),
        "detail": "high",
    }


def image_data_url(image_path: Path) -> str:
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def run_experience_writer_agent(text: str, kind: str | None = None, model: str | None = None) -> ExperienceDraft:
    from agents import Agent

    agent = Agent(
        name="Experience Writer Agent",
        instructions=experience_writer_instructions(),
        model=model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        output_type=ExperienceDraft,
    )
    prompt = f"Kind hint: {kind or 'unspecified'}\n\nExperience notes:\n{text}"
    result = run_agent_sync(agent, prompt)
    return normalise_agent_output(result.final_output, ExperienceDraft)


def normalise_agent_output(value: Any, output_type: type[StrictModel]) -> Any:
    if isinstance(value, output_type):
        return value
    if isinstance(value, dict):
        return output_type.model_validate(value)
    if isinstance(value, BaseModel):
        return output_type.model_validate(value.model_dump())
    raise TypeError(f"Unsupported agent output type: {type(value).__name__}")


def write_imported_profile(workspace: CvWorkspace, imported: ImportedCV) -> None:
    payload = imported.model_dump()
    workspace.profile_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    contact = imported.contact.model_dump()
    contact_lines = [f"- Name: {imported.name}", *[f"- {key.title()}: {value}" for key, value in contact.items() if value]]
    (workspace.experience_bank / "contact.md").write_text("---\ntype: contact\n---\n# Contact\n" + "\n".join(contact_lines) + "\n", encoding="utf-8")
    education_body = "\n".join(format_education_entry(entry) for entry in imported.education)
    if education_body:
        (workspace.experience_bank / "education.md").write_text("---\ntype: education\n---\n# Education\n" + education_body + "\n", encoding="utf-8")


def write_imported_evidence(workspace: CvWorkspace, imported: ImportedCV) -> list[Path]:
    written: list[Path] = []
    roles_dir = workspace.experience_bank / "roles"
    projects_dir = workspace.experience_bank / "projects"
    roles_dir.mkdir(parents=True, exist_ok=True)
    projects_dir.mkdir(parents=True, exist_ok=True)
    for role in imported.work_experience:
        path = unique_path(roles_dir / f"{slugify(role.company or role.title)}.md")
        path.write_text(format_role_markdown(role), encoding="utf-8")
        written.append(path)
    for project in imported.projects:
        path = unique_path(projects_dir / f"{slugify(project.name)}.md")
        path.write_text(format_project_markdown(project), encoding="utf-8")
        written.append(path)
    if imported.skills:
        skills_path = workspace.experience_bank / "skills.md"
        skills_path.write_text(format_skills_markdown(imported.skills), encoding="utf-8")
        written.append(skills_path)
    return written


def write_template(workspace: CvWorkspace, template: TemplateOutput) -> None:
    workspace.template.write_text(template.html, encoding="utf-8")


def write_import_report(workspace: CvWorkspace, imported: ImportedCV, template: TemplateOutput, page_image_paths: list[Path]) -> None:
    lines = [
        "# Import Report",
        "",
        f"Imported name: {imported.name or 'Unknown'}",
        f"Work roles: {len(imported.work_experience)}",
        f"Projects: {len(imported.projects)}",
        f"Skills: {len(imported.skills)}",
        f"Visual pages: {len(page_image_paths)}",
        "",
        "## Visual Page Images",
        *format_page_image_lines(page_image_paths),
        "",
        "## Template Notes",
        *[f"- {note}" for note in template.notes],
        "",
        "## Unresolved Questions",
    ]
    lines.extend(f"- {question}" for question in imported.unresolved_questions)
    if not imported.unresolved_questions:
        lines.append("No unresolved questions.")
    workspace.import_report.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def format_page_image_lines(page_image_paths: list[Path]) -> list[str]:
    if not page_image_paths:
        return ["No visual page images were generated."]
    return [f"- {path}" for path in page_image_paths]


def write_experience_draft(workspace: CvWorkspace, draft: ExperienceDraft) -> list[Path]:
    written: list[Path] = []
    for file in draft.files:
        relative = safe_experience_relative_path(file.relative_path)
        path = unique_path(workspace.experience_bank / relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(normalise_evidence_markdown(relative, file.content), encoding="utf-8")
        written.append(path)
    return written


def safe_experience_relative_path(relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"Unsafe experience file path: {relative_path}")
    if candidate.suffix.lower() != ".md":
        candidate = candidate.with_suffix(".md")
    return candidate


def normalise_evidence_markdown(relative_path: Path, content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("---\n"):
        return cleaned + "\n"
    evidence_type = evidence_type_from_path(relative_path)
    return f"---\ntype: {evidence_type}\nneeds_review: true\n---\n{cleaned}\n"


def evidence_type_from_path(relative_path: Path) -> str:
    first_part = relative_path.parts[0] if relative_path.parts else relative_path.name
    if first_part == "roles":
        return "role"
    if first_part == "projects":
        return "project"
    if relative_path.name == "skills.md":
        return "skills"
    if relative_path.name == "education.md":
        return "education"
    if relative_path.name == "contact.md":
        return "contact"
    return "experience"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(2, 1000):
        candidate = path.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not find available filename for {path}")


def format_education_entry(entry: ImportedEducation) -> str:
    lines = [f"## {entry.institution}"]
    if entry.degree:
        lines.append(f"- Degree: {entry.degree}")
    if entry.classification:
        lines.append(f"- Classification: {entry.classification}")
    if entry.dates:
        lines.append(f"- Dates: {entry.dates}")
    if entry.needs_review:
        lines.append("- Needs Review: true")
    return "\n".join(lines)


def format_role_markdown(role: ImportedRole) -> str:
    metadata = [
        "---",
        "type: role",
        f"company: {role.company}",
        f"title: {role.title}",
        f"dates: {role.dates}",
        f"skills: [{', '.join(role.skills)}]",
        f"needs_review: {str(role.needs_review).lower()}",
        "---",
        f"# {role.company or role.title}",
        "",
    ]
    metadata.extend(f"- {bullet}" for bullet in role.bullets)
    return "\n".join(metadata).strip() + "\n"


def format_project_markdown(project: ImportedProject) -> str:
    metadata = [
        "---",
        "type: project",
        f"title: {project.name}",
        f"skills: [{', '.join(project.skills)}]",
        f"needs_review: {str(project.needs_review).lower()}",
        "---",
        f"# {project.name}",
        "",
    ]
    metadata.extend(f"- {bullet}" for bullet in project.bullets)
    return "\n".join(metadata).strip() + "\n"


def format_skills_markdown(skills: list[str]) -> str:
    return "---\ntype: skills\n---\n# Skills\n" + "\n".join(f"- {skill}" for skill in skills) + "\n"


def cv_import_instructions() -> str:
    return """Extract a factual, structured profile from the user's existing CV.

Rules:
- Only use information present in the CV text.
- Do not infer missing dates, employers, job titles, metrics, or technologies.
- Put uncertain or incomplete details in unresolved_questions and mark the affected item needs_review=true.
- Keep bullets concise and factual; these become evidence files for future tailored CVs.
- Put contact details into the fixed contact fields when present.
"""


def template_agent_instructions() -> str:
    return f"""Create a complete standalone HTML CV template that resembles the source CV's structure and visual style.

Rules:
- Return valid HTML only in the html field.
- Include these placeholders exactly once or more: {', '.join(sorted(REQUIRED_TEMPLATE_PLACEHOLDERS_FOR_PROMPT))}.
- Use {{{{page_class}}}} on the main page/container element so one-page and multi-page modes can be styled.
- Use CSS that is print-friendly and does not depend on external assets.
- When page images are provided, use them as the primary source for layout, section positioning, font scale, whitespace, borders, columns, and visual hierarchy.
- Use extracted text and imported profile JSON only to understand which visual regions correspond to which placeholders.
- Do not include real CV content except through placeholders.
"""


REQUIRED_TEMPLATE_PLACEHOLDERS_FOR_PROMPT = {
    "{{name}}",
    "{{contact}}",
    "{{profile}}",
    "{{work_experience}}",
    "{{projects}}",
    "{{skills}}",
    "{{education}}",
}


def experience_writer_instructions() -> str:
    return """Turn rough experience notes into Markdown evidence files for a CV tailoring agent.

Rules:
- Create one or more Markdown files under roles/, projects/, skills.md, education.md, or contact.md.
- Choose the file location by evidence type: jobs and internships under roles/, side projects under projects/, skill lists in skills.md, education in education.md, contact details in contact.md.
- Use YAML frontmatter on every file with type and needs_review.
- For roles include company, title, dates, skills, and needs_review when known.
- For projects include title, skills, and needs_review when known.
- Do not invent employers, dates, metrics, technologies, clients, or outcomes.
- If a detail is ambiguous, preserve it cautiously and add questions.
- relative_path must be a safe relative Markdown path.
"""
