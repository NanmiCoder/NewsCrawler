# -*- coding: utf-8 -*-
"""Command-line helpers for running the News Extractor backend."""
from __future__ import annotations

import click
import uvicorn


@click.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Host binding for the API server")
@click.option("--port", default=8000, show_default=True, help="Port for the API server")
@click.option("--reload/--no-reload", default=False, help="Enable auto-reload (development only)")
def main(host: str, port: int, reload: bool) -> None:
    """Start the FastAPI backend."""

    uvicorn.run(
        "news_extractor_backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":  # pragma: no cover
    main()
