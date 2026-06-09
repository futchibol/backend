from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from .models import MatchStage


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# ── Teams ─────────────────────────────────────────────────────────────────────

class TeamOut(BaseModel):
    id: int
    name: str
    code: str
    flag_emoji: str
    group_letter: Optional[str]
    confederation: str

    class Config:
        from_attributes = True


# ── Matches ───────────────────────────────────────────────────────────────────

class MatchOut(BaseModel):
    id: int
    match_number: int
    stage: MatchStage
    group_letter: Optional[str]
    team1: Optional[TeamOut]
    team2: Optional[TeamOut]
    team1_placeholder: str
    team2_placeholder: str
    scheduled_at: datetime
    venue: str
    city: str
    team1_score: Optional[int]
    team2_score: Optional[int]
    winner_id: Optional[int]
    is_finished: bool
    went_to_extra_time: bool
    went_to_penalties: bool

    class Config:
        from_attributes = True


class MatchResultUpdate(BaseModel):
    team1_score: int
    team2_score: int
    went_to_extra_time: bool = False
    went_to_penalties: bool = False


# ── Groups ────────────────────────────────────────────────────────────────────

class PollaGroupCreate(BaseModel):
    name: str
    description: str = ""


class PollaGroupJoin(BaseModel):
    invite_code: str


class PollaGroupOut(BaseModel):
    id: int
    name: str
    description: str
    invite_code: str
    created_by: int
    created_at: datetime
    member_count: int = 0

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    total_points: int
    predictions_made: int
    exact_scores: int


class GroupDetailOut(BaseModel):
    id: int
    name: str
    description: str
    invite_code: str
    created_by: int
    created_at: datetime
    leaderboard: List[LeaderboardEntry]

    class Config:
        from_attributes = True


# ── Predictions ───────────────────────────────────────────────────────────────

class PredictionCreate(BaseModel):
    match_id: int
    group_id: int
    predicted_team1_score: Optional[int] = None
    predicted_team2_score: Optional[int] = None
    predicted_winner_id: Optional[int] = None


class PredictionOut(BaseModel):
    id: int
    user_id: int
    group_id: int
    match_id: int
    predicted_team1_score: Optional[int]
    predicted_team2_score: Optional[int]
    predicted_winner_id: Optional[int]
    points_earned: Optional[int]
    created_at: datetime
    updated_at: datetime
    match: Optional[MatchOut] = None

    class Config:
        from_attributes = True


class BracketStatus(BaseModel):
    group_id: int
    total_matches: int
    predicted_matches: int
    completion_pct: float
    group_stage_predicted: int
    knockout_predicted: int
