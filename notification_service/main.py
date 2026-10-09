import asyncio
from shared.queue.rabbitmq import get_channel,declare_topology
from settings import get_settings
from send_notification import process_notification
import functools

settings=get_settings()

async def main():
    connection,channel=await get_channel()
    await channel.set_qos(prefetch_count=settings.NOTIFICATION_SERVICE_PREFETCH_COUNT)
    exchange,jobs_queue, retry_queue,notification_queue, *_=await declare_topology(channel=channel)
    await notification_queue.consume(functools.partial(process_notification))
    print(" [*] Notification service started. Waiting for messages...")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())