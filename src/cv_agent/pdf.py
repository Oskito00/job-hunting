from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


DEFAULT_CHROME_PATHS = (
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
)
RENDER_REPORT_FILENAME = "render-report.md"


class PdfRenderError(RuntimeError):
    pass


@dataclass(frozen=True)
class PdfRenderRequest:
    html_path: Path
    pdf_path: Path
    chrome_path: Path | None = None


def render_pdf(request: PdfRenderRequest) -> Path:
    html_path = resolve_existing_html(request.html_path)
    pdf_path = resolve_pdf_path(request.pdf_path)
    chrome_path = request.chrome_path or find_chrome_executable()
    command = build_chrome_pdf_command(chrome_path, html_path, pdf_path)
    run_pdf_command(command)
    assert_pdf_written(pdf_path)
    append_pdf_render_report(html_path, pdf_path)
    return pdf_path


def resolve_existing_html(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise PdfRenderError(f"HTML file does not exist: {path}")
    if resolved.suffix.lower() not in {".html", ".htm"}:
        raise PdfRenderError(f"Expected an HTML file, got: {path}")
    return resolved


def resolve_pdf_path(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.suffix.lower() != ".pdf":
        raise PdfRenderError(f"Expected output path to end in .pdf, got: {path}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def find_chrome_executable() -> Path:
    for path in DEFAULT_CHROME_PATHS:
        if path.exists():
            return path
    raise PdfRenderError("Could not find Chrome, Chromium, or Microsoft Edge in /Applications.")


def build_chrome_pdf_command(chrome_path: Path, html_path: Path, pdf_path: Path) -> list[str]:
    return [
        str(chrome_path),
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        f"--print-to-pdf={pdf_path}",
        "--print-to-pdf-no-header",
        html_path.as_uri(),
    ]


def run_pdf_command(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise PdfRenderError(format_pdf_command_error(result))


def format_pdf_command_error(result: subprocess.CompletedProcess[str]) -> str:
    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    detail = stderr or stdout or "No output from Chrome."
    return f"Chrome PDF render failed with exit code {result.returncode}: {detail}"


def assert_pdf_written(pdf_path: Path) -> None:
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise PdfRenderError(f"Chrome did not write a PDF at {pdf_path}")


def count_pdf_pages(pdf_path: Path) -> int:
    data = pdf_path.read_bytes()
    return data.count(b"/Type /Page") - data.count(b"/Type /Pages")


def append_pdf_render_report(html_path: Path, pdf_path: Path) -> None:
    report_path = html_path.parent / RENDER_REPORT_FILENAME
    page_count = count_pdf_pages(pdf_path)
    lines = [
        "",
        "## PDF Render",
        "",
        f"PDF: {pdf_path}",
        f"Page count: {page_count}",
    ]
    existing = report_path.read_text(encoding="utf-8") if report_path.exists() else "# Render Report\n"
    report_path.write_text(existing.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
