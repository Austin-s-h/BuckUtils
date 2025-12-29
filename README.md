# BuckUtils 🔧

A simple, grandpa-friendly PDF utility for Windows. Easily combine PDF files with per-page control and a clean, easy-to-use Streamlit interface.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features ✨

- **📄 Combine PDFs** - Merge multiple PDF files into a single document
- **🧩 Page Previews & Reordering** - Import every page, see live text/image previews, and reorder with simple buttons
- **🖥️ Streamlit UI** - Web-based interface that stays responsive without extra pop-up windows
- **📦 Packaging-friendly** - Built to run locally or bundle with PyInstaller

## Quick Start 🚀

### Option 1: Run from Source (recommended)

1. **Install Python 3.8+** from [python.org](https://www.python.org/downloads/)
2. **Install the package:**
   ```bash
   pip install .
   ```
3. **Run the application (opens Streamlit in your browser):**
   ```bash
   python -m buckutils
   ```

### Option 2: Build a Windows Executable

1. **Install Python 3.8+** from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation

## How to Use 📖

1. Click **"Upload one or more PDFs"** to add files.
2. Use **Move Up/Move Down** to reorder pages across files.
3. Review the live image and text preview on the right.
4. Click **Generate PDF** and then **Download combined PDF**.

## Building the Windows Executable 🛠️

To create a standalone `.exe` file that can run on any Windows computer:

1. **Install development dependencies:**
   ```bash
   pip install ".[dev]"
   ```

2. **Build the executable:**
   ```bash
   make build
   ```
   
   Or manually:
   ```bash
   pyinstaller buckutils.spec
   ```

3. **Find your executable:**
   The `BuckUtils.exe` file will be in the `dist/` folder

## PDF Backend

BuckUtils now uses **pypdf** for combining and **pypdfium2** for page previews. Both are bundled when you install the project or build the executable.

## Development

This project uses modern Python tooling:

```bash
# Install development dependencies
make dev

# Run linter
make lint

# Run type checker
make typecheck

# Run tests
make test

# Build executable
make build

# Full deploy (lint, typecheck, test, build)
make deploy
```

## System Requirements 💻

- **Windows 7/8/10/11**
- **Python 3.8+** (if running from source)
- **~50 MB disk space** for the executable

## Troubleshooting 🔧

### "No PDF library found" error
Install pypdf:
```bash
pip install pypdf
```

### The app won't start
- Make sure Python is installed and in your PATH
- Try running from command line to see error messages:
  ```bash
  python -m buckutils
  ```

### Permission denied when renaming
- Make sure the PDF isn't open in another program
- Try closing Adobe Reader or other PDF viewers

## License 📄

MIT License - feel free to use and modify!

## Author

Made with ❤️ for Dad
