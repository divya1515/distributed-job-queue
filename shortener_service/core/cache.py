from settings import get_settings
from fastapi import Request
import redis.asyncio as redis

settings=get_settings()

pool=redis.ConnectionPool.from_url(settings.REDIS_URL,
                                   decode_responses=True,
                                   max_connections=20)

async def get_redis(request: Request)-> redis.Redis:
    return request.app.state.redis
