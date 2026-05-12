# app/routers/elections.py
from fastapi import APIRouter, HTTPException, Query, status, Path
from typing import Optional, List
from datetime import date, datetime

from app.models.election import (
    ElectionCreate,
    ElectionResponse,
    ElectionStatus,
    ElectionSummaryResponse,        # ← NEW
)
from app.services.summarizer import generate_election_summary  # ← NEW

# --- Router Initialization ---
# prefix: all routes in this file automatically start with /elections
# tags: groups these routes together in the /docs UI
router = APIRouter(
    prefix="/elections",
    tags=["Elections"],
)


# --- In-Memory Data Store ---
# We're using a plain Python list as our "database" for now.
# This is intentional — we want the API working before adding
# database complexity. We'll swap this for PostgreSQL later.
_elections_db: List[dict] = [
    {
        "id": 1,
        "name": "2024 Indian General Election",
        "country": "India",
        "election_type": "general",
        "election_date": "2024-04-19",
        "description": "18th General Election to the Lok Sabha.",
        "status": "completed",
    },
    {
        "id": 2,
        "name": "2025 Delhi Assembly Election",
        "country": "India",
        "election_type": "state",
        "election_date": "2025-02-05",
        "description": "Election to the 8th Delhi Legislative Assembly.",
        "status": "completed",
    },
]

# Tracks the next available ID (mimics auto-increment in a real DB)
_next_id = 3


# ─────────────────────────────────────────────
# GET /elections
# Returns all elections, with optional status filter
# ─────────────────────────────────────────────
@router.get("/", response_model=List[ElectionResponse])
def get_all_elections(
    status: ElectionStatus | None = Query(
        default=None,
        description="Filter elections by status: upcoming, ongoing, or completed",
    )
):
    """
    Retrieve all tracked elections.
    Optionally filter by status using the `?status=` query parameter.
    """
    if status:
        filtered = [e for e in _elections_db if e["status"] == status.value]
        return filtered
    return _elections_db


# ─────────────────────────────────────────────
# GET /elections/{election_id}
# Returns a single election by ID
# ─────────────────────────────────────────────
@router.get("/{election_id}", response_model=ElectionResponse)
def get_election(
    election_id: int = Path(
        ...,
        gt=0,
        description="The unique ID of the election to retrieve",
    )
):
    """
    Retrieve a specific election by its ID.
    Returns 404 if not found.
    """
    for election in _elections_db:
        if election["id"] == election_id:
            return election

    # Raising HTTPException is the FastAPI way to return error responses.
    # It automatically formats the response as {"detail": "..."} with the correct status code.
    raise HTTPException(
        status_code=404,
        detail=f"Election with ID {election_id} not found.",
    )


# ─────────────────────────────────────────────
# POST /elections
# Creates a new election entry
# ─────────────────────────────────────────────
@router.post("/", response_model=ElectionResponse, status_code=201)
def create_election(payload: ElectionCreate):
    """
    Register a new election in the platform.
    Accepts election details and returns the created record with its assigned ID.
    """
    global _next_id

    new_election = {
        "id": _next_id,
        **payload.model_dump(),  # Unpacks all validated fields from the request body
        "status": ElectionStatus.upcoming.value,
        "election_date": str(payload.election_date),
    }

    _elections_db.append(new_election)
    _next_id += 1

    return new_election


# ─────────────────────────────────────────────
# DELETE /elections/{election_id}
# Removes an election by ID
# ─────────────────────────────────────────────
@router.delete("/{election_id}", status_code=204)
def delete_election(
    election_id: int = Path(
        ...,
        gt=0,
        description="The unique ID of the election to delete",
    )
):
    """
    Remove an election from the platform by ID.
    Returns 204 No Content on success, 404 if not found.
    """
    global _elections_db

    for index, election in enumerate(_elections_db):
        if election["id"] == election_id:
            _elections_db.pop(index)
            return  # 204 returns no body

    raise HTTPException(
        status_code=404,
        detail=f"Election with ID {election_id} not found.",
    )


@router.post(
    "/{election_id}/summarize",
    response_model=ElectionSummaryResponse,
    tags=["AI"],
    summary="Generate an AI summary for this election",
)
def summarize_election(election_id: int):
    """
    Calls GPT-4o-mini to produce a structured briefing for this election.
    Pulls all matching candidates and news articles automatically.
    """
    # ── Step 1: confirm the election exists ──
    election = next(
        (e for e in _elections_db if e["id"] == election_id), None
    )
    if not election:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Election with id={election_id} not found.",
        )

    # ── Step 2: import the in-memory DBs from other routers ──
    # We import here (not at the top) to avoid circular import errors.
    from app.routers.candidates import _candidates_db
    from app.routers.news import _news_db

    # ── Step 3: filter candidates and news for this election ──
    candidates = [
        c for c in _candidates_db
        if c.get("election_id") == election_id
    ]
    articles = [
        a for a in _news_db.values()
        if a.get("election_id") == election_id
    ]

    # ── Step 4: call the summarizer service ──
    result = generate_election_summary(
        election_id=election_id,
        election_name=election["name"],
        candidates=candidates,
        articles=articles,
    )

    return result