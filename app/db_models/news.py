# app/db_models/news.py

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
from app.models.news import CredibilityLabel

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)

    # Text instead of String for long content — no length limit
    headline = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(200), nullable=True)
    url = Column(String(500), nullable=True)

    election_id = Column(Integer, ForeignKey("elections.id"), nullable=True, index=True)

    # AI analysis fields — all nullable until /analyze is called
    credibility = Column(SAEnum(CredibilityLabel), nullable=True)
    credibility_score = Column(Float, nullable=True)
    sentiment_label = Column(String(50), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    fake_news_label = Column(String(50), nullable=True)
    fake_news_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())