# app/routers/news.py

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.database import get_db
from app.db_models.news import NewsArticle
from app.models.news import (
    NewsCreate,
    NewsResponse,
    CredibilityLabel
)

router = APIRouter(prefix="/news", tags=["News"])


# ── Helper ────────────────────────────────────────────────────────────────────
async def get_article_or_404(article_id: int, db: AsyncSession) -> NewsArticle:
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
    return article


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/", response_model=List[NewsResponse])
async def list_news(
    election_id: Optional[int] = None,
    label: Optional[CredibilityLabel] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all news articles with optional filters."""
    query = select(NewsArticle)

    if election_id:
        query = query.where(NewsArticle.election_id == election_id)
    if label:
        query = query.where(NewsArticle.credibility == label)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{article_id}", response_model=NewsResponse)
async def get_article(
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a single news article by ID."""
    return await get_article_or_404(article_id, db)


@router.post("/", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    payload: NewsCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new news article."""
    # If election_id provided, verify it exists
    if payload.election_id:
        from app.db_models.election import Election
        election_check = await db.execute(
            select(Election).where(Election.id == payload.election_id)
        )
        if not election_check.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail=f"Election {payload.election_id} not found"
            )

    new_article = NewsArticle(**payload.model_dump())
    db.add(new_article)
    await db.flush()
    await db.refresh(new_article)
    return new_article


@router.post("/{article_id}/analyze", response_model=NewsResponse)
async def analyze_article(
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Run both sentiment analysis and fake news detection on an article."""
    from app.services.sentiment import analyze_sentiment
    from app.services.fake_news import detect_fake_news

    article = await get_article_or_404(article_id, db)

    # Run sentiment on headline
    sentiment = analyze_sentiment(article.headline)
    article.sentiment_label = sentiment["label"]
    article.sentiment_score = sentiment["score"]

    # Run fake news detection on full content
    fake_news = detect_fake_news(article.content)
    article.fake_news_label = fake_news["label"]
    article.fake_news_score = fake_news["score"]

    # Map fake news label to credibility enum
    label_map = {
        "credible": CredibilityLabel.credible,
        "misleading": CredibilityLabel.misleading,
        "fake": CredibilityLabel.fake
    }
    article.credibility = label_map.get(fake_news["label"], CredibilityLabel.misleading)
    article.credibility_score = fake_news["score"]

    await db.flush()
    await db.refresh(article)
    return article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a news article by ID."""
    article = await get_article_or_404(article_id, db)
    await db.delete(article)