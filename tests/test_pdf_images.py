from pathlib import Path
import tempfile
import unittest

from cv_agent.pdf_images import render_pdf_pages_to_images


class PdfImagesTest(unittest.TestCase):
    def test_render_pdf_pages_to_images_writes_stable_pngs(self) -> None:
        fitz = self.import_fitz()
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "cv.pdf"
            document = fitz.open()
            document.new_page().insert_text((72, 72), "Page one")
            document.new_page().insert_text((72, 72), "Page two")
            document.save(str(pdf_path))
            document.close()
            image_paths = render_pdf_pages_to_images(pdf_path, Path(tmp) / "pages", dpi=72)
            self.assertEqual([path.name for path in image_paths], ["page-001.png", "page-002.png"])
            self.assertTrue(all(path.exists() for path in image_paths))

    def import_fitz(self):
        try:
            import fitz
        except ImportError:
            self.skipTest("pymupdf is not installed")
        return fitz


if __name__ == "__main__":
    unittest.main()
