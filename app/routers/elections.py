# app/routers/elections.py

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.database import get_db
from app.db_models.election import Election
from app.models.election import (
    ElectionCreate,
    ElectionResponse,
    ElectionStatus,
    ElectionSummaryResponse
)

router = APIRouter(prefix="/elections", tags=["Elections"])


# ── Helper ──────────────────────────────────────────────────────────────────
async def get_election_or_404(election_id: int, db: AsyncSession) -> Election:
    """Reusable helper — fetches an election or raises 404."""
    result = await db.execute(select(Election).where(Election.id == election_id))
    election = result.scalar_one_or_none()
    if not election:
        raise HTTPException(status_code=404, detail=f"Election {election_id} not found")
    return election


# ── Routes ───────────────────────────────────────────────────────────────────
@router.get("/", response_model=List[ElectionResponse])
async def list_elections(
    status: Optional[ElectionStatus] = None,
    db: AsyncSession = Depends(get_db)         # DB session injected here
):
    """List all elections, optionally filtered by status."""
    query = select(Election)
    if status:
        query = query.where(Election.status == status)

    result = await db.execute(query)
    elections = result.scalars().all()         # .scalars() extracts the ORM objects
    return elections


@router.get("/{election_id}", response_model=ElectionResponse)
async def get_election(
    election_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a single election by ID."""
    return await get_election_or_404(election_id, db)


@router.post("/", response_model=ElectionResponse, status_code=status.HTTP_201_CREATED)
async def create_election(
    payload: ElectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new election."""
    # Convert Pydantic model → SQLAlchemy model
    new_election = Election(**payload.model_dump())
    db.add(new_election)
    await db.flush()        # sends INSERT to DB, populates new_election.id
    await db.refresh(new_election)  # re-reads the row so created_at etc are populated
    return new_election


@router.delete("/{election_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_election(
    election_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an election by ID."""
    election = await get_election_or_404(election_id, db)
    await db.delete(election)
    # commit happens automatically in get_db() when the request finishes


@router.post("/{election_id}/summarize", response_model=ElectionSummaryResponse)
async def summarize_election(
    election_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate an AI summary for an election using Groq."""
    from app.db_models.candidate import Candidate
    from app.db_models.news import NewsArticle
    from app.services.summarizer import generate_election_summary

    election = await get_election_or_404(election_id, db)

    # Fetch related candidates
    cand_result = await db.execute(
        select(Candidate).where(Candidate.election_id == election_id)
    )
    candidates = cand_result.scalars().all()

    # Fetch related news articles
    news_result = await db.execute(
        select(NewsArticle).where(NewsArticle.election_id == election_id)
    )
    articles = news_result.scalars().all()

    # Build plain dicts for the summarizer service (keeps service layer DB-agnostic)
    candidate_dicts = [{"name": c.name, "party": c.party.value} for c in candidates]
    article_dicts = [{"headline": a.headline, "source": a.source} for a in articles]

    summary = await generate_election_summary(
        election_id=election_id,
        election_name=election.name,
        candidates=candidate_dicts,
        articles=article_dicts
    )
    return summary