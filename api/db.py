"""Persistência SQLite para API de fallback."""

import sqlite3
from pathlib import Path
from typing import Any

_DEFAULT_DB_PATH = Path(__file__).resolve().parent / "fallback.db"

_USER_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    cpf TEXT NOT NULL,
    age INTEGER NOT NULL DEFAULT 0,
    weight REAL NOT NULL DEFAULT 0,
    height REAL NOT NULL DEFAULT 0
);
"""

_PRODUCT_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL DEFAULT 0
);
"""


class Database:
    """Wrapper de conexão e schema SQLite."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self._path: Path | str = db_path or _DEFAULT_DB_PATH

    def get_connection(self) -> sqlite3.Connection:
        """Abre uma nova conexão com o banco."""
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        """Cria as tabelas se não existirem."""
        conn = self.get_connection()
        try:
            conn.executescript(_USER_TABLE + _PRODUCT_TABLE)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        """Converte uma linha do banco para dicionário."""
        return dict(row)
