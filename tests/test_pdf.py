from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cv_agent.pdf import PdfRenderError, PdfRenderRequest, build_chrome_pdf_command, count_pdf_pages, render_pdf


class PdfTest(unittest.TestCase):
    def test_build_chrome_pdf_command_uses_file_uri(self) -> None:
        command = build_chrome_pdf_command(Path("/Chrome"), Path("/tmp/cv.html"), Path("/tmp/cv.pdf"))
        self.assertIn("--print-to-pdf=/tmp/cv.pdf", command)
        self.assertEqual(command[-1], "file:///tmp/cv.html")

    def test_render_pdf_rejects_non_html_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cv.txt"
            path.write_text("x", encoding="utf-8")
            request = PdfRenderRequest(html_path=path, pdf_path=Path(tmp) / "cv.pdf", chrome_path=Path("/Chrome"))
            with self.assertRaises(PdfRenderError):
                render_pdf(request)

    def test_render_pdf_runs_chrome_and_checks_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            html_path = Path(tmp) / "cv.html"
            pdf_path = Path(tmp) / "cv.pdf"
            html_path.write_text("<html></html>", encoding="utf-8")
            with patch("cv_agent.pdf.run_pdf_command", side_effect=lambda command: pdf_path.write_bytes(b"%PDF")):
                rendered = render_pdf(PdfRenderRequest(html_path=html_path, pdf_path=pdf_path, chrome_path=Path("/Chrome")))
            self.assertEqual(rendered, pdf_path.resolve())
            self.assertIn("Page count:", (Path(tmp) / "render-report.md").read_text(encoding="utf-8"))

    def test_count_pdf_pages_ignores_pages_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cv.pdf"
            path.write_bytes(b"/Type /Pages /Type /Page /Type /Page")
            self.assertEqual(count_pdf_pages(path), 2)


if __name__ == "__main__":
    unittest.main()
