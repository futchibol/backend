from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from ..auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


def _get_match_result(team1_score: int, team2_score: int):
    if team1_score > team2_score:
        return "team1"
    elif team2_score > team1_score:
        return "team2"
    return "draw"


def _calculate_points_for_match(match: models.Match, prediction: models.Prediction) -> int:
    pts_config = models.POINTS_BY_STAGE.get(match.stage, {"exact": 3, "result": 1})

    if match.stage == models.MatchStage.GROUP:
        if (
            prediction.predicted_team1_score == match.team1_score
            and prediction.predicted_team2_score == match.team2_score
        ):
            return pts_config["exact"]

        pred_result = _get_match_result(
            prediction.predicted_team1_score or 0,
            prediction.predicted_team2_score or 0,
        )
        real_result = _get_match_result(match.team1_score, match.team2_score)
        if pred_result == real_result:
            return pts_config["result"]
        return 0
    else:
        # Knockout: check predicted winner
        if prediction.predicted_winner_id and prediction.predicted_winner_id == match.winner_id:
            return pts_config["result"]
        return 0


@router.put("/matches/{match_id}/result", response_model=schemas.MatchOut)
def set_match_result(
    match_id: int,
    result: schemas.MatchResultUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    match = db.query(models.Match).get(match_id)
    if not match:
        raise HTTPException(404, "Partido no encontrado")

    match.team1_score = result.team1_score
    match.team2_score = result.team2_score
    match.went_to_extra_time = result.went_to_extra_time
    match.went_to_penalties = result.went_to_penalties
    match.is_finished = True

    # Set winner for knockout stages
    if result.team1_score > result.team2_score:
        match.winner_id = match.team1_id
    elif result.team2_score > result.team1_score:
        match.winner_id = match.team2_id
    else:
        match.winner_id = None  # draw (group stage)

    db.commit()
    db.refresh(match)
    return match


@router.post("/matches/{match_id}/calculate-points")
def calculate_points(
    match_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    match = db.query(models.Match).get(match_id)
    if not match:
        raise HTTPException(404, "Partido no encontrado")
    if not match.is_finished:
        raise HTTPException(400, "El partido aún no ha terminado")
    if match.points_calculated:
        raise HTTPException(400, "Los puntos ya fueron calculados para este partido")

    predictions = db.query(models.Prediction).filter_by(match_id=match_id).all()
    updated_users = 0

    for pred in predictions:
        pts = _calculate_points_for_match(match, pred)
        pred.points_earned = pts

        membership = db.query(models.PollaGroupMember).filter_by(
            user_id=pred.user_id, group_id=pred.group_id
        ).first()
        if membership:
            membership.total_points += pts
            updated_users += 1

    match.points_calculated = True
    db.commit()

    return {"match_id": match_id, "predictions_evaluated": len(predictions), "users_updated": updated_users}


@router.post("/seed")
def seed_database(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    from ..data.wc2026 import seed_wc2026
    seed_wc2026(db)
    return {"message": "Datos del Mundial 2026 cargados correctamente"}


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    return {
        "total_users": db.query(models.User).count(),
        "total_groups": db.query(models.PollaGroup).count(),
        "total_predictions": db.query(models.Prediction).count(),
        "total_matches": db.query(models.Match).count(),
        "finished_matches": db.query(models.Match).filter(models.Match.is_finished == True).count(),
    }
