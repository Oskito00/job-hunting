import unittest

from cv_agent.job_extract import JobExtractionError, extract_job_text, extract_visible_text


class JobExtractTest(unittest.TestCase):
    def test_extract_visible_text_ignores_scripts_and_nav(self) -> None:
        html = "<nav>Menu</nav><main><h1>Role</h1><p>Build AI products.</p></main><script>alert(1)</script>"
        text = extract_visible_text(html)
        self.assertIn("Role", text)
        self.assertIn("Build AI products.", text)
        self.assertNotIn("Menu", text)
        self.assertNotIn("alert", text)

    def test_extract_job_text_requires_enough_signal(self) -> None:
        html = "<main><p>Too short.</p></main>"
        with self.assertRaises(JobExtractionError):
            extract_job_text(html)

    def test_extract_job_text_accepts_job_like_pages(self) -> None:
        body = "Responsibilities " + ("Build product features. " * 80)
        html = f"<main><h1>Engineer</h1><p>{body}</p></main>"
        self.assertIn("Responsibilities", extract_job_text(html))


if __name__ == "__main__":
    unittest.main()
