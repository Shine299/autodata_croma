import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class CromaCacheModel(Base):
    __tablename__ = "croma_cache"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    source = Column(String, nullable=False)
    lookup_key = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, nullable=False)  # 'ok' | 'not_found' | 'error'
    fetched_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
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
        default=lambda: datetime.now(timezone.utc),
    )


class VerificationModel(Base):
    __tablename__ = "verifications"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    plate = Column(String, nullable=False, index=True)
    seller_hash = Column(String, nullable=True)
    asking_price = Column(Numeric, nullable=True)
    verdict = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=False)
    flags = Column(JSON, nullable=False, default=list)
    payload = Column(JSON, nullable=False)
    channel = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class AppraisalModel(Base):
    __tablename__ = "appraisals"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    verification_id = Column(
        UUID(as_uuid=True),
        ForeignKey("verifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asking_price = Column(Numeric, nullable=False)
    fair_price = Column(Numeric, nullable=False)
    deductions = Column(JSON, nullable=False, default=list)
    script = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ConversationModel(Base):
    __tablename__ = "conversations"

    chat_id = Column(String, primary_key=True, index=True)
    state = Column(String, nullable=False, default="IDLE")
    context = Column(JSON, nullable=False, default=dict)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
