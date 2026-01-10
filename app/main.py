from contextlib import asynccontextmanager
from typing import Callable
from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from starlette.middleware.sessions import SessionMiddleware

from app.google_auth.route import router as google_auth_router
from app.google_sheets.route import router as google_sheets_router
from app.jwt_auth.route import router as jwt_router
from app.subscriptions.route import router as subscription_router
from app.campaigns.route import router as campaign_router
from app.utils.kafka.setup import create_kafka_topic_if_not_exists
from app.utils.redis_ import close_redis_client
from common.utils.logger import logger
from common.utils.config import base_config
from common.users.model import add_relationships_for_app


@asynccontextmanager
async def lifespan(_: FastAPI):
    add_relationships_for_app()
    await create_kafka_topic_if_not_exists()
    logger.info("✅ App started")
    yield
    logger.info("❌ App ended")
    await close_redis_client()


app = FastAPI(title="QuickSend", lifespan=lifespan)


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


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        base_config.FRONTEND_URL,
        f"chrome-extension://{base_config.EXTENSION_ID}",
    ],
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
app.add_middleware(SessionMiddleware, secret_key=base_config.SESSION_SECRET_KEY)


api_router = APIRouter(prefix="/api", tags=["Api"])

api_router.include_router(google_auth_router)
api_router.include_router(jwt_router)
api_router.include_router(subscription_router)
api_router.include_router(google_sheets_router)
api_router.include_router(campaign_router)

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, host="0.0.0.0", reload=True)
