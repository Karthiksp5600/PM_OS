"""Optional MaxCrawl MCP-backed connector for live web research."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from socket import timeout as SocketTimeout
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from productpilot.discovery.connectors.base import SourceConnector
from productpilot.discovery.schemas import NormalizedRecord, SourceName


class MaxCrawlConnector(SourceConnector):
    source_name = SourceName.MAXCRAWL.value

    def __init__(
        self,
        target: Optional[str] = None,
        targets: Optional[List[str]] = None,
        endpoint: Optional[str] = None,
        max_pages: int = 3,
        depth: int = 1,
        source_goal: int = 50,
        timeout_seconds: int = 90,
    ) -> None:
        self.target = target
        self.targets = [item.strip() for item in (targets or []) if item and item.strip()]
        self.endpoint = endpoint or os.getenv("MAXCRAWL_MCP_URL", "https://api.maxcrawl.com/mcp")
        self.max_pages = max_pages
        self.depth = depth
        self.source_goal = source_goal
        self.timeout_seconds = timeout_seconds

    def fetch(self) -> List[NormalizedRecord]:
        self._initialize()
        queries = self.targets or ([self.target] if self.target else [])
        if not queries:
            return []

        collected: Dict[str, NormalizedRecord] = {}
        for query in queries:
            try:
                payload = self._call_tool(query)
            except RuntimeError:
                continue
            for record in self._parse_records(payload, query):
                collected[record.content_hash] = record
            if len(collected) >= self.source_goal:
                break
        return list(collected.values())[: self.source_goal]

    def _initialize(self) -> None:
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "productpilot", "version": "0.1.0"},
            },
        }
        self._post(body)

    def _call_tool(self, query: str) -> dict:
        body = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "maxcrawl",
                "arguments": {
                    "target": query,
                    "maxPages": self.max_pages,
                    "depth": self.depth,
                },
            },
        }
        return self._post(body)

    def _post(self, body: dict) -> dict:
        request = Request(
            self.endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "accept": "application/json",
                "user-agent": "productpilot-maxcrawl/0.1 (+https://api.maxcrawl.com/mcp)",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError("MaxCrawl HTTP error: {0}".format(exc.code)) from exc
        except SocketTimeout as exc:
            raise RuntimeError("MaxCrawl timeout") from exc
        except URLError as exc:
            raise RuntimeError("MaxCrawl connection error: {0}".format(exc.reason)) from exc

    def _parse_records(self, payload: dict, query: str) -> List[NormalizedRecord]:
        result = payload.get("result", {})
        contents = result.get("content", [])
        text_chunks = [
            item.get("text", "")
            for item in contents
            if item.get("type") == "text" and item.get("text")
        ]
        if not text_chunks:
            return []

        report = "\n".join(text_chunks)
        matches = list(
            re.finditer(
                r"### Source #\d+: \[(?P<title>.*?)\]\((?P<url>https?://.*?)\)\n(?P<body>.*?)(?=\n---|\Z)",
                report,
                flags=re.DOTALL,
            )
        )
        records: List[NormalizedRecord] = []
        if not matches:
            content_hash = NormalizedRecord.build_content_hash(SourceName.MAXCRAWL, report, self.endpoint)
            records.append(
                NormalizedRecord(
                    source=SourceName.MAXCRAWL,
                    url=self.endpoint,
                    author_id_hash=sha256(self.endpoint.encode("utf-8")).hexdigest(),
                    timestamp=datetime.utcnow(),
                    text=report.strip(),
                    rating=None,
                    upvotes_likes=None,
                    raw_payload={"query": query, "payload": payload},
                    content_hash=content_hash,
                )
            )
            return records

        for match in matches:
            url = match.group("url").strip()
            title = match.group("title").strip()
            body_text = re.sub(r"\n+", " ", match.group("body")).strip()
            combined_text = "{0}. {1}".format(title, body_text)
            content_hash = NormalizedRecord.build_content_hash(SourceName.MAXCRAWL, combined_text, url)
            records.append(
                NormalizedRecord(
                    source=SourceName.MAXCRAWL,
                    url=url,
                    author_id_hash=sha256(url.encode("utf-8")).hexdigest(),
                    timestamp=datetime.utcnow(),
                    text=combined_text,
                    rating=None,
                    upvotes_likes=None,
                    raw_payload={"query": query, "title": title, "body": body_text},
                    content_hash=content_hash,
                )
            )
        return records


def load_maxcrawl_targets(base_dir: Path) -> List[str]:
    inline_targets = os.getenv("MAXCRAWL_TARGETS", "").strip()
    if inline_targets:
        return [item.strip() for item in inline_targets.split("||") if item.strip()]

    targets_file = Path(
        os.getenv(
            "MAXCRAWL_TARGETS_FILE",
            str(base_dir / "productpilot" / "discovery" / "data" / "maxcrawl_targets.txt"),
        )
    )
    file_targets: List[str] = []
    if targets_file.exists():
        file_targets = [
            line.strip()
            for line in targets_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    generated_targets = build_generated_maxcrawl_targets()
    combined: List[str] = []
    seen = set()
    for item in file_targets + generated_targets:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        combined.append(normalized)
    return combined


def build_generated_maxcrawl_targets() -> List[str]:
    categories = [
        "footwear",
        "sneakers",
        "heels",
        "ethnic wear",
        "kurtas",
        "dresses",
        "tops",
        "jackets",
        "handbags",
        "festive outfits",
    ]
    frictions = [
        "fit doubt",
        "review gap",
        "customer photo gap",
        "styling uncertainty",
        "comparison paralysis",
        "occasion mismatch",
        "wishlist overload",
        "social validation",
        "bookmark behavior",
        "decision fatigue",
    ]
    segments = [
        "new users",
        "repeat shoppers",
        "budget shoppers under 2000",
        "fashion shoppers in India",
        "wishlist users",
    ]
    verbs = [
        "do not purchase",
        "delay purchase",
        "research elsewhere before buying",
        "leave items in wishlist",
    ]
    templates = [
        "why {segment} on Myntra wishlist {category} and {verb} because of {friction}",
        "fashion ecommerce {category} wishlist {friction} causing users to {verb}",
        "Myntra saved {category} {friction} why users {verb}",
        "{segment} saving {category} on fashion apps but {verb} due to {friction}",
    ]
    generated: List[str] = []
    for category in categories:
        for friction in frictions:
            for segment in segments:
                for verb in verbs:
                    for template in templates:
                        generated.append(
                            template.format(
                                category=category,
                                friction=friction,
                                segment=segment,
                                verb=verb,
                            )
                        )
    return generated
