import shared.db.models
from shared.queue.rabbitmq import get_channel,declare_topology
from shared.queue.constants import MAIN_QUEUE
from settings import get_settings
from worker_service.consumer_service import process_message
import asyncio
import functools

settings=get_settings()

async def init_worker():
    connection,channel=await get_channel()
    await channel.set_qos(prefetch_count=settings.WORKER_SERVICE_PREFETCH_COUNT)
    jobs_exchange, jobs_queue , *_ = await declare_topology(channel)
    return jobs_exchange,jobs_queue


async def main():
    jobs_exchange,jobs_queue=await init_worker()
    await jobs_queue.consume(functools.partial(process_message,jobs_exchange=jobs_exchange))
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())