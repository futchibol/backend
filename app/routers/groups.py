import random
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user

router = APIRouter(prefix="/groups", tags=["groups"])


def _generate_invite_code(db: Session) -> str:
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not db.query(models.PollaGroup).filter(models.PollaGroup.invite_code == code).first():
            return code


def _member_count(group: models.PollaGroup) -> int:
    return len(group.members)


@router.post("", response_model=schemas.PollaGroupOut, status_code=201)
def create_group(
    group_in: schemas.PollaGroupCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    invite_code = _generate_invite_code(db)
    group = models.PollaGroup(
        name=group_in.name,
        description=group_in.description,
        invite_code=invite_code,
        created_by=current_user.id,
    )
    db.add(group)
    db.flush()

    membership = models.PollaGroupMember(group_id=group.id, user_id=current_user.id)
    db.add(membership)
    db.commit()
    db.refresh(group)

    return {**group.__dict__, "member_count": 1}


@router.post("/join", response_model=schemas.PollaGroupOut)
def join_group(
    body: schemas.PollaGroupJoin,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    group = db.query(models.PollaGroup).filter(
        models.PollaGroup.invite_code == body.invite_code.upper()
    ).first()
    if not group:
        raise HTTPException(404, "Código de invitación inválido")

    existing = db.query(models.PollaGroupMember).filter_by(
        group_id=group.id, user_id=current_user.id
    ).first()
    if existing:
        raise HTTPException(400, "Ya eres miembro de este grupo")

    membership = models.PollaGroupMember(group_id=group.id, user_id=current_user.id)
    db.add(membership)
    db.commit()
    db.refresh(group)

    return {**group.__dict__, "member_count": _member_count(group)}


@router.get("", response_model=list[schemas.PollaGroupOut])
def list_my_groups(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    memberships = (
        db.query(models.PollaGroupMember)
        .filter(models.PollaGroupMember.user_id == current_user.id)
        .all()
    )
    result = []
    for m in memberships:
        group = m.group
        result.append({**group.__dict__, "member_count": _member_count(group)})
    return result


@router.get("/{group_id}", response_model=schemas.PollaGroupOut)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    membership = db.query(models.PollaGroupMember).filter_by(
        group_id=group_id, user_id=current_user.id
    ).first()
    if not membership:
        raise HTTPException(403, "No eres miembro de este grupo")

    group = db.query(models.PollaGroup).get(group_id)
    return {**group.__dict__, "member_count": _member_count(group)}


@router.get("/{group_id}/leaderboard", response_model=list[schemas.LeaderboardEntry])
def get_leaderboard(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    membership = db.query(models.PollaGroupMember).filter_by(
        group_id=group_id, user_id=current_user.id
    ).first()
    if not membership:
        raise HTTPException(403, "No eres miembro de este grupo")

    members = (
        db.query(models.PollaGroupMember)
        .filter(models.PollaGroupMember.group_id == group_id)
        .order_by(models.PollaGroupMember.total_points.desc())
        .all()
    )

    result = []
    for rank, m in enumerate(members, start=1):
        preds = db.query(models.Prediction).filter_by(
            user_id=m.user_id, group_id=group_id
        ).all()
        exact = sum(
            1 for p in preds
            if p.points_earned is not None and p.match.is_finished and
            p.predicted_team1_score == p.match.team1_score and
            p.predicted_team2_score == p.match.team2_score
        )
        result.append(schemas.LeaderboardEntry(
            rank=rank,
            user_id=m.user_id,
            username=m.user.username,
            total_points=m.total_points,
            predictions_made=len(preds),
            exact_scores=exact,
        ))
    return result
