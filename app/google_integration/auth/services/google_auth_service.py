from datetime import datetime, timedelta
from typing import Annotated
import httpx
from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from common.db.database import get_db
from common.log.logger import logger
from google_integration.auth.models.google_token import GoogleToken
from google_integration.auth.services.google_token_service import (
    GoogleTokenService,
    get_google_token_service,
)
from google_integration.calendar.services.calendar_service import (
    GoogleCalendarService,
    get_google_calendar_service,
)
from users.schemas.find_or_create_user import FindOrCreateUser
from google_integration.auth.schemas.find_or_create_google_token import (
    FindOrCreateGoogleToken,
)
from users.services.jwt_service import JwtService, get_jwt_service
from users.services.user_service import UserService, get_user_service
from common.config.base_config import base_settings
from google_integration.config.google_config import google_settings


class GoogleAuthService:
    def __init__(
        self,
        user_service: UserService,
        google_token_service: GoogleTokenService,
        google_calendar_service: GoogleCalendarService,
        jwt_service: JwtService,
        db: AsyncSession,
    ) -> None:
        self._db = db
        self._user_service = user_service
        self._google_token_service = google_token_service
        self._jwt_service = jwt_service
        self._google_calendar_service = google_calendar_service
        self._client_config = {
            "web": {
                "client_id": google_settings.GOOGLE_CLIENT_ID,
                "client_secret": google_settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [
                    f"{base_settings.BACKEND_URL}/api/auth/google/callback"
                ],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

    async def _create_flow(self) -> Flow:
        return Flow.from_client_config(
            client_config=self._client_config,
            scopes=google_settings.GOOGLE_AUTH_SCOPES,
            redirect_uris=[f"{base_settings.BACKEND_URL}/"],
        )

    async def _check_state(self, request: Request) -> None:
        state = request.session.get("state")

        if not state or state != request.query_params.get("state"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid state parameter",
            )

    async def login(self, request: Request) -> RedirectResponse:
        flow = await self._create_flow()

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
        )

        request.session["state"] = state

        return RedirectResponse(authorization_url)

    async def callback(self, request: Request):
        await self._check_state(request)

        flow = await self._create_flow()
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

        google_token = await self._google_token_service.find_or_create_google_token(
            FindOrCreateGoogleToken(
                user=user,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_type="Bearer",
                expires_in=None,
                expires_at=credentials.expiry,
                scope=" ".join(credentials.scopes) if credentials.scopes else None,
            )
        )

        timezone = await self._google_calendar_service.get_user_timezone(google_token)
        await self._user_service.set_timezone_for_user(user, str(timezone))

        user_data_for_jwt = await self._user_service.get_user_info_for_jwt(user)

        (
            access_jwt_token,
            refresh_jwt_token,
        ) = await self._jwt_service.create_jwt_pair_from_data(user_data_for_jwt)

        return await self._get_redirect_response_and_set_cookie(
            access_jwt_token, refresh_jwt_token
        )

    async def _get_redirect_response_and_set_cookie(
        self,
        access_jwt_token: str,
        refresh_jwt_token: str,
    ) -> RedirectResponse:
        response = RedirectResponse("/")

        response.headers["Authorization"] = f"Bearer {access_jwt_token}"

        await self._jwt_service.set_tokens_cookie(
            response=response,
            access_token=access_jwt_token,
            refresh_token=refresh_jwt_token,
        )

        return response

    async def refresh_google_token(self, google_token: GoogleToken) -> str:
        if not google_token or not google_token.refresh_token:
            raise Exception(
                "google_token_service:refresh_google_token: Google refresh token is missing"
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": google_token.refresh_token,
                        "client_id": google_settings.GOOGLE_CLIENT_ID,
                        "client_secret": google_settings.GOOGLE_CLIENT_SECRET,
                    },
                )
                response.raise_for_status()
                new_token_data = response.json()

            stmt = (
                update(GoogleToken)
                .where(GoogleToken.id == google_token.id)
                .values(
                    access_token=new_token_data["access_token"],
                    expires_in=new_token_data["expires_in"],
                    expires_at=datetime.now()
                    + timedelta(seconds=new_token_data["expires_in"]),
                )
            )
            await self._db.execute(stmt)
            await self._db.commit()

            return new_token_data["access_token"]

        except httpx.HTTPError as e:
            await self._db.rollback()

            raise Exception(
                f"google_auth_service:refresh_google_token: Failed to refresh token: {str(e)}"
            )
        except Exception as e:
            await self._db.rollback()

            raise Exception(
                f"google_auth_service:refresh_google_token: Unexpected error while refreshing token: {str(e)}"
            )


async def get_google_auth_service(
    user_service: Annotated[UserService, Depends(get_user_service)],
    google_token_service: Annotated[
        GoogleTokenService, Depends(get_google_token_service)
    ],
    google_calendar_service: Annotated[
        GoogleCalendarService, Depends(get_google_calendar_service)
    ],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GoogleAuthService:
    return GoogleAuthService(
        user_service=user_service,
        google_token_service=google_token_service,
        google_calendar_service=google_calendar_service,
        jwt_service=jwt_service,
        db=db,
    )
