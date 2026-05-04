from pathlib import Path
import tempfile
import unittest

from cv_agent.config import load_static_profile_config


class ConfigTest(unittest.TestCase):
    def test_load_static_profile_config_from_bank_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bank = Path(tmp)
            (bank / "contact.md").write_text("---\ntype: contact\n---\n# Contact\n- Email: test@example.com", encoding="utf-8")
            (bank / "education.md").write_text(
                "---\ntype: education\n---\n# Education\n## University\n- Degree: AI BSc\n- Dates: 2019-2023",
                encoding="utf-8",
            )
            config = load_static_profile_config(bank)
            self.assertEqual(config.contact["email"], "test@example.com")
            self.assertEqual(config.education[0]["institution"], "University")


if __name__ == "__main__":
    unittest.main()
