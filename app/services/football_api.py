import os
import httpx

_API_KEY = os.getenv("FOOTBALL_API_KEY", "")
_BASE = "https://api.football-data.org/v4"

# Códigos de etapa que devuelve football-data.org → nuestros valores de stage
STAGE_MAP = {
    "GROUP_STAGE":    "GROUP",
    "LAST_32":        "ROUND_OF_32",
    "LAST_16":        "ROUND_OF_16",
    "QUARTER_FINALS": "QUARTERFINAL",
    "SEMI_FINALS":    "SEMIFINAL",
    "THIRD_PLACE":    "THIRD_PLACE",
    "FINAL":          "FINAL",
}

# TLA de football-data.org que difieren del código FIFA que usamos en la BD
TLA_OVERRIDES = {
    "KOR": "KOR",
    "IRN": "IRN",
    "CRC": "CRC",
    "GHA": "GHA",
}


async def fetch_wc_matches() -> list[dict]:
    """Devuelve todos los partidos del Mundial 2026 desde football-data.org."""
    if not _API_KEY:
        raise ValueError("Variable de entorno FOOTBALL_API_KEY no configurada")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{_BASE}/competitions/WC/matches",
            headers={"X-Auth-Token": _API_KEY},
        )
        resp.raise_for_status()
        return resp.json().get("matches", [])
