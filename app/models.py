import enum
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class MatchStage(str, enum.Enum):
    GROUP = "GROUP"
    R32 = "ROUND_OF_32"
    R16 = "ROUND_OF_16"
    QF = "QUARTERFINAL"
    SF = "SEMIFINAL"
    THIRD = "THIRD_PLACE"
    FINAL = "FINAL"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    group_memberships = relationship("PollaGroupMember", back_populates="user")
    predictions = relationship("Prediction", back_populates="user")


class PollaGroup(Base):
    __tablename__ = "polla_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    invite_code = Column(String, unique=True, index=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("PollaGroupMember", back_populates="group")
    creator = relationship("User", foreign_keys=[created_by])


class PollaGroupMember(Base):
    __tablename__ = "polla_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("polla_groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_points = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("group_id", "user_id"),)

    group = relationship("PollaGroup", back_populates="members")
    user = relationship("User", back_populates="group_memberships")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String(3), nullable=False)
    flag_emoji = Column(String, default="🏳️")
    group_letter = Column(String(1), nullable=True)
    confederation = Column(String, default="")

    home_matches = relationship("Match", foreign_keys="Match.team1_id", back_populates="team1")
    away_matches = relationship("Match", foreign_keys="Match.team2_id", back_populates="team2")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    match_number = Column(Integer, unique=True)
    # String en lugar de SAEnum nativo → compatible con SQLite y PostgreSQL sin problema
    stage = Column(String(20), nullable=False)
    group_letter = Column(String(1), nullable=True)

    team1_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    team2_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    team1_placeholder = Column(String, default="")
    team2_placeholder = Column(String, default="")

    scheduled_at = Column(DateTime, nullable=False)
    venue = Column(String, default="")
    city = Column(String, default="")

    team1_score = Column(Integer, nullable=True)
    team2_score = Column(Integer, nullable=True)
    winner_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    went_to_extra_time = Column(Boolean, default=False)
    went_to_penalties = Column(Boolean, default=False)
    is_finished = Column(Boolean, default=False)
    points_calculated = Column(Boolean, default=False)

    team1 = relationship("Team", foreign_keys=[team1_id], back_populates="home_matches")
    team2 = relationship("Team", foreign_keys=[team2_id], back_populates="away_matches")
    winner = relationship("Team", foreign_keys=[winner_id])
    predictions = relationship("Prediction", back_populates="match")


POINTS_BY_STAGE = {
    MatchStage.GROUP:  {"exact": 3,  "result": 1},
    MatchStage.R32:    {"exact": 5,  "result": 3},
    MatchStage.R16:    {"exact": 8,  "result": 5},
    MatchStage.QF:     {"exact": 12, "result": 8},
    MatchStage.SF:     {"exact": 18, "result": 12},
    MatchStage.THIRD:  {"exact": 6,  "result": 4},
    MatchStage.FINAL:  {"exact": 25, "result": 15},
}


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("polla_groups.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)

    predicted_team1_score = Column(Integer, nullable=True)
    predicted_team2_score = Column(Integer, nullable=True)
    predicted_winner_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    points_earned = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "group_id", "match_id"),)

    user = relationship("User", back_populates="predictions")
    match = relationship("Match", back_populates="predictions")
    polla_group = relationship("PollaGroup")
    predicted_winner = relationship("Team", foreign_keys=[predicted_winner_id])
