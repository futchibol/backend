import os

# Carga .env solo en desarrollo (en Render las env vars vienen del dashboard)
if os.getenv("ENVIRONMENT") != "production":
    try:
        from pathlib import Path
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .database import engine, Base, SessionLocal
from . import models
from .routers import auth, groups, matches, predictions, admin, sync
from .auth import hash_password
from .data.wc2026 import seed_wc2026

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Polla Mundial 2026",
    description="API para la polla del Mundial FIFA 2026",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(matches.router)
app.include_router(predictions.router)
app.include_router(admin.router)
app.include_router(sync.router)

_scheduler = AsyncIOScheduler()


@app.on_event("startup")
def startup_db():
    db = SessionLocal()
    try:
        seed_wc2026(db)

        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin2026")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@polla.com")

        existing = db.query(models.User).filter(
            models.User.username == admin_username
        ).first()
        if not existing:
            db.add(models.User(
                username=admin_username,
                email=admin_email,
                hashed_password=hash_password(admin_password),
                is_admin=True,
            ))
            db.commit()
            print(f"✅ Admin creado: {admin_username}")
    finally:
        db.close()


@app.on_event("startup")
async def startup_scheduler():
    if not os.getenv("FOOTBALL_API_KEY"):
        print("⚠️  FOOTBALL_API_KEY no configurada — scheduler desactivado")
        return

    from .services.sync_service import run_sync_standalone

    # Sincronización diaria a las 6:00 AM UTC
    _scheduler.add_job(
        run_sync_standalone,
        "cron",
        hour=6,
        minute=0,
        id="wc_sync_daily",
        replace_existing=True,
    )
    _scheduler.start()
    print("✅ Scheduler activado — sincronización diaria a las 6:00 AM UTC")


@app.on_event("shutdown")
async def shutdown_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)


@app.get("/")
def root():
    return {"app": "Polla Mundial 2026", "docs": "/docs", "status": "running"}
