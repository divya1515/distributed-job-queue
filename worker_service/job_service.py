from shared.db.models.jobs import Job , JobStatus
from shared.db.models.job_items import JobItems,JobItemStatus
from shared.db.crud import _increment_failed
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession


async def get_job(db:AsyncSession ,job_id) -> Optional[Job]:
    return await db.get(Job,job_id)

async def mark_processing(db:AsyncSession,job:Job) -> None:
    job.status=JobStatus.processing
    job.updated_at=datetime.now(timezone.utc)
    await db.commit()

async  def mark_failed(db:AsyncSession,job:Job,error:str) -> None:
    job.status=JobStatus.failed
    job.result={"error":error}
    job.updated_at=datetime.now(timezone.utc)
    await db.commit

async def mark_completed(db:AsyncSession,job: Job,result) -> None:
    job.status=JobStatus.completed
    job.result=result
    job.updated_at=datetime.now(timezone.utc)
    await db.commit

async def handle_transient_failure(item: JobItems,db: AsyncSession):
    item.attempts += 1
    if item.attempts >= item.max_attempts:
        item.status=JobItemStatus.dead_letter
        item.error_message="Max retries exceeded"
        await db.commit()
        await _increment_failed(db,item.job_id) 
    else:
        item.status=JobItemStatus.failed









