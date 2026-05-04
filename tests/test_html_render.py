from pathlib import Path
import tempfile
import unittest

from cv_agent.html_render import deterministic_skill_rating, display_role_dates, render_cv_html_file, render_stars


class HtmlRenderTest(unittest.TestCase):
    def test_deterministic_skill_rating(self) -> None:
        self.assertEqual([deterministic_skill_rating(index) for index in range(6)], [5, 5, 5, 5, 4, 4])

    def test_render_stars(self) -> None:
        self.assertEqual(render_stars(4), "★★★★☆")

    def test_display_role_dates_hides_exact_start_day(self) -> None:
        self.assertEqual(display_role_dates("25 June 2025 to Present"), "June 2025 - Present")

    def test_render_cv_html_file_writes_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            html_path = render_cv_html_file(sample_content(), Path(tmp))
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Oscar Alberigo", html)
            self.assertIn("Client-Facing Experience", html)
            self.assertIn('href="mailto:test@example.com"', html)
            self.assertIn('aria-label="LinkedIn"', html)
            self.assertIn("★★★★☆", html)
            self.assertNotIn("generated side project", html)

    def test_render_cv_html_file_reports_overflow_but_writes_html(self) -> None:
        content = sample_content()
        content["profile"]["content"] = "x" * 1000
        with tempfile.TemporaryDirectory() as tmp:
            html_path = render_cv_html_file(content, Path(tmp))
            self.assertTrue(html_path.exists())
            self.assertTrue((Path(tmp) / "render-report.md").exists())

    def test_renderer_limits_visible_right_column_content(self) -> None:
        content = sample_content()
        content["projects"] = [
            {"name": f"Project {index}", "bullets": [{"text": "A", "evidence": ["x.md"]}, {"text": "B", "evidence": ["x.md"]}, {"text": "hidden", "evidence": ["x.md"]}]}
            for index in range(4)
        ]
        with tempfile.TemporaryDirectory() as tmp:
            html_path = render_cv_html_file(content, Path(tmp))
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Project 3", html)
            self.assertNotIn("<li>hidden</li>", html)


def sample_content() -> dict[str, object]:
    return {
        "profile": {"content": "AI Product Engineer.", "evidence": ["roles/logan-sinclair.md"]},
        "work_experience": [
            {
                "company": "Logan Sinclair",
                "title": "AI Product Engineer",
                "dates": "June 2025 - Present",
                "bullets": [{"text": "Built production AI tools.", "evidence": ["roles/logan-sinclair.md"]}],
            }
        ],
        "projects": [{"name": "CV Database", "bullets": [{"text": "Built semantic ranking.", "evidence": ["projects/cv-database-and-ranking-system.md"]}]}],
        "skills": [
            {"name": "LLM Applications", "category": "ai"},
            {"name": "Python", "category": "software"},
            {"name": "Product Engineering", "category": "product"},
            {"name": "Docker", "category": "infra"},
            {"name": "React", "category": "software"},
            {"name": "Cloud Hosting", "category": "infra"},
        ],
        "education": [{"institution": "The University of Edinburgh", "degree": "AI and Computer Science BSc", "classification": "1st Class Honours", "dates": "2019-2023"}],
        "contact": {"email": "test@example.com", "phone": "+44", "linkedin": "linkedin", "website": "site", "github": "github"},
        "additional_experience": [{"text": "generated side project", "evidence": ["experience-bank"]}],
    }


if __name__ == "__main__":
    unittest.main()
