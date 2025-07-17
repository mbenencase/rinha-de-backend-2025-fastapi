import asyncio
import httpx
import os
import redis.asyncio as redis
import json
from .config import settings
from .schemas import HealthStatus

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis"))

async def check_service_health(client: httpx.AsyncClient, url: str, service_name: str):
    try:
        response = await client.get(f"{url}/payments/service-health")
        if response.status_code == 200:
            health_data = HealthStatus(**response.json())
            await redis_client.set(f"health:{service_name}", health_data.json())
        else:
            # Se recebermos erro (ex: 429), consideramos o serviço como indisponível
            health_data = HealthStatus(failing=True, minResponseTime=99999)
            await redis_client.set(f"health:{service_name}", health_data.json())
    except (httpx.RequestError, json.JSONDecodeError) as e:
        health_data = HealthStatus(failing=True, minResponseTime=99999)
        await redis_client.set(f"health:{service_name}", health_data.json())


async def health_check_scheduler():
    async with httpx.AsyncClient() as client:
        while True:
            await asyncio.gather(
                check_service_health(client, settings.PROCESSOR_DEFAULT_URL, "default"),
                check_service_health(client, settings.PROCESSOR_FALLBACK_URL, "fallback")
            )
            await asyncio.sleep(5)

async def get_cached_health(service_name: str) -> HealthStatus:
    cached = await redis_client.get(f"health:{service_name}")
    if cached:
        return HealthStatus(**json.loads(cached))
    return HealthStatus(failing=True, minResponseTime=99999)
