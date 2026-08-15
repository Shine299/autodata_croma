r"""Crea las tablas en una SQLite local para probar el bot sin depender de Supabase.

Uso (PowerShell, desde la raíz del proyecto):
    $env:DATABASE_URL = "sqlite+aiosqlite:///./autodata_local.db"
    .\.venv\Scripts\python.exe setup_local_db.py

Lee DATABASE_URL del entorno. Solo para pruebas locales — no commitear la .db.
"""
import asyncio
import os

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database import Base
import app.repositories.models  # noqa: F401  registra todos los modelos en Base.metadata


async def main() -> None:
    url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./autodata_local.db")
    engine = create_async_engine(url, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("OK. Tablas:", ", ".join(sorted(Base.metadata.tables.keys())))
    print("DB:", url)


if __name__ == "__main__":
    asyncio.run(main())
