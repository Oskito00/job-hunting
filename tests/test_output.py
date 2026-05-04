import unittest

from cv_agent.output import build_coverage_report, collect_evidence_paths


class OutputTest(unittest.TestCase):
    def test_collect_evidence_paths_recurses(self) -> None:
        content = {"projects": [{"bullets": [{"text": "x", "evidence": ["projects/a.md"]}]}]}
        self.assertEqual(collect_evidence_paths(content), {"projects/a.md"})

    def test_coverage_report_lists_evidence(self) -> None:
        content = {"profile": {"content": "x", "evidence": ["roles/a.md"]}}
        report = build_coverage_report(content, "https://example.com/job")
        self.assertIn("- roles/a.md", report)


if __name__ == "__main__":
    unittest.main()
