from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path


class SQLiteCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )

    def get(self, key: str) -> object | None:
        now = datetime.now(UTC)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload, expires_at FROM cache_entries WHERE key = ?",
                (key,),
            ).fetchone()
        if row is None:
            return None
        payload, expires_at = row
        if datetime.fromisoformat(expires_at) <= now:
            self.delete(key)
            return None
        return json.loads(payload)

    def set(self, key: str, payload: object, ttl_seconds: int) -> None:
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO cache_entries(key, payload, expires_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    payload = excluded.payload,
                    expires_at = excluded.expires_at
                """,
                (key, json.dumps(payload), expires_at.isoformat()),
            )

    def delete(self, key: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
