"""
Shared utility functions for the ProductPilot Discovery Agent.

This module contains only pure utility functions.
No discovery business logic belongs here.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from datetime import UTC, datetime
from typing import Any, Iterable, Mapping


# ============================================================
# IDs
# ============================================================


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique identifier.

    Example:
        disc_3f3b21...
    """

    uid = uuid.uuid4().hex

    return f"{prefix}_{uid}" if prefix else uid


# ============================================================
# Time
# ============================================================


def utc_now() -> datetime:
    """Return timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def utc_timestamp() -> str:
    """Return ISO timestamp."""

    return utc_now().isoformat()


# ============================================================
# Hashing
# ============================================================


def sha256_hash(value: str) -> str:
    """Generate SHA256 hash."""

    return hashlib.sha256(value.encode()).hexdigest()


# ============================================================
# Text
# ============================================================


def normalize_whitespace(text: str) -> str:
    """Collapse duplicate whitespace."""

    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, max_chars: int = 200) -> str:
    """Safely truncate text."""

    text = normalize_whitespace(text)

    if len(text) <= max_chars:
        return text

    return text[: max_chars - 3] + "..."


def word_count(text: str) -> int:
    return len(text.split())


def sentence_count(text: str) -> int:
    return len(
        [
            s
            for s in re.split(r"[.!?]", text)
            if s.strip()
        ]
    )


# ============================================================
# JSON
# ============================================================


def safe_json_loads(value: str) -> Mapping[str, Any]:
    """
    Parse JSON safely.
    """

    try:
        result = json.loads(value)

        if isinstance(result, Mapping):
            return result

        return {}

    except Exception:

        return {}


def safe_json_dumps(obj: Any) -> str:

    return json.dumps(
        obj,
        indent=2,
        default=str,
        ensure_ascii=False,
    )


# ============================================================
# Confidence
# ============================================================


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:

    return max(minimum, min(maximum, value))


def average(values: Iterable[float]) -> float:

    values = list(values)

    if not values:
        return 0.0

    return sum(values) / len(values)


def normalize_score(
    value: float,
    old_min: float,
    old_max: float,
    new_min: float = 0.0,
    new_max: float = 1.0,
) -> float:

    if old_max == old_min:
        return new_min

    scaled = (
        (value - old_min)
        / (old_max - old_min)
    )

    return new_min + scaled * (new_max - new_min)


# ============================================================
# Weighted Scoring
# ============================================================


def weighted_average(
    scores: Mapping[str, float],
    weights: Mapping[str, float],
) -> float:

    total_weight = 0.0

    weighted_sum = 0.0

    for metric, score in scores.items():

        weight = weights.get(metric, 0)

        weighted_sum += score * weight

        total_weight += weight

    if total_weight == 0:
        return 0

    return weighted_sum / total_weight


# ============================================================
# Ranking
# ============================================================


def rank_by_score(
    items: list[Any],
    key: str,
    descending: bool = True,
):

    return sorted(
        items,
        key=lambda x: getattr(x, key),
        reverse=descending,
    )


# ============================================================
# Token Estimation
# ============================================================


def estimate_tokens(text: str) -> int:
    """
    Approximate GPT token count.

    Rule of thumb:
        1 token ≈ 0.75 words
    """

    return math.ceil(word_count(text) * 1.33)


# ============================================================
# Similarity
# ============================================================


def jaccard_similarity(
    text_a: str,
    text_b: str,
) -> float:

    a = set(text_a.lower().split())

    b = set(text_b.lower().split())

    if not a or not b:
        return 0.0

    return len(a & b) / len(a | b)


# ============================================================
# Collections
# ============================================================


def deduplicate_by_key(
    items: list[Any],
    key: str,
):

    seen = set()

    output = []

    for item in items:

        value = getattr(item, key)

        if value in seen:
            continue

        seen.add(value)

        output.append(item)

    return output


# ============================================================
# Validation
# ============================================================


def require_non_empty(
    value: str,
    field_name: str,
):

    if not value.strip():

        raise ValueError(
            f"{field_name} cannot be empty."
        )


# ============================================================
# Retry Helper
# ============================================================


async def retry_async(
    fn,
    retries: int = 2,
):
    """
    Generic async retry helper.
    """

    last_exception = None

    for _ in range(retries + 1):

        try:

            return await fn()

        except Exception as exc:

            last_exception = exc

    raise last_exception


# ============================================================
# Evidence Helpers
# ============================================================


def confidence_bucket(score: float) -> str:

    if score >= 0.90:
        return "very_high"

    if score >= 0.75:
        return "high"

    if score >= 0.55:
        return "medium"

    if score >= 0.30:
        return "low"

    return "very_low"


def is_high_confidence(score: float) -> bool:

    return score >= 0.75


# ============================================================
# Opportunity
# ============================================================


def opportunity_level(score: float) -> str:

    if score >= 8:
        return "very_high"

    if score >= 6:
        return "high"

    if score >= 4:
        return "medium"

    return "low"