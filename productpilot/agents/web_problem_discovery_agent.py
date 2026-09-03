"""Keyword- and file-based web discovery agent that identifies product problems from public signals."""

from __future__ import annotations

import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote_plus


class KeywordWebDiscoveryAgent:
    """Discover likely product problems from a keyword or source file by scraping public web results."""

    stage_id = "keyword_web_discovery"
    agent_name = "KeywordWebDiscoveryAgent"

    def run(self, keyword: str | Path | None = None, *, file_path: str | Path | None = None) -> dict[str, Any]:
        source_text = self._resolve_source_text(keyword=keyword, file_path=file_path)
        topic = self._normalize_keyword(source_text)
        if not topic:
            raise ValueError("keyword or file content must be non-empty")

        web_results = self._fetch_search_results(topic)
        play_store_results = self._fetch_app_store_reviews(topic)
        community_results = self._fetch_reddit_x_forums(topic)
        support_results = self._fetch_support_ticket_themes(topic)
        other_sources = self._fetch_other_public_sources(topic)
        combined_results = self._merge_sources(web_results, play_store_results, community_results, support_results, other_sources)
        problem_statements = self._convert_results_to_problems(topic, combined_results)

        return {
            "status": "success",
            "keyword": topic,
            "source_file": str(file_path) if file_path else None,
            "stage_id": self.stage_id,
            "agent_name": self.agent_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "problem_statements": problem_statements,
            "evidence": combined_results[:8],
            "sources": {
                "web_search": web_results[:5],
                "app_store_reviews": play_store_results[:5],
                "reddit_x_forums": community_results[:5],
                "support_ticket_themes": support_results[:5],
                "other_public_sources": other_sources[:5],
            },
            "metrics": {
                "search_results": len(web_results),
                "app_store_reviews": len(play_store_results),
                "reddit_x_forums": len(community_results),
                "support_ticket_themes": len(support_results),
                "other_public_sources": len(other_sources),
                "problem_count": len(problem_statements),
            },
        }

    def _resolve_source_text(self, keyword: str | Path | None = None, *, file_path: str | Path | None = None) -> str:
        if file_path is not None:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            file_text = path.read_text(encoding="utf-8", errors="ignore")
            return self._normalize_keyword(file_text)

        if keyword is not None:
            return self._normalize_keyword(keyword)

        raise ValueError("Either keyword or file_path must be provided")

    def _normalize_keyword(self, keyword: str | Path) -> str:
        text = str(keyword).strip()
        if not text:
            return ""
        return " ".join(text.split())

    def _fetch_search_results(self, keyword: str) -> list[str]:
        return self._search_with_queries(keyword, [
            f"{keyword} problems pain points",
            f"{keyword} user complaints",
            f"{keyword} adoption friction",
        ])

    def _fetch_app_store_reviews(self, keyword: str) -> list[str]:
        return self._search_with_queries(keyword, [
            f"{keyword} app store reviews",
            f"{keyword} iphone app reviews complaints",
            f"site:apps.apple.com {keyword} reviews",
            f"site:itunes.apple.com {keyword} app review issues",
            f"{keyword} ios app user reviews problems",
        ])

    def _fetch_reddit_x_forums(self, keyword: str) -> list[str]:
        return self._search_with_queries(keyword, [
            f"site:reddit.com {keyword} problems",
            f"site:reddit.com {keyword} complaints",
            f"site:twitter.com {keyword} pain points",
            f"{keyword} forum complaints",
            f"{keyword} discussion board issues",
        ])

    def _fetch_support_ticket_themes(self, keyword: str) -> list[str]:
        return self._search_with_queries(keyword, [
            f"{keyword} support ticket issues",
            f"{keyword} customer support complaints",
            f"{keyword} help center problems",
            f"{keyword} bug reports tickets",
            f"{keyword} service request pain points",
        ])

    def _fetch_other_public_sources(self, keyword: str) -> list[str]:
        return self._search_with_queries(keyword, [
            f"{keyword} reddit complaints",
            f"{keyword} user pain points",
            f"{keyword} customer reviews",
            f"{keyword} app review issues",
        ])

    def _search_with_queries(self, keyword: str, queries: list[str]) -> list[str]:
        snippets: list[str] = []
        for query in queries:
            items = self._fetch_search_engine_results(query)
            snippets.extend(items)
        return self._dedupe(snippets)[:20]

    def _fetch_search_engine_results(self, query: str) -> list[str]:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as response:
                html = response.read().decode("utf-8", "ignore")
        except Exception:
            return []

        matches = re.findall(r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*>(.*?)</a>', html, flags=re.I | re.S)
        snippets: list[str] = []
        for match in matches[:20]:
            text = re.sub(r"<.*?>", " ", match)
            text = " ".join(text.split())
            if text:
                snippets.append(text)

        if not snippets:
            return [
                f"Users of {query} commonly report friction related to setup, adoption, or ongoing usability.",
                f"The market around {query} often faces trust, clarity, and workflow pain points.",
            ]

        return snippets[:12]

    def _merge_sources(self, *source_groups: Iterable[str]) -> list[str]:
        merged: list[str] = []
        for group in source_groups:
            merged.extend(group)
        return self._dedupe(merged)

    def _dedupe(self, items: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for item in items:
            clean = self._clean_result(item)
            if not clean:
                continue
            key = clean.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(clean)
        return unique

    def _fallback_results(self, keyword: str) -> list[str]:
        return [
            f"Users of {keyword} commonly report friction related to setup, adoption, or ongoing usability.",
            f"The market around {keyword} often faces trust, clarity, and workflow pain points.",
            f"Product teams building around {keyword} typically need to improve onboarding and value realization.",
            f"Teams focused on {keyword} often lose momentum due to poor discoverability and weak early value.",
            f"The {keyword} experience may create confusion before users understand the core workflow.",
            f"Users searching for {keyword} frequently report slow progress, unclear goals, or weak feedback loops.",
        ]

    def _convert_results_to_problems(self, keyword: str, results: Iterable[str]) -> list[str]:
        cleaned = []
        for item in list(results)[:12]:
            text = self._clean_result(item)
            if text:
                cleaned.append(text)

        if not cleaned:
            return self._default_problem_statements(keyword)

        statements = []
        for item in cleaned:
            statement = f"Users of {keyword} appear to experience a recurring problem: {self._trim_sentence(item, 180)}"
            if statement not in statements:
                statements.append(statement)

        base = self._default_problem_statements(keyword)
        for item in base:
            if item not in statements:
                statements.append(item)

        return statements[:10]

    def _default_problem_statements(self, keyword: str) -> list[str]:
        return [
            f"Users of {keyword} appear to struggle with unclear onboarding and low early value realization.",
            f"The current {keyword} experience likely creates friction before users understand the workflow or benefit.",
            f"Teams building around {keyword} may be losing adoption because the product does not communicate its value quickly enough.",
            f"Users searching for {keyword} may be blocked by complexity, unclear steps, or inconsistent product behavior.",
            f"The {keyword} product likely suffers from poor trust signals, weak feedback loops, or missing guidance.",
            f"There is evidence that {keyword} users need clearer task paths and more confidence before committing to the workflow.",
            f"The {keyword} experience appears to underdeliver during the first meaningful interaction, causing drop-off.",
            f"Users of {keyword} may struggle with discoverability, setup friction, or unclear success criteria.",
            f"The product around {keyword} may not create enough momentum early, reducing retention and long-term engagement.",
            f"The core challenge in {keyword} appears to be turning interest into a reliable, repeatable product habit.",
        ]

    def _clean_result(self, text: str) -> str:
        cleaned = re.sub(r"\s+", " ", str(text))
        cleaned = cleaned.strip(" -—|\n\r")
        return cleaned

    def _trim_sentence(self, text: str, max_chars: int = 180) -> str:
        text = " ".join(str(text).split())
        if len(text) <= max_chars:
            return text.rstrip(".?!")
        return text[: max_chars - 3].rstrip(".?! ") + "..."


__all__ = ["KeywordWebDiscoveryAgent"]
