import shared.db.models  # noqa: F401 — forces model registration for FK resolution
from fastapi import FastAPI
from router.job_routes import router
from contextlib import asynccontextmanager
from shared.queue.rabbitmq import get_connection,declare_topology
from dotenv import load_dotenv
load_dotenv()


@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.rabbit_connection=await get_connection()
    channel=await app.state.rabbit_connection.channel()
    app.state.jobs_exchange,*_ = await declare_topology(channel)
    yield
    await app.state.rabbit_connection.close()
    
app=FastAPI(lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000 , reload=True)