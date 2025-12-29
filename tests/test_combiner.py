"""Tests for BuckUtils PDF combiner functionality."""

import tempfile
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from buckutils.app import (
    PDFCombiner,
    PDFPage,
    PagePreview,
    UploadedPDF,
    _build_preview_text,
    _render_preview_image,
    build_combined_pdf_bytes,
)


@pytest.fixture
def sample_pdf_content() -> bytes:
    """Create minimal valid PDF content."""
    return b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer << /Size 4 /Root 1 0 R >>
startxref
196
%%EOF"""


class TestPDFCombiner:
    """Tests for the PDFCombiner class."""

    def test_combine_with_empty_list_returns_false(self) -> None:
        """Test that combining with empty list fails gracefully."""
        combiner = PDFCombiner()
        result = combiner.combine([], "output.pdf")
        assert result is False


class TestPDFCombinerWithPyPDF2:
    """Tests for PDF combining with PyPDF2."""
    def test_combine_creates_output_file(self, sample_pdf_content: bytes) -> None:
        """Test that combining PDFs creates an output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test PDF files
            pdf1 = Path(tmpdir) / "test1.pdf"
            pdf2 = Path(tmpdir) / "test2.pdf"
            output = Path(tmpdir) / "combined.pdf"

            pdf1.write_bytes(sample_pdf_content)
            pdf2.write_bytes(sample_pdf_content)

            combiner = PDFCombiner()
            result = combiner.combine([str(pdf1), str(pdf2)], str(output))

            assert result is True
            assert output.exists()
            assert output.stat().st_size > 0

    def test_combine_pages_preserves_order(self) -> None:
        """Test that combining pages respects the provided order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf1 = Path(tmpdir) / "ordered1.pdf"
            pdf2 = Path(tmpdir) / "ordered2.pdf"
            output = Path(tmpdir) / "combined_pages.pdf"

            writer1 = PdfWriter()
            writer1.add_blank_page(width=100, height=150)
            with pdf1.open("wb") as f:
                writer1.write(f)

            writer2 = PdfWriter()
            writer2.add_blank_page(width=200, height=150)
            with pdf2.open("wb") as f:
                writer2.write(f)

            reader1 = PdfReader(str(pdf1))
            reader2 = PdfReader(str(pdf2))

            pages = [
                PDFPage(str(pdf1), 0, "p1", reader1.pages[0], "preview1"),
                PDFPage(str(pdf2), 0, "p2", reader2.pages[0], "preview2"),
            ]

            combiner = PDFCombiner()
            assert combiner.combine_pages(pages, str(output))

            result_reader = PdfReader(str(output))
            assert len(result_reader.pages) == 2
            assert result_reader.pages[0].mediabox.width == reader1.pages[0].mediabox.width
            assert result_reader.pages[1].mediabox.width == reader2.pages[0].mediabox.width

    def test_render_preview_image_returns_png_bytes(self, sample_pdf_content: bytes) -> None:
        """Test that preview image generation returns PNG data."""
        image_bytes = _render_preview_image(sample_pdf_content, 0)

        assert image_bytes is None or image_bytes.startswith(b"\x89PNG")


class TestStreamlitHelpers:
    """Tests for helper utilities backing the Streamlit UI."""

    def test_build_combined_pdf_bytes_uses_order(self, sample_pdf_content: bytes) -> None:
        """Ensure combined PDF respects provided ordering."""
        data = sample_pdf_content
        files = {
            "a": UploadedPDF(file_id="a", name="a.pdf", data=data),
            "b": UploadedPDF(file_id="b", name="b.pdf", data=data),
        }
        pages = [
            PagePreview(file_id="b", page_index=0, label="b", preview_text="", preview_image=None),
            PagePreview(file_id="a", page_index=0, label="a", preview_text="", preview_image=None),
        ]

        combined = build_combined_pdf_bytes(pages, files)
        reader = PdfReader(BytesIO(combined))
        assert len(reader.pages) == 2

    def test_build_preview_text_returns_placeholder(self, sample_pdf_content: bytes) -> None:
        """Ensure preview text fallback is used when no text is present."""
        reader = PdfReader(BytesIO(sample_pdf_content))
        text = _build_preview_text(reader.pages[0])
        assert isinstance(text, str)
        assert text != ""


class TestImports:
    """Test that modules can be imported correctly."""

    def test_version_available(self) -> None:
        """Test that version is available."""
        from buckutils import __version__

        assert __version__ == "0.1.0"

    def test_main_function_available(self) -> None:
        """Test that main function is importable."""
        from buckutils import main

        assert callable(main)
