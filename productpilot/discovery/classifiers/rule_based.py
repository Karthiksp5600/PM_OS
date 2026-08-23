"""Rule-based fallback classifier for the vertical slice."""

from __future__ import annotations

from productpilot.discovery.schemas import (
    ClassificationResult,
    ClassifiedRecord,
    FrictionType,
    IntentSignal,
    NormalizedRecord,
    OffPlatformResearch,
    SegmentHints,
)


class RuleBasedWishlistClassifier:
    def classify(self, record: NormalizedRecord) -> ClassifiedRecord:
        text = record.text.lower()
        intent = IntentSignal.UNCLEAR
        if "wishlist" in text or "save" in text or "bookmark" in text:
            intent = IntentSignal.BOOKMARK
        if "buy later" in text or "waiting" in text:
            intent = IntentSignal.PRICE_WATCH
        if "going to buy" in text or "plan to buy" in text:
            intent = IntentSignal.PURCHASE_INTENT

        frictions: list[FrictionType] = []
        if any(word in text for word in ["size", "fit", "return"]):
            frictions.append(FrictionType.FIT_SIZE_DOUBT)
        if any(word in text for word in ["style", "match", "pair"]):
            frictions.append(FrictionType.STYLING_UNCERTAINTY)
        if any(word in text for word in ["price", "sale", "expensive"]):
            frictions.append(FrictionType.PRICE_TIMING)
        if any(word in text for word in ["review", "photo", "rating"]):
            frictions.append(FrictionType.REVIEW_GAP)
        if any(word in text for word in ["occasion", "event", "wedding"]):
            frictions.append(FrictionType.OCCASION_MISMATCH)
        if any(word in text for word in ["friend", "people", "instagram", "influencer"]):
            frictions.append(FrictionType.SOCIAL_VALIDATION)
        if any(word in text for word in ["forgot", "lost", "too many"]):
            frictions.append(FrictionType.FORGOTTEN_LOST_IN_LIST)
        if any(word in text for word in ["compare", "comparison", "ajio", "flipkart"]):
            frictions.append(FrictionType.COMPARISON_PARALYSIS)
        if not frictions:
            frictions.append(FrictionType.OTHER)

        off_platform: list[OffPlatformResearch] = []
        if "youtube" in text or "video" in text:
            off_platform.append(OffPlatformResearch.TRYON_VIDEO)
        if "influencer" in text or "instagram" in text:
            off_platform.append(OffPlatformResearch.INFLUENCER_OPINION)
        if "size chart" in text or "fit guide" in text:
            off_platform.append(OffPlatformResearch.FIT_GUIDE)
        if "ajio" in text or "competitor" in text:
            off_platform.append(OffPlatformResearch.COMPETITOR_PRICE_CHECK)
        if not off_platform:
            off_platform.append(OffPlatformResearch.NONE)

        category = None
        if any(word in text for word in ["shoe", "sneaker", "heel", "footwear"]):
            category = "footwear"
        elif any(word in text for word in ["dress", "kurta", "top", "jeans"]):
            category = "apparel"

        price_tier = None
        if "₹2000" in record.text or "under 2000" in text:
            price_tier = "under_2000"
        elif any(word in text for word in ["premium", "luxury"]):
            price_tier = "premium"

        user_type = None
        if any(word in text for word in ["new user", "first time"]):
            user_type = "new_user"
        elif any(word in text for word in ["regular", "frequent"]):
            user_type = "repeat_user"

        excerpt = record.text[:220]
        classification = ClassificationResult(
            is_relevant="wishlist" in text or "saved" in text or "cart" in text,
            intent_signal=intent,
            friction_type=frictions,
            comparison_behavior=FrictionType.COMPARISON_PARALYSIS in frictions,
            off_platform_research=off_platform,
            segment_hints=SegmentHints(category=category, price_tier=price_tier, user_type=user_type),
            confidence=0.76,
            excerpt=excerpt,
        )
        return ClassifiedRecord(record=record, classification=classification)
