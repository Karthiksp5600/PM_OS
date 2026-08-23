"""Fashion forum/blog connector using local seed data."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

from productpilot.discovery.connectors.base import SourceConnector
from productpilot.discovery.schemas import NormalizedRecord, SourceName


class ForumConnector(SourceConnector):
    source_name = SourceName.FORUM.value

    def __init__(self, seed_path: str | Path) -> None:
        self.seed_path = Path(seed_path)

    def fetch(self) -> list[NormalizedRecord]:
        payload = json.loads(self.seed_path.read_text(encoding="utf-8"))
        records: list[NormalizedRecord] = []
        for item in payload:
            author_hash = sha256(item["author"].encode("utf-8")).hexdigest()
            content_hash = NormalizedRecord.build_content_hash(SourceName.FORUM, item["text"], item["url"])
            records.append(
                NormalizedRecord(
                    source=SourceName.FORUM,
                    url=item["url"],
                    author_id_hash=author_hash,
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    text=item["text"],
                    rating=None,
                    upvotes_likes=item.get("likes"),
                    raw_payload=item,
                    content_hash=content_hash,
                )
            )
        return records
