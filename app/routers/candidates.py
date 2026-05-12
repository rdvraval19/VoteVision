from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.database import get_db
from app.db_models.candidate import Candidate
from app.db_models.election import Election

from app.models.candidate import (
    CandidateCreate,
    CandidateResponse,
    CandidateStatus,
    PoliticalParty,
)

from app.services.sentiment import analyze_sentiment as run_sentiment

router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"],
)


# ─────────────────────────────────────────────
# Helper Function
# ─────────────────────────────────────────────
async def get_candidate_or_404(
    candidate_id: int,
    db: AsyncSession
) -> Candidate:

    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id)
    )

    candidate = result.scalar_one_or_none()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate with ID {candidate_id} not found."
        )

    return candidate


# ─────────────────────────────────────────────
# GET /candidates
# Returns all candidates with optional filters
# ─────────────────────────────────────────────
@router.get("/", response_model=List[CandidateResponse])
async def get_all_candidates(
    election_id: Optional[int] = Query(
        default=None,
        description="Filter candidates by election ID",
    ),
    party: Optional[PoliticalParty] = Query(
        default=None,
        description="Filter candidates by political party",
    ),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all candidates with optional filters."""

    query = select(Candidate)

    if election_id:
        query = query.where(Candidate.election_id == election_id)

    if party:
        query = query.where(Candidate.party == party)

    result = await db.execute(query)

    return result.scalars().all()


# ─────────────────────────────────────────────
# GET /candidates/{candidate_id}
# Returns a single candidate
# ─────────────────────────────────────────────
@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a specific candidate by ID."""

    return await get_candidate_or_404(candidate_id, db)


# ─────────────────────────────────────────────
# POST /candidates
# Create a new candidate
# ─────────────────────────────────────────────
@router.post(
    "/",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_candidate(
    payload: CandidateCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new candidate in the platform."""

    # Verify election exists
    election_result = await db.execute(
        select(Election).where(Election.id == payload.election_id)
    )

    election = election_result.scalar_one_or_none()

    if not election:
        raise HTTPException(
            status_code=404,
            detail=f"Election {payload.election_id} not found."
        )

    new_candidate = Candidate(
        **payload.model_dump(),
        status=CandidateStatus.active.value,
    )

    db.add(new_candidate)

    await db.commit()
    await db.refresh(new_candidate)

    return new_candidate


# ─────────────────────────────────────────────
# POST /candidates/{candidate_id}/analyze-sentiment
# AI Sentiment Analysis
# ─────────────────────────────────────────────
@router.post(
    "/{candidate_id}/analyze-sentiment",
    response_model=CandidateResponse,
)
async def analyze_candidate_sentiment(
    candidate_id: int = Path(..., gt=0),
    text: str = Query(
        ...,
        min_length=5,
        max_length=512,
        description="Text to analyze — tweet, speech, article, etc.",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Run AI-powered sentiment analysis on candidate-related text.
    """

    candidate = await get_candidate_or_404(candidate_id, db)

    # Run AI sentiment analysis
    sentiment_result = run_sentiment(text)

    # Save AI results into DB
    candidate.sentiment_label = sentiment_result["label"]
    candidate.sentiment_score = sentiment_result["score"]

    await db.commit()
    await db.refresh(candidate)

    return candidate


# ─────────────────────────────────────────────
# DELETE /candidates/{candidate_id}
# Delete candidate
# ─────────────────────────────────────────────
@router.delete(
    "/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_candidate(
    candidate_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
):
    """Delete a candidate."""

    candidate = await get_candidate_or_404(candidate_id, db)

    await db.delete(candidate)
    await db.commit()

    return