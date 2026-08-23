"""SQLite storage for discovery pipeline artifacts."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional, Union

from productpilot.discovery.schemas import ClassifiedRecord, EvidenceChunk, NormalizedRecord, OpportunityRecord


class DiscoverySQLiteStore:
    def __init__(self, db_path: Union[str, Path]) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS raw_records (
                    content_hash TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    url TEXT NOT NULL,
                    author_id_hash TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    text TEXT NOT NULL,
                    rating REAL,
                    upvotes_likes INTEGER,
                    raw_payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS classified_records (
                    content_hash TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    chunk_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    text TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS opportunities (
                    name TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    retrieved_chunks TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    feedback TEXT,
                    correction TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS run_metadata (
                    key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )

    def reset_pipeline_data(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM raw_records")
            conn.execute("DELETE FROM classified_records")
            conn.execute("DELETE FROM evidence_chunks")
            conn.execute("DELETE FROM opportunities")

    def upsert_records(self, records: Iterable[NormalizedRecord]) -> None:
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO raw_records
                (content_hash, source, url, author_id_hash, timestamp, text, rating, upvotes_likes, raw_payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        record.content_hash,
                        record.source.value,
                        record.url,
                        record.author_id_hash,
                        record.timestamp.isoformat(),
                        record.text,
                        record.rating,
                        record.upvotes_likes,
                        json.dumps(record.raw_payload),
                    )
                    for record in records
                ],
            )

    def fetch_unclassified_records(self) -> List[NormalizedRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT r.content_hash, r.source, r.url, r.author_id_hash, r.timestamp, r.text, r.rating, r.upvotes_likes, r.raw_payload
                FROM raw_records r
                LEFT JOIN classified_records c ON r.content_hash = c.content_hash
                WHERE c.content_hash IS NULL
                """
            ).fetchall()
        records: List[NormalizedRecord] = []
        for row in rows:
            records.append(
                NormalizedRecord(
                    content_hash=row[0],
                    source=row[1],
                    url=row[2],
                    author_id_hash=row[3],
                    timestamp=row[4],
                    text=row[5],
                    rating=row[6],
                    upvotes_likes=row[7],
                    raw_payload=json.loads(row[8]),
                )
            )
        return records

    def upsert_classifications(self, records: Iterable[ClassifiedRecord]) -> None:
        with self._connect() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO classified_records (content_hash, payload) VALUES (?, ?)",
                [
                    (record.record.content_hash, record.model_dump_json())
                    for record in records
                ],
            )

    def fetch_classified_records(self) -> List[ClassifiedRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM classified_records").fetchall()
        return [ClassifiedRecord.model_validate_json(row[0]) for row in rows]

    def count_raw_records(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM raw_records").fetchone()
        return int(row[0]) if row else 0

    def count_classified_records(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM classified_records").fetchone()
        return int(row[0]) if row else 0

    def count_relevant_classified_records(self) -> int:
        records = self.fetch_classified_records()
        return sum(1 for record in records if record.classification.is_relevant)

    def count_evidence_chunks(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM evidence_chunks").fetchone()
        return int(row[0]) if row else 0

    def source_breakdown(self) -> Dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT source, COUNT(*) FROM raw_records GROUP BY source ORDER BY source"
            ).fetchall()
        return {str(source): int(count) for source, count in rows}

    def replace_evidence_chunks(self, chunks: Iterable[EvidenceChunk]) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM evidence_chunks")
            conn.executemany(
                "INSERT INTO evidence_chunks (chunk_id, chunk_type, source, source_url, text, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (chunk.chunk_id, chunk.chunk_type, chunk.source, chunk.source_url, chunk.text, json.dumps(chunk.metadata))
                    for chunk in chunks
                ],
            )

    def fetch_evidence_chunks(self) -> List[EvidenceChunk]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT chunk_id, chunk_type, source, source_url, text, metadata FROM evidence_chunks"
            ).fetchall()
        return [
            EvidenceChunk(
                chunk_id=row[0],
                chunk_type=row[1],
                source=row[2],
                source_url=row[3],
                text=row[4],
                metadata=json.loads(row[5]),
            )
            for row in rows
        ]

    def replace_opportunities(self, opportunities: Iterable[OpportunityRecord]) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM opportunities")
            conn.executemany(
                "INSERT INTO opportunities (name, payload) VALUES (?, ?)",
                [(opp.name, opp.model_dump_json()) for opp in opportunities],
            )

    def fetch_opportunities(self) -> List[OpportunityRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM opportunities").fetchall()
        return [OpportunityRecord.model_validate_json(row[0]) for row in rows]

    def log_chat(
        self,
        question: str,
        retrieved_chunks: List[str],
        answer: str,
        feedback: Optional[str] = None,
        correction: Optional[str] = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO chat_logs (question, retrieved_chunks, answer, feedback, correction) VALUES (?, ?, ?, ?, ?)",
                (question, json.dumps(retrieved_chunks), answer, feedback, correction),
            )

    def save_run_metadata(self, key: str, payload: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO run_metadata (key, payload) VALUES (?, ?)",
                (key, json.dumps(payload)),
            )

    def load_run_metadata(self, key: str) -> dict:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM run_metadata WHERE key = ?",
                (key,),
            ).fetchone()
        if not row:
            return {}
        return json.loads(row[0])
