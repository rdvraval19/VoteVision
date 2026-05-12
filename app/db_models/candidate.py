# app/db_models/candidate.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
from app.models.candidate import PoliticalParty, CandidateStatus

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    party = Column(SAEnum(PoliticalParty), nullable=False)
    status = Column(SAEnum(CandidateStatus), default=CandidateStatus.active)
    age = Column(Integer, nullable=True)
    constituency = Column(String(200), nullable=True)

    # ForeignKey links this row to an election row — enforced at DB level
    election_id = Column(Integer, ForeignKey("elections.id"), nullable=False, index=True)

    # AI sentiment fields — nullable because they're populated after analysis
    sentiment_label = Column(String(50), nullable=True)
    sentiment_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())