#!/usr/bin/env python3
"""
BuckUtils - Streamlit PDF helper with page-level previews and ordering.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING
from uuid import uuid4

import pypdfium2 as pdfium
import streamlit as st
from pypdf import PdfReader, PdfWriter

if TYPE_CHECKING:  # pragma: no cover - used for type checking only
    from pypdf import PageObject


@dataclass
class PDFPage:
    """Represents a single PDF page with preview metadata."""

    source_path: str
    page_index: int
    label: str
    page: "PageObject"
    preview: str
    preview_image_path: Optional[str] = None


@dataclass
class UploadedPDF:
    """In-memory representation of an uploaded PDF file."""

    file_id: str
    name: str
    data: bytes


@dataclass
class PagePreview:
    """Preview details for a single page."""

    file_id: str
    page_index: int
    label: str
    preview_text: str
    preview_image: Optional[bytes]


class PDFCombiner:
    """Handles PDF combining operations."""

    @staticmethod
    def combine(input_files: list[str], output_file: str) -> bool:
        """Combine PDFs using pypdf."""
        if not input_files:
            return False

        try:
            writer = PdfWriter()
            for pdf_path in input_files:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)

            with Path(output_file).open("wb") as output:
                writer.write(output)

            return True
        except Exception:
            return False

    @staticmethod
    def combine_pages(pages: list[PDFPage], output_file: str) -> bool:
        """Combine individual pages into a single PDF in the given order."""
        if not pages:
            return False

        try:
            writer = PdfWriter()
            for page in pages:
                writer.add_page(page.page)

            with Path(output_file).open("wb") as output:
                writer.write(output)

            return True
        except Exception:
            return False


def _build_preview_text(page: "PageObject") -> str:
    """Create a short text preview for a page."""
    text = ""
    try:
        text = page.extract_text() or ""
    except Exception:
        text = ""

    cleaned = " ".join(text.split())
    if not cleaned:
        return "No text preview available for this page."

    return (cleaned[:240] + "…") if len(cleaned) > 240 else cleaned


def _render_preview_image(pdf_bytes: bytes, page_index: int, scale: float = 0.4) -> Optional[bytes]:
    """Render a preview image for a PDF page using pypdfium2."""
    pdf = pdfium.PdfDocument(pdf_bytes)
    try:
        page_count = len(pdf)
        if page_index < 0 or page_index >= page_count:
            return None

        page_handle = pdf.get_page(page_index)
        try:
            bitmap = page_handle.render(scale=scale)
            pil_image = bitmap.to_pil()
            buffer = BytesIO()
            pil_image.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer.read()
        finally:
            page_handle.close()
    except Exception:
        return None
    finally:
        pdf.close()


def _init_state() -> None:
    """Ensure Streamlit session state keys exist."""
    st.session_state.setdefault("files", {})  # file_id -> UploadedPDF
    st.session_state.setdefault("pages", [])  # list[PagePreview]
    st.session_state.setdefault("selected_index", 0)
    st.session_state.setdefault("combined_pdf", None)


def _add_uploaded_files(uploaded_files: list) -> None:
    """Import uploaded PDFs into session state with previews."""
    files: Dict[str, UploadedPDF] = st.session_state["files"]
    pages: list[PagePreview] = st.session_state["pages"]

    for uploaded in uploaded_files:
        data = uploaded.getbuffer().tobytes()
        file_id = f"{Path(uploaded.name).stem}-{uuid4().hex[:8]}"
        files[file_id] = UploadedPDF(file_id=file_id, name=uploaded.name, data=data)

        reader = PdfReader(BytesIO(data))
        for idx, page in enumerate(reader.pages):
            label = f"{uploaded.name} - Page {idx + 1}"
            preview_text = _build_preview_text(page)
            preview_image = _render_preview_image(data, idx)
            pages.append(
                PagePreview(
                    file_id=file_id,
                    page_index=idx,
                    label=label,
                    preview_text=preview_text,
                    preview_image=preview_image,
                )
            )


def _clear_state() -> None:
    """Remove all stored files and pages."""
    st.session_state["files"] = {}
    st.session_state["pages"] = []
    st.session_state["selected_index"] = 0
    st.session_state["combined_pdf"] = None


def _swap_pages(idx_a: int, idx_b: int) -> None:
    """Swap two pages in the current order."""
    pages: list[PagePreview] = st.session_state["pages"]
    pages[idx_a], pages[idx_b] = pages[idx_b], pages[idx_a]


def build_combined_pdf_bytes(pages: list[PagePreview], files: Dict[str, UploadedPDF]) -> bytes:
    """Build a combined PDF from ordered previews."""
    writer = PdfWriter()
    for page in pages:
        file_entry = files.get(page.file_id)
        if not file_entry:
            raise KeyError(f"PDF file data not found for '{page.file_id}'")
        reader = PdfReader(BytesIO(file_entry.data))
        writer.add_page(reader.pages[page.page_index])

    buffer = BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    return buffer.read()


def _render_order_controls() -> None:
    """Render page ordering and preview controls."""
    pages: list[PagePreview] = st.session_state["pages"]
    if not pages:
        st.info("Add PDFs to see page previews and reorder them.")
        return

    st.session_state["selected_index"] = min(
        st.session_state.get("selected_index", 0), len(pages) - 1
    )
    selected_index = st.selectbox(
        "Select a page to preview & reorder",
        options=list(range(len(pages))),
        format_func=lambda i: f"{i + 1}. {pages[i].label}",
        index=st.session_state["selected_index"],
    )
    st.session_state["selected_index"] = selected_index

    move_col1, move_col2, move_col3, move_col4 = st.columns(4)
    if move_col1.button("⬆️ Move Up", disabled=selected_index == 0):
        _swap_pages(selected_index, selected_index - 1)
        st.session_state["selected_index"] = selected_index - 1

    if move_col2.button("⬇️ Move Down", disabled=selected_index == len(pages) - 1):
        _swap_pages(selected_index, selected_index + 1)
        st.session_state["selected_index"] = selected_index + 1

    if move_col3.button("❌ Remove Selected", type="secondary"):
        pages.pop(selected_index)
        st.session_state["selected_index"] = max(0, selected_index - 1)

    if move_col4.button("🗑️ Clear All", type="secondary"):
        _clear_state()

    # Preview pane
    if pages:
        selected_page = pages[st.session_state["selected_index"]]
        st.subheader(selected_page.label)
        if selected_page.preview_image:
            st.image(selected_page.preview_image, caption="Page preview", use_column_width=True)
        st.text_area(
            "Text preview",
            selected_page.preview_text,
            height=200,
            disabled=True,
        )


def render_app() -> None:
    """Streamlit application entry point."""
    st.set_page_config(page_title="BuckUtils - PDF Helper", page_icon="🌸", layout="wide")
    _init_state()

    st.title("🌸 BuckUtils PDF Helper (Streamlit)")
    st.write(
        "Combine PDF pages with rich previews, simple reordering, and a download-ready result. "
        "Rendering is handled in-process to avoid extra pop-up windows."
    )

    with st.expander("Add PDF files", expanded=True):
        uploaded_files = st.file_uploader(
            "Upload one or more PDFs", type=["pdf"], accept_multiple_files=True
        )
        if uploaded_files and st.button("Import selected files", type="primary"):
            _add_uploaded_files(uploaded_files)
            st.success("Pages imported. Adjust the order below.")

    pages: list[PagePreview] = st.session_state["pages"]
    if pages:
        left_col, right_col = st.columns([1.4, 1])
        with left_col:
            _render_order_controls()
        with right_col:
            st.subheader("Export combined PDF")
            default_name = "combined.pdf"
            output_name = st.text_input("Output filename", value=default_name)
            if st.button("Generate PDF", type="primary"):
                st.session_state["combined_pdf"] = build_combined_pdf_bytes(
                    pages, st.session_state["files"]
                )
                st.success("Combined PDF ready to download below.")

            if st.session_state.get("combined_pdf"):
                st.download_button(
                    "⬇️ Download combined PDF",
                    data=st.session_state["combined_pdf"],
                    file_name=output_name or default_name,
                    mime="application/pdf",
                    use_container_width=True,
                )
    else:
        st.info("No pages loaded yet. Upload PDFs above to get started.")


def main() -> None:
    """Launch the Streamlit server when executed directly."""
    try:
        if st.runtime.exists():
            render_app()
            return
    except Exception as exc:
        print(f"Streamlit runtime check failed: {exc}", file=sys.stderr)

    from streamlit.web import bootstrap

    script_path = Path(__file__).resolve()
    bootstrap.run(str(script_path), "", [], {})
    sys.exit(0)


if __name__ == "__main__":
    main()
