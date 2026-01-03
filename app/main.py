from contextlib import asynccontextmanager
from typing import Callable
from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

from google_integration.auth.routes.google_auth_routes import google_auth_router
from google_integration.sheet.routes.sheet_router import google_sheets_router
from users.routes.jwt_routes import jwt_router
from subscriptions.routes.subscription_routes import subscription_router
from campaigns.routes.campaign_routes import campaign_router
from common.log.logger import logger
from common.config.base_config import base_settings
from common.redis.redis_client import close_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
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
        base_settings.FRONTEND_URL,
        base_settings.CHROME_EXTENSION_URL,
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


api_router = APIRouter(prefix="/api", tags=["Api"])

api_router.include_router(google_auth_router)
api_router.include_router(jwt_router)
api_router.include_router(subscription_router)
api_router.include_router(google_sheets_router)
api_router.include_router(campaign_router)

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
