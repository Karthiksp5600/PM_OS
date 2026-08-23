"""Crawlee for Python runner used by the discovery connector."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
sys.path = [entry for entry in sys.path if Path(entry or ".").resolve() != CURRENT_DIR]

from crawlee import ConcurrencySettings
from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext

RAW_INPUT = json.loads(__import__("os").environ.get("CRAWLEE_INPUT_JSON", "{}"))
START_URLS = list(RAW_INPUT.get("startUrls", []))
SOURCE_GOAL = int(RAW_INPUT.get("sourceGoal", 500))
MAX_REQUESTS = int(RAW_INPUT.get("maxRequests", 250))
MAX_CONCURRENCY = int(RAW_INPUT.get("maxConcurrency", 8))


def normalize_whitespace(value: str) -> str:
    return " ".join(str(value or "").split()).strip()


def is_search_page(url: str) -> bool:
    return "html.duckduckgo.com/html/" in url


def is_relevant_text(text: str) -> bool:
    lowered = text.lower()
    keywords = [
        "wishlist",
        "wish list",
        "saved item",
        "saved product",
        "fashion",
        "ecommerce",
        "shopper",
        "purchase",
        "buy later",
    ]
    return any(keyword in lowered for keyword in keywords)


async def run() -> None:
    collected: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    seen_texts: set[str] = set()

    crawler = BeautifulSoupCrawler(
        max_requests_per_crawl=MAX_REQUESTS,
        concurrency_settings=ConcurrencySettings(
            desired_concurrency=MAX_CONCURRENCY,
            max_concurrency=MAX_CONCURRENCY,
        ),
    )

    async def push_record(url: str, title: str, text: str, source_page: str) -> None:
        normalized_text = normalize_whitespace(text).lower()
        if not url or not normalized_text or len(normalized_text) < 80:
            return
        if url in seen_urls or normalized_text in seen_texts:
            return
        if not is_relevant_text(normalized_text):
            return
        seen_urls.add(url)
        seen_texts.add(normalized_text)
        collected.append(
            {
                "url": url,
                "title": normalize_whitespace(title),
                "text": normalize_whitespace(text),
                "sourcePage": source_page,
            }
        )

    @crawler.router.default_handler
    async def request_handler(context: BeautifulSoupCrawlingContext) -> None:
        if len(collected) >= SOURCE_GOAL:
            return

        loaded_url = str(context.request.loaded_url or context.request.url)
        if is_search_page(loaded_url):
            links = []
            for anchor in context.soup.select("a.result__a"):
                href = anchor.get("href")
                if not href:
                    continue
                links.append(href)
                if len(links) >= 10:
                    break
            if links:
                await crawler.add_requests(links)
            return

        title_tag = context.soup.title.string if context.soup.title and context.soup.title.string else ""
        headings = [normalize_whitespace(tag.get_text()) for tag in context.soup.select("h1, h2, h3")]
        paragraphs = [normalize_whitespace(tag.get_text()) for tag in context.soup.select("p")]
        meaningful_paragraphs = [item for item in paragraphs if len(item) > 40][:12]
        content = " ".join([item for item in headings[:4] + meaningful_paragraphs if item])
        title = normalize_whitespace(title_tag or (headings[0] if headings else ""))
        if content:
            await push_record(
                url=loaded_url,
                title=title,
                text="{0}. {1}".format(title, content) if title else content,
                source_page=str(context.request.url),
            )
            await context.enqueue_links(strategy="same-origin")

    await crawler.run(START_URLS)
    print(json.dumps(collected[:SOURCE_GOAL]))


if __name__ == "__main__":
    asyncio.run(run())
