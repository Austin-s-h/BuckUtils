#!/usr/bin/env python3
"""
BuckUtils - A simple PDF utility for combining PDF files with page-level control.
Designed to be grandpa-friendly with a clear, easy-to-use interface.
"""

import os
import shutil
import tempfile
import subprocess
import sys
import tkinter as tk
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - used for type checking only
    from pypdf import PageObject

# Try to import pypdf, fall back to Ghostscript if not available
try:
    from pypdf import PdfReader, PdfWriter

    HAS_PYPDF = True
except ImportError:
    PdfReader = None  # type: ignore[assignment]
    PdfWriter = None  # type: ignore[assignment]
    HAS_PYPDF = False


CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _generate_preview_for_page(
    task: tuple[str, int, Optional[str]]
) -> tuple[str, int, str, Optional[str]]:
    """Generate preview text and image for a single page (worker-safe)."""
    file_path, page_index, gs_path = task
    preview_text = "No text preview available for this page."
    preview_image_path: Optional[str] = None

    try:
        reader = PdfReader(file_path)
        page = reader.pages[page_index]
        text = ""
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        cleaned = " ".join(text.split())
        if cleaned:
            preview_text = (cleaned[:240] + "…") if len(cleaned) > 240 else cleaned
    except Exception:
        pass

    if gs_path:
        try:
            tmp_dir = Path(tempfile.gettempdir())
            output_path = tmp_dir / f"buckutils_preview_{Path(file_path).stem}_{page_index}.png"
            cmd = [
                gs_path,
                "-dBATCH",
                "-dNOPAUSE",
                "-sDEVICE=png16m",
                "-dSAFER",
                f"-dFirstPage={page_index + 1}",
                f"-dLastPage={page_index + 1}",
                "-r50",
                f"-sOutputFile={output_path}",
                file_path,
            ]
            run_kwargs = {"capture_output": True, "text": True}
            if CREATE_NO_WINDOW:
                run_kwargs["creationflags"] = CREATE_NO_WINDOW
            result = subprocess.run(cmd, **run_kwargs)
            if result.returncode == 0 and output_path.exists():
                preview_image_path = str(output_path)
        except Exception:
            preview_image_path = None

    return file_path, page_index, preview_text, preview_image_path


@dataclass
class PDFPage:
    """Represents a single PDF page with preview metadata."""

    source_path: str
    page_index: int
    label: str
    page: "PageObject"
    preview: str
    preview_image_path: Optional[str] = None


