from pathlib import Path
import tempfile
import unittest

from cv_agent.cli import parse_args, requested_page_mode, resolve_cv_json_path, resolve_html_path
from cv_agent.html_render import ONE_PAGE_MODE


class CliTest(unittest.TestCase):
    def test_parse_create_accepts_jd_file_without_url(self) -> None:
        args = parse_args(["create", "--jd-file", "job.md", "--company", "Acme", "--role", "Engineer"])
        self.assertEqual(args.jd_file, "job.md")
        self.assertIsNone(args.url)
        self.assertFalse(args.no_pdf)

    def test_parse_create_accepts_no_pdf_escape_hatch(self) -> None:
        args = parse_args(["create", "--jd-file", "job.md", "--company", "Acme", "--role", "Engineer", "--no-pdf"])
        self.assertTrue(args.no_pdf)

    def test_parse_setup_alias_maps_to_init_command(self) -> None:
        args = parse_args(["setup", "--cv", "cv.pdf"])
        self.assertEqual(args.command, "setup")
        self.assertEqual(args.cv, "cv.pdf")

    def test_parse_wizard_accepts_root(self) -> None:
        args = parse_args(["wizard", "--root", "/tmp/project"])
        self.assertEqual(args.command, "wizard")
        self.assertEqual(args.root, "/tmp/project")

    def test_requested_page_mode_reads_one_page_flag(self) -> None:
        args = parse_args(["render", "applications/acme", "--one-page"])
        self.assertEqual(requested_page_mode(args), ONE_PAGE_MODE)

    def test_resolve_application_folder_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp)
            self.assertEqual(resolve_cv_json_path(app), app / "cv-content.json")
            self.assertEqual(resolve_html_path(app), app / "cv.html")


if __name__ == "__main__":
    unittest.main()
