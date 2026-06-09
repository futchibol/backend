from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[schemas.MatchOut])
def list_matches(
    stage: Optional[str] = None,
    group_letter: Optional[str] = None,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    q = db.query(models.Match)
    if stage:
        try:
            q = q.filter(models.Match.stage == models.MatchStage(stage))
        except ValueError:
            raise HTTPException(400, f"Etapa inválida: {stage}")
    if group_letter:
        q = q.filter(models.Match.group_letter == group_letter.upper())
    return q.order_by(models.Match.scheduled_at).all()


@router.get("/{match_id}", response_model=schemas.MatchOut)
def get_match(
    match_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    match = db.query(models.Match).get(match_id)
    if not match:
        raise HTTPException(404, "Partido no encontrado")
    return match
