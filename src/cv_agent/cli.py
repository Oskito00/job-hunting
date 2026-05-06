from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from cv_agent.env import load_dotenv
from cv_agent.html_render import FLOW_PAGE_MODE, ONE_PAGE_MODE, RenderOptions, render_cv_html_file
from cv_agent.job_extract import JobExtractionError
from cv_agent.job_fetch import JobFetchError
from cv_agent.logging import CliLogger
from cv_agent.onboarding import add_experience_from_file, add_experience_from_text, initialise_from_cv
from cv_agent.pdf import PdfRenderRequest, render_pdf
from cv_agent.run import ApplicationRequest, create_application_pack, extract_job_description_from_url
from cv_agent.workspace import resolve_workspace


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    args = parse_args(argv)
    if args.command in {"init", "setup"}:
        run_init(args)
        return
    if args.command == "add-experience":
        run_add_experience(args)
        return
    if args.command == "create":
        run_create(args)
        return
    if args.command == "wizard":
        run_wizard(args)
        return
    if args.command == "render":
        run_render(args)
        return
    if args.command == "pdf":
        run_pdf(args)
        return
    raise SystemExit("Unknown command")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="cv-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_init_parser(subparsers)
    add_add_experience_parser(subparsers)
    add_create_parser(subparsers)
    add_wizard_parser(subparsers)
    add_render_parser(subparsers)
    add_pdf_parser(subparsers)
    return parser.parse_args(argv)


def add_init_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("init", aliases=["setup"], help="Create a local CV workspace from an existing CV.")
    parser.add_argument("--cv", required=True, help="Path to the user's current CV as PDF, Markdown, or text.")
    parser.add_argument("--model", default=None, help="OpenAI model override.")
    parser.add_argument("--root", default=None, help="Project root override.")
    parser.add_argument("--quiet", action="store_true", help="Only print final output paths.")


def add_add_experience_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("add-experience", help="Turn rough notes into experience-bank Markdown files.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", default=None, help="Experience notes to convert.")
    source.add_argument("--file", default=None, help="Markdown/text file containing experience notes.")
    parser.add_argument("--kind", choices=["role", "project", "skill", "education"], default=None, help="Optional hint for the notes.")
    parser.add_argument("--model", default=None, help="OpenAI model override.")
    parser.add_argument("--root", default=None, help="Project root override.")
    parser.add_argument("--quiet", action="store_true", help="Only print final output paths.")


def add_create_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("create", help="Create a tailored CV pack from a job URL or job description file.")
    parser.add_argument("--url", default=None, help="Job role URL.")
    parser.add_argument("--company", required=True, help="Company name for the application folder.")
    parser.add_argument("--role", required=True, help="Role title for the application folder.")
    parser.add_argument("--model", default=None, help="OpenAI model override.")
    parser.add_argument("--root", default=None, help="Project root override.")
    parser.add_argument("--jd-file", default=None, help="Use this job description file instead of fetching the URL.")
    parser.add_argument("--chrome", default=None, help="Optional Chrome/Chromium executable path for PDF export.")
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF export and only write JSON/HTML/report files.")
    add_page_mode_flags(parser)
    parser.add_argument("--quiet", action="store_true", help="Only print final output paths.")


def add_wizard_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("wizard", help="Guided setup, experience capture, and CV generation flow.")
    parser.add_argument("--model", default=None, help="OpenAI model override.")
    parser.add_argument("--root", default=None, help="Project root override.")
    parser.add_argument("--chrome", default=None, help="Optional Chrome/Chromium executable path for PDF export.")
    parser.add_argument("--quiet", action="store_true", help="Only print final output paths.")


def add_render_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("render", help="Render CV content JSON or an application folder to HTML.")
    parser.add_argument("target", help="Path to cv-content.json or an application folder.")
    parser.add_argument("--output-dir", default=None, help="Directory for cv.html and render-report.md.")
    parser.add_argument("--root", default=None, help="Project root override.")
    add_page_mode_flags(parser)
    parser.add_argument("--quiet", action="store_true", help="Only print final output path.")


