FROM python:3.12-slim AS base

WORKDIR /app

RUN pip install --no-cache-dir uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN uv pip install --system -r pyproject.toml

COPY . .

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

FROM base AS app

EXPOSE 8000

CMD ["python", "app/main.py"]

FROM base AS consumer

CMD ["python", "consumer/consumer.py"]