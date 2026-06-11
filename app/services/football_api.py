import os
import httpx

_API_KEY = os.getenv("FOOTBALL_API_KEY", "")
_BASE = "https://api-football-v1.p.rapidapi.com/v3"
_HEADERS = {
    "X-RapidAPI-Key": _API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
}

# Round string de API-Football → nuestro stage
STAGE_MAP: dict[str, str] = {}
for _r in ["Group Stage - 1", "Group Stage - 2", "Group Stage - 3"]:
    STAGE_MAP[_r] = "GROUP"
STAGE_MAP["Round of 32"]     = "ROUND_OF_32"
STAGE_MAP["Round of 16"]     = "ROUND_OF_16"
STAGE_MAP["Quarter-finals"]  = "QUARTERFINAL"
STAGE_MAP["Semi-finals"]     = "SEMIFINAL"
STAGE_MAP["3rd Place Final"] = "THIRD_PLACE"
STAGE_MAP["Final"]           = "FINAL"

# Códigos de estado que indica partido terminado
FINISHED_STATUSES = {"FT", "AET", "PEN"}


async def fetch_wc_matches() -> list[dict]:
    """Devuelve todos los partidos del Mundial 2026 (league=1, season=2026)."""
    if not _API_KEY:
        raise ValueError("Variable de entorno FOOTBALL_API_KEY no configurada")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{_BASE}/fixtures",
            headers=_HEADERS,
            params={"league": "1", "season": "2026"},
        )
        resp.raise_for_status()
        return resp.json().get("response", [])
