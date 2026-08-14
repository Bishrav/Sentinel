"""SQLite-backed incident persistence for single-service deployments."""

import sqlite3
from collections.abc import Iterable
from pathlib import Path
from threading import Lock

from sentinel_detection.models import Incident


class SqliteIncidentStore:
    """Persist complete incident projections with deterministic upserts."""

    def __init__(self, path: str | Path) -> None:
        self._path = str(path)
        self._lock = Lock()
        self._connection = sqlite3.connect(self._path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                fingerprint TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def upsert(self, incident: Incident) -> None:
        payload = incident.model_dump_json()
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO incidents (fingerprint, payload) VALUES (?, ?)
                ON CONFLICT(fingerprint) DO UPDATE SET payload = excluded.payload
                """,
                (incident.fingerprint, payload),
            )
            self._connection.commit()

    def get(self, fingerprint: str) -> Incident | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT payload FROM incidents WHERE fingerprint = ?", (fingerprint,)
            ).fetchone()
        return Incident.model_validate_json(row[0]) if row else None

    def all(self) -> Iterable[Incident]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT payload FROM incidents ORDER BY fingerprint"
            ).fetchall()
        return tuple(Incident.model_validate_json(row[0]) for row in rows)

    def close(self) -> None:
        with self._lock:
            self._connection.close()
