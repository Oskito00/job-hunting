from pathlib import Path
import tempfile
import unittest

from cv_agent.onboarding import ExperienceDraft, EvidenceFileDraft, ImportedCV, build_template_agent_input, extract_cv_text, image_data_url, normalise_evidence_markdown, safe_experience_relative_path, write_experience_draft
from cv_agent.workspace import ensure_workspace, resolve_workspace


class OnboardingTest(unittest.TestCase):
    def test_extract_cv_text_reads_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cv.md"
            path.write_text("# CV\n\nExperience", encoding="utf-8")
            self.assertEqual(extract_cv_text(path), "# CV\n\nExperience")

    def test_safe_experience_relative_path_rejects_escape(self) -> None:
        with self.assertRaises(ValueError):
            safe_experience_relative_path("../secret.md")

    def test_write_experience_draft_writes_under_workspace_bank(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = resolve_workspace(Path(tmp))
            ensure_workspace(workspace)
            draft = ExperienceDraft(files=[EvidenceFileDraft(relative_path="projects/sample", content="# Sample")])
            written = write_experience_draft(workspace, draft)
            self.assertEqual(written[0], workspace.experience_bank / "projects" / "sample.md")
            self.assertTrue(written[0].exists())
            self.assertIn("type: project", written[0].read_text(encoding="utf-8"))

    def test_normalise_evidence_markdown_preserves_frontmatter(self) -> None:
        content = "---\ntype: role\n---\n# Role"
        self.assertEqual(normalise_evidence_markdown(Path("roles/acme.md"), content), content + "\n")

    def test_build_template_agent_input_includes_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "page-001.png"
            image_path.write_bytes(b"png")
            agent_input = build_template_agent_input("CV text", ImportedCV(name="Candidate"), [image_path])
            self.assertIsInstance(agent_input, list)
            content = agent_input[0]["content"]
            self.assertEqual(content[0]["type"], "input_text")
            self.assertEqual(content[1]["type"], "input_image")
            self.assertTrue(str(content[1]["image_url"]).startswith("data:image/png;base64,"))

    def test_image_data_url_encodes_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "page.png"
            image_path.write_bytes(b"png")
            self.assertEqual(image_data_url(image_path), "data:image/png;base64,cG5n")


if __name__ == "__main__":
    unittest.main()
