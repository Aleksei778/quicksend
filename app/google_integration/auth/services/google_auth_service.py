from typing import Annotated
from fastapi import Request, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config.base_config import base_settings
from app.common.db.database import get_db
from app.google_integration.auth.enum.source import Source
from app.google_integration.auth.services.google_token_service import GoogleTokenService, get_google_token_service
from app.google_integration.config.google_config import google_settings
from app.subscriptions.services.subscription_service import SubscriptionService, get_subscription_service
from app.users.config.jwt_config import jwt_settings
from app.users.schemas.find_or_create_user import FindOrCreateUser
from app.google_integration.auth.schemas.find_or_create_google_token import FindOrCreateGoogleToken
from app.users.services.jwt_service import JwtService, get_jwt_service
from app.users.services.user_service import UserService, get_user_service
from app.common.log.logger import logger


class GoogleAuthService:
    def __init__(
        self,
        user_service: UserService,
        google_token_service: GoogleTokenService,
        jwt_service: JwtService,
        subscription_service: SubscriptionService,
        db: AsyncSession,
    ) -> None:
        self._db = db
        self._user_service = user_service
        self._google_token_service = google_token_service
        self._jwt_service = jwt_service
        self._subscription_service = subscription_service

    async def _create_flow(self, source: Source) -> Flow:
        return Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": google_settings.GOOGLE_CLIENT_ID,
                    "client_secret": google_settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": google_settings.GOOGLE_AUTH_URI,
                    "token_uri": google_settings.GOOGLE_TOKEN_URI,
                }
            },
            scopes=google_settings.WEBSITE_GOOGLE_SCOPES
                if source == Source.Website
                else google_settings.EXTENSION_GOOGLE_SCOPES,
            redirect_uri=google_settings.REDIRECT_URI,
        )

    async def login(
        self,
        request: Request,
        source: Source,
        lang: str,
    ) -> RedirectResponse:
        flow = await self._create_flow(source)

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
        )

        request.session["state"] = state
        request.session["source"] = source.value
        request.session["lang"] = lang

        return RedirectResponse(authorization_url)

    async def callback(self, request: Request):
        state = request.session.get("state")

        if not state or state != request.query_params.get("state"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid state parameter",
            )

        source = Source(request.session.get('source', 'website'))
        lang = request.session.get('lang', 'en')

        flow = await self._create_flow(source)
        flow.fetch_token(authorization_response=str(request.url))

        credentials = flow.credentials

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No google token data",
                headers={"WWW-Authenticate": "Bearer"},
            )

        oauth_service = build("oauth2", "v2", credentials=credentials)
        user_info = oauth_service.userinfo().get().execute()

        if not user_info or "error" in user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user info provided",
                headers={"WWW-Authenticate": "Bearer"},
            )

        (logger.bind(user_info=user_info).debug("User info retrieved"))

        user = await self._user_service.find_or_create_user(
            FindOrCreateUser(
                email=user_info.get("email"),
                first_name=user_info.get("given_name"),
                last_name=user_info.get("family_name"),
                picture=user_info.get("picture"),
                oauth_id=user_info.get("id"),
            )
        )

        if source == Source.Extension:
            await self._google_token_service.find_or_create_google_token(
                FindOrCreateGoogleToken(
                    user=user,
                    access=credentials.token,
                    refresh=credentials.refresh_token,
                    expiry=credentials.expiry
                )
            )

            await self._subscription_service.create_trial(user)

        user_data_for_jwt = await self._user_service.get_user_info_for_jwt(user)

        access_jwt_token = await self._jwt_service.create_access_token(user_data_for_jwt)
        refresh_jwt_token = await self._jwt_service.create_refresh_token(user_data_for_jwt)

        return await self._get_redirect(
            access_jwt_token=access_jwt_token,
            refresh_jwt_token=refresh_jwt_token,
            source=source,
            lang=lang,
        )

    async def _get_redirect(
        self,
        access_jwt_token: str,
        refresh_jwt_token: str,
        lang: str,
        source: Source,
    ) -> RedirectResponse:
        if source == Source.Website:
            response = RedirectResponse(
                f"{base_settings.FRONTEND_URL}/{lang}/profile"
            )

            response.set_cookie(
                key="access_jwt_token",
                value=f"Bearer {access_jwt_token}",
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=jwt_settings.JWT_ACCESS_TOKEN_EXPIRATION_HOURS * 3600,
            )

            response.set_cookie(
                key="refresh_jwt_token",
                value=f"Bearer {access_jwt_token}",
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=jwt_settings.JWT_REFRESH_TOKEN_EXPIRATION_DAYS * 3600 * 24,
            )

            return response
        else:
            return RedirectResponse(
                f"https://{base_settings.EXTENSION_ID}.chromiumapp.org/callback"
                + f"?access_jwt_token={access_jwt_token}"
                + f"&refresh_jwt_token={refresh_jwt_token}"
            )


async def get_google_auth_service(
    user_service: Annotated[UserService, Depends(get_user_service)],
    google_token_service: Annotated[
        GoogleTokenService, Depends(get_google_token_service)
    ],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GoogleAuthService:
    return GoogleAuthService(
        user_service=user_service,
        google_token_service=google_token_service,
        jwt_service=jwt_service,
        subscription_service=subscription_service,
        db=db
    )
