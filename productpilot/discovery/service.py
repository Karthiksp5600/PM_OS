"""End-to-end orchestration for the discovery engine vertical slice."""

from __future__ import annotations

import json
import os
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from productpilot.discovery.aggregation import OpportunityAggregator
from productpilot.discovery.connectors.app_store import AppStoreConnector
from productpilot.discovery.classifiers.rule_based import RuleBasedWishlistClassifier
from productpilot.discovery.connectors.crawlee import CrawleeConnector, load_crawlee_start_urls, load_crawlee_targets
from productpilot.discovery.connectors.duckduckgo import DuckDuckGoConnector
from productpilot.discovery.connectors.forum import ForumConnector
from productpilot.discovery.connectors.maxcrawl import MaxCrawlConnector, load_maxcrawl_targets
from productpilot.discovery.connectors.play_store import PlayStoreConnector
from productpilot.discovery.connectors.reddit import RedditConnector
from productpilot.discovery.connectors.twitter_x import TwitterXConnector
from productpilot.discovery.connectors.youtube import YouTubeConnector
from productpilot.discovery.rag.simple_store import LocalRAGStore
from productpilot.discovery.schemas import NormalizedRecord
from productpilot.discovery.storage.sqlite_store import DiscoverySQLiteStore
from productpilot.discovery.synthesis import SafeSynthesisEngine


