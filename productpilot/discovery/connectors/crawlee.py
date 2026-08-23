"""Optional Crawlee-for-Python-backed live web connector."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import List, Optional
from urllib.parse import quote_plus

from productpilot.discovery.connectors.base import SourceConnector
from productpilot.discovery.connectors.maxcrawl import load_maxcrawl_targets
from productpilot.discovery.schemas import NormalizedRecord, SourceName


class CrawleeConnector(SourceConnector):
    source_name = SourceName.CRAWLEE.value

    def __init__(
        self,
        start_urls: Optional[List[str]] = None,
        queries: Optional[List[str]] = None,
        source_goal: int = 500,
        max_requests: int = 250,
        max_concurrency: int = 8,
        timeout_seconds: int = 120,
        python_bin: Optional[str] = None,
        runner_path: Optional[str | Path] = None,
    ) -> None:
        self.start_urls = [item.strip() for item in (start_urls or []) if item and item.strip()]
        self.queries = [item.strip() for item in (queries or []) if item and item.strip()]
        self.source_goal = source_goal
        self.max_requests = max_requests
        self.max_concurrency = max_concurrency
        self.timeout_seconds = timeout_seconds
        default_python = str(Path(__file__).resolve().parents[3] / ".venv-crawlee" / "bin" / "python")
        self.python_bin = python_bin or os.getenv(
            "CRAWLEE_PYTHON_BIN",
            default_python if Path(default_python).exists() else "python3.11",
        )
        self.runner_path = Path(runner_path) if runner_path else Path(__file__).with_name("crawlee_runner.py")

    def fetch(self) -> List[NormalizedRecord]:
        crawl_start_urls = list(self.start_urls)
        if not crawl_start_urls and self.queries:
            crawl_start_urls = [
                "https://html.duckduckgo.com/html/?q={0}".format(quote_plus(query))
                for query in self.queries[: min(len(self.queries), int(os.getenv("CRAWLEE_QUERY_LIMIT", "50")))]
            ]

        if not crawl_start_urls:
            return []

        payload = {
            "startUrls": crawl_start_urls,
            "sourceGoal": self.source_goal,
            "maxRequests": self.max_requests,
            "maxConcurrency": self.max_concurrency,
        }
        env = os.environ.copy()
        env["CRAWLEE_INPUT_JSON"] = json.dumps(payload)
        with tempfile.TemporaryDirectory(prefix="productpilot-crawlee-") as storage_dir:
            env["CRAWLEE_STORAGE_DIR"] = storage_dir

            process = subprocess.run(
                [self.python_bin, str(self.runner_path)],
                cwd=Path(__file__).resolve().parents[3],
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        if process.returncode != 0:
            stderr = (process.stderr or process.stdout or "").strip()
            raise RuntimeError(
                "Crawlee fetch failed: {0}. Install Crawlee with `python3.11 -m venv .venv-crawlee && .venv-crawlee/bin/pip install \"crawlee[beautifulsoup]\"` or set CRAWLEE_PYTHON_BIN.".format(
                    stderr or "unknown error"
                )
            )

        raw_records = json.loads(process.stdout or "[]")
        records: List[NormalizedRecord] = []
        for item in raw_records[: self.source_goal]:
            text = str(item.get("text", "")).strip()
            url = str(item.get("url", "")).strip()
            if not text or not url:
                continue
            content_hash = NormalizedRecord.build_content_hash(SourceName.CRAWLEE, text, url)
            records.append(
                NormalizedRecord(
                    source=SourceName.CRAWLEE,
                    url=url,
                    author_id_hash=sha256(url.encode("utf-8")).hexdigest(),
                    timestamp=datetime.utcnow(),
                    text=text,
                    rating=None,
                    upvotes_likes=None,
                    raw_payload=item,
                    content_hash=content_hash,
                )
            )
        return records


def load_crawlee_targets(base_dir: Path) -> List[str]:
    return load_maxcrawl_targets(base_dir)


def load_crawlee_start_urls(base_dir: Path) -> List[str]:
    inline_urls = os.getenv("CRAWLEE_START_URLS", "").strip()
    if inline_urls:
        return [item.strip() for item in inline_urls.split("||") if item.strip()]

    urls_file = Path(
        os.getenv(
            "CRAWLEE_START_URLS_FILE",
            str(base_dir / "productpilot" / "discovery" / "data" / "crawlee_start_urls.txt"),
        )
    )
    if not urls_file.exists():
        return []
    return [
        line.strip()
        for line in urls_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
