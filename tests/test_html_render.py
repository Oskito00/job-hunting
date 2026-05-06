from pathlib import Path
import tempfile
import unittest

from cv_agent.html_render import ONE_PAGE_MODE, PRINT_NORMALIZATION_MARKER, RenderOptions, apply_print_normalization, display_role_dates, find_unresolved_template_tokens, page_mode_classes, render_cv_html_file, validate_template_html


class HtmlRenderTest(unittest.TestCase):
    def test_page_mode_classes_supports_css_variants(self) -> None:
        self.assertEqual(page_mode_classes(ONE_PAGE_MODE), "one_page one-page")

    def test_display_role_dates_hides_exact_start_day(self) -> None:
        self.assertEqual(display_role_dates("25 June 2025 to Present"), "June 2025 - Present")

    def test_render_cv_html_file_writes_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            html_path = render_cv_html_file(sample_content(), Path(tmp))
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Test Candidate", html)
            self.assertNotIn("Client-Facing Experience", html)
            self.assertIn('href="mailto:test@example.com"', html)
            self.assertIn('aria-label="LinkedIn"', html)
            self.assertIn('aria-label="Location"', html)
            self.assertIn('class="skill"', html)
            self.assertNotIn("★★★★", html)
            self.assertNotIn("stars", html)
            self.assertNotIn("4-star skills", html)
            self.assertIn("generated side project", html)
            self.assertIn(PRINT_NORMALIZATION_MARKER, html)
            self.assertEqual(find_unresolved_template_tokens(html), [])

    def test_render_cv_html_file_reports_overflow_but_writes_html(self) -> None:
        content = sample_content()
        content["profile"]["content"] = "x" * 1000
        with tempfile.TemporaryDirectory() as tmp:
            html_path = render_cv_html_file(content, Path(tmp), options=RenderOptions(page_mode=ONE_PAGE_MODE))
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

    def test_validate_template_html_requires_core_placeholders(self) -> None:
        errors = validate_template_html("<html>{{name}}{{profile}}</html>")
        self.assertIn("template is missing placeholders", errors[0])

    def test_render_cv_html_file_uses_template(self) -> None:
        template = "<html><body><h1>{{ name }}</h1>{{profile}}{{work_experience}}{{projects}}{{skills}}{{education}}{{contact}}</body></html>"
        with tempfile.TemporaryDirectory() as tmp:
            template_path = Path(tmp) / "template.html"
            template_path.write_text(template, encoding="utf-8")
            html_path = render_cv_html_file(sample_content(), Path(tmp), options=RenderOptions(template_path=template_path))
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("<h1>Test Candidate</h1>", html)
            self.assertEqual(find_unresolved_template_tokens(html), [])

    def test_print_normalization_allows_experience_to_flow_across_pages(self) -> None:
        html = apply_print_normalization("<html><head></head><body></body></html>")
        self.assertIn(".experience-section", html)
        self.assertIn("break-inside: auto !important", html)
        self.assertEqual(html.count(PRINT_NORMALIZATION_MARKER), 1)


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
        "contact": {"name": "Test Candidate", "email": "test@example.com", "phone": "+44", "linkedin": "linkedin", "website": "site", "github": "github", "location": "London"},
        "additional_experience": [{"text": "generated side project", "evidence": ["experience-bank"]}],
    }


if __name__ == "__main__":
    unittest.main()
