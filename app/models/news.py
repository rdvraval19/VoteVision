from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from enum import Enum
from datetime import datetime


# ─────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────

class CredibilityLabel(str, Enum):
    """
    Possible outcomes of fake-news detection.
    """
    credible = "credible"
    misleading = "misleading"
    fake = "fake"


# ─────────────────────────────────────────
# NESTED AI RESULT MODELS
# ─────────────────────────────────────────

class SentimentResult(BaseModel):
    """
    Sentiment analysis response structure.
    """
    label: str
    score: float
    analyzed_text: str


class FakeNewsResult(BaseModel):
    """
    Fake news analysis response structure.
    """
    label: CredibilityLabel
    score: float
    analyzed_text: str


# ─────────────────────────────────────────
# BASE MODEL
# ─────────────────────────────────────────

class NewsBase(BaseModel):
    """
    Shared fields for NewsCreate and NewsResponse.
    """

    headline: str = Field(
        ...,
        min_length=5,
        max_length=500
    )

    content: str = Field(
        ...,
        min_length=10,
        max_length=5000
    )

    source: Optional[str] = Field(
        default=None,
        max_length=200
    )

    url: Optional[str] = Field(
        default=None,
        max_length=500
    )

    election_id: Optional[int] = None


# ─────────────────────────────────────────
# CREATE MODEL
# ─────────────────────────────────────────

class NewsCreate(NewsBase):
    """
    Request body for creating a news article.
    """
    pass


# ─────────────────────────────────────────
# RESPONSE MODEL
# ─────────────────────────────────────────

class NewsResponse(NewsBase):
    """
    Full API response model for news articles.
    Includes AI analysis results.
    """

    id: int

    # AI Analysis Fields
    credibility: Optional[CredibilityLabel] = None
    credibility_score: Optional[float] = None

    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None

    fake_news_label: Optional[str] = None
    fake_news_score: Optional[float] = None

    # Optional detailed nested objects
    sentiment: Optional[SentimentResult] = None
    fake_news: Optional[FakeNewsResult] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Pydantic v2 ORM compatibility
    model_config = ConfigDict(from_attributes=True)