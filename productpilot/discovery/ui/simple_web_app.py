"""No-dependency web UI for the Myntra wishlist discovery vertical slice.

Run with:
    python3 -m productpilot.discovery.ui.simple_web_app

Then open:
    http://127.0.0.1:8765
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from productpilot.discovery.service import DiscoveryEngineService

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CRAWLEE_PYTHON = ROOT / ".venv-crawlee" / "bin" / "python"
if "CRAWLEE_ENABLE" not in __import__("os").environ and DEFAULT_CRAWLEE_PYTHON.exists():
    __import__("os").environ["CRAWLEE_ENABLE"] = "1"
SERVICE = DiscoveryEngineService(ROOT)
FINAL_ANSWER_PATH = ROOT / "productpilot" / "discovery" / "data" / "outputs" / "final_answer.md"
RANKED_OPPORTUNITIES_PATH = ROOT / "productpilot" / "discovery" / "data" / "outputs" / "report.md"
RUN_STATE_LOCK = threading.Lock()
RUN_STATE: Dict[str, Any] = {
    "status": "idle",
    "message": "Idle",
    "sources_completed": 0,
    "total_sources": 0,
    "completed_sources": [],
    "fetched_records": 0,
    "cleaned_records": 0,
    "classified_records": 0,
    "opportunity_count": 0,
    "is_running": False,
}


def sort_opportunities_payload(opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def is_other(opportunity: dict[str, Any]) -> bool:
        name = str(opportunity.get("name", ""))
        friction_types = [str(item) for item in (opportunity.get("friction_types") or [])]
        return name.startswith("other:") or "other" in friction_types

    def is_unclear(opportunity: dict[str, Any]) -> bool:
        name = str(opportunity.get("name", ""))
        intent_signals = [str(item) for item in (opportunity.get("intent_signals") or [])]
        return name.endswith(":unclear") or "unclear" in intent_signals

    return sorted(
        opportunities,
        key=lambda item: (
            is_other(item) or is_unclear(item),
            -int(item.get("evidence_count", 0) or 0),
            -int(item.get("source_count", 0) or 0),
            str(item.get("name", "")),
        ),
    )


def update_run_state(**kwargs: Any) -> None:
    with RUN_STATE_LOCK:
        RUN_STATE.update(kwargs)


def snapshot_run_state() -> Dict[str, Any]:
    with RUN_STATE_LOCK:
        return dict(RUN_STATE)


def execute_pipeline_job() -> None:
    try:
        update_run_state(
            status="running",
            message="Starting ingestion...",
            sources_completed=0,
            total_sources=0,
            completed_sources=[],
            fetched_records=0,
            cleaned_records=0,
            classified_records=0,
            opportunity_count=0,
            is_running=True,
        )

        def progress_callback(stage: str, payload: Dict[str, Any]) -> None:
            if stage == "ingest_started":
                update_run_state(
                    status="running",
                    message="Starting source ingestion...",
                    sources_completed=payload.get("sources_completed", 0),
                    total_sources=payload.get("total_sources", 0),
                    completed_sources=payload.get("completed_sources", []),
                    fetched_records=payload.get("fetched_records", 0),
                    cleaned_records=payload.get("cleaned_records", 0),
                )
            elif stage == "source_ingested":
                source_name = str(payload.get("source", "source"))
                update_run_state(
                    status="running",
                    message="Ingested {0} ({1}/{2} sources)".format(
                        source_name,
                        payload.get("sources_completed", 0),
                        payload.get("total_sources", 0),
                    ),
                    sources_completed=payload.get("sources_completed", 0),
                    total_sources=payload.get("total_sources", 0),
                    completed_sources=payload.get("completed_sources", []),
                    fetched_records=payload.get("fetched_records", 0),
                    cleaned_records=payload.get("cleaned_records", 0),
                )
            elif stage == "ingest_completed":
                update_run_state(
                    status="running",
                    message="Ingestion complete. Classifying records...",
                    sources_completed=payload.get("sources_completed", 0),
                    total_sources=payload.get("total_sources", 0),
                    completed_sources=payload.get("completed_sources", []),
                    fetched_records=payload.get("fetched_records", 0),
                    cleaned_records=payload.get("cleaned_records", 0),
                )

        ingest_result = SERVICE.ingest(progress_callback=progress_callback)
        update_run_state(
            status="running",
            message="Classification in progress...",
            fetched_records=ingest_result.get("total_records", 0),
            cleaned_records=ingest_result.get("cleaned_records", 0),
        )
        classified_count = SERVICE.classify()
        update_run_state(
            status="running",
            message="Aggregation in progress...",
            classified_records=classified_count,
        )
        aggregate_result = SERVICE.aggregate()
        update_run_state(
            status="completed",
            message="Run complete.",
            sources_completed=ingest_result.get("source_count", 0),
            total_sources=ingest_result.get("source_count", 0),
            fetched_records=ingest_result.get("total_records", 0),
            cleaned_records=ingest_result.get("cleaned_records", 0),
            classified_records=classified_count,
            opportunity_count=aggregate_result.get("opportunity_count", 0),
            is_running=False,
        )
    except Exception as exc:
        update_run_state(
            status="error",
            message="Run failed: {0}".format(exc),
            is_running=False,
        )

HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Myntra Wishlist Discovery</title>
  <style>
    :root {
      --bg: #07111f;
      --bg-soft: #0e172a;
      --panel: rgba(12, 22, 40, 0.82);
      --panel-strong: #101c32;
      --line: rgba(148, 163, 184, 0.18);
      --text: #e5eefc;
      --muted: #9fb0cc;
      --primary: #7c9cff;
      --primary-strong: #4f6ef7;
      --success: #22c55e;
      --warning: #f59e0b;
      --danger: #f97316;
      --chip: rgba(124, 156, 255, 0.12);
      --card-shadow: 0 20px 50px rgba(0, 0, 0, 0.28);
      --radius-xl: 28px;
      --radius-lg: 20px;
      --radius-md: 14px;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(79, 110, 247, 0.30), transparent 28%),
        radial-gradient(circle at top right, rgba(6, 182, 212, 0.18), transparent 30%),
        linear-gradient(180deg, #0a1324 0%, #07111f 100%);
      color: var(--text);
    }

    .shell {
      max-width: 1360px;
      margin: 0 auto;
      padding: 28px;
    }

    .hero {
      display: grid;
      grid-template-columns: 1.4fr 0.9fr;
      gap: 18px;
      margin-bottom: 18px;
    }

    .hero-card,
    .summary-card,
    .panel,
    .opportunity-card,
    .citation-card,
    .metric-card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      box-shadow: var(--card-shadow);
      backdrop-filter: blur(14px);
    }

    .hero-card {
      padding: 28px;
      overflow: hidden;
      position: relative;
    }

    .hero-card::after {
      content: "";
      position: absolute;
      inset: auto -40px -40px auto;
      width: 180px;
      height: 180px;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(124, 156, 255, 0.30), transparent 65%);
      pointer-events: none;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: var(--chip);
      color: #bfd0ff;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 16px;
    }

    h1 {
      margin: 0;
      font-size: clamp(34px, 5vw, 56px);
      line-height: 0.95;
      letter-spacing: -0.05em;
      max-width: 10ch;
    }

    .hero-copy {
      margin: 16px 0 0;
      max-width: 62ch;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.6;
    }

    .hero-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 22px;
    }

    .chip {
      padding: 9px 12px;
      border-radius: 999px;
      border: 1px solid rgba(124, 156, 255, 0.18);
      color: #d6e2ff;
      background: rgba(124, 156, 255, 0.10);
      font-size: 13px;
    }

    .summary-card {
      padding: 24px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 100%;
    }

    .summary-label {
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .summary-value {
      margin-top: 8px;
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.03em;
    }

    .summary-note {
      margin-top: 12px;
      color: var(--muted);
      line-height: 1.5;
      font-size: 14px;
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 14px;
    }

    .tab-shell {
      display: grid;
      gap: 18px;
    }

    .tabs {
      display: inline-flex;
      gap: 10px;
      padding: 8px;
      border-radius: 18px;
      background: rgba(148, 163, 184, 0.10);
      border: 1px solid rgba(148, 163, 184, 0.14);
      width: fit-content;
    }

    .tab-button {
      background: transparent;
      color: var(--muted);
      border: 1px solid transparent;
      padding: 12px 18px;
    }

    .tab-button.active {
      color: white;
      background: linear-gradient(135deg, var(--primary-strong), var(--primary));
      box-shadow: 0 10px 30px rgba(79, 110, 247, 0.22);
    }

    .tab-pane {
      display: none;
    }

    .tab-pane.active {
      display: block;
    }

    .main-focus {
      display: grid;
      grid-template-columns: minmax(0, 1.08fr) minmax(360px, 0.92fr);
      gap: 18px;
      align-items: start;
    }

    .metric-card {
      padding: 18px;
    }

    .metric-label {
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 12px;
    }

    .metric-value {
      font-size: 26px;
      font-weight: 700;
      letter-spacing: -0.04em;
    }

    .metric-sub {
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
      min-height: 18px;
    }

    .dashboard {
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(340px, 0.8fr);
      gap: 18px;
      align-items: start;
    }

    .stack {
      display: grid;
      gap: 18px;
    }

    .panel {
      padding: 22px;
    }

    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 18px;
    }

    .panel-title {
      margin: 0;
      font-size: 22px;
      letter-spacing: -0.03em;
    }

    .panel-subtitle {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 14px;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    button,
    input {
      font: inherit;
    }

    button,
    .button-link {
      border: none;
      border-radius: 14px;
      padding: 12px 16px;
      cursor: pointer;
      transition: transform 0.16s ease, opacity 0.16s ease, background 0.16s ease;
      font-weight: 700;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    button:hover,
    .button-link:hover {
      transform: translateY(-1px);
    }

    button.primary,
    .button-link.primary {
      color: white;
      background: linear-gradient(135deg, var(--primary-strong), var(--primary));
      box-shadow: 0 10px 30px rgba(79, 110, 247, 0.35);
    }

    button.secondary,
    .button-link.secondary {
      color: var(--text);
      background: rgba(148, 163, 184, 0.16);
      border: 1px solid rgba(148, 163, 184, 0.18);
    }

    .button-link.disabled {
      opacity: 0.5;
      pointer-events: none;
    }

    .pipeline-grid {
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 16px;
    }

    .pipeline-steps {
      display: grid;
      gap: 12px;
    }

    .step {
      padding: 14px 16px;
      border-radius: 16px;
      background: rgba(148, 163, 184, 0.08);
      border: 1px solid rgba(148, 163, 184, 0.12);
    }

    .step-kicker {
      color: #bfd0ff;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
    }

    .step-copy {
      color: var(--muted);
      line-height: 1.5;
      font-size: 14px;
    }

    .status-box {
      min-height: 100%;
      padding: 18px;
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(124, 156, 255, 0.13), rgba(14, 23, 42, 0.5));
      border: 1px solid rgba(124, 156, 255, 0.18);
      white-space: pre-wrap;
      line-height: 1.6;
    }

    .question-input {
      width: 100%;
      border: 1px solid rgba(148, 163, 184, 0.20);
      background: rgba(10, 18, 34, 0.85);
      color: var(--text);
      border-radius: 16px;
      padding: 14px 16px;
      margin: 0;
    }

    .ask-row {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 16px;
    }

    .answer-card {
      margin-top: 18px;
      padding: 18px;
      border-radius: 18px;
      background: rgba(124, 156, 255, 0.10);
      border: 1px solid rgba(124, 156, 255, 0.18);
    }

    .answer-meta {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 14px;
      flex-wrap: wrap;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      border: 1px solid transparent;
    }

    .badge.high { background: rgba(34, 197, 94, 0.15); color: #bbf7d0; border-color: rgba(34, 197, 94, 0.25); }
    .badge.medium { background: rgba(245, 158, 11, 0.15); color: #fde68a; border-color: rgba(245, 158, 11, 0.25); }
    .badge.low { background: rgba(249, 115, 22, 0.15); color: #fed7aa; border-color: rgba(249, 115, 22, 0.25); }

    .answer-text {
      line-height: 1.7;
      color: #edf4ff;
    }

    .notice {
      margin-top: 14px;
      padding: 12px 14px;
      border-radius: 14px;
      background: rgba(245, 158, 11, 0.10);
      border: 1px solid rgba(245, 158, 11, 0.18);
      color: #fde68a;
      line-height: 1.5;
    }

    .citations-grid,
    .opportunities-grid {
      display: grid;
      gap: 14px;
    }

    .citations-grid {
      margin-top: 16px;
    }

    .opportunities-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .citation-card,
    .opportunity-card {
      padding: 16px;
    }

    .citation-card a {
      color: #c7d6ff;
      text-decoration: none;
      word-break: break-word;
    }

    .citation-card a:hover {
      text-decoration: underline;
    }

    .citation-snippet,
    .opportunity-copy {
      margin-top: 10px;
      color: var(--muted);
      line-height: 1.6;
      font-size: 14px;
    }

    .opportunity-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }

    .opportunity-title {
      margin: 0;
      font-size: 18px;
      letter-spacing: -0.03em;
    }

    .opportunity-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 14px;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(148, 163, 184, 0.10);
      border: 1px solid rgba(148, 163, 184, 0.12);
      color: #d7e3fb;
      font-size: 12px;
    }

    .samples {
      margin-top: 16px;
      display: grid;
      gap: 10px;
    }

    .source-list {
      display: grid;
      gap: 12px;
    }

    .source-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      border-radius: 16px;
      background: rgba(148, 163, 184, 0.08);
      border: 1px solid rgba(148, 163, 184, 0.12);
    }

    .source-name {
      font-weight: 600;
    }

    .source-meta {
      color: var(--muted);
      font-size: 13px;
    }

    .sample {
      padding: 12px 14px;
      border-radius: 14px;
      background: rgba(10, 18, 34, 0.65);
      border: 1px solid rgba(148, 163, 184, 0.12);
      color: #ccdaef;
      font-size: 13px;
      line-height: 1.55;
    }

    .empty {
      padding: 22px;
      border-radius: 18px;
      border: 1px dashed rgba(148, 163, 184, 0.18);
      color: var(--muted);
      text-align: center;
      background: rgba(148, 163, 184, 0.06);
    }

    .footer-note {
      margin-top: 14px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }

    .live-counter {
      margin-top: 16px;
      padding: 14px 16px;
      border-radius: 16px;
      background: rgba(34, 197, 94, 0.10);
      border: 1px solid rgba(34, 197, 94, 0.18);
    }

    .live-counter-label {
      color: #bbf7d0;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .live-counter-value {
      margin-top: 8px;
      font-size: 28px;
      font-weight: 700;
    }

    .live-counter-note {
      margin-top: 6px;
      color: var(--muted);
      font-size: 13px;
    }

    .completed-sources {
      margin-top: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .completed-source-chip {
      display: inline-flex;
      align-items: center;
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(34, 197, 94, 0.12);
      border: 1px solid rgba(34, 197, 94, 0.2);
      color: #bbf7d0;
      font-size: 12px;
    }

    @media (max-width: 1120px) {
      .hero,
      .main-focus,
      .dashboard,
      .pipeline-grid,
      .metrics {
        grid-template-columns: 1fr;
      }

      .opportunities-grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 720px) {
      .shell { padding: 16px; }
      .hero-card,
      .summary-card,
      .panel,
      .metric-card { padding: 18px; }
      .ask-row { grid-template-columns: 1fr; }
      .actions { flex-direction: column; }
      .actions button { width: 100%; }
      h1 { max-width: none; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="hero-card">
        <div class="eyebrow">Internal research copilot</div>
        <h1>Myntra Wishlist Discovery</h1>
        <p class="hero-copy">
          Explore why high-intent shoppers add fashion items to wishlists but do not convert.
          This dashboard keeps the output grounded in evidence and explicitly filters out
          discounts, cashback, coupons, and other monetary incentives.
        </p>
        <div class="hero-chips">
          <span class="chip">Play Store, Reddit, DuckDuckGo, forum, Kaggle Myntra reviews</span>
          <span class="chip">Evidence-backed answers</span>
          <span class="chip">Non-monetary recommendation guardrail</span>
        </div>
      </div>
      <div class="summary-card">
        <div>
          <div class="summary-label">Coverage snapshot</div>
          <div class="summary-value" id="summaryCoverage">No data loaded</div>
          <div class="summary-note" id="summaryCoverageCopy">Run the slice or reload outputs to populate the latest source coverage and opportunity counts.</div>
        </div>
        <div class="live-counter">
          <div class="live-counter-label">Live source counter</div>
          <div class="live-counter-value" id="liveSourceCounter">0 / 0</div>
          <div class="live-counter-note" id="liveSourceCounterNote">Waiting for a run to start.</div>
          <div class="completed-sources" id="completedSourcesBox"></div>
        </div>
        <div class="footer-note">
          Designed for fast product analysis: run the pipeline, inspect ranked opportunities, and ask grounded follow-up questions in one place.
        </div>
      </div>
    </section>

    <section class="tab-shell">
      <div class="tabs" role="tablist" aria-label="Discovery views">
        <button id="insightsTabBtn" class="tab-button active" type="button" data-tab="insights" role="tab" aria-selected="true">Ranked opportunities</button>
        <button id="coverageTabBtn" class="tab-button" type="button" data-tab="coverage" role="tab" aria-selected="false">Coverage metrics</button>
      </div>

      <section id="insightsTab" class="tab-pane active" role="tabpanel">
        <div class="main-focus">
          <div class="panel">
            <div class="panel-header">
              <div>
                <h2 class="panel-title">Ranked opportunities</h2>
                <p class="panel-subtitle">Top friction themes are shown as cards with confidence, evidence counts, and sample excerpts.</p>
              </div>
              <div class="actions">
                <a id="downloadOpportunitiesBtn" class="button-link secondary" href="/api/ranked-opportunities.md" download="ranked_opportunities.md">Download opportunities (.md)</a>
              </div>
            </div>
            <div id="opportunitiesBox" class="opportunities-grid"></div>
          </div>

          <div class="panel">
            <div class="panel-header">
              <div>
                <h2 class="panel-title">Ask the engine</h2>
                <p class="panel-subtitle">Query the indexed evidence and get a grounded answer with confidence and source citations.</p>
              </div>
            </div>
            <input id="questionInput" class="question-input" type="text" value="What's the top friction point for footwear under ₹2000?" />
            <div class="ask-row">
              <button id="askBtn" class="primary" type="button">Ask question</button>
              <a id="downloadAnswerBtn" class="button-link secondary disabled" href="/api/final-answer.md" download="final_answer.md">Download answer (.md)</a>
            </div>
            <div id="answerBox" class="answer-card">
              <div class="answer-meta">
                <strong>Answer</strong>
                <span class="badge low" id="confidenceBadge">Not run</span>
              </div>
              <div id="answerText" class="answer-text">Run the slice and ask a question to see a grounded answer.</div>
              <div id="noticeBox"></div>
            </div>
            <div id="citationsBox" class="citations-grid"></div>
          </div>
        </div>
      </section>

      <section id="coverageTab" class="tab-pane" role="tabpanel">
        <div class="dashboard">
          <div class="stack">
            <section class="metrics">
              <div class="metric-card">
                <div class="metric-label">Source Types</div>
                <div class="metric-value" id="metricSources">0</div>
                <div class="metric-sub" id="metricSourcesSub">No source coverage yet</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Parsed</div>
                <div class="metric-value" id="metricFetched">0</div>
                <div class="metric-sub" id="metricFetchedSub">Raw records ingested</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Cleaned</div>
                <div class="metric-value" id="metricCleaned">0</div>
                <div class="metric-sub" id="metricCleanedSub">Unique normalized records</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Relevant</div>
                <div class="metric-value" id="metricRelevant">0</div>
                <div class="metric-sub" id="metricRelevantSub">Wishlist-related text units</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Opportunities</div>
                <div class="metric-value" id="metricOpportunities">0</div>
                <div class="metric-sub" id="metricOpportunitiesSub">No ranked themes yet</div>
              </div>
            </section>

            <div class="panel">
              <div class="panel-header">
                <div>
                  <h2 class="panel-title">Pipeline control</h2>
                  <p class="panel-subtitle">Run the local seeded vertical slice, then inspect source coverage and output quality.</p>
                </div>
                <div class="actions">
                  <button id="runBtn" class="primary" type="button">Run full pipeline</button>
                  <button id="refreshBtn" class="secondary" type="button">Reload outputs</button>
                </div>
              </div>

              <div class="pipeline-grid">
                <div class="pipeline-steps">
                  <div class="step">
                    <div class="step-kicker">Step 1</div>
                    <div>Ingest evidence</div>
                    <div class="step-copy">Loads Play Store, Reddit, DuckDuckGo, forum, Crawlee, and optional Myntra Kaggle sources into the local SQLite store with deduped content hashes.</div>
                  </div>
                  <div class="step">
                    <div class="step-kicker">Step 2</div>
                    <div>Classify intent + friction</div>
                    <div class="step-copy">Tags each unit with intent, friction type, comparison behavior, off-platform research, and other context hints.</div>
                  </div>
                  <div class="step">
                    <div class="step-kicker">Step 3</div>
                    <div>Rank opportunities</div>
                    <div class="step-copy">Groups evidence into opportunity themes and applies the hard filter against monetary-incentive recommendations.</div>
                  </div>
                </div>
                <div id="statusBox" class="status-box">Ready. Click “Run full pipeline” to refresh source coverage, cleaned records, and the latest opportunities.</div>
              </div>
            </div>
          </div>

          <div class="stack">
            <div class="panel">
              <div class="panel-header">
                <div>
                  <h2 class="panel-title">Source coverage</h2>
                  <p class="panel-subtitle">See how many sources were taken, how many records were cleaned, and the breakdown by source.</p>
                </div>
              </div>
              <div id="sourceBox" class="source-list"></div>
            </div>
          </div>
        </div>
      </section>
    </section>
  </div>

  <script>
    let progressPollTimer = null;
    let latestAnswerMarkdownUrl = '/api/final-answer.md';

    function byId(id) {
      return document.getElementById(id);
    }

    function withCacheBust(url) {
      const separator = url.indexOf('?') >= 0 ? '&' : '?';
      return url + separator + 't=' + Date.now();
    }

    function escapeHtml(value) {
      return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function titleizeToken(value) {
      return String(value || '')
        .replace(/_/g, ' ')
        .replace(/:/g, ' · ')
        .replace(/\b\w/g, function(match) { return match.toUpperCase(); });
    }

    function activateTab(tabName) {
      const isInsights = tabName !== 'coverage';
      byId('insightsTab').classList.toggle('active', isInsights);
      byId('coverageTab').classList.toggle('active', !isInsights);
      byId('insightsTabBtn').classList.toggle('active', isInsights);
      byId('coverageTabBtn').classList.toggle('active', !isInsights);
      byId('insightsTabBtn').setAttribute('aria-selected', isInsights ? 'true' : 'false');
      byId('coverageTabBtn').setAttribute('aria-selected', isInsights ? 'false' : 'true');
    }

    async function fetchJson(url, options) {
      const requestOptions = Object.assign({ cache: 'no-store' }, options || {});
      const method = (requestOptions.method || 'GET').toUpperCase();
      const requestUrl = method === 'GET' ? withCacheBust(url) : url;
      const res = await fetch(requestUrl, requestOptions);
      if (!res.ok) {
        throw new Error('Request failed with status ' + res.status);
      }
      return await res.json();
    }

    function renderMetrics(stats, opportunities) {
      const sourceTypes = stats.source_type_count || stats.source_count || 0;
      const parsedRecords = stats.parsed_records || stats.raw_records || 0;
      const uniqueRecords = stats.unique_records || stats.cleaned_records || 0;
      byId('metricSources').textContent = String(sourceTypes);
      byId('metricSourcesSub').textContent = sourceTypes ? 'Distinct connector/source types currently indexed' : 'No source coverage yet';
      byId('metricFetched').textContent = String(parsedRecords);
      byId('metricFetchedSub').textContent = 'Total records parsed before dedupe/classification';
      byId('metricCleaned').textContent = String(uniqueRecords);
      byId('metricCleanedSub').textContent = 'Unique normalized records';
      byId('metricRelevant').textContent = String(stats.relevant_records || 0);
      byId('metricRelevantSub').textContent = 'Wishlist-related records after classification';
      byId('metricOpportunities').textContent = String(stats.opportunity_count || opportunities.length || 0);
      byId('metricOpportunitiesSub').textContent = (stats.opportunity_count || opportunities.length) ? 'Ranked friction themes loaded' : 'No ranked themes yet';

      const sources = sourceTypes;
      const cleaned = uniqueRecords;
      const opportunitiesCount = stats.opportunity_count || opportunities.length || 0;
      byId('summaryCoverage').textContent = sources + ' source types · ' + cleaned + ' unique records';
      byId('summaryCoverageCopy').textContent =
        opportunitiesCount
          ? opportunitiesCount + ' ranked opportunities are available for grounded Q&A.'
          : 'Run the slice or reload outputs to populate the latest source coverage and opportunity counts.';
    }

    function renderOpportunities(opportunities) {
      const box = byId('opportunitiesBox');
      if (!opportunities.length) {
        box.innerHTML = '<div class="empty">No opportunities found yet. Run the slice to generate them.</div>';
        return;
      }

      const sortedOpportunities = opportunities.slice().sort(function(left, right) {
        function isBottomBucket(opportunity) {
          const name = String(opportunity.name || '');
          const frictionTypes = opportunity.friction_types || [];
          const intentSignals = opportunity.intent_signals || [];
          const isOther = name.indexOf('other:') === 0 || frictionTypes.indexOf('other') !== -1;
          const isUnclear = name.endsWith(':unclear') || intentSignals.indexOf('unclear') !== -1;
          return isOther || isUnclear;
        }

        const leftBottom = isBottomBucket(left);
        const rightBottom = isBottomBucket(right);
        if (leftBottom !== rightBottom) return leftBottom ? 1 : -1;

        const leftEvidence = Number(left.evidence_count || 0);
        const rightEvidence = Number(right.evidence_count || 0);
        if (leftEvidence !== rightEvidence) return rightEvidence - leftEvidence;

        const leftSources = Number(left.source_count || 0);
        const rightSources = Number(right.source_count || 0);
        if (leftSources !== rightSources) return rightSources - leftSources;

        return String(left.name || '').localeCompare(String(right.name || ''));
      });

      box.innerHTML = sortedOpportunities.map(function(opportunity) {
        const samples = (opportunity.sample_excerpts || []).slice(0, 2).map(function(sample) {
          return '<div class="sample">' + escapeHtml(sample) + '</div>';
        }).join('');

        return (
          '<article class="opportunity-card">' +
            '<div class="opportunity-head">' +
              '<div>' +
                '<h3 class="opportunity-title">' + escapeHtml(titleizeToken(opportunity.name)) + '</h3>' +
                '<div class="opportunity-copy">' + escapeHtml(opportunity.description) + '</div>' +
              '</div>' +
              '<span class="badge ' + escapeHtml(opportunity.confidence_tier) + '">' + escapeHtml(opportunity.confidence_tier) + '</span>' +
            '</div>' +
            '<div class="opportunity-meta">' +
              '<span class="pill">' + escapeHtml(String(opportunity.evidence_count)) + ' evidence</span>' +
              '<span class="pill">' + escapeHtml(String(opportunity.source_count)) + ' sources</span>' +
            '</div>' +
            '<div class="samples">' + samples + '</div>' +
          '</article>'
        );
      }).join('');
    }

    function renderAnswer(data) {
      const badge = byId('confidenceBadge');
      const answerText = byId('answerText');
      const noticeBox = byId('noticeBox');
      const citationsBox = byId('citationsBox');
      const downloadAnswerBtn = byId('downloadAnswerBtn');

      badge.className = 'badge ' + (data.confidence_tier || 'low');
      badge.textContent = (data.confidence_tier || 'low') + ' confidence';
      answerText.textContent = data.answer_text || 'No answer returned.';
      latestAnswerMarkdownUrl = data.answer_markdown_url || '/api/final-answer.md';
      downloadAnswerBtn.href = latestAnswerMarkdownUrl;
      downloadAnswerBtn.classList.remove('disabled');

      if (data.out_of_scope_notice) {
        noticeBox.innerHTML = '<div class="notice">' + escapeHtml(data.out_of_scope_notice) + '</div>';
      } else {
        noticeBox.innerHTML = '';
      }

      if (!data.citations || !data.citations.length) {
        citationsBox.innerHTML = '<div class="empty">No citations returned.</div>';
        return;
      }

      citationsBox.innerHTML = data.citations.map(function(citation) {
        return (
          '<div class="citation-card">' +
            '<a href="' + escapeHtml(citation.url) + '" target="_blank" rel="noreferrer">' + escapeHtml(citation.url) + '</a>' +
            '<div class="citation-snippet">' + escapeHtml(citation.snippet) + '</div>' +
          '</div>'
        );
      }).join('');
    }

    function renderSources(stats) {
      const box = byId('sourceBox');
      const breakdown = stats.source_breakdown || {};
      const names = Object.keys(breakdown);

      if (!names.length) {
        box.innerHTML = '<div class="empty">No source coverage yet. Run the slice to load the source breakdown.</div>';
        return;
      }

      box.innerHTML = names.map(function(name) {
        return (
          '<div class="source-item">' +
            '<div>' +
              '<div class="source-name">' + escapeHtml(titleizeToken(name)) + '</div>' +
              '<div class="source-meta">' + escapeHtml(String(breakdown[name])) + ' cleaned records</div>' +
            '</div>' +
            '<span class="pill">' + escapeHtml(String(breakdown[name])) + '</span>' +
          '</div>'
        );
      }).join('');
    }

    function renderStatus(data) {
      byId('statusBox').textContent =
        'Sources taken: ' + data.ingest.source_count + '\\n' +
        'Fetched records: ' + data.ingest.total_records + '\\n' +
        'Cleaned records: ' + data.ingest.cleaned_records + '\\n' +
        'Duplicates removed: ' + data.ingest.duplicates_removed + '\\n' +
        'Classified this run: ' + data.classify.classified + '\\n' +
        'Opportunities generated: ' + data.aggregate.opportunity_count + '\\n' +
        'Outputs refreshed successfully.';
    }

    function renderDashboardStatus(stats, opportunities, progress, mode) {
      const sourceCount = stats.source_type_count || stats.source_count || 0;
      const fetched = stats.parsed_records || stats.raw_records || 0;
      const cleaned = stats.unique_records || stats.cleaned_records || 0;
      const classified = stats.classified_records || 0;
      const opportunitiesCount = stats.opportunity_count || opportunities.length || 0;
      const duplicatesRemoved = stats.duplicates_removed || 0;
      const prefix = mode === 'reload' ? 'Dashboard reloaded' : 'Dashboard ready';
      byId('statusBox').textContent =
        prefix + '\\n' +
        'Source types: ' + sourceCount + '\\n' +
        'Parsed records: ' + fetched + '\\n' +
        'Unique records: ' + cleaned + '\\n' +
        'Duplicates removed: ' + duplicatesRemoved + '\\n' +
        'Classified records: ' + classified + '\\n' +
        'Opportunities available: ' + opportunitiesCount + '\\n' +
        'Status: ' + ((progress && progress.message) || 'Ready');
    }

    function renderLiveProgress(progress) {
      const completed = progress.sources_completed || 0;
      const total = progress.total_sources || 0;
      const completedSources = progress.completed_sources || [];
      byId('liveSourceCounter').textContent = completed + ' / ' + total;
      byId('liveSourceCounterNote').textContent = progress.message || 'Waiting for a run to start.';
      byId('completedSourcesBox').innerHTML = completedSources.length
        ? completedSources.map(function(source) {
            return '<span class="completed-source-chip">' + escapeHtml(titleizeToken(source)) + ' done</span>';
          }).join('')
        : '';
      if (progress.status === 'running') {
        byId('statusBox').textContent =
          'Live progress\\n' +
          'Sources ingested: ' + completed + ' / ' + total + '\\n' +
          'Fetched records: ' + (progress.fetched_records || 0) + '\\n' +
          'Cleaned records: ' + (progress.cleaned_records || 0) + '\\n' +
          'Message: ' + (progress.message || 'Running...');
        return;
      }
      if (progress.status === 'completed') {
        byId('statusBox').textContent =
          'Pipeline complete\\n' +
          'Sources ingested: ' + completed + ' / ' + total + '\\n' +
          'Fetched records: ' + (progress.fetched_records || 0) + '\\n' +
          'Cleaned records: ' + (progress.cleaned_records || 0) + '\\n' +
          'Classified records: ' + (progress.classified_records || 0) + '\\n' +
          'Opportunities generated: ' + (progress.opportunity_count || 0);
      }
    }

    async function fetchProgress() {
      const progress = await fetchJson('/api/progress');
      renderLiveProgress(progress);
      if (progress.status === 'running') {
        return;
      }
      if (progress.status === 'completed') {
        stopProgressPolling();
        await reloadOutputs('completed');
        return;
      }
      if (progress.status === 'error') {
        stopProgressPolling();
        byId('statusBox').textContent = progress.message || 'Run failed.';
      }
    }

    function startProgressPolling() {
      stopProgressPolling();
      progressPollTimer = setInterval(function() {
        fetchProgress().catch(function(error) {
          byId('statusBox').textContent = 'Progress polling failed: ' + error.message;
          stopProgressPolling();
        });
      }, 1000);
    }

    function stopProgressPolling() {
      if (progressPollTimer) {
        clearInterval(progressPollTimer);
        progressPollTimer = null;
      }
    }

    async function reloadOutputs(mode) {
      try {
        byId('statusBox').textContent = mode === 'reload' ? 'Reloading dashboard...' : 'Loading dashboard...';
        const data = await fetchJson('/api/dashboard');
        const opportunities = data.opportunities || [];
        const stats = data.stats || {};
        const progress = data.progress || {};
        const effectiveProgress = (progress.total_sources || progress.sources_completed)
          ? progress
          : {
              status: (stats.source_type_count || stats.source_count) ? 'completed' : 'idle',
              message: (stats.source_type_count || stats.source_count) ? 'Loaded latest stored pipeline results.' : 'Waiting for a run to start.',
              sources_completed: stats.source_type_count || stats.source_count || 0,
              total_sources: stats.source_type_count || stats.source_count || 0,
              completed_sources: [],
              fetched_records: stats.parsed_records || stats.raw_records || 0,
              cleaned_records: stats.unique_records || stats.cleaned_records || 0,
              classified_records: stats.classified_records || 0,
              opportunity_count: stats.opportunity_count || opportunities.length || 0
            };
        renderMetrics(stats, opportunities);
        renderOpportunities(opportunities);
        renderSources(stats);
        renderLiveProgress(effectiveProgress);
        renderDashboardStatus(stats, opportunities, effectiveProgress, mode);
      } catch (error) {
        byId('statusBox').textContent = 'Reload failed: ' + error.message;
      }
    }

    async function runSlice() {
      byId('statusBox').textContent = 'Starting background run...';
      byId('liveSourceCounter').textContent = '0 / 0';
      byId('liveSourceCounterNote').textContent = 'Preparing ingestion...';
      byId('completedSourcesBox').innerHTML = '';
      try {
        await fetchJson('/api/run-all', { method: 'POST' });
        startProgressPolling();
        await fetchProgress();
      } catch (error) {
        byId('statusBox').textContent = 'Run failed: ' + error.message;
      }
    }

    async function askQuestion() {
      const question = byId('questionInput').value.trim();
      if (!question) {
        byId('answerText').textContent = 'Please enter a question.';
        return;
      }

      byId('answerText').textContent = 'Retrieving evidence and drafting a grounded answer...';
      byId('citationsBox').innerHTML = '';
      byId('downloadAnswerBtn').classList.add('disabled');
      byId('downloadAnswerBtn').href = latestAnswerMarkdownUrl;

      try {
        const data = await fetchJson('/api/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: question })
        });
        renderAnswer(data);
      } catch (error) {
        byId('answerText').textContent = 'Question failed: ' + error.message;
      }
    }

    byId('runBtn').addEventListener('click', runSlice);
    byId('refreshBtn').addEventListener('click', function() { reloadOutputs('reload'); });
    byId('askBtn').addEventListener('click', askQuestion);
    byId('insightsTabBtn').addEventListener('click', function() { activateTab('insights'); });
    byId('coverageTabBtn').addEventListener('click', function() { activateTab('coverage'); });
    byId('questionInput').addEventListener('keydown', function(event) {
      if (event.key === 'Enter') askQuestion();
    });

    activateTab('insights');
    reloadOutputs('initial');
    fetchProgress().catch(function() { return null; });
  </script>
</body>
</html>
"""


class DiscoveryRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(HTML_PAGE)
            return
        if parsed.path == "/api/dashboard":
            opportunities_path = ROOT / "productpilot" / "discovery" / "data" / "outputs" / "opportunities.json"
            opportunities = []
            if opportunities_path.exists():
                opportunities = sort_opportunities_payload(json.loads(opportunities_path.read_text(encoding="utf-8")))
            self._send_json(
                {
                    "stats": SERVICE.dashboard_stats(),
                    "opportunities": opportunities,
                    "progress": snapshot_run_state(),
                }
            )
            return
        if parsed.path == "/api/progress":
            self._send_json(snapshot_run_state())
            return
        if parsed.path == "/api/final-answer.md":
            if not FINAL_ANSWER_PATH.exists():
                self._send_json({"error": "Final answer markdown not found"}, status=404)
                return
            self._send_markdown(
                FINAL_ANSWER_PATH.read_text(encoding="utf-8"),
                filename="final_answer.md",
            )
            return
        if parsed.path == "/api/ranked-opportunities.md":
            if not RANKED_OPPORTUNITIES_PATH.exists():
                self._send_json({"error": "Ranked opportunities markdown not found"}, status=404)
                return
            self._send_markdown(
                RANKED_OPPORTUNITIES_PATH.read_text(encoding="utf-8"),
                filename="ranked_opportunities.md",
            )
            return
        if parsed.path == "/api/opportunities":
            opportunities_path = ROOT / "productpilot" / "discovery" / "data" / "outputs" / "opportunities.json"
            opportunities = []
            if opportunities_path.exists():
                opportunities = sort_opportunities_payload(json.loads(opportunities_path.read_text(encoding="utf-8")))
            self._send_json({"opportunities": opportunities})
            return
        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/run-all":
            state = snapshot_run_state()
            if state.get("is_running"):
                self._send_json({"started": False, "status": "already_running"})
                return
            worker = threading.Thread(target=execute_pipeline_job, daemon=True)
            worker.start()
            self._send_json({"started": True, "status": "running"})
            return
        if parsed.path == "/api/ask":
            body = self._read_json()
            question = str(body.get("question", "")).strip()
            answer = SERVICE.answer(question)
            answer["answer_markdown_url"] = "/api/final-answer.md"
            self._send_json(answer)
            return
        self._send_json({"error": "Not found"}, status=404)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _send_html(self, html: str, status: int = 200) -> None:
        payload = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, data: Dict[str, Any], status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_markdown(self, content: str, filename: str, status: int = 200) -> None:
        payload = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/markdown; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Content-Disposition", 'attachment; filename="{0}"'.format(filename))
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    host = "127.0.0.1"
    port = 8765
    server = ThreadingHTTPServer((host, port), DiscoveryRequestHandler)
    print("Serving Myntra discovery UI at http://{0}:{1}".format(host, port))
    server.serve_forever()


if __name__ == "__main__":
    main()
