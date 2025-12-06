from typing import Callable

from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from contextlib import asynccontextmanager
from redis import asyncio as aioredis
import uvicorn
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError, KafkaError
from elasticsearch import Elasticsearch
from datetime import datetime
import logging
from starlette.middleware.sessions import SessionMiddleware

from auth.google_auth import auth_router
from subpay.subscriptions import subscription_router
from config import (
    SESSION_SECRET_KEY,
    KAFKA_BASE_CONFIG,
    KAFKA_TOPIC,
    KAFKA_NUM_PARTITIONS,
    KAFKA_REPLICATION_FACTOR,
    CORS_ORIGINS,
)
from utils.google_sheets import sheets_router
from subpay.yookassa import payment_router
from send import send_router
from logger import logger

# ---- ВСЕ НАСТРОЙКИ ПРИЛОЖЕНИЯ ----




# Инициализация REDIS
@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = aioredis.from_url(
        "redis://localhost", encoding="utf8", decode_responses=True
    )

    # Инициализация кеша после создания Redis соединения
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

    await create_kafka_topic_with_check()

    yield


app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    start_time = datetime.utcnow()
    response = await call_next(request)
    end_time = datetime.utcnow()

    log_data = {
        "timestamp": start_time.isoformat(),
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": (end_time - start_time).total_seconds() * 1000,
    }

    logger.info(log_data)

    return response

async def create_kafka_topic():
    admin_client = AIOKafkaAdminClient(**KAFKA_BASE_CONFIG)

    try:
        await admin_client.start()

        topic = NewTopic(
            name=KAFKA_TOPIC,
            num_partitions=KAFKA_NUM_PARTITIONS,
            replication_factor=KAFKA_REPLICATION_FACTOR,
        )

        await admin_client.create_topics([topic])

        logger.info(f"Created topic {KAFKA_TOPIC}")
    except TopicAlreadyExistsError:
        logger.info(f"Topic {KAFKA_TOPIC} already exists")
    except ValueError as ve:
        logger.error(f"Ошибка преобразования типов: {ve}")
    except KafkaError as ke:
        logger.error(f"Ошибка при создании темы: {ke}")


async def check_kafka_topic_exists(topic: str) -> bool:
    admin_client = AIOKafkaAdminClient(**KAFKA_BASE_CONFIG)

    try:
        await admin_client.start()

        metadata = await admin_client.describe_topics([topic])
        return topic in metadata

    except Exception as e:
        logger.error(f"Ошибка при проверке существования темы kafka: {e}")
        return False
    finally:
        await admin_client.close()


async def create_kafka_topic_with_check():
    try:
        if await check_kafka_topic_exists(KAFKA_TOPIC):
            logger.info(f"Kafka topic {KAFKA_TOPIC} already exists")
            return

        await create_kafka_topic()

    except Exception as e:
        logger.error(f"Ошибка при создании топика: {e}")
        raise


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Set-Cookie",
        "Access-Control-Allow-Headers",
        "Authorization",
        "Access-Control-Allow-Origins",
        "accept",
    ],
)

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)

api_router = APIRouter(prefix="/api/v1")

# ---- РОУТЕРЫ ----
api_router.include_router(send_router)
api_router.include_router(auth_router)
api_router.include_router(subscription_router)
api_router.include_router(payment_router)
api_router.include_router(sheets_router)
app.include_router(api_router)

# ---- ЗАПУСК ПРИЛОЖЕНИЯ ----
if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
