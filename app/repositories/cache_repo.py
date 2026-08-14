from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.models import CromaCacheModel


class CacheRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_cached(self, source: str, lookup_key: str) -> Optional[Dict[str, Any]]:
        """
        Busca una respuesta en caché para el source y lookup_key.
        Solo retorna el payload si no ha expirado (expires_at > now).
        """
        stmt = select(CromaCacheModel).where(
            CromaCacheModel.source == source,
            CromaCacheModel.lookup_key == lookup_key
        )
        result = await self.session.execute(stmt)
        cache_item = result.scalars().first()

        if cache_item:
            now = datetime.now(timezone.utc)
            expires_at = cache_item.expires_at
            
            if expires_at.tzinfo is None:
                now = now.replace(tzinfo=None)
            else:
                now = now.astimezone(expires_at.tzinfo)

            if expires_at > now:
                return cache_item.payload
            
        return None

    async def set_cached(
        self, 
        source: str, 
        lookup_key: str, 
        payload: Dict[str, Any], 
        status: str, 
        ttl_seconds: int
    ) -> None:
        """
        Inserta o actualiza un registro en la caché con el TTL indicado.
        """
        stmt = select(CromaCacheModel).where(
            CromaCacheModel.source == source,
            CromaCacheModel.lookup_key == lookup_key
        )
        result = await self.session.execute(stmt)
        cache_item = result.scalars().first()

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)

        if cache_item:
            cache_item.payload = payload
            cache_item.status = status
            cache_item.fetched_at = now
            cache_item.expires_at = expires_at
        else:
            new_item = CromaCacheModel(
                source=source,
                lookup_key=lookup_key,
                payload=payload,
                status=status,
                fetched_at=now,
                expires_at=expires_at
            )
            self.session.add(new_item)
        
        await self.session.commit()
