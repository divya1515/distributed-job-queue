import aio_pika
import logging
from datetime import datetime,timezone,timedelta
import httpx
from sqlalchemy import select,func
from shared.db.database import async_session_maker
from shared.db.models.jobs import Job,JobStatus
from shared.db.models.job_items import JobItems,JobItemStatus
from shared.db.crud import _increment_completed,_increment_failed,full_job_status,finalize_job
from shared.rate_limiter.limiter import wait_for_token
from shared.queue.rabbitmq import enqueue_retry
from job_service import handle_transient_failure
from settings import get_settings
import asyncio
import json

logger=logging.getLogger(__name__)
settings=get_settings()
SHORTEN_URL=f"{settings.SHORTNER_SERVICE}/url-shorten"
SWEEP_INTERVAL_SECONDS = 15  # how often the sweep wakes up
RETRY_DELAY_SECONDS = 10  
BASE_BACKOFF_SECONDS=300

async def process_single_item(item_id,client:httpx.AsyncClient):
    async with async_session_maker() as db:
        item = await db.get(JobItems,item_id)
        try:
            await wait_for_token(
                key="rate_limit:url_shortener_service",
                capacity=20,
                refill_rate=10,
            )
            resp=await client.post(SHORTEN_URL,
                            json={
                                "long_url": item.original_url,
                            },
                            timeout=5)
            resp.raise_for_status()
            data=resp.json()
            item.short_url=data["short_url"]
            item.status=JobItemStatus.success
            await db.commit()
            await _increment_completed(db,item.job_id)

        except httpx.HTTPStatusError as e:
            status_code=e.response.status_code
            if status_code == 422:
                item.status=JobItemStatus.dead_letter
                item.error_message=str(e)
                await db.commit()
                await _increment_failed(db,item.job_id) 
            elif status_code in (503,502,504):
                await handle_transient_failure(item, db)
            else:
                item.status=JobItemStatus.dead_letter
                item.error_message=str(e)
                await db.commit()
                await _increment_failed(db,item.job_id) 
        except httpx.TimeoutException:
            await handle_transient_failure(item, db)
        except httpx.RequestError:
            await handle_transient_failure(item, db)

    
async def process_job(job_id,jobs_exchange,email):
    async with async_session_maker() as db:
        job=(
            await db.execute(select(Job).where(Job.job_id == job_id))
        ).scalar_one_or_none()
        if job is None:
            print(f" [!] No job found for {job_id}")
            return

        if job.status in (JobStatus.completed,JobStatus.partial_failure):
            if job.result and job.result.get("notification_enqued_at"):
                print(f" [~] Job {job_id} already finished and notified — skipping")
                return
            else:
                print(f" [~] Job {job_id} finished but notification missing — resuming from there")
                await finalize_job(db,job, jobs_exchange, job_id, email)
                return

        stmt=select(JobItems.id).where(
            JobItems.job_id==job.id,
            JobItems.status.in_([JobItemStatus.failed,JobItemStatus.pending]),
        )
        item_ids=(await db.execute(stmt)).scalars().all()

    sem=asyncio.Semaphore(settings.WORKER_SERVICE_PREFETCH_COUNT)

    async def bounded(item_id,client):
        async with sem:
            await process_single_item(item_id,client)

    async with httpx.AsyncClient() as client:
        await asyncio.gather(*(bounded(item_id,client) for item_id in item_ids),
                             return_exceptions=True)

    async with async_session_maker() as db:
        job=(
            await db.execute(select(Job).where(Job.job_id == job_id))
        ).scalar_one_or_none()

        stmt= select(func.min(JobItems.attempts)).where(
            JobItems.job_id==job.id,
            JobItems.status==JobItemStatus.failed
        )
        min_attempts=(await db.execute(stmt)).scalar_one_or_none()

        if min_attempts is not None:
            backoff=min(BASE_BACKOFF_SECONDS*(2 ** min_attempts),300)
            await enqueue_retry(jobs_exchange,job_id,backoff)

        else:
            await full_job_status(db,job.id)
            await finalize_job(db,job, jobs_exchange, job_id, email)

async def process_message(message: aio_pika.abc.AbstractIncomingMessage,jobs_exchange):
    async with message.process():
        payload=json.loads(message.body.decode());
        job_id=payload["job_id"]   
        email=payload["email"]
        await process_job(job_id,jobs_exchange,email);
        print(f" [x] Successfully processed: {payload}")