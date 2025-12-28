# BuckUtils Copilot Instructions

- Use **uv** for Python workflows. Prefer `uv pip install -e ".[dev]"` for setup, `uv run` for running tools, and `uvx` for ad-hoc CLIs.
- Prefer **Makefile** targets to run tasks:
  - `make dev` to install dependencies
  - `make lint` / `make typecheck` / `make test` for validation
  - `make build` to package the app
- Do not introduce alternate tooling when a Makefile target exists.
