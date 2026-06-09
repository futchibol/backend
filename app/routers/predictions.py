from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("", response_model=schemas.PredictionOut, status_code=201)
def upsert_prediction(
    pred_in: schemas.PredictionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Verify membership
    membership = db.query(models.PollaGroupMember).filter_by(
        group_id=pred_in.group_id, user_id=current_user.id
    ).first()
    if not membership:
        raise HTTPException(403, "No eres miembro de este grupo")

    match = db.query(models.Match).get(pred_in.match_id)
    if not match:
        raise HTTPException(404, "Partido no encontrado")

    if match.is_finished:
        raise HTTPException(400, "No puedes predecir partidos ya terminados")

    if datetime.utcnow() >= match.scheduled_at:
        raise HTTPException(400, "El plazo para predecir este partido ya cerró")

    existing = db.query(models.Prediction).filter_by(
        user_id=current_user.id,
        group_id=pred_in.group_id,
        match_id=pred_in.match_id,
    ).first()

    if existing:
        existing.predicted_team1_score = pred_in.predicted_team1_score
        existing.predicted_team2_score = pred_in.predicted_team2_score
        existing.predicted_winner_id = pred_in.predicted_winner_id
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    prediction = models.Prediction(
        user_id=current_user.id,
        group_id=pred_in.group_id,
        match_id=pred_in.match_id,
        predicted_team1_score=pred_in.predicted_team1_score,
        predicted_team2_score=pred_in.predicted_team2_score,
        predicted_winner_id=pred_in.predicted_winner_id,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


@router.get("", response_model=list[schemas.PredictionOut])
def list_predictions(
    group_id: Optional[int] = None,
    match_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.Prediction).filter(models.Prediction.user_id == current_user.id)
    if group_id:
        q = q.filter(models.Prediction.group_id == group_id)
    if match_id:
        q = q.filter(models.Prediction.match_id == match_id)
    return q.all()


@router.get("/status/{group_id}", response_model=schemas.BracketStatus)
def bracket_status(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    membership = db.query(models.PollaGroupMember).filter_by(
        group_id=group_id, user_id=current_user.id
    ).first()
    if not membership:
        raise HTTPException(403, "No eres miembro de este grupo")

    total = db.query(models.Match).count()
    predicted = db.query(models.Prediction).filter_by(
        user_id=current_user.id, group_id=group_id
    ).count()

    group_predicted = (
        db.query(models.Prediction)
        .join(models.Match)
        .filter(
            models.Prediction.user_id == current_user.id,
            models.Prediction.group_id == group_id,
            models.Match.stage == models.MatchStage.GROUP,
        )
        .count()
    )

    knockout_predicted = predicted - group_predicted

    return schemas.BracketStatus(
        group_id=group_id,
        total_matches=total,
        predicted_matches=predicted,
        completion_pct=round(predicted / total * 100, 1) if total else 0,
        group_stage_predicted=group_predicted,
        knockout_predicted=knockout_predicted,
    )
