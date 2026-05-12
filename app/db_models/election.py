# app/db_models/election.py

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from app.database import Base
from app.models.election import ElectionType, ElectionStatus

class Election(Base):
    __tablename__ = "elections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    election_type = Column(SAEnum(ElectionType), nullable=False)
    status = Column(SAEnum(ElectionStatus), default=ElectionStatus.upcoming)
    state = Column(String(100), nullable=False)
    constituency = Column(String(200), nullable=True)
    total_voters = Column(Integer, nullable=True)

    # created_at is set automatically by the DB when a row is inserted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())