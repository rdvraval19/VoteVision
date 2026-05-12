# app/models/candidate.py

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# --- Enum for Political Party ---
class PoliticalParty(str, Enum):
    bjp = "BJP"
    inc = "INC"
    aap = "AAP"
    sp = "SP"
    tmc = "TMC"
    other = "Other"


# --- Enum for Candidate Status ---
class CandidateStatus(str, Enum):
    active = "active"
    withdrawn = "withdrawn"
    disqualified = "disqualified"


# --- Base Model ---
class CandidateBase(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Full name of the candidate",
        examples=["Narendra Modi"],
    )
    party: PoliticalParty = Field(
        ...,
        description="Political party affiliation",
    )
    constituency: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Constituency the candidate is contesting from",
        examples=["Varanasi"],
    )
    election_id: int = Field(
        ...,
        gt=0,
        description="ID of the election this candidate belongs to",
    )
    bio: Optional[str] = Field(
        None,
        max_length=1000,
        description="Short biography or background of the candidate",
    )


# --- Create Model (client input) ---
class CandidateCreate(CandidateBase):
    pass


# --- Sentiment Result (nested inside response) ---
# This will hold the AI-generated sentiment score
class SentimentResult(BaseModel):
    label: str = Field(..., description="Sentiment label: positive, negative, or neutral")
    score: float = Field(..., description="Confidence score between 0 and 1")
    analyzed_text: str = Field(..., description="The text that was analyzed")


# --- Response Model (server output) ---
class CandidateResponse(CandidateBase):
    id: int
    status: CandidateStatus = CandidateStatus.active
    sentiment: Optional[SentimentResult] = Field(
        None,
        description="AI sentiment analysis result (populated when text is analyzed)",
    )

    class Config:
        from_attributes = True