"""FastAPI app for the discovery engine chat endpoint."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from productpilot.discovery.service import DiscoveryEngineService


app = FastAPI(title="Myntra Wishlist Discovery Engine")
service = DiscoveryEngineService(Path(__file__).resolve().parents[3])


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/chat")
def chat(question: str) -> Dict[str, object]:
    return service.answer(question)
