from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from google_integration.auth.services.google_auth_service import GoogleAuthService


google_auth_router = APIRouter(prefix="/auth/google", tags=["google_auth"])

@google_auth_router.get("/login")
async def login(
    request: Request,
    google_auth_service: GoogleAuthService = Depends(GoogleAuthService)
) -> RedirectResponse:
    return await google_auth_service.login(request)

@google_auth_router.get("/callback")
async def callback(
    request: Request,
    google_auth_service: GoogleAuthService = Depends(GoogleAuthService)
) -> RedirectResponse:
    return await google_auth_service.callback(request)
