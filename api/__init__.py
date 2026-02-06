"""API entrypoint for SQLite backend, portable fallback for redis_testing."""

from .main import app

__all__ = ["app"]
