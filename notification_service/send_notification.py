import aio_pika
import json
import asyncio
import aiosmtplib
from settings import get_settings
from email.message import EmailMessage
from utils import mark_notified,already_notified
from shared.rate_limiter.limiter import wait_for_token

settings=get_settings()

GMAIL_ADDRESS=settings.GMAIL_ADDRESS
GMAIL_APP_PASSWORD=settings.GMAIL_APP_PASSWORD

async def send_completion_email(email: str,job_id: str, file_path: str):
    message=EmailMessage()
    message["From"]=GMAIL_ADDRESS
    message["To"]=email
    message["Subject"]="Your job is complete"
    message.set_content(
        f"Your job {job_id} has finished processing. Please find the results attached."
    )

    file_bytes=await asyncio.to_thread(lambda: open(file_path,"rb").read())

    message.add_attachment(
        file_bytes,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx MIME type
        filename="job_report.xlsx",  # client-facing name
    )
    await wait_for_token(
        key="rate_limit:gmail_smtp",
        capacity=5,
        refill_rate=2,
    )

    await aiosmtplib.send(
        message,
        hostname="smtp.gmail.com",
        port=587,
        start_tls=True,
        username=GMAIL_ADDRESS,
        password=GMAIL_APP_PASSWORD,
    )

async def process_notification(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process():
        payload=json.loads(message.body.decode())
        job_id=payload["job_id"]
        email=payload["email"]
        file_path=payload["file_path"]
        if await already_notified(job_id):
            print(f" [~] Job {job_id} already notified — skipping duplicate")
            return
        try:
            await send_completion_email(email,job_id,file_path)
        except Exception as e:
            print(f" [!] Failed to send notification for job {job_id}: {e}")
            raise

        await mark_notified(job_id)
        print(f" [x] Notification sent for job {job_id}")
            
