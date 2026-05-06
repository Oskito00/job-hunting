from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cv_agent.logging import null_logger
from cv_agent.run import ApplicationRequest, create_application_pack


class RunTest(unittest.TestCase):
    def test_create_application_pack_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "experience-bank").mkdir()
            request = ApplicationRequest(
                company="Acme",
                role="AI Engineer",
                url="https://example.com/job",
                job_text="Responsibilities: build AI products.",
                root=root,
                logger=null_logger(),
            )
            with (
                patch("cv_agent.run.run_cv_agent", return_value=sample_cv_content()),
                patch("cv_agent.run.render_pdf", side_effect=lambda request: request.pdf_path.write_bytes(b"%PDF")),
            ):
                result = create_application_pack(request)
            self.assertTrue(result.cv_json_path.exists())
            self.assertTrue(result.coverage_report_path.exists())
            self.assertEqual(result.pdf_path, result.output_dir / "cv.pdf")
            self.assertTrue((result.output_dir / "jd.md").exists())

    def test_create_application_pack_can_skip_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "experience-bank").mkdir()
            request = ApplicationRequest(
                company="Acme",
                role="AI Engineer",
                url="https://example.com/job",
                job_text="Responsibilities: build AI products.",
                root=root,
                include_pdf=False,
                logger=null_logger(),
            )
            with (
                patch("cv_agent.run.run_cv_agent", return_value=sample_cv_content()),
                patch("cv_agent.run.render_pdf") as render_pdf,
            ):
                result = create_application_pack(request)
            render_pdf.assert_not_called()
            self.assertIsNone(result.pdf_path)


def sample_cv_content() -> dict[str, object]:
    return {
        "profile": {"content": "AI Product Engineer.", "evidence": ["roles/logan-sinclair.md"]},
        "work_experience": [],
        "projects": [],
        "skills": [],
        "education": [],
        "contact": {},
        "additional_experience": [],
    }


if __name__ == "__main__":
    unittest.main()
