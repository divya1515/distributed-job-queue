from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import RedirectResponse
from core.cache import get_redis
from shortener_service.schemas import ShortenRequest, ShortenResponse
from shortener_service.core.shorten import generate_short_url
import redis.asyncio as redis

router=APIRouter()

@router.post("/url-shorten")
async def url_shorten(request: ShortenRequest,r: redis.Redis = Depends(get_redis)):
    if "fail-transient" in str(request.long_url):
        raise HTTPException(status_code=503,detail="Simulated transient failure")
    short_code,short_url=generate_short_url(request.long_url)
    await r.set(
        short_code,
        str(request.long_url),
        ex=3600
    )
    return ShortenResponse(short_url=short_url)

@router.get("/{short_code}")
async def redirect(short_code: str,r: redis.Redis = Depends(get_redis)):
    long_url=await r.get(short_code)
    if not long_url:
        pass
    return RedirectResponse(url=long_url,status_code=307)
    
        