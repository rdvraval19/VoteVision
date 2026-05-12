# app/models/election.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum
from datetime import date, datetime


class ElectionType(str, Enum):
    general = "general"
    state = "state"
    local = "local"
    by_election = "by_election"


class ElectionStatus(str, Enum):
    upcoming = "upcoming"
    ongoing = "ongoing"
    completed = "completed"


class ElectionBase(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Full name of the election",
        examples=["2024 Indian General Election"],
    )
    election_type: ElectionType = Field(
        ...,
        description="Type of election",
    )
    status: ElectionStatus = Field(
        default=ElectionStatus.upcoming,
        description="Current status of the election",
    )
    state: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="State where the election is held",
        examples=["Maharashtra"],
    )
    constituency: Optional[str] = Field(
        None,
        max_length=200,
        description="Constituency name if applicable",
    )
    total_voters: Optional[int] = Field(
        None,
        gt=0,
        description="Total number of registered voters",
    )


class ElectionCreate(ElectionBase):
    pass


class ElectionResponse(ElectionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Pydantic v2 style — allows SQLAlchemy ORM objects to be read directly
    model_config = ConfigDict(from_attributes=True)


class ElectionSummaryResponse(BaseModel):
    election_id: int
    election_name: str
    summary: str
    key_topics: List[str]
    overall_sentiment: str
    model_used: str
    raw_response: str