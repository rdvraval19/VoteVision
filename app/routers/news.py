# app/routers/news.py

from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional, List
from datetime import datetime

from app.models.news import NewsCreate, NewsResponse, FakeNewsResult
from app.models.candidate import SentimentResult   # reuse the same model shape
from app.services.fake_news import detect_fake_news
from app.services.sentiment import analyze_sentiment

router = APIRouter(prefix="/news", tags=["News"])

# ─────────────────────────────────────────
# In-memory "database" (replaced by PostgreSQL in Step 6)
# Using a dict for O(1) lookup by id.
# ─────────────────────────────────────────
_news_db: dict[int, dict] = {}
_next_id: int = 1  # auto-increment counter


# ─────────────────────────────────────────
# GET /news/
# ─────────────────────────────────────────
@router.get("/", response_model=List[NewsResponse])
def list_articles(
    election_id: Optional[int] = Query(None, description="Filter by election ID"),
    label:       Optional[str] = Query(None, description="Filter by credibility label: credible, misleading, fake"),
):
    """
    Returns all news articles.
    Optional filters: ?election_id=1 and/or ?label=fake
    """
    articles = list(_news_db.values())

    if election_id is not None:
        articles = [a for a in articles if a.get("election_id") == election_id]

    if label is not None:
        # credibility is stored as a string inside the dict
        articles = [a for a in articles if a.get("credibility") == label]

    return articles


# ─────────────────────────────────────────
# GET /news/{id}
# ─────────────────────────────────────────
@router.get("/{article_id}", response_model=NewsResponse)
def get_article(article_id: int):
    """Returns a single news article by ID. 404 if not found."""
    if article_id not in _news_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News article with id={article_id} not found.",
        )
    return _news_db[article_id]


# ─────────────────────────────────────────
# POST /news/
# ─────────────────────────────────────────
@router.post("/", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
def create_article(article: NewsCreate):
    """
    Create a new news article.
    AI analysis is NOT run automatically — call /news/{id}/analyze separately.
    """
    global _next_id

    new_article = {
        **article.model_dump(),   # unpack all Pydantic fields into a dict
        "id":         _next_id,
        "created_at": datetime.utcnow(),
        # AI fields start as None — populated by /analyze
        "credibility": None,
        "sentiment":   None,
        "fake_news":   None,
    }

    _news_db[_next_id] = new_article
    _next_id += 1

    return new_article


# ─────────────────────────────────────────
# POST /news/{id}/analyze
# ─────────────────────────────────────────
@router.post("/{article_id}/analyze", response_model=NewsResponse)
def analyze_article(article_id: int):
    """
    Run BOTH sentiment analysis AND fake news detection on this article.

    Uses the article's 'content' field as input to both models.
    Updates the stored article with results and returns the full record.

    Note: First call downloads AI models (~1.6 GB). Be patient.
    """
    if article_id not in _news_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News article with id={article_id} not found.",
        )

    article = _news_db[article_id]

    # ── Run sentiment analysis (from Step 3) ──
    sentiment_raw = analyze_sentiment(article["content"])
    # Wrap in the Pydantic model, then convert back to dict for storage
    sentiment_result = SentimentResult(**sentiment_raw).model_dump()

    # ── Run fake news detection (Step 4) ──
    fake_news_raw = detect_fake_news(article["content"])
    fake_news_result = FakeNewsResult(**fake_news_raw).model_dump()

    # ── Update the stored record ──
    article["sentiment"]   = sentiment_result
    article["fake_news"]   = fake_news_result
    article["credibility"] = fake_news_result["label"]  # top-level shortcut

    return article


# ─────────────────────────────────────────
# DELETE /news/{id}
# ─────────────────────────────────────────
@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(article_id: int):
    """Removes a news article. Returns 204 No Content on success."""
    if article_id not in _news_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News article with id={article_id} not found.",
        )
    del _news_db[article_id]