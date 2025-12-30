.PHONY: help install dev lint format typecheck test build clean deploy all

# Default target
help:
	@echo "BuckUtils - PDF Helper"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Install development dependencies"
	@echo "  make lint       - Run ruff linter"
	@echo "  make format     - Format code with ruff"
	@echo "  make typecheck  - Run mypy type checker"
	@echo "  make test       - Run tests"
	@echo "  make build      - Build desktop executable with streamlit-desktop-app"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make deploy     - Build and prepare for distribution"
	@echo "  make all        - Run lint, typecheck, test, and build"

# Install production dependencies
install:
	uv pip install -e .

# Install development dependencies
dev:
	uv pip install -e ".[dev]"

# Run ruff linter
lint:
	uv run ruff check src/ tests/

# Format code with ruff
format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

# Run mypy type checker
typecheck:
	uv run mypy src/

# Run tests
test:
	uv run pytest tests/ -v

# Build Windows executable with streamlit-desktop-app (PyInstaller under the hood)
build:
	uv run streamlit-desktop-app build src/buckutils/app.py --name BuckUtils --pyinstaller-options --onefile --noconfirm --hidden-import pypdf --distpath dist --workpath build

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .mypy_cache/ .pytest_cache/ .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Build and prepare for distribution
deploy: clean lint typecheck test build
	@echo ""
	@echo "✅ Build complete!"
	@echo "📦 Executable is in dist/BuckUtils.exe"
	@echo ""

# Run all checks and build
all: lint typecheck test build
