from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from common.logger import logger
from google_integration.auth.services.google_token_service import GoogleTokenService
from subscriptions.services.subscription_service import SubscriptionService
from users.schemas.find_or_create_user import FindOrCreateUser
from google_integration.auth.schemas.find_or_create_google_token import FindOrCreateGoogleToken
from users.services.user_service import UserService
from common.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URL,
    GOOGLE_AUTH_SCOPES,
)


class GoogleAuthService:
    def __init__(
        self,
        db: AsyncSession = Depends(AsyncSession),
        user_service: UserService = Depends(UserService),
        subscription_service: SubscriptionService = Depends(SubscriptionService),
        google_token_service: GoogleTokenService = Depends(GoogleTokenService),
    ) -> None:
        self.db = db
        self.user_service = user_service
        self.subscription_service = subscription_service
        self.google_token_service = google_token_service
        self.client_config = {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [GOOGLE_REDIRECT_URL],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

    async def _create_flow(self) -> Flow:
        return Flow.from_client_config(
            client_config=self.client_config,
            scopes=GOOGLE_AUTH_SCOPES.split(),
            redirect_uris=GOOGLE_REDIRECT_URL,
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

    async def callback(self,request: Request):
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

        (logger
         .bind(user_info=user_info)
         .debug("User info retrieved"))

        user = await self.user_service.find_or_create_user(FindOrCreateUser(
            email=user_info.get("email"),
            first_name=user_info.get("given_name"),
            last_name=user_info.get("family_name"),
            picture=user_info.get("picture"),
            oauth_id=user_info.get("id"),
        ))

        await self.google_token_service.create_or_update_token(FindOrCreateGoogleToken(
            user=user,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_type="Bearer",
            expires_in=None,
            expires_at=credentials.expiry,
            scope=" ".join(credentials.scopes) if credentials.scopes else None,
        ))



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
