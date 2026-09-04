"""Optional Myntra-specific Kaggle dataset connectors."""

from __future__ import annotations

import csv
import gzip
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.request import Request, urlopen

from productpilot.discovery.connectors.base import SourceConnector
from productpilot.discovery.schemas import NormalizedRecord, SourceName


TEXT_KEYS = (
    "content",
    "review",
    "review description",
    "reviewdescription",
    "comment",
    "body",
    "description",
    "productdescription",
    "review text",
    "review_text",
    "about",
    "details",
    "summary",
)
TITLE_KEYS = (
    "review title",
    "reviewtitle",
    "product name",
    "product_name",
    "name",
    "title",
    "product",
)
BRAND_KEYS = ("brand", "brand name", "brand_name")
URL_KEYS = ("url", "product_url", "link", "product link")
PRICE_KEYS = ("price", "selling price", "final selling price", "mrp", "discount price")
RATING_KEYS = ("score", "rating", "ratings", "average rating", "star rating")
LIKES_KEYS = ("thumbsupcount", "thumbs up count", "number of ratings", "rating count", "likes", "review count", "reviews")
TIMESTAMP_KEYS = ("at", "date", "review date", "reviewdate", "created_at", "timestamp")


class KaggleMyntraConnector(SourceConnector):
    def __init__(
        self,
        source: SourceName,
        dataset_url: str,
        local_path: str | Path | None,
        fallback_author: str,
        remote_url: str | None = None,
    ) -> None:
        self.source = source
        self.source_name = source.value
        self.dataset_url = dataset_url
        self.local_path = Path(local_path) if local_path else None
        self.fallback_author = fallback_author
        self.remote_url = remote_url.strip() if remote_url else None

    def fetch(self) -> list[NormalizedRecord]:
        rows = list(self._load_rows())
        records: list[NormalizedRecord] = []
        for index, row in enumerate(rows):
            normalized = {self._normalize_key(key): value for key, value in row.items()}
            title = self._first_value(normalized, TITLE_KEYS)
            description = self._first_value(normalized, TEXT_KEYS)
            brand = self._first_value(normalized, BRAND_KEYS)
            price = self._first_value(normalized, PRICE_KEYS)
            rating = self._parse_float(self._first_value(normalized, RATING_KEYS))
            likes = self._parse_int(self._first_value(normalized, LIKES_KEYS))
            timestamp = self._parse_timestamp(self._first_value(normalized, TIMESTAMP_KEYS)) or datetime.utcnow()
            url_seed = self.remote_url or self.dataset_url
            url = self._first_value(normalized, URL_KEYS) or "{0}#row-{1}".format(url_seed, index + 1)
            text = self._build_text(title=title, description=description, brand=brand, price=price, normalized=normalized)
            if not text:
                continue
            author_seed = (
                self._first_value(normalized, ("user name", "username", "user", "author", "reviewer"))
                or brand
                or self.fallback_author
            )
            content_hash = NormalizedRecord.build_content_hash(self.source, text, url)
            records.append(
                NormalizedRecord(
                    source=self.source,
                    url=url,
                    author_id_hash=sha256(author_seed.encode("utf-8")).hexdigest(),
                    timestamp=timestamp,
                    text=text,
                    rating=rating,
                    upvotes_likes=likes,
                    raw_payload=row,
                    content_hash=content_hash,
                )
            )
        return records

    def _load_rows(self) -> Iterable[Dict[str, str]]:
        if self.local_path and self.local_path.exists():
            yield from self._load_rows_from_path(self.local_path)
            return
        if self.remote_url:
            yield from self._load_rows_from_remote(self.remote_url)
            return
        raise ValueError("No local file or remote URL configured for {0}".format(self.source_name))

    def _load_rows_from_path(self, path: Path) -> Iterable[Dict[str, str]]:
        filename = path.name.lower()
        if filename.endswith((".csv", ".csv.gz")):
            if filename.endswith(".gz"):
                handle = gzip.open(path, mode="rt", encoding="utf-8", newline="")
            else:
                handle = path.open(mode="r", encoding="utf-8", newline="")
            with handle:
                yield from csv.DictReader(handle)
            return
        if filename.endswith((".json", ".json.gz")):
            if filename.endswith(".gz"):
                handle = gzip.open(path, mode="rt", encoding="utf-8")
            else:
                handle = path.open(mode="r", encoding="utf-8")
            with handle:
                payload = json.load(handle)
            yield from self._coerce_row_dicts(payload)
            return
        if filename.endswith(".jsonl"):
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                yield from self._coerce_row_dicts(item)
            return
        raise ValueError("Unsupported Kaggle dataset format: {0}".format(path.name))

    def _load_rows_from_remote(self, remote_url: str) -> Iterable[Dict[str, str]]:
        request = Request(remote_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
        if remote_url.lower().endswith(".jsonl"):
            for line in payload.splitlines():
                line = line.strip()
                if not line:
                    continue
                yield from self._coerce_row_dicts(json.loads(line))
            return
        if remote_url.lower().endswith(".csv"):
            yield from csv.DictReader(payload.splitlines())
            return
        yield from self._coerce_row_dicts(json.loads(payload))

    def _coerce_row_dicts(self, payload: object) -> Iterable[Dict[str, str]]:
        if isinstance(payload, list):
            for item in payload:
                yield from self._coerce_row_dicts(item)
            return
        if isinstance(payload, dict):
            scalar_items = {
                str(key): "" if value is None else str(value)
                for key, value in payload.items()
                if not isinstance(value, (dict, list))
            }
            if scalar_items:
                yield scalar_items
            for value in payload.values():
                if isinstance(value, (dict, list)):
                    yield from self._coerce_row_dicts(value)
            return

    def _build_text(
        self,
        title: str,
        description: str,
        brand: str,
        price: str,
        normalized: Dict[str, str],
    ) -> str:
        details: list[str] = []
        if title:
            details.append(title)
        user_name = normalized.get("user name") or normalized.get("username")
        if user_name:
            details.append("User: {0}".format(user_name))
        if brand:
            details.append("Brand: {0}".format(brand))
        if price:
            details.append("Price: {0}".format(price))
        if description:
            details.append(description)
        score = normalized.get("score")
        if score:
            details.append("Score: {0}".format(score))
        app_version = normalized.get("app version") or normalized.get("review created version")
        if app_version:
            details.append("App version: {0}".format(app_version))
        reply = normalized.get("reply content") or normalized.get("developer response")
        if reply:
            details.append("Developer reply: {0}".format(reply))

        category = normalized.get("category") or normalized.get("sub category") or normalized.get("gender")
        colour = normalized.get("color") or normalized.get("colour")
        discount = normalized.get("discount (%)") or normalized.get("discount")
        if category:
            details.append("Category: {0}".format(category))
        if colour:
            details.append("Colour: {0}".format(colour))
        if discount:
            details.append("Discount: {0}".format(discount))

        if not details:
            fallback_values = [
                value.strip()
                for value in normalized.values()
                if isinstance(value, str) and value.strip()
            ]
            details = fallback_values[:5]
        return ". ".join(item for item in details if item).strip()

    def _first_value(self, row: Dict[str, str], keys: Iterable[str]) -> str:
        for key in keys:
            value = row.get(self._normalize_key(key), "")
            if value and value.strip():
                return value.strip()
        return ""

    def _normalize_key(self, key: str) -> str:
        return " ".join(str(key).strip().lower().replace("_", " ").split())

    def _parse_float(self, value: str) -> Optional[float]:
        if not value:
            return None
        cleaned = value.replace(",", "").replace("₹", "").replace("$", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _parse_int(self, value: str) -> Optional[int]:
        if not value:
            return None
        digits = "".join(character for character in value if character.isdigit())
        if not digits:
            return None
        return int(digits)

    def _parse_timestamp(self, value: str) -> Optional[datetime]:
        if not value:
            return None
        cleaned = value.strip().replace("Z", "+00:00")
        for parser in (datetime.fromisoformat,):
            try:
                return parser(cleaned)
            except ValueError:
                continue
        known_formats = (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%b %d, %Y",
            "%B %d, %Y",
        )
        for fmt in known_formats:
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue
        return None


def load_myntra_kaggle_connectors(base_dir: Path) -> list[SourceConnector]:
    data_dir = base_dir / "productpilot" / "discovery" / "data" / "kaggle_myntra"
    configs = [
        {
            "source": SourceName.KAGGLE_MYNTRA_APP_REVIEWS,
            "dataset_url": "https://www.kaggle.com/datasets/jocelyndumlao/shoppingappreviews-dataset",
            "filenames": (
                "myntra-shopping-app-reviews.json.gz",
                "myntra-shopping-app-reviews.json",
                "myntra-shopping-app-reviews.csv",
                "myntra-shopping-app-reviews.jsonl",
                "Myntra.json.gz",
                "Myntra.json",
                "Myntra.csv",
            ),
            "url_filenames": ("myntra-shopping-app-reviews.url",),
            "fallback_author": "kaggle-myntra-app-reviews",
        },
        {
            "source": SourceName.KAGGLE_MYNTRA_FASHION,
            "dataset_url": "https://www.kaggle.com/datasets/manishmathias/myntra-fashion-dataset",
            "filenames": ("myntra-fashion-dataset.csv", "myntra-fashion-dataset.json", "myntra-fashion-dataset.jsonl"),
            "fallback_author": "kaggle-myntra-fashion",
        },
        {
            "source": SourceName.KAGGLE_MYNTRA_FASHION_PRODUCTS,
            "dataset_url": "https://www.kaggle.com/datasets/nirokey/myntra-fashion-products",
            "filenames": ("myntra-fashion-products.csv", "myntra-fashion-products.json", "myntra-fashion-products.jsonl"),
            "fallback_author": "kaggle-myntra-fashion-products",
        },
        {
            "source": SourceName.KAGGLE_MYNTRA_SALES,
            "dataset_url": "https://www.kaggle.com/datasets/skmewati/myntra-sales-dataset",
            "filenames": ("myntra-sales-dataset.csv", "myntra-sales-dataset.json", "myntra-sales-dataset.jsonl"),
            "fallback_author": "kaggle-myntra-sales",
        },
        {
            "source": SourceName.KAGGLE_MYNTRA_FASHION_PRODUCT,
            "dataset_url": "https://www.kaggle.com/datasets/djagatiya/myntra-fashion-product-dataset",
            "filenames": ("myntra-fashion-product-dataset.csv", "myntra-fashion-product-dataset.json", "myntra-fashion-product-dataset.jsonl"),
            "fallback_author": "kaggle-myntra-fashion-product",
        },
        {
            "source": SourceName.KAGGLE_MYNTRA_PRODUCTS,
            "dataset_url": "https://www.kaggle.com/datasets/ronakbokaria/myntra-products-dataset/versions/1",
            "filenames": ("myntra-products-dataset.csv", "myntra-products-dataset.json", "myntra-products-dataset.jsonl"),
            "fallback_author": "kaggle-myntra-products",
        },
    ]

    connectors: list[SourceConnector] = []
    for config in configs:
        matched_path = next((data_dir / filename for filename in config["filenames"] if (data_dir / filename).exists()), None)
        remote_url = None
        for url_filename in config.get("url_filenames", ()):
            url_path = data_dir / url_filename
            if url_path.exists():
                remote_url = url_path.read_text(encoding="utf-8").strip()
                if remote_url:
                    break
        if not matched_path and not remote_url:
            continue
        connectors.append(
            KaggleMyntraConnector(
                source=config["source"],
                dataset_url=config["dataset_url"],
                local_path=matched_path,
                fallback_author=config["fallback_author"],
                remote_url=remote_url,
            )
        )
    return connectors
