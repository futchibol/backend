from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import require_admin
from .. import models
from ..services.sync_service import run_sync, get_sync_status

router = APIRouter(prefix="/admin/sync", tags=["sync"])


@router.post("")
async def trigger_sync(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    """Fuerza una sincronización inmediata con football-data.org."""
    try:
        result = await run_sync(db)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error al sincronizar: {e}")


@router.get("/status")
def sync_status(_: models.User = Depends(require_admin)):
    """Devuelve la hora y resultado de la última sincronización."""
    return get_sync_status()
