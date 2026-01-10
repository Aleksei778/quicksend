from typing import Annotated
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse

from app.google_auth.enum_ import Source
from app.google_auth.service import GoogleAuthService, get_google_auth_service


router = APIRouter(prefix="/auth/google", tags=["google_auth"])


@router.get("/login")
async def login(
    request: Request,
    source: Source,
    lang: str,
    google_auth_service: Annotated[GoogleAuthService, Depends(get_google_auth_service)],
) -> RedirectResponse:
    return await google_auth_service.login(request, source, lang)


@router.get("/callback")
async def callback(
    request: Request,
    google_auth_service: Annotated[GoogleAuthService, Depends(get_google_auth_service)],
) -> RedirectResponse:
    return await google_auth_service.callback(request)
