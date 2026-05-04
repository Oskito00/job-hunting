import os
import unittest
from unittest.mock import patch

from cv_agent.env import load_env_line, split_env_line


class EnvTest(unittest.TestCase):
    def test_split_env_line_strips_quotes(self) -> None:
        self.assertEqual(split_env_line('OPENAI_API_KEY="abc"'), ("OPENAI_API_KEY", "abc"))

    def test_load_env_line_does_not_override_existing_value(self) -> None:
        with patch.dict(os.environ, {"OPENAI_MODEL": "custom"}, clear=True):
            load_env_line("OPENAI_MODEL=gpt-5.5")
            self.assertEqual(os.environ["OPENAI_MODEL"], "custom")


if __name__ == "__main__":
    unittest.main()
