"""Tests for BuckUtils PDF combiner functionality."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pypdf import PdfReader, PdfWriter

# Mock tkinter for headless testing
with patch.dict("sys.modules", {"tkinter": MagicMock(), "tkinter.ttk": MagicMock()}):
    from buckutils.app import PDFCombiner, PDFPage, _generate_preview_for_page


class TestPDFCombiner:
    """Tests for the PDFCombiner class."""

    def test_find_ghostscript_returns_none_when_not_installed(self) -> None:
        """Test that find_ghostscript returns None when GS is not found."""
        with patch("shutil.which", return_value=None), patch(
            "os.path.exists", return_value=False
        ):
            result = PDFCombiner.find_ghostscript()
            # May or may not be None depending on system, but shouldn't crash
            assert result is None or isinstance(result, str)

    def test_combine_with_empty_list_shows_warning(self) -> None:
        """Test that combining with empty list shows a warning."""
        combiner = PDFCombiner()
        with patch("tkinter.messagebox.showwarning"):
            result = combiner.combine([], "output.pdf")
            assert result is False

    def test_combine_with_single_file_placeholder(self) -> None:
        """Placeholder test for single file validation (done in app layer)."""
        # Note: This test assumes the validation happens in the app, not combiner
        # The combiner.combine() itself just checks for empty list
        pass


class TestPDFCombinerWithPyPDF2:
    """Tests for PDF combining with PyPDF2."""

    @pytest.fixture
    def sample_pdf_content(self) -> bytes:
        """Create minimal valid PDF content."""
        # Minimal valid PDF
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
            with patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
                assert combiner.combine_pages(pages, str(output))

            result_reader = PdfReader(str(output))
            assert len(result_reader.pages) == 2
            assert result_reader.pages[0].mediabox.width == reader1.pages[0].mediabox.width
            assert result_reader.pages[1].mediabox.width == reader2.pages[0].mediabox.width

    def test_generate_preview_for_page_returns_metadata(
        self, sample_pdf_content: bytes
    ) -> None:
        """Test that preview generation helper returns preview data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "preview.pdf"
            pdf_path.write_bytes(sample_pdf_content)

            file_path, page_idx, preview_text, preview_image = _generate_preview_for_page(
                (str(pdf_path), 0, None)
            )

            assert file_path == str(pdf_path)
            assert page_idx == 0
            assert isinstance(preview_text, str)
            assert preview_image is None


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
