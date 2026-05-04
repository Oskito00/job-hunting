from datetime import date
import unittest

from cv_agent.paths import application_folder_name, slugify


class PathsTest(unittest.TestCase):
    def test_slugify_removes_punctuation(self) -> None:
        self.assertEqual(slugify("AI Product Engineer!"), "ai-product-engineer")

    def test_application_folder_name_is_stable(self) -> None:
        folder = application_folder_name("Acme Ltd", "AI Engineer", date(2026, 5, 4))
        self.assertEqual(folder, "acme-ltd-ai-engineer-2026-05-04")


if __name__ == "__main__":
    unittest.main()
