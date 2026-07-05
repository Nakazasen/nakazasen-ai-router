"""SQLite-backed router state store.

This store persists only current provider/model/key operational state. It does
not store prompts, raw API keys, headers, responses, or attempt logs.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from .state import KeyModelState, MemoryStateStore


class SQLiteStateStore(MemoryStateStore):
    """SQLite-backed state store suitable for multiple local workers."""

    def __init__(self, path: str | Path) -> None:
        super().__init__({})
        self.path = Path(path)
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def get_key_model_state(self, provider: str, model: str, key_id: str) -> KeyModelState:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                """
                SELECT provider, model, key_id, status, enabled, cooldown_until,
                       last_error_type, last_error_message, success_count,
                       failure_count, failure_streak, last_latency_ms,
                       last_success_at, last_failure_at
                FROM router_key_model_state
                WHERE provider = ? AND model = ? AND key_id = ?
                """,
                (provider, model, key_id),
            ).fetchone()
            if row is None:
                entry = KeyModelState(provider=provider, model=model, key_id=key_id)
                self._upsert(connection, entry)
                return entry
            return _row_to_state(row)

    def record_success(self, provider: str, model: str, key_id: str, *, latency_ms: int = 0) -> None:
        with self._lock, self._connect() as connection:
            entry = self.get_key_model_state(provider, model, key_id)
            entry.status = "healthy"
            entry.enabled = True
            entry.cooldown_until = 0.0
            entry.last_error_type = ""
            entry.last_error_message = ""
            entry.success_count += 1
            entry.failure_streak = 0
            entry.last_latency_ms = latency_ms
            entry.last_success_at = time.time()
            self._upsert(connection, entry)

    def record_failure(
        self,
        provider: str,
        model: str,
        key_id: str,
        *,
        error_type: str,
        error_message: str = "",
        latency_ms: int = 0,
        cooldown_until: float = 0.0,
        disable: bool = False,
    ) -> None:
        with self._lock, self._connect() as connection:
            entry = self.get_key_model_state(provider, model, key_id)
            entry.failure_count += 1
            entry.failure_streak += 1
            entry.last_error_type = str(error_type or "unknown_error")
            entry.last_error_message = _safe_message(error_message)
            entry.last_latency_ms = latency_ms
            entry.last_failure_at = time.time()
            if cooldown_until > 0:
                entry.cooldown_until = cooldown_until
                entry.status = "cooldown"
            else:
                entry.status = "failed"
            if disable:
                entry.enabled = False
                entry.status = "dead"
            self._upsert(connection, entry)

    def list_states(self) -> list[KeyModelState]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT provider, model, key_id, status, enabled, cooldown_until,
                       last_error_type, last_error_message, success_count,
                       failure_count, failure_streak, last_latency_ms,
                       last_success_at, last_failure_at
                FROM router_key_model_state
                ORDER BY provider, model, key_id
                """
            ).fetchall()
            return [_row_to_state(row) for row in rows]

    def save(self) -> None:
        return None

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _initialize(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS router_key_model_state (
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    key_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    enabled INTEGER NOT NULL,
                    cooldown_until REAL NOT NULL,
                    last_error_type TEXT NOT NULL,
                    last_error_message TEXT NOT NULL,
                    success_count INTEGER NOT NULL,
                    failure_count INTEGER NOT NULL,
                    failure_streak INTEGER NOT NULL,
                    last_latency_ms INTEGER NOT NULL,
                    last_success_at REAL NOT NULL,
                    last_failure_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (provider, model, key_id)
                )
                """
            )

    @staticmethod
    def _upsert(connection: sqlite3.Connection, entry: KeyModelState) -> None:
        connection.execute(
            """
            INSERT INTO router_key_model_state (
                provider, model, key_id, status, enabled, cooldown_until,
                last_error_type, last_error_message, success_count,
                failure_count, failure_streak, last_latency_ms,
                last_success_at, last_failure_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider, model, key_id) DO UPDATE SET
                status = excluded.status,
                enabled = excluded.enabled,
                cooldown_until = excluded.cooldown_until,
                last_error_type = excluded.last_error_type,
                last_error_message = excluded.last_error_message,
                success_count = excluded.success_count,
                failure_count = excluded.failure_count,
                failure_streak = excluded.failure_streak,
                last_latency_ms = excluded.last_latency_ms,
                last_success_at = excluded.last_success_at,
                last_failure_at = excluded.last_failure_at,
                updated_at = excluded.updated_at
            """,
            (
                entry.provider,
                entry.model,
                entry.key_id,
                entry.status,
                int(entry.enabled),
                entry.cooldown_until,
                entry.last_error_type,
                entry.last_error_message,
                entry.success_count,
                entry.failure_count,
                entry.failure_streak,
                entry.last_latency_ms,
                entry.last_success_at,
                entry.last_failure_at,
                time.time(),
            ),
        )


def _row_to_state(row: sqlite3.Row | tuple) -> KeyModelState:
    return KeyModelState(
        provider=str(row[0]),
        model=str(row[1]),
        key_id=str(row[2]),
        status=str(row[3]),
        enabled=bool(row[4]),
        cooldown_until=float(row[5]),
        last_error_type=str(row[6]),
        last_error_message=str(row[7]),
        success_count=int(row[8]),
        failure_count=int(row[9]),
        failure_streak=int(row[10]),
        last_latency_ms=int(row[11]),
        last_success_at=float(row[12]),
        last_failure_at=float(row[13]),
    )


def _safe_message(message: str) -> str:
    compact = " ".join(str(message or "").replace("\r", " ").replace("\n", " ").split())
    return compact[:200]
