import redis.asyncio as redis
from settings import get_settings

settings=get_settings()

redis_client=redis.from_url(settings.REDIS_URL)
NOTIFIED_KEY_PREFIX="notification:sent"
NOTIFIED_TTL_SECONDS=60*60*24*3

async def already_notified(job_id:str) -> bool:
    return await redis_client.exists(f"{NOTIFIED_KEY_PREFIX}{job_id}") == 1

async def mark_notified(job_id:str):
    await redis_client.set(f"{NOTIFIED_KEY_PREFIX}{job_id}","1",ex=NOTIFIED_TTL_SECONDS)