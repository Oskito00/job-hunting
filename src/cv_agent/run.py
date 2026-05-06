from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cv_agent.agent import revise_cv_content_for_fit, run_cv_agent
from cv_agent.html_render import ONE_PAGE_MODE, RenderOptions, render_cv_html_file, render_validation_errors
from cv_agent.job_extract import extract_job_text
from cv_agent.job_fetch import fetch_html
from cv_agent.logging import CliLogger, null_logger
from cv_agent.output import write_application_files
from cv_agent.paths import ProjectPaths, create_application_dir, resolve_project_paths
from cv_agent.pdf import PdfRenderRequest, render_pdf
from cv_agent.workspace import resolve_workspace


@dataclass(frozen=True)
class ApplicationRequest:
    company: str
    role: str
    url: str
    job_text: str
    model: str | None = None
    root: Path | None = None
    page_mode: str | None = None
    include_pdf: bool = True
    chrome_path: Path | None = None
    logger: CliLogger | None = None


@dataclass(frozen=True)
class ApplicationResult:
    output_dir: Path
    cv_json_path: Path
    coverage_report_path: Path
    html_path: Path
    pdf_path: Path | None
    render_report_path: Path


def extract_job_description_from_url(url: str) -> str:
    result = fetch_html(url)
    return extract_job_text(result.html, result.url)


def create_application_pack(request: ApplicationRequest) -> ApplicationResult:
    logger = request.logger or null_logger()
    logger.step("Resolving project paths")
    paths = resolve_project_paths(request.root)
    logger.step(f"Creating application folder for {request.company} / {request.role}")
    output_dir = create_application_dir(paths, request.company, request.role)
    logger.step("Running OpenAI agent to generate CV content JSON")
    cv_content = generate_cv_content(request, paths)
    render_options = build_render_options(request, cv_content)
    render_errors = render_validation_errors(cv_content, render_options)
    if request.page_mode == ONE_PAGE_MODE and render_errors:
        logger.step("One-page limits failed; running one revision pass")
        cv_content = revise_cv_content_for_fit(
            cv_content=cv_content,
            render_errors=render_errors,
            job_text=request.job_text,
            company=request.company,
            role=request.role,
            bank_dir=paths.experience_bank,
            model=request.model,
        )
    logger.step("Writing application files")
    write_application_files(output_dir, request.job_text, cv_content, request.url)
    logger.step("Rendering HTML CV")
    html_path = render_cv_html_file(cv_content, output_dir, options=render_options)
    if request.include_pdf:
        logger.step("Rendering PDF CV")
        render_pdf(PdfRenderRequest(html_path=html_path, pdf_path=html_path.with_suffix(".pdf"), chrome_path=request.chrome_path))
    logger.success(f"Application pack written to {output_dir}")
    return build_application_result(output_dir)


def generate_cv_content(request: ApplicationRequest, paths: ProjectPaths) -> dict[str, object]:
    return run_cv_agent(
        job_text=request.job_text,
        company=request.company,
        role=request.role,
        bank_dir=paths.experience_bank,
        model=request.model,
        page_mode=request.page_mode,
    )


def build_render_options(request: ApplicationRequest, cv_content: dict[str, object] | None = None) -> RenderOptions:
    workspace = resolve_workspace(request.root)
    template_path = workspace.template if workspace.template.exists() else None
    content_page_mode = str((cv_content or {}).get("page_mode", "") or "")
    return RenderOptions(page_mode=request.page_mode or content_page_mode or "flow", template_path=template_path)


def build_application_result(output_dir: Path) -> ApplicationResult:
    return ApplicationResult(
        output_dir=output_dir,
        cv_json_path=output_dir / "cv-content.json",
        coverage_report_path=output_dir / "coverage-report.md",
        html_path=output_dir / "cv.html",
        pdf_path=output_dir / "cv.pdf" if (output_dir / "cv.pdf").exists() else None,
        render_report_path=output_dir / "render-report.md",
    )
