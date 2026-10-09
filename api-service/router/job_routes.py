from shared.schemas.job import JobCreate
from typing import Annotated
from fastapi import APIRouter,Depends,Header,Request,HTTPException,UploadFile,File,Form
from pydantic import EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.database import get_async_db
from shared.db.models.jobs import Job
from shared.db.crud import create_job_entry,create_job_items
from shared.queue.rabbitmq import enqueue_job
from settings import get_settings
from shared.utils.csv_utils import parse_csv
from shared.db.models.jobs import JobType
from shared.rate_limiter.limiter import is_allowed

router=APIRouter()
settings=get_settings()

# @router.post("/jobs")
# async def create_job(request:JobCreate,req: Request,x_client_id:str|None=Header(default=None),db: AsyncSession=Depends(get_async_db)):
#     ip_address=req.client.host

#     if not x_client_id:
#         client=await register_client(db)
#         x_client_id=client.client_id
#     client_row=await validate_client(x_client_id,db)
#     if client_row:
#         job=await create_job_entry(client_row.id,request.type,request.payload,db)
#         callback_url=(
#             f"{settings.API_SERVICE_URL}"
#         )
#         await enqueue_job(
#             job_id=job.job_id,
#             completion_callback_url=callback_url
#         )
#         return {
#             "job_id":job.job_id,
#             "status":"queued",
#             "client_id": x_client_id
#         }
#     else:
#         raise HTTPException(status_code=403, detail="Invalid client ID")

@router.post("/jobs/bulk_url_shorten")
async def create_bulk_url_job(
    request: Request,
    file:Annotated[UploadFile, File()],
    email: Annotated[EmailStr,Form()],
    db:AsyncSession=Depends(get_async_db)):

    client_ip=request.client.host
    allowed=await is_allowed(
        key=f"rate_limit:{client_ip}",
        capacity=3,
        refill_rate=1,
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    
    file_bytes=await file.read()
    urls=parse_csv(file_bytes)
    payload={
        "source_file_name":file.filename,
        "total_items":len(urls),
        "email":email
    }
    job=await create_job_entry(JobType.bulk_url_shortening,payload,db)
    await create_job_items(job.id,urls,db)
    await enqueue_job(
        request.app.state.jobs_exchange,
        job_id=str(job.job_id),
        email=email
    )
    return {
        "job_id":job.job_id,
        "status":"queued"
    }
