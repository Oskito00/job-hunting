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
            with patch("cv_agent.run.run_cv_agent", return_value=sample_cv_content()):
                result = create_application_pack(request)
            self.assertTrue(result.cv_json_path.exists())
            self.assertTrue(result.coverage_report_path.exists())
            self.assertTrue((result.output_dir / "jd.md").exists())


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
