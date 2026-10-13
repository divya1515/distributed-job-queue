import redis.asyncio as redis 
from settings import get_settings
from pathlib import Path
import time
import asyncio

settings=get_settings()

redis_client=redis.from_url(settings.REDIS_URL)

SCRIPT_PATH=Path(__file__).parent/"token_bucket.lua"
TOKEN_BUCKET_SCRIPT = SCRIPT_PATH.read_text()

SCRIPT_SHA=None 

async def get_script_sha():
    return await redis_client.script_load(TOKEN_BUCKET_SCRIPT)

async def is_allowed(key: str,capacity: int,refill_rate: float,requested: float = 1 )-> bool:
    global SCRIPT_SHA
    if SCRIPT_SHA is None:
        SCRIPT_SHA = await get_script_sha()

    now = time.time()
    try:
        result=await redis_client.evalsha(
            SCRIPT_SHA,1,key,capacity,refill_rate,now,requested
        )
    except redis.exceptions.NoScriptError:
        SCRIPT_SHA = await get_script_sha()
        result = await redis_client.evalsha(
            SCRIPT_SHA, 1, key, capacity, refill_rate, now, requested
        )
    return result == 1

async def wait_for_token(key: str,capacity: int,refill_rate: float ,requested : float=1,poll_interval: float = 0.1):
    while True:
        allowed=await is_allowed(key,capacity,refill_rate,requested)
        if allowed:
            return True
        await asyncio.sleep(poll_interval)

