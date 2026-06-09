import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

_RAW_URL = os.getenv("DATABASE_URL", "sqlite:///./polla_mundial.db")

# Render expone postgres:// pero SQLAlchemy necesita postgresql://
if _RAW_URL.startswith("postgres://"):
    _RAW_URL = _RAW_URL.replace("postgres://", "postgresql://", 1)

_IS_SQLITE = _RAW_URL.startswith("sqlite")

engine = create_engine(
    _RAW_URL,
    connect_args={"check_same_thread": False} if _IS_SQLITE else {},
    pool_pre_ping=True,          # reconecta si la conexión cayó
    pool_recycle=300,            # recicla conexiones cada 5 min
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
