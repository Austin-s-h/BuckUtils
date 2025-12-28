#!/usr/bin/env python3
"""
BuckUtils - A simple PDF utility for combining and renaming PDF files.
Designed to be grandpa-friendly with a clear, easy-to-use interface.
"""

import shutil
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

# Try to import pypdf, fall back to Ghostscript if not available
try:
    from pypdf import PdfReader, PdfWriter

    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


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
        import os

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

        # File list for combining
        self.pdf_files: list[str] = []

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

        # Rename PDFs tab
        rename_frame = ttk.Frame(notebook, padding="20")
        notebook.add(rename_frame, text="  ✏️ Rename PDF  ")
        self._create_rename_tab(rename_frame)

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
            text="Add PDF files below, arrange them in order, then click 'Combine'.",
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

        self.file_listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 12),
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            height=10,
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

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

        # Combine button (prominent)
        combine_btn = ttk.Button(
            parent, text="🔗 COMBINE PDFs", style="Large.TButton", command=self._combine_pdfs
        )
        combine_btn.pack(pady=20, ipadx=30, ipady=10)

    def _create_rename_tab(self, parent: ttk.Frame) -> None:
        """Create the Rename PDF tab."""
        # Instructions
        instructions = ttk.Label(
            parent,
            text="Select a PDF file and give it a new name.",
            style="Large.TLabel",
            wraplength=600,
        )
        instructions.pack(pady=(0, 20))

        # Current file selection
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill=tk.X, pady=10)

        file_label = ttk.Label(file_frame, text="Current File:", style="Header.TLabel")
        file_label.pack(anchor=tk.W)

        self.current_file_var = tk.StringVar()
        self.current_file_entry = ttk.Entry(
            file_frame, textvariable=self.current_file_var, font=("Segoe UI", 12), state="readonly"
        )
        self.current_file_entry.pack(fill=tk.X, pady=(5, 10))

        browse_btn = ttk.Button(
            file_frame,
            text="📂 Browse for PDF...",
            style="Large.TButton",
            command=self._browse_rename_file,
        )
        browse_btn.pack(anchor=tk.W)

        # New name entry
        name_frame = ttk.Frame(parent)
        name_frame.pack(fill=tk.X, pady=20)

        name_label = ttk.Label(name_frame, text="New Name (without .pdf):", style="Header.TLabel")
        name_label.pack(anchor=tk.W)

        self.new_name_var = tk.StringVar()
        self.new_name_entry = ttk.Entry(
            name_frame, textvariable=self.new_name_var, font=("Segoe UI", 14)
        )
        self.new_name_entry.pack(fill=tk.X, pady=(5, 0), ipady=5)

        # Rename button
        rename_btn = ttk.Button(
            parent, text="✏️ RENAME FILE", style="Large.TButton", command=self._rename_file
        )
        rename_btn.pack(pady=20, ipadx=30, ipady=10)

    # ========== Combine Tab Methods ==========

    def _add_files(self) -> None:
        """Add PDF files to the combine list."""
        files = filedialog.askopenfilenames(
            title="Select PDF Files to Combine",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
        )

        for f in files:
            if f not in self.pdf_files:
                self.pdf_files.append(f)
                self.file_listbox.insert(tk.END, Path(f).name)

    def _remove_selected(self) -> None:
        """Remove selected files from the list."""
        selected = list(self.file_listbox.curselection())
        selected.reverse()  # Remove from end to avoid index shifting

        for idx in selected:
            self.file_listbox.delete(idx)
            del self.pdf_files[idx]

    def _clear_files(self) -> None:
        """Clear all files from the list."""
        self.file_listbox.delete(0, tk.END)
        self.pdf_files.clear()

    def _move_up(self) -> None:
        """Move selected file up in the list."""
        selected = self.file_listbox.curselection()
        if not selected or selected[0] == 0:
            return

        idx = selected[0]
        # Swap in the list
        self.pdf_files[idx], self.pdf_files[idx - 1] = self.pdf_files[idx - 1], self.pdf_files[idx]

        # Update listbox
        text = self.file_listbox.get(idx)
        self.file_listbox.delete(idx)
        self.file_listbox.insert(idx - 1, text)
        self.file_listbox.selection_set(idx - 1)

    def _move_down(self) -> None:
        """Move selected file down in the list."""
        selected = self.file_listbox.curselection()
        if not selected or selected[0] == len(self.pdf_files) - 1:
            return

        idx = selected[0]
        # Swap in the list
        self.pdf_files[idx], self.pdf_files[idx + 1] = self.pdf_files[idx + 1], self.pdf_files[idx]

        # Update listbox
        text = self.file_listbox.get(idx)
        self.file_listbox.delete(idx)
        self.file_listbox.insert(idx + 1, text)
        self.file_listbox.selection_set(idx + 1)

    def _combine_pdfs(self) -> None:
        """Combine all PDFs in the list."""
        if not self.pdf_files:
            messagebox.showwarning("No Files", "Please add some PDF files first!")
            return

        if len(self.pdf_files) < 2:
            messagebox.showwarning(
                "Not Enough Files", "Please add at least 2 PDF files to combine!"
            )
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
        if self.combiner.combine(self.pdf_files, output_file):
            messagebox.showinfo(
                "Success! ✅", f"PDFs combined successfully!\n\nSaved to:\n{output_file}"
            )

            # Ask if user wants to open the folder
            if messagebox.askyesno(
                "Open Folder?", "Would you like to open the folder containing the file?"
            ):
                folder = str(Path(output_file).parent)
                if sys.platform == "win32":
                    import os

                    os.startfile(folder)
                elif sys.platform == "darwin":
                    subprocess.run(["open", folder], check=False)
                else:
                    subprocess.run(["xdg-open", folder], check=False)

    # ========== Rename Tab Methods ==========

    def _browse_rename_file(self) -> None:
        """Browse for a file to rename."""
        file = filedialog.askopenfilename(
            title="Select PDF File to Rename",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
        )

        if file:
            self.current_file_var.set(file)
            # Pre-fill the new name with current name (without extension)
            basename = Path(file).stem
            self.new_name_var.set(basename)

    def _rename_file(self) -> None:
        """Rename the selected file."""
        current_file = self.current_file_var.get()
        new_name = self.new_name_var.get().strip()

        if not current_file:
            messagebox.showwarning("No File", "Please select a PDF file first!")
            return

        if not new_name:
            messagebox.showwarning("No Name", "Please enter a new name for the file!")
            return

        current_file_path = Path(current_file)
        if not current_file_path.exists():
            messagebox.showerror("File Not Found", "The selected file no longer exists!")
            return

        # Sanitize filename - remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            new_name = new_name.replace(char, "_")

        # Create new path
        new_path = current_file_path.parent / f"{new_name}.pdf"

        # Check if target already exists
        if (
            new_path.exists()
            and str(new_path) != current_file
            and not messagebox.askyesno(
                "File Exists",
                f"A file named '{new_name}.pdf' already exists.\n\nDo you want to replace it?",
            )
        ):
            return

        try:
            current_file_path.rename(new_path)
            messagebox.showinfo(
                "Success! ✅", f"File renamed successfully!\n\nNew name:\n{new_name}.pdf"
            )

            # Update the UI
            self.current_file_var.set(str(new_path))

        except PermissionError:
            messagebox.showerror(
                "Permission Denied", "Cannot rename the file. It may be open in another program."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename file: {e!s}")


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
