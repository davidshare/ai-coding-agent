"""Entry point for the task management service.

Runs the FastAPI application defined in :mod:`src.api`.
"""

from __future__ import annotations

import uvicorn

from src.api import app


def main() -> None:
    """Start the uvicorn development server."""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()