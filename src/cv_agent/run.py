from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cv_agent.agent import run_cv_agent
from cv_agent.job_extract import extract_job_text
from cv_agent.job_fetch import fetch_html
from cv_agent.logging import CliLogger, null_logger
from cv_agent.output import write_application_files
from cv_agent.paths import ProjectPaths, create_application_dir, resolve_project_paths


@dataclass(frozen=True)
class ApplicationRequest:
    company: str
    role: str
    url: str
    job_text: str
    model: str | None = None
    root: Path | None = None
    logger: CliLogger | None = None


@dataclass(frozen=True)
class ApplicationResult:
    output_dir: Path
    cv_json_path: Path
    coverage_report_path: Path


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
    logger.step("Writing application files")
    write_application_files(output_dir, request.job_text, cv_content, request.url)
    logger.success(f"Application pack written to {output_dir}")
    return build_application_result(output_dir)


def generate_cv_content(request: ApplicationRequest, paths: ProjectPaths) -> dict[str, object]:
    return run_cv_agent(
        job_text=request.job_text,
        company=request.company,
        role=request.role,
        bank_dir=paths.experience_bank,
        model=request.model,
    )


def build_application_result(output_dir: Path) -> ApplicationResult:
    return ApplicationResult(
        output_dir=output_dir,
        cv_json_path=output_dir / "cv-content.json",
        coverage_report_path=output_dir / "coverage-report.md",
    )
