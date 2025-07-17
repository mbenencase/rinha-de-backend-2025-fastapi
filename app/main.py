import asyncio
import httpx
from uuid import UUID
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from . import crud, models, schemas, database
from .config import settings
from .health_checker import health_check_scheduler, get_cached_health

app = FastAPI()

payment_queue = asyncio.Queue(maxsize=10000)
NUM_WORKERS = 150 

@app.on_event("startup")
async def startup_event():
    async with database.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    asyncio.create_task(health_check_scheduler())
    
    for i in range(NUM_WORKERS):
        asyncio.create_task(payment_worker(f"worker-{i}"))

http_client = httpx.AsyncClient(timeout=10.0, limits=httpx.Limits(max_connections=200, max_keepalive_connections=50))

async def payment_worker(worker_id: str):
    while True:
        try:
            # Pega um item da fila para processar
            payment_data = await payment_queue.get()
            
            async with database.AsyncSessionLocal() as db:
                try:
                    await crud.create_payment_in_db(db, payment_data)
                except IntegrityError:
                    payment_queue.task_done()
                    continue

                success = await process_payment_logic(db, payment_data)
                if not success:
                    await asyncio.sleep(0.1)
                    await payment_queue.put(payment_data)

            payment_queue.task_done()
        except Exception as e:
            logger.error(f"Error in {worker_id}: {e}")

async def process_payment_logic(db: AsyncSession, payment_data: dict) -> bool:
    correlation_id = payment_data['correlationId']
    amount = payment_data['amount']
    
    default_health = await get_cached_health("default")
    fallback_health = await get_cached_health("fallback")

    if default_health.failing and not fallback_health.failing:
        primary, secondary = "fallback", "default"
    else:
        primary, secondary = "default", "fallback"
        
    if await attempt_payment(db, correlation_id, amount, primary):
        return True
    
    if await attempt_payment(db, correlation_id, amount, secondary):
        return True

    return False

async def attempt_payment(db: AsyncSession, correlation_id: UUID, amount: float, processor_name: str) -> bool:
    url = settings.PROCESSOR_DEFAULT_URL if processor_name == "default" else settings.PROCESSOR_FALLBACK_URL
    status_on_success = models.PaymentStatus.PROCESSED_DEFAULT if processor_name == "default" else models.PaymentStatus.PROCESSED_FALLBACK

    payload = {
        "correlationId": str(correlation_id),
        "amount": amount,
        "requestedAt": datetime.utcnow().isoformat() + "Z"
    }

    try:
        response = await http_client.post(f"{url}/payments", json=payload)
        if response.status_code == 200:
            await crud.update_payment_status_and_summary(db, correlation_id, status_on_success, amount)
            return True
        else:
            return False
    except httpx.RequestError as e:
        return False


@app.post("/payments", status_code=status.HTTP_202_ACCEPTED)
async def create_payment_endpoint(request: Request):
    try:
        body = await request.json()
        payment_data = {
            "correlationId": UUID(body['correlationId']),
            "amount": float(body['amount'])
        }
        await payment_queue.put(payment_data)
        return
    except (KeyError, ValueError):
        raise HTTPException(status_code=422, detail="Invalid payment data")
    except asyncio.QueueFull:
        raise HTTPException(status_code=503, detail="Service busy, please try again later.")


@app.get("/payments-summary", response_model=schemas.PaymentSummaryResponse)
async def get_payments_summary_endpoint():
    return await crud.get_summary_from_redis()


@app.post("/purge-payments", status_code=status.HTTP_204_NO_CONTENT)
async def purge_database(db: AsyncSession = Depends(database.get_db)):
    await crud.purge_all_data(db)
    return