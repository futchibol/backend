"""
Sincroniza resultados del Mundial 2026 desde football-data.org.
Detecta partidos terminados, actualiza marcadores y calcula puntos automáticamente.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from .. import models
from ..database import SessionLocal
from .football_api import fetch_wc_matches, STAGE_MAP
from ..routers.admin import _calculate_points_for_match, _get_match_result

_last_sync_at: Optional[datetime] = None
_last_sync_result: Optional[dict] = None

FINISHED = {"FINISHED"}


def get_sync_status() -> dict:
    return {
        "last_sync": _last_sync_at.isoformat() if _last_sync_at else None,
        "last_result": _last_sync_result,
    }


async def run_sync(db: Session) -> dict:
    global _last_sync_at, _last_sync_result

    api_matches = await fetch_wc_matches()

    # Índice de equipos por código TLA (3 letras)
    teams_by_code: dict[str, models.Team] = {
        t.code: t for t in db.query(models.Team).all()
    }
    # Índice de equipos por nombre (fallback)
    teams_by_name: dict[str, models.Team] = {
        t.name.lower(): t for t in teams_by_code.values()
    }

    # Índice de partidos de la BD por (team1_id, team2_id)
    db_matches_by_teams: dict[tuple, models.Match] = {}
    for m in db.query(models.Match).all():
        if m.team1_id and m.team2_id:
            db_matches_by_teams[(m.team1_id, m.team2_id)] = m

    updated = skipped = errors = 0

    for api_m in api_matches:
        try:
            if api_m.get("status") not in FINISHED:
                skipped += 1
                continue

            home_info = api_m.get("homeTeam", {})
            away_info = api_m.get("awayTeam", {})

            # Resolver equipo local
            team1 = _resolve_team(home_info, teams_by_code, teams_by_name)
            team2 = _resolve_team(away_info, teams_by_code, teams_by_name)

            if not team1 or not team2:
                print(f"⚠️  No se encontró: {home_info.get('tla')} vs {away_info.get('tla')}")
                skipped += 1
                continue

            # Buscar partido en BD (probar ambas orientaciones)
            db_match, swapped = _find_db_match(team1.id, team2.id, db_matches_by_teams)
            if not db_match:
                skipped += 1
                continue

            if db_match.is_finished and db_match.points_calculated:
                skipped += 1
                continue

            score = api_m.get("score", {})
            ft = score.get("fullTime", {})
            home_score = ft.get("home")
            away_score = ft.get("away")

            if home_score is None or away_score is None:
                skipped += 1
                continue

            # Si los equipos estaban al revés, intercambiar marcador
            if swapped:
                home_score, away_score = away_score, home_score

            extra = score.get("extraTime", {})
            pens = score.get("penalties", {})

            # Actualizar partido
            db_match.team1_score = home_score
            db_match.team2_score = away_score
            db_match.is_finished = True
            db_match.went_to_extra_time = extra.get("home") is not None
            db_match.went_to_penalties = pens.get("home") is not None

            if home_score > away_score:
                db_match.winner_id = db_match.team1_id
            elif away_score > home_score:
                db_match.winner_id = db_match.team2_id
            else:
                db_match.winner_id = None

            db.commit()

            # Calcular puntos si aún no se hizo
            if not db_match.points_calculated:
                _apply_points(db, db_match)

            print(f"✅ Partido actualizado: {team1.code} {home_score}-{away_score} {team2.code}")
            updated += 1

        except Exception as e:
            print(f"❌ Error procesando partido: {e}")
            errors += 1

    _last_sync_at = datetime.utcnow()
    _last_sync_result = {"updated": updated, "skipped": skipped, "errors": errors}
    print(f"🔄 Sync completado: {_last_sync_result}")
    return _last_sync_result


def _resolve_team(
    team_info: dict,
    by_code: dict[str, models.Team],
    by_name: dict[str, models.Team],
) -> Optional[models.Team]:
    tla = (team_info.get("tla") or "").upper()
    if tla and tla in by_code:
        return by_code[tla]
    # Fallback por nombre
    name = (team_info.get("name") or "").lower()
    return by_name.get(name)


def _find_db_match(
    team1_id: int,
    team2_id: int,
    index: dict[tuple, models.Match],
) -> tuple[Optional[models.Match], bool]:
    """Retorna (match, swapped). swapped=True si los equipos estaban invertidos."""
    m = index.get((team1_id, team2_id))
    if m:
        return m, False
    m = index.get((team2_id, team1_id))
    if m:
        return m, True
    return None, False


def _apply_points(db: Session, match: models.Match) -> None:
    """Calcula y asigna puntos a todas las predicciones de un partido."""
    predictions = db.query(models.Prediction).filter_by(match_id=match.id).all()

    for pred in predictions:
        pts = _calculate_points_for_match(match, pred)
        pred.points_earned = pts

        membership = db.query(models.PollaGroupMember).filter_by(
            user_id=pred.user_id, group_id=pred.group_id
        ).first()
        if membership:
            membership.total_points = (membership.total_points or 0) + pts

    match.points_calculated = True
    db.commit()


async def run_sync_standalone() -> dict:
    """Para llamar desde el scheduler (crea su propia sesión de BD)."""
    db = SessionLocal()
    try:
        return await run_sync(db)
    finally:
        db.close()
