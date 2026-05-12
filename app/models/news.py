# app/models/news.py

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime

# ─────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────

class CredibilityLabel(str, Enum):
    """
    The three possible outcomes of fake-news detection.
    'str' mixin means the value IS the string (e.g. "credible"),
    which makes JSON serialization automatic.
    """
    credible    = "credible"
    misleading  = "misleading"
    fake        = "fake"


# ─────────────────────────────────────────
# NESTED RESULT MODELS (used inside NewsResponse)
# ─────────────────────────────────────────

class SentimentResult(BaseModel):
    """Mirrors the SentimentResult in candidate.py — reused here for news."""
    label:         str   # "positive", "negative", or "neutral"
    score:         float # confidence from 0.0 to 1.0
    analyzed_text: str   # the text that was actually sent to the model


class FakeNewsResult(BaseModel):
    """What the fake-news detection service returns."""
    label:         CredibilityLabel  # credible / misleading / fake
    score:         float             # confidence from 0.0 to 1.0
    analyzed_text: str               # text sent to the model


# ─────────────────────────────────────────
# CORE MODELS
# ─────────────────────────────────────────

class NewsBase(BaseModel):
    """
    Shared fields between Create and Response.
    Never use this directly in a route — only subclass it.
    """
    headline:    str = Field(..., min_length=5,   max_length=300)
    content:     str = Field(..., min_length=20,  max_length=5000)
    source:      str = Field(..., min_length=2,   max_length=100)
    url:         Optional[str] = None
    election_id: Optional[int] = None  # links article to an election


class NewsCreate(NewsBase):
    """
    What the client sends in the POST /news/ request body.
    No 'id', no AI results — those are server-side.
    """
    pass  # inherits everything from NewsBase


class NewsResponse(NewsBase):
    """
    What the API returns. Includes server-generated fields
    and optional AI analysis results (None until /analyze is called).
    """
    id:              int
    created_at:      datetime

    # These are None until POST /news/{id}/analyze is called
    credibility:     Optional[CredibilityLabel] = None
    sentiment:       Optional[SentimentResult]  = None
    fake_news:       Optional[FakeNewsResult]   = None

    # Pydantic v2: enables reading from ORM objects / dicts
    model_config = {"from_attributes": True}