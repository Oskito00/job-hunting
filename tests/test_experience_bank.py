from pathlib import Path
import tempfile
import unittest

from cv_agent.experience_bank import load_experience_files, resolve_bank_path, search_experience_files, split_frontmatter


class ExperienceBankTest(unittest.TestCase):
    def test_split_frontmatter_parses_simple_lists(self) -> None:
        raw = "---\nid: sample\nskills:\n  - python\n  - llm\n---\n# Body"
        metadata, body = split_frontmatter(raw)
        self.assertEqual(metadata["id"], "sample")
        self.assertEqual(metadata["skills"], ["python", "llm"])
        self.assertEqual(body, "# Body")

    def test_resolve_bank_path_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bank = Path(tmp) / "bank"
            bank.mkdir()
            with self.assertRaises(ValueError):
                resolve_bank_path("../secret.md", bank)

    def test_search_uses_metadata_and_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bank = Path(tmp) / "bank"
            bank.mkdir()
            (bank / "project.md").write_text(
                "---\ntitle: Vector Search\nskills:\n  - chromadb\n---\n# Project\nBuilt ranking with embeddings.",
                encoding="utf-8",
            )
            files = load_experience_files(bank)
            results = search_experience_files("ChromaDB embeddings", files)
            self.assertEqual(results[0].path, "project.md")

    def test_search_returns_wider_candidate_set_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bank = Path(tmp) / "bank"
            bank.mkdir()
            for index in range(12):
                (bank / f"project-{index}.md").write_text(f"---\ntitle: Project {index}\n---\nPython AI product {index}", encoding="utf-8")
            files = load_experience_files(bank)
            results = search_experience_files("Python AI product", files)
            self.assertEqual(len(results), 12)

    def test_worldquant_query_surfaces_inbetments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bank = Path(tmp) / "bank"
            projects = bank / "projects"
            projects.mkdir(parents=True)
            (projects / "inbetments-football-prediction-model.md").write_text(
                "---\ntitle: Football Prediction Model\nskills:\n  - Python\n  - predictive signals\n  - vector databases\n---\n"
                "# Project\nBuilt analytical alphas for complex WorldQuant-style modelling problems.",
                encoding="utf-8",
            )
            (projects / "crm-workflow.md").write_text("---\ntitle: CRM Workflow\n---\n# Project\nBuilt recruiting workflow tools.", encoding="utf-8")
            files = load_experience_files(bank)
            query = "WorldQuant predictive signals alphas Python analytical complex problems vector databases language models scalable AI-driven products"
            paths = [result.path for result in search_experience_files(query, files)]
            self.assertIn("projects/inbetments-football-prediction-model.md", paths)


if __name__ == "__main__":
    unittest.main()
