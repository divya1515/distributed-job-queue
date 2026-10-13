# One image for all four Python services; docker-compose.yaml picks the command.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 8001

CMD ["uvicorn", "app:app", "--app-dir", "api-service", "--host", "0.0.0.0", "--port", "8000"]
