"""
Ejecuta las migraciones de Alembic de forma segura:
- Si las tablas ya existen pero no hay registro alembic_version,
  hace 'stamp head' para marcar el estado actual sin re-crear nada.
- Si la BD está vacía, aplica todas las migraciones desde cero.
- Si ya tiene alembic_version, aplica solo las migraciones pendientes.
"""
import os
from alembic.config import Config
from alembic import command
from sqlalchemy import inspect, create_engine, text

_RAW_URL = os.getenv("DATABASE_URL", "sqlite:///./polla_mundial.db")
if _RAW_URL.startswith("postgres://"):
    _RAW_URL = _RAW_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(_RAW_URL)
alembic_cfg = Config("alembic.ini")

with engine.connect() as conn:
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    has_app_tables = "users" in tables
    has_alembic = "alembic_version" in tables

    if has_app_tables and not has_alembic:
        print("Tablas existentes sin alembic_version → stamp head")
        command.stamp(alembic_cfg, "head")
    else:
        print("Aplicando migraciones pendientes...")
        command.upgrade(alembic_cfg, "head")

print("Migraciones completadas.")
