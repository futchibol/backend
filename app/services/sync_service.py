"""
Sincronización diaria con football-data.org.
Actualiza: horarios, equipos en eliminatorias, marcadores y puntos.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from .. import models
from ..database import SessionLocal
from .football_api import fetch_wc_matches, STAGE_MAP
from ..routers.admin import _calculate_points_for_match

_last_sync_at: Optional[datetime] = None
_last_sync_result: Optional[dict] = None

FINISHED_STATUSES = {"FINISHED"}
LIVE_STATUSES = {"IN_PLAY", "PAUSED", "HALFTIME"}


def get_sync_status() -> dict:
    return {
        "last_sync": _last_sync_at.isoformat() if _last_sync_at else None,
        "last_result": _last_sync_result,
    }


async def run_sync(db: Session) -> dict:
    global _last_sync_at, _last_sync_result

    api_matches = await fetch_wc_matches()

    # Índices de la BD
    teams_by_code: dict[str, models.Team] = {
        t.code: t for t in db.query(models.Team).all()
    }
    teams_by_name: dict[str, models.Team] = {
        t.name.lower(): t for t in teams_by_code.values()
    }

    # Partidos indexados por external_id (ya vinculados de syncs anteriores)
    db_by_ext: dict[int, models.Match] = {
        m.external_id: m
        for m in db.query(models.Match).filter(models.Match.external_id.isnot(None)).all()
    }
    # Partidos de grupo indexados por (team1_id, team2_id) para primer match
    db_by_teams: dict[tuple, models.Match] = {}
    # Partidos eliminatorios sin equipos asignados, indexados por stage
    db_knockout_empty: dict[str, list[models.Match]] = {}
    for m in db.query(models.Match).all():
        if m.team1_id and m.team2_id:
            db_by_teams[(m.team1_id, m.team2_id)] = m
            db_by_teams[(m.team2_id, m.team1_id)] = m
        elif m.stage != "GROUP" and m.external_id is None:
            db_knockout_empty.setdefault(m.stage, []).append(m)

    results = {
        "schedules_updated": 0,
        "teams_assigned": 0,
        "scores_updated": 0,
        "points_calculated": 0,
        "errors": 0,
    }

    for api_m in api_matches:
        try:
            # ── Estructura de API-Football ─────────────────────────────────
            fixture  = api_m.get("fixture", {})
            ext_id: int = fixture["id"]
            status: str = fixture.get("status", {}).get("short", "")
            api_round: str = api_m.get("league", {}).get("round", "")
            our_stage: str = STAGE_MAP.get(api_round, "")

            home_info = api_m.get("teams", {}).get("home", {})
            away_info = api_m.get("teams", {}).get("away", {})

            # ── 1. Resolver el partido en nuestra BD ───────────────────────
            db_match: Optional[models.Match] = db_by_ext.get(ext_id)

            if not db_match:
                team1 = _resolve_team(home_info, teams_by_code, teams_by_name)
                team2 = _resolve_team(away_info, teams_by_code, teams_by_name)

                if team1 and team2:
                    db_match = db_by_teams.get((team1.id, team2.id))

                if not db_match and our_stage and our_stage != "GROUP":
                    slots = db_knockout_empty.get(our_stage, [])
                    if slots:
                        db_match = slots.pop(0)

            if not db_match:
                continue

            # Guardar external_id para próximos syncs
            if db_match.external_id != ext_id:
                db_match.external_id = ext_id
                db_by_ext[ext_id] = db_match
                db.commit()

            # Partido ya cerrado: no tocar nada más
            if db_match.is_finished and db_match.points_calculated:
                continue

            # ── 2. Actualizar horario y sede ───────────────────────────────
            utc_date = fixture.get("date")
            if utc_date:
                try:
                    new_dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00")).replace(tzinfo=None)
                    if db_match.scheduled_at != new_dt:
                        db_match.scheduled_at = new_dt
                        results["schedules_updated"] += 1
                except ValueError:
                    pass

            venue_info = (fixture.get("venue") or {}).get("name") or ""
            city_info  = (fixture.get("venue") or {}).get("city") or ""
            if venue_info and db_match.venue != venue_info:
                db_match.venue = venue_info
            if city_info and db_match.city != city_info:
                db_match.city = city_info

            # ── 3. Asignar equipos en eliminatorias cuando ya se conocen ──
            if our_stage and our_stage != "GROUP":
                team1 = _resolve_team(home_info, teams_by_code, teams_by_name)
                team2 = _resolve_team(away_info, teams_by_code, teams_by_name)
                changed = False
                if team1 and db_match.team1_id != team1.id:
                    db_match.team1_id = team1.id
                    db_match.team1_placeholder = ""
                    changed = True
                if team2 and db_match.team2_id != team2.id:
                    db_match.team2_id = team2.id
                    db_match.team2_placeholder = ""
                    changed = True
                if changed:
                    results["teams_assigned"] += 1

            # ── 4. Actualizar marcador si el partido terminó ───────────────
            if status in FINISHED_STATUSES:
                goals = api_m.get("goals", {})
                score = api_m.get("score", {})
                home_score = goals.get("home")
                away_score = goals.get("away")

                if home_score is None or away_score is None:
                    db.commit()
                    continue

                # Si los equipos estaban invertidos en nuestra BD, rotar marcador
                team1 = _resolve_team(home_info, teams_by_code, teams_by_name)
                if team1 and db_match.team1_id and team1.id != db_match.team1_id:
                    home_score, away_score = away_score, home_score

                if not db_match.is_finished or db_match.team1_score != home_score:
                    db_match.team1_score = home_score
                    db_match.team2_score = away_score
                    db_match.is_finished = True
                    db_match.went_to_extra_time = score.get("extratime", {}).get("home") is not None
                    db_match.went_to_penalties  = score.get("penalty", {}).get("home") is not None

                    if home_score > away_score:
                        db_match.winner_id = db_match.team1_id
                    elif away_score > home_score:
                        db_match.winner_id = db_match.team2_id
                    else:
                        db_match.winner_id = None

                    results["scores_updated"] += 1

                db.commit()

                if not db_match.points_calculated:
                    _apply_points(db, db_match)
                    results["points_calculated"] += 1
            else:
                db.commit()

        except Exception as e:
            db.rollback()
            print(f"❌ Error en partido {api_m.get('id')}: {e}")
            results["errors"] += 1

    _last_sync_at = datetime.utcnow()
    _last_sync_result = results
    print(f"🔄 Sync diario completado: {results}")
    return results


def _resolve_team(
    info: dict,
    by_code: dict,
    by_name: dict,
) -> Optional[models.Team]:
    # API-Football usa "code" (3 letras) y "name"
    code = (info.get("code") or info.get("tla") or "").upper()
    if code and code in by_code:
        return by_code[code]
    name = (info.get("name") or "").lower()
    return by_name.get(name)


def _apply_points(db: Session, match: models.Match) -> None:
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
    db = SessionLocal()
    try:
        return await run_sync(db)
    finally:
        db.close()
