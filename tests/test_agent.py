import unittest

from cv_agent.agent import agent_instructions


class AgentInstructionsTest(unittest.TestCase):
    def test_instructions_keep_work_roles_by_default(self) -> None:
        instructions = agent_instructions()
        self.assertIn("Include all work roles by default", instructions)
        self.assertIn("agent_decides_preserve_all_roles", instructions)
        self.assertNotIn("maximum 2 work roles", instructions)
        self.assertNotIn("renderer assigns ratings", instructions)


if __name__ == "__main__":
    unittest.main()
