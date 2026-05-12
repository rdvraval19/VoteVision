# app/routers/candidates.py

from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Optional
from app.models.candidate import (
    CandidateCreate,
    CandidateResponse,
    CandidateStatus,
    SentimentResult,
)
from app.services.sentiment import analyze_sentiment

router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"],
)

# --- In-Memory Store ---
_candidates_db: List[dict] = [
    {
        "id": 1,
        "name": "Narendra Modi",
        "party": "BJP",
        "constituency": "Varanasi",
        "election_id": 1,
        "bio": "14th Prime Minister of India.",
        "status": "active",
        "sentiment": None,
    },
    {
        "id": 2,
        "name": "Rahul Gandhi",
        "party": "INC",
        "constituency": "Wayanad",
        "election_id": 1,
        "bio": "Leader of the Indian National Congress.",
        "status": "active",
        "sentiment": None,
    },
]

_next_id = 3


# ─────────────────────────────────────────────
# GET /candidates
# Returns all candidates, with optional filters
# ─────────────────────────────────────────────
@router.get("/", response_model=List[CandidateResponse])
def get_all_candidates(
    election_id: Optional[int] = Query(
        default=None,
        description="Filter candidates by election ID",
    ),
    party: Optional[str] = Query(
        default=None,
        description="Filter candidates by party name",
    ),
):
    """Retrieve all candidates with optional filters."""
    results = _candidates_db

    if election_id:
        results = [c for c in results if c["election_id"] == election_id]
    if party:
        results = [c for c in results if c["party"].lower() == party.lower()]

    return results


# ─────────────────────────────────────────────
# GET /candidates/{candidate_id}
# Returns a single candidate by ID
# ─────────────────────────────────────────────
@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    candidate_id: int = Path(..., gt=0),
):
    """Retrieve a specific candidate by their ID."""
    for candidate in _candidates_db:
        if candidate["id"] == candidate_id:
            return candidate

    raise HTTPException(
        status_code=404,
        detail=f"Candidate with ID {candidate_id} not found.",
    )


# ─────────────────────────────────────────────
# POST /candidates
# Register a new candidate
# ─────────────────────────────────────────────
@router.post("/", response_model=CandidateResponse, status_code=201)
def create_candidate(payload: CandidateCreate):
    """Register a new candidate in the platform."""
    global _next_id

    new_candidate = {
        "id": _next_id,
        **payload.model_dump(),
        "status": CandidateStatus.active.value,
        "sentiment": None,
    }

    _candidates_db.append(new_candidate)
    _next_id += 1

    return new_candidate


# ─────────────────────────────────────────────
# POST /candidates/{candidate_id}/analyze-sentiment
# THE AI ENDPOINT — runs sentiment analysis on provided text
# ─────────────────────────────────────────────
@router.post("/{candidate_id}/analyze-sentiment", response_model=CandidateResponse)
def analyze_candidate_sentiment(
    candidate_id: int = Path(..., gt=0),
    text: str = Query(
        ...,
        min_length=5,
        max_length=512,
        description="Text to analyze — a news headline, tweet, or speech excerpt about the candidate",
    ),
):
    """
    Run AI-powered sentiment analysis on any text related to a candidate.

    The result is stored on the candidate record and returned in the response.
    This endpoint powers VoteVision's public perception tracking feature.
    """
    # Find the candidate
    for candidate in _candidates_db:
        if candidate["id"] == candidate_id:

            # Call the AI service
            sentiment_result = analyze_sentiment(text)

            # Store the result on the candidate record
            candidate["sentiment"] = sentiment_result

            return candidate

    raise HTTPException(
        status_code=404,
        detail=f"Candidate with ID {candidate_id} not found.",
    )


# ─────────────────────────────────────────────
# DELETE /candidates/{candidate_id}
# ─────────────────────────────────────────────
@router.delete("/{candidate_id}", status_code=204)
def delete_candidate(candidate_id: int = Path(..., gt=0)):
    """Remove a candidate from the platform."""
    global _candidates_db

    for index, candidate in enumerate(_candidates_db):
        if candidate["id"] == candidate_id:
            _candidates_db.pop(index)
            return

    raise HTTPException(
        status_code=404,
        detail=f"Candidate with ID {candidate_id} not found.",
    )