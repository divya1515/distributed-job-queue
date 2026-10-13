import asyncio 
import aio_pika
import json 
from aio_pika import ExchangeType
from settings import get_settings
from shared.queue.constants import JOBS_EXCHANGE,MAIN_QUEUE,JOBS_ROUTING_KEY,RETRY_QUEUE,RETRY_ROUTING_KEY,NOTIFICATION_QUEUE,NOTIFICATION_ROUTING_KEY

settings=get_settings()

async def get_connection():
    return await aio_pika.connect_robust(settings.RABBITMQ_URL)

async def declare_topology(channel):
    exchange=await channel.declare_exchange(JOBS_EXCHANGE,ExchangeType.DIRECT,durable=True)
    jobs_queue=await channel.declare_queue(
        MAIN_QUEUE,
        durable=True)
    await jobs_queue.bind(exchange,routing_key=JOBS_ROUTING_KEY)

    retry_queue=await channel.declare_queue(
        RETRY_QUEUE,
        durable=True,
        arguments={
            "x-dead-letter-exchange":JOBS_EXCHANGE,
            "x-dead-letter-routing-key": JOBS_ROUTING_KEY
        }
        )
    await retry_queue.bind(exchange,routing_key=RETRY_ROUTING_KEY)

    notification_queue=await channel.declare_queue(
        NOTIFICATION_QUEUE,
        durable=True
    )
    await notification_queue.bind(exchange,routing_key=NOTIFICATION_ROUTING_KEY)

    return exchange,jobs_queue,retry_queue,notification_queue


async def enqueue_retry(exchange,message_body: dict, backoff_seconds: int):
    await exchange.publish(
        aio_pika.Message(
            body=json.dumps(message_body).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            expiration=str(backoff_seconds * 1000),
        ),
        routing_key=RETRY_ROUTING_KEY
    )

async def enqueue_job(jobs_exchange,job_id :str,email: str):
    message={
        "job_id":job_id,
        "email":email
    }
    await jobs_exchange.publish(
        aio_pika.Message(
            body=json.dumps(message).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key=JOBS_ROUTING_KEY
    )

async def enqueue_notification(jobs_exchange,job_id:str,email,file_path):
    message={
        "job_id":job_id,
        "email":email,
        "file_path":file_path,
    }
    await jobs_exchange.publish(
        aio_pika.Message(
            body=json.dumps(message).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key=NOTIFICATION_ROUTING_KEY
    )


async def get_channel():
    connection= await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel= await connection.channel()
    return connection,channel
