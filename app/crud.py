from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
import os
from . import models, schemas
from uuid import UUID
from datetime import datetime

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis"))

async def create_payment_in_db(db: AsyncSession, payment_data: dict):
    db_payment = models.Payment(
        id=payment_data['correlationId'], 
        amount=payment_data['amount'], 
        status=models.PaymentStatus.PENDING
    )
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    return db_payment

async def update_payment_status_and_summary(db: AsyncSession, correlation_id: UUID, status: models.PaymentStatus, amount: float):
    payment = await db.get(models.Payment, correlation_id)
    if payment:
        payment.status = status
        payment.processed_at = datetime.utcnow()
        await db.commit()

        processor_type = "default" if status == models.PaymentStatus.PROCESSED_DEFAULT else "fallback"
        
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.incr(f"summary:{processor_type}:requests")
            pipe.incrbyfloat(f"summary:{processor_type}:amount", amount)
            await pipe.execute()

    return payment

async def get_summary_from_redis() -> schemas.PaymentSummaryResponse:
    async with redis_client.pipeline(transaction=False) as pipe:
        pipe.get("summary:default:requests")
        pipe.get("summary:default:amount")
        pipe.get("summary:fallback:requests")
        pipe.get("summary:fallback:amount")
        results = await pipe.execute()

    return schemas.PaymentSummaryResponse(
        default=schemas.PaymentSummary(
            totalRequests=int(results[0] or 0),
            totalAmount=float(results[1] or 0.0)
        ),
        fallback=schemas.PaymentSummary(
            totalRequests=int(results[2] or 0),
            totalAmount=float(results[3] or 0.0)
        )
    )

async def purge_all_data(db: AsyncSession):
    await db.execute(models.Payment.__table__.delete())
    await db.commit()
    await redis_client.flushdb()