import unittest

from cv_agent.schemas import validate_cv_content


class SchemasTest(unittest.TestCase):
    def test_validate_cv_content_rejects_missing_bullet_evidence(self) -> None:
        data = {
            "profile": {"content": "AI engineer", "evidence": ["roles/logan-sinclair.md"]},
            "work_experience": [
                {
                    "company": "Logan Sinclair",
                    "title": "AI Product Engineer",
                    "dates": "June 2025 - Present",
                    "bullets": [{"text": "Built a product.", "evidence": []}],
                }
            ],
            "projects": [],
            "additional_experience": [],
        }
        self.assertEqual(validate_cv_content(data), ["work_experience[0].bullets[0] requires evidence"])

    def test_validate_cv_content_accepts_supported_claims(self) -> None:
        data = {
            "profile": {"content": "AI engineer", "evidence": ["roles/logan-sinclair.md"]},
            "work_experience": [],
            "projects": [{"name": "CV DB", "bullets": [{"text": "Built ranking.", "evidence": ["projects/cv-database-and-ranking-system.md"]}]}],
            "additional_experience": [],
        }
        self.assertEqual(validate_cv_content(data), [])


if __name__ == "__main__":
    unittest.main()
