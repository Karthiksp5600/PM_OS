"""Schemas for the Myntra wishlist discovery engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from hashlib import sha256
import re
from typing import Any, Dict, List, Optional, Type, TypeVar, get_args, get_origin, get_type_hints
import json


class SourceName(str, Enum):
    PLAY_STORE = "play_store"
    REDDIT = "reddit"
    DUCKDUCKGO = "duckduckgo"
    CRAWLEE = "crawlee"
    MAXCRAWL = "maxcrawl"
    APP_STORE = "app_store"
    YOUTUBE = "youtube"
    TWITTER_X = "twitter_x"
    FORUM = "forum"


class IntentSignal(str, Enum):
    BOOKMARK = "bookmark"
    PRICE_WATCH = "price_watch"
    PURCHASE_INTENT = "purchase_intent"
    UNCLEAR = "unclear"


class FrictionType(str, Enum):
    FIT_SIZE_DOUBT = "fit_size_doubt"
    STYLING_UNCERTAINTY = "styling_uncertainty"
    PRICE_TIMING = "price_timing"
    REVIEW_GAP = "review_gap"
    OCCASION_MISMATCH = "occasion_mismatch"
    SOCIAL_VALIDATION = "social_validation"
    FORGOTTEN_LOST_IN_LIST = "forgotten_lost_in_list"
    COMPARISON_PARALYSIS = "comparison_paralysis"
    OTHER = "other"


class OffPlatformResearch(str, Enum):
    FIT_GUIDE = "fit_guide"
    TRYON_VIDEO = "tryon_video"
    INFLUENCER_OPINION = "influencer_opinion"
    COMPETITOR_PRICE_CHECK = "competitor_price_check"
    NONE = "none"


class ConfidenceTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DiscoveryDataclass:
    def model_dump(self, mode: Optional[str] = None) -> Dict[str, Any]:
        return _serialize(asdict(self))

    def model_dump_json(self) -> str:
        return json.dumps(self.model_dump())

    @classmethod
    def model_validate_json(cls, payload: str):
        data = json.loads(payload)
        return _from_dict(cls, data)


@dataclass
class NormalizedRecord(DiscoveryDataclass):
    source: SourceName
    url: str
    author_id_hash: str
    timestamp: datetime
    text: str
    rating: Optional[float] = None
    upvotes_likes: Optional[int] = None
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""

    @classmethod
    def build_content_hash(cls, source: SourceName, text: str, url: str) -> str:
        return sha256(f"{source.value}|{url}|{text.strip()}".encode("utf-8")).hexdigest()

    @classmethod
    def canonicalize_text(cls, text: str) -> str:
        normalized = text.strip()
        synthetic_patterns = [
            r"Users mentioned this in another saved-item discussion\.",
            r"Another shopper described a similar wishlist delay\.",
            r"A parallel source echoed the same friction pattern\.",
            r"This variant reflects another closely related user account\.",
            r"The same hesitation appeared in an additional community mention\.",
            r"Variant \d+\.",
        ]
        for pattern in synthetic_patterns:
            normalized = re.sub(pattern, "", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\s+", " ", normalized).strip().lower()
        return normalized

    @classmethod
    def build_dedup_key(cls, text: str) -> str:
        return sha256(cls.canonicalize_text(text).encode("utf-8")).hexdigest()


@dataclass
class SegmentHints(DiscoveryDataclass):
    category: Optional[str] = None
    price_tier: Optional[str] = None
    user_type: Optional[str] = None


@dataclass
class ClassificationResult(DiscoveryDataclass):
    is_relevant: bool
    intent_signal: IntentSignal
    friction_type: List[FrictionType]
    comparison_behavior: bool
    off_platform_research: List[OffPlatformResearch]
    segment_hints: SegmentHints
    confidence: float
    excerpt: str


@dataclass
class ClassifiedRecord(DiscoveryDataclass):
    record: NormalizedRecord
    classification: ClassificationResult


@dataclass
class OpportunityRecord(DiscoveryDataclass):
    name: str
    description: str
    evidence_count: int
    sample_excerpts: List[str]
    segments_affected: List[str]
    confidence_tier: ConfidenceTier
    source_count: int
    friction_types: List[FrictionType]
    intent_signals: List[IntentSignal]


@dataclass
class EvidenceChunk(DiscoveryDataclass):
    chunk_id: str
    chunk_type: str
    source: str
    source_url: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatAnswer(DiscoveryDataclass):
    answer_text: str
    confidence_tier: ConfidenceTier
    citations: List[Dict[str, str]]
    out_of_scope_notice: Optional[str] = None


T = TypeVar("T")


def _serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


def _from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
    kwargs: Dict[str, Any] = {}
    annotations = get_type_hints(cls)
    for field_name, field_type in annotations.items():
        if field_name not in data:
            continue
        kwargs[field_name] = _coerce_value(field_type, data[field_name])
    return cls(**kwargs)


def _coerce_value(field_type: Any, value: Any) -> Any:
    origin = get_origin(field_type)
    if origin is list:
        inner = get_args(field_type)[0]
        return [_coerce_value(inner, item) for item in value]
    if origin is dict:
        return value
    if origin is None:
        if isinstance(field_type, type) and issubclass(field_type, Enum):
            return field_type(value)
        if field_type is datetime:
            return datetime.fromisoformat(value)
        if hasattr(field_type, "__dataclass_fields__"):
            return _from_dict(field_type, value)
        return value
    union_args = [arg for arg in get_args(field_type) if arg is not type(None)]
    if len(union_args) == 1:
        return None if value is None else _coerce_value(union_args[0], value)
    return value