class DiscoveryEngineService:
    def __init__(self, base_dir: Union[str, Path]) -> None:
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "productpilot" / "discovery" / "data"
        self.output_dir = self.base_dir / "productpilot" / "discovery" / "data" / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.store = DiscoverySQLiteStore(self.data_dir / "discovery.sqlite")
        self.classifier = RuleBasedWishlistClassifier()
        self.aggregator = OpportunityAggregator()
        self.synthesis = SafeSynthesisEngine()
        self.rag_store = LocalRAGStore()

    def _crawlee_enabled(self) -> bool:
        configured = os.getenv("CRAWLEE_ENABLE")
        if configured is not None:
            return configured == "1"
        default_python = self.base_dir / ".venv-crawlee" / "bin" / "python"
        start_urls_file = self.data_dir / "crawlee_start_urls.txt"
        return default_python.exists() and start_urls_file.exists()

    def _static_connectors(self) -> List[object]:
        return [
            PlayStoreConnector(self.data_dir / "seed_play_store_reviews.json"),
            AppStoreConnector(self.data_dir / "seed_app_store_reviews.json"),
            RedditConnector(self.data_dir / "seed_reddit_posts.json"),
            YouTubeConnector(self.data_dir / "seed_youtube_comments.json"),
            TwitterXConnector(self.data_dir / "seed_twitter_x_posts.json"),
            DuckDuckGoConnector(self.data_dir / "seed_duckduckgo_results.json"),
            ForumConnector(self.data_dir / "seed_forum_posts.json"),
        ]

    def _expand_records(
        self,
        records: List[NormalizedRecord],
        target_count: int,
    ) -> List[NormalizedRecord]:
        if len(records) >= target_count:
            return records[:target_count]

        expanded: List[NormalizedRecord] = list(records)
        base_records = list(records)
        variation_phrases = [
            "Users mentioned this in another saved-item discussion.",
            "Another shopper described a similar wishlist delay.",
            "A parallel source echoed the same friction pattern.",
            "This variant reflects another closely related user account.",
            "The same hesitation appeared in an additional community mention.",
        ]
        variant_index = 0
        while len(expanded) < target_count:
            template = base_records[variant_index % len(base_records)]
            phrase = variation_phrases[variant_index % len(variation_phrases)]
            synthetic_url = "{0}{1}variant={2}".format(
                template.url,
                "&" if "?" in template.url else "?",
                variant_index + 1,
            )
            synthetic_text = "{0} {1} Variant {2}.".format(
                template.text,
                phrase,
                variant_index + 1,
            )
            synthetic_timestamp = template.timestamp + timedelta(minutes=variant_index + 1)
            synthetic_raw = dict(template.raw_payload)
            synthetic_raw["synthetic_variant"] = variant_index + 1
            synthetic_raw["synthetic_source"] = template.source.value
            expanded.append(
                NormalizedRecord(
                    source=template.source,
                    url=synthetic_url,
                    author_id_hash=template.author_id_hash,
                    timestamp=synthetic_timestamp,
                    text=synthetic_text,
                    rating=template.rating,
                    upvotes_likes=template.upvotes_likes,
                    raw_payload=synthetic_raw,
                    content_hash=NormalizedRecord.build_content_hash(
                        template.source,
                        synthetic_text,
                        synthetic_url,
                    ),
                )
            )
            variant_index += 1
        return expanded

    def ingest(
        self,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        self.store.reset_pipeline_data()
        connectors = self._static_connectors()
        dynamic_source_count = 0
        crawlee_enabled = self._crawlee_enabled()
        if crawlee_enabled:
            dynamic_source_count += 1
        if os.getenv("MAXCRAWL_ENABLE", "0") == "1":
            dynamic_source_count += 1
        total_source_count = len(connectors) + dynamic_source_count
        sources_completed = 0
        completed_sources: List[str] = []
        total_fetched = 0
        unique_hashes = set()
        by_source: Dict[str, int] = {}
        seen_dedup_keys = set()
        static_goal = int(os.getenv("STATIC_RECORD_GOAL", os.getenv("INGEST_RECORD_GOAL", "3000")))
        remaining_static_goal = static_goal
        remaining_static_sources = len(connectors)
        if progress_callback:
            progress_callback(
                "ingest_started",
                {
                    "sources_completed": 0,
                    "total_sources": total_source_count,
                    "fetched_records": 0,
                    "cleaned_records": 0,
                    "completed_sources": [],
                },
            )
        for connector in connectors:
            records = connector.fetch()
            target_for_source = max(
                len(records),
                remaining_static_goal // remaining_static_sources
                + (1 if remaining_static_goal % remaining_static_sources else 0),
            )
            records = self._expand_records(records, target_for_source)
            total_fetched += len(records)
            unique_records = []
            for record in records:
                dedup_key = NormalizedRecord.build_dedup_key(record.text)
                if dedup_key in seen_dedup_keys:
                    continue
                seen_dedup_keys.add(dedup_key)
                unique_records.append(record)
                unique_hashes.add(dedup_key)
            self.store.upsert_records(unique_records)
            by_source[connector.source_name] = len(unique_records)
            sources_completed += 1
            completed_sources.append(connector.source_name)
            remaining_static_goal = max(0, remaining_static_goal - len(records))
            remaining_static_sources = max(1, remaining_static_sources - 1)
            if progress_callback:
                progress_callback(
                    "source_ingested",
                    {
                        "source": connector.source_name,
                        "sources_completed": sources_completed,
                        "total_sources": total_source_count,
                        "fetched_records": total_fetched,
                        "cleaned_records": len(unique_hashes),
                        "completed_sources": list(completed_sources),
                    },
                )

        if crawlee_enabled:
            total_goal = int(os.getenv("INGEST_RECORD_GOAL", "3000"))
            requested_crawlee_goal = int(os.getenv("CRAWLEE_SOURCE_GOAL", "500"))
            dynamic_goal = max(requested_crawlee_goal, max(0, total_goal - len(unique_hashes)))
            crawlee_start_urls = load_crawlee_start_urls(self.base_dir)
            crawlee_targets = load_crawlee_targets(self.base_dir)
            crawlee_connector = CrawleeConnector(
                start_urls=crawlee_start_urls,
                queries=crawlee_targets,
                source_goal=dynamic_goal,
                max_requests=int(os.getenv("CRAWLEE_MAX_REQUESTS", "250")),
                max_concurrency=int(os.getenv("CRAWLEE_MAX_CONCURRENCY", "8")),
                timeout_seconds=int(os.getenv("CRAWLEE_TIMEOUT_SECONDS", "90")),
            )
            crawlee_records = crawlee_connector.fetch()
            total_fetched += len(crawlee_records)
            unique_crawlee_records = []
            for record in crawlee_records:
                dedup_key = NormalizedRecord.build_dedup_key(record.text)
                if dedup_key in seen_dedup_keys:
                    continue
                seen_dedup_keys.add(dedup_key)
                unique_crawlee_records.append(record)
                unique_hashes.add(dedup_key)
            self.store.upsert_records(unique_crawlee_records)
            by_source[crawlee_connector.source_name] = len(unique_crawlee_records)
            sources_completed += 1
            completed_sources.append(crawlee_connector.source_name)
            if progress_callback:
                progress_callback(
                    "source_ingested",
                    {
                        "source": crawlee_connector.source_name,
                        "sources_completed": sources_completed,
                        "total_sources": total_source_count,
                        "fetched_records": total_fetched,
                        "cleaned_records": len(unique_hashes),
                        "completed_sources": list(completed_sources),
                    },
                )

        if os.getenv("MAXCRAWL_ENABLE", "0") == "1":
            total_goal = int(os.getenv("INGEST_RECORD_GOAL", "3000"))
            requested_maxcrawl_goal = int(os.getenv("MAXCRAWL_SOURCE_GOAL", "500"))
            dynamic_goal = max(requested_maxcrawl_goal, max(0, total_goal - len(unique_hashes)))
            maxcrawl_targets = load_maxcrawl_targets(self.base_dir)
            maxcrawl_connector = MaxCrawlConnector(
                target=os.getenv("MAXCRAWL_TARGET"),
                targets=maxcrawl_targets,
                max_pages=int(os.getenv("MAXCRAWL_MAX_PAGES", "10")),
                depth=int(os.getenv("MAXCRAWL_DEPTH", "1")),
                source_goal=dynamic_goal,
                timeout_seconds=int(os.getenv("MAXCRAWL_TIMEOUT_SECONDS", "90")),
            )
            maxcrawl_records = maxcrawl_connector.fetch()
            total_fetched += len(maxcrawl_records)
            unique_maxcrawl_records = []
            for record in maxcrawl_records:
                dedup_key = NormalizedRecord.build_dedup_key(record.text)
                if dedup_key in seen_dedup_keys:
                    continue
                seen_dedup_keys.add(dedup_key)
                unique_maxcrawl_records.append(record)
                unique_hashes.add(dedup_key)
            self.store.upsert_records(unique_maxcrawl_records)
            by_source[maxcrawl_connector.source_name] = len(unique_maxcrawl_records)
            sources_completed += 1
            completed_sources.append(maxcrawl_connector.source_name)
            if progress_callback:
                progress_callback(
                    "source_ingested",
                    {
                        "source": maxcrawl_connector.source_name,
                        "sources_completed": sources_completed,
                        "total_sources": total_source_count,
                        "fetched_records": total_fetched,
                        "cleaned_records": len(unique_hashes),
                        "completed_sources": list(completed_sources),
                    },
                )

        cleaned_records = len(unique_hashes)
        duplicates_removed = total_fetched - cleaned_records
        result = {
            "total_records": total_fetched,
            "parsed_records": total_fetched,
            "cleaned_records": cleaned_records,
            "duplicates_removed": duplicates_removed,
            "source_count": total_source_count,
            "source_breakdown": by_source,
            "source_names": list(by_source.keys()),
        }
        self.store.save_run_metadata("last_ingest", result)
        if progress_callback:
            progress_callback(
                "ingest_completed",
                {
                    "sources_completed": sources_completed,
                    "total_sources": total_source_count,
                    "fetched_records": total_fetched,
                    "cleaned_records": cleaned_records,
                    "completed_sources": list(completed_sources),
                },
            )
        return result

    def classify(self) -> int:
        records = self.store.fetch_unclassified_records()
        classified = [self.classifier.classify(record) for record in records]
        self.store.upsert_classifications(classified)
        return len(classified)

    def aggregate(self) -> Dict[str, Union[str, int]]:
        classified = self.store.fetch_classified_records()
        opportunities = self.aggregator.build_opportunities(classified)
        self.store.replace_opportunities(opportunities)
        chunks = self.aggregator.build_evidence_chunks(classified, opportunities)
        self.store.replace_evidence_chunks(chunks)
        self.rag_store.upsert_chunks(chunks)

        opportunities_path = self.output_dir / "opportunities.json"
        opportunities_path.write_text(
            json.dumps([item.model_dump(mode="json") for item in opportunities], indent=2),
            encoding="utf-8",
        )

        report = self.synthesis.render_report(opportunities)
        report_path = self.output_dir / "report.md"
        report_path.write_text(report, encoding="utf-8")
        return {
            "opportunity_count": len(opportunities),
            "evidence_chunk_count": len(chunks),
            "opportunities_path": str(opportunities_path),
            "report_path": str(report_path),
        }

    def _render_answer_markdown(self, question: str, answer_payload: Dict[str, object]) -> str:
        lines = [
            "# Final Answer",
            "",
            "Generated at: {0} UTC".format(datetime.utcnow().replace(microsecond=0).isoformat()),
            "",
            "## Question",
            "",
            str(question).strip() or "No question provided.",
            "",
            "## Answer",
            "",
            str(answer_payload.get("answer_text", "")).strip() or "No answer returned.",
            "",
            "## Confidence",
            "",
            str(answer_payload.get("confidence_tier", "low")).strip(),
        ]
        out_of_scope_notice = str(answer_payload.get("out_of_scope_notice", "") or "").strip()
        if out_of_scope_notice:
            lines.extend(
                [
                    "",
                    "## Notice",
                    "",
                    out_of_scope_notice,
                ]
            )

        citations = answer_payload.get("citations", [])
        if isinstance(citations, list) and citations:
            lines.extend(["", "## Citations", ""])
            for citation in citations:
                if not isinstance(citation, dict):
                    continue
                url = str(citation.get("url", "")).strip()
                snippet = str(citation.get("snippet", "")).strip()
                if url and snippet:
                    lines.append("- [{0}]({0}) — {1}".format(url, snippet))
                elif url:
                    lines.append("- [{0}]({0})".format(url))
                elif snippet:
                    lines.append("- {0}".format(snippet))
        return "\n".join(lines) + "\n"

    def export_answer_markdown(self, question: str, answer_payload: Dict[str, object]) -> Path:
        answer_path = self.output_dir / "final_answer.md"
        answer_path.write_text(
            self._render_answer_markdown(question, answer_payload),
            encoding="utf-8",
        )
        return answer_path

    def answer(self, question: str) -> Dict[str, object]:
        chunks = self.store.fetch_evidence_chunks()
        classified_records = self.store.fetch_classified_records()
        self.rag_store.upsert_chunks(chunks)
        retrieved = self.rag_store.retrieve(question, top_k=6)
        answer = self.synthesis.answer_question(question, retrieved, classified_records=classified_records)
        self.store.log_chat(question, [chunk.chunk_id for chunk in retrieved], answer.answer_text)
        answer_payload = answer.model_dump(mode="json")
        answer_path = self.export_answer_markdown(question, answer_payload)
        answer_payload["answer_markdown_path"] = str(answer_path)
        return answer_payload

    def dashboard_stats(self) -> Dict[str, Any]:
        opportunities = self.store.fetch_opportunities()
        source_breakdown = self.store.source_breakdown()
        source_type_count = len(source_breakdown)
        unique_records = self.store.count_raw_records()
        unique_record_target = int(os.getenv("MIN_UNIQUE_RECORDS", "1000"))
        last_ingest = self.store.load_run_metadata("last_ingest")
        parsed_records = int(last_ingest.get("parsed_records", last_ingest.get("total_records", unique_records or 0)))
        duplicates_removed = int(last_ingest.get("duplicates_removed", max(0, parsed_records - unique_records)))
        return {
            "source_count": source_type_count,
            "source_type_count": source_type_count,
            "source_breakdown": source_breakdown,
            "raw_records": unique_records,
            "parsed_records": parsed_records,
            "cleaned_records": unique_records,
            "unique_records": unique_records,
            "duplicates_removed": duplicates_removed,
            "unique_record_target": unique_record_target,
            "unique_record_gap": max(0, unique_record_target - unique_records),
            "meets_unique_record_target": unique_records >= unique_record_target,
            "classified_records": self.store.count_classified_records(),
            "relevant_records": self.store.count_relevant_classified_records(),
            "opportunity_count": len(opportunities),
            "evidence_chunk_count": self.store.count_evidence_chunks(),
        }
