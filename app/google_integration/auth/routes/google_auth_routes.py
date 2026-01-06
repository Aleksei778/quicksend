from typing import Annotated
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse

from google_integration.auth.enum.source import Source
from google_integration.auth.services.google_auth_service import (
    GoogleAuthService,
    get_google_auth_service,
)


google_auth_router = APIRouter(prefix="/auth/google", tags=["google_auth"])


@google_auth_router.get("/login")
async def login(
    request: Request,
    redirect_to: str,
    lang: str,
    google_auth_service: Annotated[GoogleAuthService, Depends(get_google_auth_service)],
) -> RedirectResponse:
    return await google_auth_service.login(
        request=request,
        redirect_to=Source(redirect_to),
        lang=lang,
    )


@google_auth_router.get("/callback")
async def callback(
    request: Request,
    google_auth_service: Annotated[GoogleAuthService, Depends(get_google_auth_service)],
) -> RedirectResponse:
    return await google_auth_service.callback(request)
