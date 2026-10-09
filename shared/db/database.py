import os
import redis
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import async_sessionmaker
from dotenv import load_dotenv
import os
from sqlalchemy.orm import declarative_base

Base = declarative_base()   # defined ONCE here

load_dotenv()
DATABASE_URL=os.getenv("DATABASE_URL")
REDIS_URL=os.getenv("REDIS_URL")
print(DATABASE_URL)
engine=create_async_engine(DATABASE_URL,pool_size=10,max_overflow=5)
async_session_maker=async_sessionmaker(bind=engine,class_=AsyncSession,expire_on_commit=False)


def get_db():
    db=async_session_maker()
    try:
        yield db 
    finally:
        db.close()

async def get_async_db():
    async with async_session_maker() as db:
        yield db

def get_redis():
    client=redis.Redis.from_url(REDIS_URL,decode_responses=True)
    try:
        yield client
    finally:
        client.close()