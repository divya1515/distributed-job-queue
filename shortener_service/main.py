from fastapi import FastAPI
from router.shorten import router
from core.cache import pool as redis_pool
from contextlib import asynccontextmanager
import redis.asyncio as redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis=redis.Redis(connection_pool=redis_pool)
    try:
        await app.state.redis.ping()
        print("Redis Connection Established!!")
    except Exception as e:
        print(f" [!] Redis connection failed: {e}")
        raise

    yield

    await app.state.redis.close()
    await redis_pool.disconnect()
    print(" [x] Redis connection closed")


app=FastAPI(lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001 , reload=True)