class PDFCombiner:
    """Handles PDF combining operations."""

    @staticmethod
    def find_ghostscript() -> Optional[str]:
        """Find Ghostscript executable on the system."""
        # Common Ghostscript paths on Windows
        gs_names = ["gswin64c", "gswin32c", "gs"]

        # Check in PATH first
        for name in gs_names:
            if shutil.which(name):
                return name

        # Check common Windows installation paths
        program_files = [
            os.environ.get("PROGRAMFILES", "C:\\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
        ]

        for pf in program_files:
            gs_dir = Path(pf) / "gs"
            if gs_dir.exists():
                # Look for gsXX.XX directories
                for subdir in gs_dir.iterdir():
                    gs_path = subdir / "bin" / "gswin64c.exe"
                    if gs_path.exists():
                        return str(gs_path)
                    gs_path = subdir / "bin" / "gswin32c.exe"
                    if gs_path.exists():
                        return str(gs_path)

        return None

    @staticmethod
    def combine_with_pypdf2(input_files: list[str], output_file: str) -> bool:
        """Combine PDFs using pypdf."""
        try:
            writer = PdfWriter()

            for pdf_path in input_files:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)

            with Path(output_file).open("wb") as output:
                writer.write(output)

            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to combine PDFs: {e!s}")
            return False

    @staticmethod
    def combine_with_ghostscript(
        input_files: list[str], output_file: str, gs_path: str
    ) -> bool:
        """Combine PDFs using Ghostscript."""
        try:
            cmd = [
                gs_path,
                "-dBATCH",
                "-dNOPAUSE",
                "-dSAFER",
                "-sDEVICE=pdfwrite",
                "-dPDFSETTINGS=/prepress",
                f"-sOutputFile={output_file}",
                *input_files,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                messagebox.showerror("Error", f"Ghostscript error: {result.stderr}")
                return False

            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run Ghostscript: {e!s}")
            return False

    def combine(self, input_files: list[str], output_file: str) -> bool:
        """Combine multiple PDFs into one."""
        if not input_files:
            messagebox.showwarning("Warning", "No files selected to combine!")
            return False

        if HAS_PYPDF:
            return self.combine_with_pypdf2(input_files, output_file)

        gs_path = self.find_ghostscript()
        if gs_path:
            return self.combine_with_ghostscript(input_files, output_file, gs_path)

        messagebox.showerror(
            "Error",
            "No PDF library found!\n\n"
            "Please install either:\n"
            "1. pypdf (pip install pypdf)\n"
            "2. Ghostscript (https://ghostscript.com)",
        )
        return False

    def combine_pages(self, pages: list[PDFPage], output_file: str) -> bool:
        """Combine individual pages into a single PDF in the given order."""
        if not pages:
            messagebox.showwarning("Warning", "No pages selected to combine!")
            return False

        if not HAS_PYPDF:
            messagebox.showerror(
                "Error",
                "Page-level combining requires pypdf. "
                "Run 'make dev' (uv pip install -e \".[dev]\") to install the dependencies and try again.",
            )
            return False

        try:
            writer = PdfWriter()
            for page in pages:
                writer.add_page(page.page)

            with Path(output_file).open("wb") as output:
                writer.write(output)

            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to combine pages: {e!s}")
            return False


class BuckUtilsApp:
    """Main application class for BuckUtils PDF utility."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BuckUtils - PDF Helper")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        # Configure style for larger, more readable UI
        self.style = ttk.Style()
        self.style.configure("Large.TButton", font=("Segoe UI", 14), padding=10)
        self.style.configure("Large.TLabel", font=("Segoe UI", 12))
        self.style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))

        # PDF combiner
        self.combiner = PDFCombiner()

        # Page list for combining
        self.pages: list[PDFPage] = []
        self._open_readers: list[PdfReader] = []
        self._drag_start_index: Optional[int] = None
        self._preview_files: list[str] = []
        self._current_photo: Optional[tk.PhotoImage] = None

        # Create main UI
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the main user interface."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="🔧 BuckUtils PDF Helper", style="Title.TLabel")
        title_label.pack(pady=(0, 20))

        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Combine PDFs tab
        combine_frame = ttk.Frame(notebook, padding="20")
        notebook.add(combine_frame, text="  📄 Combine PDFs  ")
        self._create_combine_tab(combine_frame)

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        backend = (
            "pypdf"
            if HAS_PYPDF
            else ("Ghostscript" if self.combiner.find_ghostscript() else "None")
        )
        status_label = ttk.Label(status_frame, text=f"PDF Backend: {backend}", style="Large.TLabel")
        status_label.pack(side=tk.LEFT)

    def _create_combine_tab(self, parent: ttk.Frame) -> None:
        """Create the Combine PDFs tab."""
        # Instructions
        instructions = ttk.Label(
            parent,
            text=(
                "Add PDF files to import every page, then drag-and-drop or use the buttons "
                "below to reorder pages across files. Click 'Combine' to export the final PDF."
            ),
            style="Large.TLabel",
            wraplength=600,
        )
        instructions.pack(pady=(0, 15))

        # Buttons frame (top)
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        add_btn = ttk.Button(
            button_frame, text="+ Add PDF Files", style="Large.TButton", command=self._add_files
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))

        remove_btn = ttk.Button(
            button_frame,
            text="❌ Remove Selected",
            style="Large.TButton",
            command=self._remove_selected,
        )
        remove_btn.pack(side=tk.LEFT, padx=(0, 10))

        clear_btn = ttk.Button(
            button_frame, text="🗑️ Clear All", style="Large.TButton", command=self._clear_files
        )
        clear_btn.pack(side=tk.LEFT)

        # File list with scrollbar
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.page_listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 12),
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            height=10,
        )
        self.page_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.page_listbox.yview)
        self.page_listbox.bind("<<ListboxSelect>>", self._update_preview)
        self.page_listbox.bind("<Button-1>", self._start_drag)
        self.page_listbox.bind("<B1-Motion>", self._on_drag_motion)
        self.page_listbox.bind("<ButtonRelease-1>", self._end_drag)

        # Move buttons frame
        move_frame = ttk.Frame(parent)
        move_frame.pack(fill=tk.X, pady=10)

        move_up_btn = ttk.Button(
            move_frame, text="⬆️ Move Up", style="Large.TButton", command=self._move_up
        )
        move_up_btn.pack(side=tk.LEFT, padx=(0, 10))

        move_down_btn = ttk.Button(
            move_frame, text="⬇️ Move Down", style="Large.TButton", command=self._move_down
        )
        move_down_btn.pack(side=tk.LEFT)

        # Preview frame
        preview_frame = ttk.LabelFrame(parent, text="Page Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        self.preview_title_var = tk.StringVar(value="Select a page to preview")
        preview_title = ttk.Label(
            preview_frame, textvariable=self.preview_title_var, style="Header.TLabel"
        )
        preview_title.pack(anchor=tk.W, pady=(0, 5))

        self.preview_image_label = ttk.Label(preview_frame)
        self.preview_image_label.pack(anchor=tk.CENTER, pady=(0, 8))

        self.preview_text = tk.Text(
            preview_frame,
            height=6,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            state=tk.DISABLED,
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        # Combine button (prominent)
        combine_btn = ttk.Button(
            parent, text="🔗 COMBINE PDFs", style="Large.TButton", command=self._combine_pdfs
        )
        combine_btn.pack(pady=20, ipadx=30, ipady=10)

    # ========== Combine Tab Methods ==========

    def _add_files(self) -> None:
        """Add PDF files and import their pages."""
        files = filedialog.askopenfilenames(
            title="Select PDF Files to Combine",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
        )

        if not files:
            return

        for file_path in files:
            self._import_pdf_pages(file_path)

        self._refresh_page_list()

    def _import_pdf_pages(self, file_path: str) -> None:
        """Load pages from a PDF file into the working list."""
        if not HAS_PYPDF:
            messagebox.showerror(
                "Missing PDF Support",
                "Page previews require pypdf. Run 'make dev' (uv pip install -e \".[dev]\") "
                "to install dependencies and try again.",
            )
            return

        try:
            reader = PdfReader(file_path)
        except Exception as exc:  # pragma: no cover - pypdf will raise its own errors
            messagebox.showerror("Error", f"Unable to open {Path(file_path).name}: {exc!s}")
            return

        self._open_readers.append(reader)
        existing = {(page.source_path, page.page_index) for page in self.pages}
        tasks: list[tuple[str, int, Optional[str]]] = []
        gs_path = self.combiner.find_ghostscript()

        for idx, page in enumerate(reader.pages):
            key = (file_path, idx)
            if key in existing:
                continue

            label = f"{Path(file_path).name} - Page {idx + 1}"
            self.pages.append(
                PDFPage(file_path, idx, label, page, "Generating preview…", None)
            )
            tasks.append((file_path, idx, gs_path))

        if tasks:
            self._generate_previews_in_background(tasks)

    def _build_preview_text(self, page: "PageObject") -> str:
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

    def _generate_previews_in_background(self, tasks: list[tuple[str, int, Optional[str]]]) -> None:
        """Generate previews using multiprocessing while showing a progress bar."""
        if not tasks:
            return

        progress_win = tk.Toplevel(self.root)
        progress_win.title("Generating previews…")
        progress_win.resizable(False, False)
        progress_win.transient(self.root)
        progress_win.grab_set()

        ttk.Label(progress_win, text="Generating page previews…", padding=10).pack(
            fill=tk.X, padx=10, pady=(10, 0)
        )
        progress = ttk.Progressbar(
            progress_win, mode="determinate", maximum=len(tasks), length=320
        )
        progress.pack(fill=tk.X, padx=12, pady=(0, 12))
        progress_win.update_idletasks()

        try:
            with ProcessPoolExecutor() as executor:
                futures = [executor.submit(_generate_preview_for_page, task) for task in tasks]
                completed = 0
                for future in as_completed(futures):
                    try:
                        file_path, page_index, preview_text, preview_image_path = future.result()
                    except Exception:
                        continue
                    self._apply_preview_result(
                        file_path, page_index, preview_text, preview_image_path
                    )
                    completed += 1
                    progress["value"] = completed
                    progress_win.update_idletasks()
        finally:
            progress_win.grab_release()
            progress_win.destroy()
        self._update_preview()

    def _apply_preview_result(
        self, file_path: str, page_index: int, preview: str, preview_image_path: Optional[str]
    ) -> None:
        """Update stored page previews after background generation completes."""
        for page in self.pages:
            if page.source_path == file_path and page.page_index == page_index:
                page.preview = preview
                page.preview_image_path = preview_image_path
                if preview_image_path:
                    self._preview_files.append(preview_image_path)
                break

    def _render_preview_image(self, file_path: str, page_index: int) -> Optional[str]:
        """Render a low-resolution preview image for a PDF page using Ghostscript."""
        gs_path = self.combiner.find_ghostscript()
        if not gs_path:
            return None

        try:
            tmp_dir = Path(tempfile.gettempdir())
            output_path = tmp_dir / f"buckutils_preview_{Path(file_path).stem}_{page_index}.png"
            cmd = [
                gs_path,
                "-dBATCH",
                "-dNOPAUSE",
                "-sDEVICE=png16m",
                "-dSAFER",
                "-dFirstPage={}".format(page_index + 1),
                "-dLastPage={}".format(page_index + 1),
                "-r50",
                f"-sOutputFile={output_path}",
                file_path,
            ]
            run_kwargs = {"capture_output": True, "text": True}
            if CREATE_NO_WINDOW:
                run_kwargs["creationflags"] = CREATE_NO_WINDOW
            result = subprocess.run(cmd, **run_kwargs)
            if result.returncode != 0:
                return None
            if output_path.exists():
                return str(output_path)
        except Exception:
            return None
        return None

    def _refresh_page_list(self, select_index: Optional[int] = None) -> None:
        """Refresh the listbox to reflect the current page order."""
        self.page_listbox.delete(0, tk.END)
        for page in self.pages:
            self.page_listbox.insert(tk.END, page.label)

        if select_index is None and self.pages:
            select_index = 0

        if select_index is not None and 0 <= select_index < len(self.pages):
            self.page_listbox.selection_set(select_index)
            self.page_listbox.activate(select_index)
        self._update_preview()

    def _remove_selected(self) -> None:
        """Remove selected pages from the list."""
        selected = list(self.page_listbox.curselection())
        selected.reverse()  # Remove from end to avoid index shifting

        for idx in selected:
            del self.pages[idx]

        self._refresh_page_list()

    def _update_preview(self, event: Optional[tk.Event] = None) -> None:
        """Update the preview panel based on the selected page."""
        if not hasattr(self, "preview_text"):
            return

        selection = self.page_listbox.curselection()
        if not selection:
            self.preview_title_var.set("Select a page to preview")
            self.preview_text.configure(state=tk.NORMAL)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert(tk.END, "No page selected.")
            self.preview_text.configure(state=tk.DISABLED)
            return

        page = self.pages[selection[0]]
        self.preview_title_var.set(page.label)
        if page.preview_image_path and Path(page.preview_image_path).exists():
            self._current_photo = tk.PhotoImage(file=page.preview_image_path)
            self.preview_image_label.configure(image=self._current_photo)
        else:
            self._current_photo = None
            self.preview_image_label.configure(image="")
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, page.preview)
        self.preview_text.configure(state=tk.DISABLED)

    def _start_drag(self, event: tk.Event) -> None:
        """Mark the starting index for drag-and-drop operations."""
        index = self.page_listbox.nearest(event.y)
        if 0 <= index < len(self.pages):
            self._drag_start_index = index
            self.page_listbox.selection_clear(0, tk.END)
            self.page_listbox.selection_set(index)

    def _on_drag_motion(self, event: tk.Event) -> None:
        """Handle drag motion to reorder pages."""
        if self._drag_start_index is None:
            return

        target_index = self.page_listbox.nearest(event.y)
        if (
            target_index == self._drag_start_index
            or target_index < 0
            or target_index >= len(self.pages)
        ):
            return

        self.pages[self._drag_start_index], self.pages[target_index] = (
            self.pages[target_index],
            self.pages[self._drag_start_index],
        )
        self._drag_start_index = target_index
        self._refresh_page_list(select_index=target_index)

    def _end_drag(self, event: tk.Event) -> None:
        """End drag operation."""
        self._drag_start_index = None

    def _clear_files(self) -> None:
        """Clear all pages from the list."""
        self.page_listbox.delete(0, tk.END)
        self.pages.clear()
        for reader in self._open_readers:
            stream = getattr(reader, "stream", None)
            if stream:
                try:
                    stream.close()
                except OSError as exc:
                    print(f"Warning: failed to close PDF stream: {exc}", file=sys.stderr)
        self._open_readers.clear()
        self._drag_start_index = None
        for preview in self._preview_files:
            try:
                Path(preview).unlink(missing_ok=True)
            except OSError:
                pass
        self._preview_files.clear()
        self._update_preview()

    def _move_up(self) -> None:
        """Move selected page up in the list."""
        selected = self.page_listbox.curselection()
        if not selected or selected[0] == 0:
            return

        idx = selected[0]
        # Swap in the list
        self.pages[idx], self.pages[idx - 1] = self.pages[idx - 1], self.pages[idx]

        # Update listbox
        self._refresh_page_list(select_index=idx - 1)

    def _move_down(self) -> None:
        """Move selected page down in the list."""
        selected = self.page_listbox.curselection()
        if not selected or selected[0] == len(self.pages) - 1:
            return

        idx = selected[0]
        # Swap in the list
        self.pages[idx], self.pages[idx + 1] = self.pages[idx + 1], self.pages[idx]

        # Update listbox
        self._refresh_page_list(select_index=idx + 1)

    def _combine_pdfs(self) -> None:
        """Combine all pages in the list."""
        if not self.pages:
            messagebox.showwarning("No Pages", "Please add PDF files so we can import pages!")
            return

        # Ask for output file
        output_file = filedialog.asksaveasfilename(
            title="Save Combined PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile="combined.pdf",
        )

        if not output_file:
            return

        # Combine PDFs
        if self.combiner.combine_pages(self.pages, output_file):
            messagebox.showinfo(
                "Success! ✅", f"PDF pages combined successfully!\n\nSaved to:\n{output_file}"
            )

            # Ask if user wants to open the folder
            if messagebox.askyesno(
                "Open Folder?", "Would you like to open the folder containing the file?"
            ):
                folder = str(Path(output_file).parent)
                if sys.platform == "win32":
                    os.startfile(folder)
                elif sys.platform == "darwin":
                    subprocess.run(["open", folder], check=False)
                else:
                    subprocess.run(["xdg-open", folder], check=False)


def main() -> None:
    """Main entry point."""
    root = tk.Tk()

    # Set icon if available
    try:
        # For Windows, try to set icon
        if sys.platform == "win32":
            root.iconbitmap("icon.ico")
    except Exception:
        pass

    BuckUtilsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
