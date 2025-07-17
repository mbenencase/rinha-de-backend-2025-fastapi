from sqlalchemy import Column, Float, DateTime, Enum as SQLAlchemyEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import enum
from .database import Base

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED_DEFAULT = "PROCESSED_DEFAULT"
    PROCESSED_FALLBACK = "PROCESSED_FALLBACK"
    FAILED = "FAILED"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    status = Column(SQLAlchemyEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), index=True)

    __table_args__ = (
        Index('ix_payments_status_processed_at', 'status', 'processed_at'),
    )