"""
Configuration for the ProductPilot Discovery Agent.

This module centralizes every configurable parameter used by the
Discovery pipeline.

No business logic belongs here.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Base
# ============================================================


class PPConfig(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


# ============================================================
# LLM
# ============================================================


class LLMConfig(PPConfig):

    provider: str = "openai"

    model: str = "gpt-5"

    temperature: float = 0.2

    max_tokens: int = 4000

    timeout_seconds: int = 120

    max_retries: int = 2


# ============================================================
# Retrieval
# ============================================================


class RetrievalConfig(PPConfig):

    provider: str = "pinecone"

    top_k: int = 12

    min_relevance_score: float = 0.55

    rerank_results: bool = True

    hybrid_search: bool = True

    include_metadata: bool = True


# ============================================================
# Evidence Ranking
# ============================================================


class RankingConfig(PPConfig):

    weight_relevance: float = 0.35

    weight_confidence: float = 0.25

    weight_freshness: float = 0.20

    weight_trust: float = 0.20


# ============================================================
# Opportunity Scoring
# ============================================================


class OpportunityWeights(PPConfig):

    reach: float = 0.20

    severity: float = 0.20

    frequency: float = 0.15

    strategic_alignment: float = 0.15

    revenue: float = 0.10

    retention: float = 0.10

    confidence: float = 0.05

    risk: float = 0.05


# ============================================================
# Evaluation
# ============================================================


class EvaluationConfig(PPConfig):

    minimum_score: float = 0.75

    minimum_confidence: float = 0.70

    maximum_hallucination_risk: float = 0.25

    require_citations: bool = True

    require_persona: bool = True

    require_kpi: bool = True

    require_jtbd: bool = True


# ============================================================
# Metrics
# ============================================================


class MetricsConfig(PPConfig):

    enable_metrics: bool = True

    enable_cost_tracking: bool = True

    enable_latency_tracking: bool = True

    enable_token_tracking: bool = True

    enable_eval_tracking: bool = True


# ============================================================
# Logging
# ============================================================


class LoggingConfig(PPConfig):

    level: str = "INFO"

    structured: bool = True

    log_prompts: bool = False

    log_responses: bool = False

    log_retrieval: bool = True


# ============================================================
# Prompt Settings
# ============================================================


class PromptConfig(PPConfig):

    include_chain_of_thought: bool = False

    include_examples: bool = True

    strict_json_output: bool = True

    system_prompt_version: str = "v1"


# ============================================================
# Runtime
# ============================================================


class RuntimeConfig(PPConfig):

    environment: str = "development"

    debug: bool = True

    cache_enabled: bool = True

    cache_ttl_seconds: int = 3600

    parallel_execution: bool = True


# ============================================================
# Paths
# ============================================================


class PathConfig(PPConfig):

    root: Path = Path.cwd()

    prompts: Path = root / "prompts"

    logs: Path = root / "logs"

    cache: Path = root / ".cache"

    artifacts: Path = root / "artifacts"


# ============================================================
# Discovery Config
# ============================================================


class DiscoveryConfig(PPConfig):

    llm: LLMConfig = Field(default_factory=LLMConfig)

    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)

    ranking: RankingConfig = Field(default_factory=RankingConfig)

    opportunity: OpportunityWeights = Field(default_factory=OpportunityWeights)

    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)

    metrics: MetricsConfig = Field(default_factory=MetricsConfig)

    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    prompts: PromptConfig = Field(default_factory=PromptConfig)

    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)

    paths: PathConfig = Field(default_factory=PathConfig)


# ============================================================
# Singleton
# ============================================================


settings = DiscoveryConfig()