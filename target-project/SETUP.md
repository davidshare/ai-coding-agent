# Environment Setup

This project uses `uv` for Python environment and dependency management.

## Requirements

- Python >= 3.11
- `uv` installed

## Setup

From the project root:

```bash
uv sync
```

This creates `.venv` and installs dependencies from `pyproject.toml` and `uv.lock`.

## Running Tests

```bash
uv run pytest -q
```

## Notes

- Dependencies are managed in `pyproject.toml`.
- The lock file is `uv.lock`.
- The virtual environment is `.venv`.