def add_pdf_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("pdf", help="Render an HTML CV or application folder to a clickable-link PDF.")
    parser.add_argument("target", help="Path to cv.html or an application folder containing cv.html.")
    parser.add_argument("--output", default=None, help="PDF output path. Defaults to cv.pdf next to the HTML file.")
    parser.add_argument("--chrome", default=None, help="Optional Chrome/Chromium executable path.")
    parser.add_argument("--quiet", action="store_true", help="Only print final output path.")


def add_page_mode_flags(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--one-page", action="store_true", help="Target a strict one-page CV.")
    group.add_argument("--multi-page", action="store_true", help="Allow a flowing multi-page CV.")


def run_init(args: argparse.Namespace) -> None:
    require_openai_api_key()
    logger = CliLogger(quiet=args.quiet)
    result = initialise_from_cv(cv_path=Path(args.cv), root=Path(args.root) if args.root else None, model=args.model, logger=logger)
    print(f"Wrote profile: {result.profile_path}")
    print(f"Wrote template: {result.template_path}")
    print(f"Wrote import report: {result.import_report_path}")


def run_add_experience(args: argparse.Namespace) -> None:
    require_openai_api_key()
    logger = CliLogger(quiet=args.quiet)
    root = Path(args.root) if args.root else None
    if args.file:
        result = add_experience_from_file(Path(args.file), root=root, kind=args.kind, model=args.model, logger=logger)
    else:
        result = add_experience_from_text(args.text, root=root, kind=args.kind, model=args.model, logger=logger)
    for path in result.written_files:
        print(f"Wrote experience file: {path}")
    print_questions(result.questions)


def run_create(args: argparse.Namespace) -> None:
    require_openai_api_key()
    logger = CliLogger(quiet=args.quiet)
    logger.step("Starting CV generation")
    job_text = load_job_text(args, logger)
    logger.success(f"Loaded job description ({len(job_text)} characters)")
    request = ApplicationRequest(
        company=args.company,
        role=args.role,
        url=args.url or str(Path(args.jd_file).resolve()),
        job_text=job_text,
        model=args.model,
        root=Path(args.root) if args.root else None,
        page_mode=requested_page_mode(args),
        include_pdf=not args.no_pdf,
        chrome_path=Path(args.chrome) if args.chrome else None,
        logger=logger,
    )
    result = create_application_pack(request)
    print(f"Wrote CV JSON: {result.cv_json_path}")
    print(f"Wrote HTML CV: {result.html_path}")
    if result.pdf_path:
        print(f"Wrote PDF CV: {result.pdf_path}")
    print(f"Wrote coverage report: {result.coverage_report_path}")


def run_wizard(args: argparse.Namespace) -> None:
    require_openai_api_key()
    logger = CliLogger(quiet=args.quiet)
    root = Path(args.root) if args.root else None
    workspace = resolve_workspace(root)
    if not workspace.template.exists():
        cv_path = prompt_required_path("Path to your current CV")
        initialise_from_cv(cv_path=cv_path, root=root, model=args.model, logger=logger)
    if prompt_yes_no("Add new experience notes now?", default=False):
        notes = prompt_multiline("Paste experience notes. Finish with a single '.' on its own line.")
        if notes:
            result = add_experience_from_text(notes, root=root, model=args.model, logger=logger)
            for path in result.written_files:
                print(f"Wrote experience file: {path}")
            print_questions(result.questions)
    company = prompt_required_text("Company")
    role = prompt_required_text("Role")
    url = prompt_optional_text("Job URL")
    jd_file = None
    if not url:
        jd_file = prompt_optional_text("Job description file")
    job_text = load_job_text_from_values(url=url, jd_file=jd_file, logger=logger)
    source = url or (str(Path(jd_file).resolve()) if jd_file else "pasted-job-description")
    request = ApplicationRequest(
        company=company,
        role=role,
        url=source,
        job_text=job_text,
        model=args.model,
        root=root,
        include_pdf=True,
        chrome_path=Path(args.chrome) if args.chrome else None,
        logger=logger,
    )
    result = create_application_pack(request)
    print(f"Wrote CV JSON: {result.cv_json_path}")
    print(f"Wrote HTML CV: {result.html_path}")
    if result.pdf_path:
        print(f"Wrote PDF CV: {result.pdf_path}")
    print(f"Wrote coverage report: {result.coverage_report_path}")


def run_render(args: argparse.Namespace) -> None:
    logger = CliLogger(quiet=args.quiet)
    target = Path(args.target)
    cv_json_path = resolve_cv_json_path(target)
    output_dir = Path(args.output_dir) if args.output_dir else cv_json_path.parent
    workspace = resolve_workspace(Path(args.root) if args.root else None)
    template_path = workspace.template if workspace.template.exists() else None
    logger.step(f"Reading CV content JSON from {cv_json_path}")
    cv_content = read_json(cv_json_path)
    logger.step("Rendering HTML CV")
    html_path = render_cv_html_file(cv_content, output_dir, options=RenderOptions(page_mode=requested_page_mode(args) or str(cv_content.get("page_mode", "") or FLOW_PAGE_MODE), template_path=template_path))
    logger.success(f"Rendered HTML to {html_path}")
    print(f"Wrote HTML CV: {html_path}")


def run_pdf(args: argparse.Namespace) -> None:
    logger = CliLogger(quiet=args.quiet)
    html_path = resolve_html_path(Path(args.target))
    pdf_path = Path(args.output) if args.output else html_path.with_suffix(".pdf")
    chrome_path = Path(args.chrome) if args.chrome else None
    logger.step(f"Rendering PDF from {html_path}")
    rendered_path = render_pdf(PdfRenderRequest(html_path=html_path, pdf_path=pdf_path, chrome_path=chrome_path))
    logger.success(f"Rendered PDF to {rendered_path}")
    print(f"Wrote PDF CV: {rendered_path}")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_cv_json_path(target: Path) -> Path:
    return target / "cv-content.json" if target.is_dir() else target


def resolve_html_path(target: Path) -> Path:
    return target / "cv.html" if target.is_dir() else target


def requested_page_mode(args: argparse.Namespace) -> str | None:
    if getattr(args, "one_page", False):
        return ONE_PAGE_MODE
    if getattr(args, "multi_page", False):
        return "multi_page"
    return None


def load_job_text(args: argparse.Namespace, logger: CliLogger) -> str:
    return load_job_text_from_values(url=args.url, jd_file=args.jd_file, logger=logger)


def load_job_text_from_values(url: str | None, jd_file: str | None, logger: CliLogger) -> str:
    if jd_file:
        logger.step(f"Reading job description from {jd_file}")
        return Path(jd_file).read_text(encoding="utf-8")
    if not url:
        return prompt_for_job_description("No URL or job description file provided.")
    try:
        logger.step(f"Fetching job page: {url}")
        return extract_job_description_from_url(url)
    except (JobFetchError, JobExtractionError) as exc:
        logger.warn("Automatic job extraction failed; switching to paste fallback")
        return prompt_for_job_description(str(exc))


def prompt_for_job_description(reason: str) -> str:
    print(f"Could not extract the job description automatically: {reason}", file=sys.stderr)
    print("Paste the job description, then press Ctrl-D:", file=sys.stderr)
    pasted = sys.stdin.read().strip()
    if not pasted:
        raise SystemExit("No job description provided.")
    return pasted


def require_openai_api_key() -> None:
    if os.getenv("OPENAI_API_KEY", "").strip():
        return
    raise SystemExit("OPENAI_API_KEY is not set. Add it to .env or export it before running agent commands.")


def prompt_required_text(label: str) -> str:
    value = input(f"{label}: ").strip()
    if not value:
        raise SystemExit(f"{label} is required.")
    return value


def prompt_optional_text(label: str) -> str:
    return input(f"{label} (optional): ").strip()


def prompt_required_path(label: str) -> Path:
    return Path(prompt_required_text(label)).expanduser()


def prompt_yes_no(label: str, default: bool = False) -> bool:
    suffix = "Y/n" if default else "y/N"
    value = input(f"{label} [{suffix}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes"}


def prompt_multiline(label: str) -> str:
    print(label, file=sys.stderr)
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == ".":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def print_questions(questions: list[str]) -> None:
    if not questions:
        return
    print("Questions:")
    for question in questions:
        print(f"- {question}")
