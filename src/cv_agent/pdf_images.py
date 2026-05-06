from __future__ import annotations

from pathlib import Path


DEFAULT_DPI = 160


def render_pdf_pages_to_images(pdf_path: Path, output_dir: Path, dpi: int = DEFAULT_DPI) -> list[Path]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("Visual template generation requires pymupdf. Install project dependencies and retry.") from exc
    output_dir.mkdir(parents=True, exist_ok=True)
    clear_existing_page_images(output_dir)
    document = fitz.open(str(pdf_path))
    try:
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        return [render_page_to_image(page, output_dir, matrix, index) for index, page in enumerate(document, start=1)]
    finally:
        document.close()


def render_page_to_image(page, output_dir: Path, matrix, index: int) -> Path:
    image_path = output_dir / f"page-{index:03d}.png"
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    pixmap.save(str(image_path))
    return image_path


def clear_existing_page_images(output_dir: Path) -> None:
    for image_path in output_dir.glob("page-*.png"):
        image_path.unlink()
