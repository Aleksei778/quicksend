from datetime import datetime
from typing import Optional
from fastapi import Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.ext.asyncio import AsyncSession

from common.logger import logger
from schemas.user_schema import UserCreate
from schemas.token_schema import GoogleTokenDto
from services.google_token_service import GoogleTokenService
from subscriptions.services.subscription_service import SubscriptionService
from services.user_service import UserService
from common.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URL,
    GOOGLE_AUTH_SCOPES,
    GOOGLE_ACCESS_TOKEN_URL,
    GOOGLE_AUTHORIZE_URL,
    GOOGLE_CONFIGURATION_URL,
    GOOGLE_USERINFO_URL
)


class GoogleAuthService:
    def __init__(
            self,
            db: AsyncSession,
            user_service: UserService,
            subscription_service: SubscriptionService,
            google_token_service: GoogleTokenService,
    ) -> None:
        self.db = db
        self.oauth = self._init_oauth()
        self.google = self.oauth.create_client("google")
        self.user_service = user_service
        self.subscription_service = subscription_service
        self.google_token_service = google_token_service

    def _init_oauth(self) -> OAuth:
        oauth = OAuth()

        oauth.register(
            name="google",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            authorize_url=GOOGLE_AUTHORIZE_URL,
            authorize_params=None,
            access_token_url=GOOGLE_ACCESS_TOKEN_URL,
            access_token_params=None,
            client_kwargs={
                "scope": GOOGLE_AUTH_SCOPES,
                "redirect_uri": GOOGLE_REDIRECT_URL,
            },
            server_metadata_url=GOOGLE_CONFIGURATION_URL,
        )

        return oauth


    async def login(self, request: Request) -> RedirectResponse:
        redirect_uri = request.url_for("oauth2callback")

        redirect = await self.google.authorize_redirect(
            request, redirect_uri, access_type="offline", prompt="consent"
        )

        return redirect

    async def callback(self,request: Request):
        token_data = await self.google.authorize_access_token(request)
        if not token_data:
            return RedirectResponse(url="/error")

        resp = await self.google.get(
            GOOGLE_USERINFO_URL,
            token=token_data
        )
        user_info = resp.json()

        logger.info(f"user_info: {user_info}")

        if not user_info or "error" in user_info:
            return RedirectResponse(url="/error")

        user = await self.user_service.find_user_by_email(user_info["email"])

        if not user:
            user_create_dto = UserCreate(
                email=user_info["email"],
                first_name=user_info["first_name"],
                last_name=user_info["family_name"],
                picture=user_info["picture"]
            )

            user = await self.user_service.create_user(user_create_dto)

        active_sub = await self.subscription_service.get_user_active_sub(user)
        subscription_info = {"plan": "No active subscription"}

        if active_sub:
            subscription_info["plan"] = active_sub.plan

        create_or_update_token_dto = GoogleTokenDto(
            user=user,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            expires_at=datetime.fromtimestamp(token_data["expires_at"]),
            scope=token_data["scope"],
        )
        google_token = self.google_token_service.create_or_update_token(create_or_update_token_dto)

        data = {
            "user_info": {"id": user.id, "first_name": user.first_name, "last_name": user.last_name, "email": user.email},
            "subscription_info": {**subscription_info},
        }

        access_jwt_token = await create_access_token(data=data)
        refresh_jwt_token = await create_refresh_token(data=data)

        response = RedirectResponse("/")

        response.headers["Authorization"] = f"Bearer {access_jwt_token}"

        response.set_cookie(
            key="access_token",
            httponly=True,
            value=f"Bearer {access_jwt_token}",
            secure=True,
            samesite="lax",
        )
        response.set_cookie(
            key="refresh_token",
            httponly=True,
            value=f"Bearer {refresh_jwt_token}",
            secure=True,
            samesite="lax",
        )

        return response

    async def _fetch_user_info(self, token_data: dict) -> Optional[dict]:
        google_user_response = await self.google.get(
            url=GOOGLE_USERINFO_URL,
            token=token_data
        )

        data = google_user_response.json()

        if not data or "error" in data:
            return None

        return data
