import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, BigInteger, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

class CromaCacheModel(Base):
    __tablename__ = "croma_cache"

    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4, 
        index=True
    )
    source = Column(String, nullable=False)
    lookup_key = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, nullable=False)  # 'ok' | 'not_found' | 'error'
    fetched_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc)
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "lookup_key", name="uq_source_lookup_key"),
        Index("idx_croma_cache_expires_at", "expires_at"),
    )


class QuotaLogModel(Base):
    __tablename__ = "quota_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    remaining = Column(Integer, nullable=True)
    request_id = Column(String, nullable=True)
    cache_hit = Column(Boolean, nullable=False, default=False)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc)
    )
