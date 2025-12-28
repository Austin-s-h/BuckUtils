# BuckUtils 🔧

A simple, grandpa-friendly PDF utility for Windows. Easily combine and rename PDF files with a clean, easy-to-use interface.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features ✨

- **📄 Combine PDFs** - Merge multiple PDF files into a single document
- **✏️ Rename PDFs** - Easily rename PDF files with a simple interface
- **🖥️ Clean UI** - Large buttons and clear text, designed for ease of use
- **📦 Minimal Dependencies** - Works with just Python and pypdf

## Quick Start 🚀

### Option 1: Run the Windows Executable (Easiest)

1. Download `BuckUtils.exe` from the [Releases](../../releases) page
2. Double-click to run - no installation needed!

### Option 2: Run from Source

1. **Install Python 3.8+** from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation

2. **Install the package:**
   ```bash
   pip install .
   ```

3. **Run the application:**
   ```bash
   python -m buckutils
   ```

## How to Use 📖

### Combining PDFs

1. Click the **"Combine PDFs"** tab
2. Click **"+ Add PDF Files"** to select your PDF files
3. Use **"⬆️ Move Up"** and **"⬇️ Move Down"** to arrange the order
4. Click **"🔗 COMBINE PDFs"**
5. Choose where to save your combined PDF
6. Done! ✅

### Renaming PDFs

1. Click the **"Rename PDF"** tab
2. Click **"📂 Browse for PDF..."** to select a file
3. Type the new name in the text box
4. Click **"✏️ RENAME FILE"**
5. Done! ✅

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

## PDF Backend Options

BuckUtils can work with two different PDF backends:

| Backend | Installation | Notes |
|---------|-------------|-------|
| **pypdf** (Recommended) | `pip install pypdf` | Fast, pure Python, no external dependencies |
| **Ghostscript** | [Download](https://ghostscript.com) | Fallback option if pypdf isn't available |

The app automatically detects which backend is available and uses it.

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
