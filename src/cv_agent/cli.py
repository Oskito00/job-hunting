from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cv_agent.env import load_dotenv
from cv_agent.html_render import render_cv_html_file
from cv_agent.job_extract import JobExtractionError
from cv_agent.job_fetch import JobFetchError
from cv_agent.logging import CliLogger
from cv_agent.pdf import PdfRenderRequest, render_pdf
from cv_agent.run import ApplicationRequest, create_application_pack, extract_job_description_from_url


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    args = parse_args(argv)
    if args.command == "create":
        run_create(args)
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
    add_create_parser(subparsers)
    add_render_parser(subparsers)
    add_pdf_parser(subparsers)
    return parser.parse_args(argv)


def add_create_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("create", help="Create tailored CV JSON from a job URL.")
    parser.add_argument("--url", required=True, help="Job role URL.")
    parser.add_argument("--company", required=True, help="Company name for the application folder.")
    parser.add_argument("--role", required=True, help="Role title for the application folder.")
    parser.add_argument("--model", default=None, help="OpenAI model override.")
    parser.add_argument("--root", default=None, help="Project root override.")
    parser.add_argument("--jd-file", default=None, help="Use this job description file instead of fetching the URL.")
    parser.add_argument("--quiet", action="store_true", help="Only print final output paths.")


def add_render_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("render", help="Render CV content JSON to HTML.")
    parser.add_argument("cv_json", help="Path to cv-content.json.")
    parser.add_argument("--output-dir", default=None, help="Directory for cv.html and render-report.md.")
    parser.add_argument("--quiet", action="store_true", help="Only print final output path.")


def add_pdf_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("pdf", help="Render an HTML CV to a clickable-link PDF.")
    parser.add_argument("html", help="Path to cv.html.")
    parser.add_argument("--output", default=None, help="PDF output path. Defaults to cv.pdf next to the HTML file.")
    parser.add_argument("--chrome", default=None, help="Optional Chrome/Chromium executable path.")
    parser.add_argument("--quiet", action="store_true", help="Only print final output path.")


def run_create(args: argparse.Namespace) -> None:
    logger = CliLogger(quiet=args.quiet)
    logger.step("Starting CV generation")
    job_text = load_job_text(args, logger)
    logger.success(f"Loaded job description ({len(job_text)} characters)")
    request = ApplicationRequest(
        company=args.company,
        role=args.role,
        url=args.url,
        job_text=job_text,
        model=args.model,
        root=Path(args.root) if args.root else None,
        logger=logger,
    )
    result = create_application_pack(request)
    print(f"Wrote CV JSON: {result.cv_json_path}")
    print(f"Wrote coverage report: {result.coverage_report_path}")


def run_render(args: argparse.Namespace) -> None:
    logger = CliLogger(quiet=args.quiet)
    cv_json_path = Path(args.cv_json)
    output_dir = Path(args.output_dir) if args.output_dir else cv_json_path.parent
    logger.step(f"Reading CV content JSON from {cv_json_path}")
    cv_content = read_json(cv_json_path)
    logger.step("Rendering HTML CV")
    html_path = render_cv_html_file(cv_content, output_dir)
    logger.success(f"Rendered HTML to {html_path}")
    print(f"Wrote HTML CV: {html_path}")


def run_pdf(args: argparse.Namespace) -> None:
    logger = CliLogger(quiet=args.quiet)
    html_path = Path(args.html)
    pdf_path = Path(args.output) if args.output else html_path.with_suffix(".pdf")
    chrome_path = Path(args.chrome) if args.chrome else None
    logger.step(f"Rendering PDF from {html_path}")
    rendered_path = render_pdf(PdfRenderRequest(html_path=html_path, pdf_path=pdf_path, chrome_path=chrome_path))
    logger.success(f"Rendered PDF to {rendered_path}")
    print(f"Wrote PDF CV: {rendered_path}")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_job_text(args: argparse.Namespace, logger: CliLogger) -> str:
    if args.jd_file:
        logger.step(f"Reading job description from {args.jd_file}")
        return Path(args.jd_file).read_text(encoding="utf-8")
    try:
        logger.step(f"Fetching job page: {args.url}")
        return extract_job_description_from_url(args.url)
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
