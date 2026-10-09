from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert,text
from shared.db.models.jobs import Job,JobStatus
from fastapi import HTTPException
from shared.db.models.job_items import JobItemStatus,JobItems
from worker_service.file_generator import generate_job_result_file
import aio_pika
import logging
from sqlalchemy import select
import asyncio
from datetime import datetime,timezone,timedelta
from shared.queue.rabbitmq import enqueue_notification

async def create_job_entry(type,payload,db: AsyncSession):
    try:
        job=Job(
            type=type,
            payload=payload,
            status="pending",
            email=payload["email"],
            total_items=payload["total_items"]
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

async def create_job_items(job_id:int,urls:list,db: AsyncSession):
    try:
        items=[
            {
                "job_id":job_id,
                "item_index":idx,
                "original_url":url,
                "status":JobItemStatus.pending

            }
            for idx,url in enumerate(urls)
        ]
        if not items:
            return

        await db.execute(insert(JobItems),items)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job items: {str(e)}")


async def _increment_completed(db: AsyncSession,job_id):
    try:
        Sql_query=text(
            "UPDATE job SET completed_items = completed_items + 1 WHERE id = :job_id "
            )
        await db.execute(Sql_query,{"job_id":job_id})
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e

async def _increment_failed(db: AsyncSession, job_id):
    try:
        Sql_query=text(
            "UPDATE job SET failed_items = failed_items + 1 WHERE id = :job_id"
        )
        await db.execute(Sql_query,{"job_id":job_id})
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e

async def full_job_status(db: AsyncSession, job_id):
    try:
        job=await db.get(Job,job_id)
        print(
            f"JOB STATUS CHECK: "
            f"job_id={job.id}, "
            f"total={job.total_items}, "
            f"completed={job.completed_items}, "
            f"failed={job.failed_items}"
        )
        if job.completed_items + job.failed_items == job.total_items:
            job.status=(
                JobStatus.completed
                if job.failed_items == 0
                else JobStatus.partial_failure
            )
            await db.commit()
    except Exception as e:
        await db.rollback()
        raise e

async def finalize_job(db,job,jobs_exchange,job_id,email):
    if job.file_path:
        print(f" [~] File already generated for job {job_id} — reusing")
    else:
        items = (
            await db.execute(select(JobItems).where(JobItems.job_id == job.id))
        ).scalars().all()
        try:
            file_path = await asyncio.to_thread(generate_job_result_file, job, items)
            job.file_path=file_path
            await db.commit()
        except Exception:
            await db.rollback()
            print(f" [!] Failed to generate file for job {job_id}")
            raise

    if job.result and job.result.get("notification_enqueued_at"):
        print(f" [~] Notification already enqueued for job {job_id} — skipping")
        return
    await enqueue_notification(jobs_exchange, job_id, email, file_path)
    job.result = {**(job.result or {}), "notification_enqueued_at": datetime.now(timezone.utc).isoformat()}
    await db.commit()

