import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from app.config import settings

logger = logging.getLogger("autodata.database")

# Convierte el driver de postgresql a asyncpg si es necesario
db_url = settings.database_url
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif not db_url:
    # Fallback para desarrollo local / tests si no hay base de datos configurada
    logger.warning("DATABASE_URL no configurado. Usando SQLite en memoria para desarrollo.")
    db_url = "sqlite+aiosqlite:///:memory:"

# Configuración del engine asíncrono
# Para SQLite en memoria se deshabilita check_same_thread
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    db_url,
    connect_args=connect_args,
    echo=settings.app_env == "dev",
    future=True
)

# Creador de sesiones asíncronas
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base declarativa para modelos
Base = declarative_base()

# Dependencia para inyección en FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
