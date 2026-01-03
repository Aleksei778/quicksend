from datetime import datetime, timedelta
import jwt
from typing import Dict, Any, Optional, Tuple, Annotated
from fastapi import HTTPException, status, Depends
from fastapi.responses import Response

from users.config.jwt_config import jwt_settings
from subscriptions.services.subscription_service import (
    SubscriptionService,
    get_subscription_service,
)
from users.services.user_service import UserService, get_user_service
from common.log.logger import logger


class JwtService:
    def __init__(
        self,
        user_service: UserService,
        subscription_service: SubscriptionService,
    ) -> None:
        self._access_secret = jwt_settings.JWT_ACCESS_SECRET_FOR_AUTH
        self._refresh_secret = jwt_settings.JWT_REFRESH_SECRET_FOR_AUTH
        self._algorithm = jwt_settings.JWT_ALGORITHM
        self._subscription_service = subscription_service
        self._user_service = user_service

    async def create_access_token(self, user_data: Dict[str, Any]) -> str:
        to_encode = user_data.copy()
        expire = datetime.utcnow() + timedelta(
            minutes=jwt_settings.JWT_ACCESS_TOKEN_EXPIRES_MINUTES
        )
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

        return jwt.encode(to_encode, self._access_secret, algorithm=self._algorithm)

    async def create_refresh_token(self, user_data: Dict[str, Any]) -> str:
        to_encode = user_data.copy()
        expire = datetime.utcnow() + timedelta(
            minutes=jwt_settings.JWT_REFRESH_TOKEN_EXPIRES_DAYS
        )
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})

        return jwt.encode(to_encode, self._refresh_secret, algorithm=self._algorithm)

    async def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        return await self._verify_token(token, "access", self._access_secret)

    async def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        return await self._verify_token(token, "refresh", self._refresh_secret)

    async def _verify_token(
        self,
        token: str,
        expected_type: str,
        secret: str,
    ) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, secret, algorithms=[self._algorithm])

            if payload.get("type") != expected_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {expected_type}",
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Expired token",
            )

        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )

    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        payload = await self.verify_refresh_token(refresh_token)
        user_data = payload.get("user_info")

        if not user_data:
            logger.info(f"No user data {user_data}")

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=f"No user data"
            )

        user_email = user_data.get("email")
        user = await self._user_service.find_by_email(user_email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"No such user: {user_email}",
            )

        new_user_data = await self._user_service.get_user_info_for_jwt(user)
        new_access_token, new_refresh_token = await self.create_jwt_pair_from_data(
            new_user_data
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
        }

    async def create_jwt_pair_from_data(self, data: dict) -> Tuple[str, str]:
        access_jwt_token = await self.create_access_token(user_data=data)
        refresh_jwt_token = await self.create_refresh_token(user_data=data)

        return access_jwt_token, refresh_jwt_token

    async def extract_token(self, token: str | None) -> Optional[str]:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided"
            )

        try:
            token_type, token = token.split(maxsplit=1)
            if token_type.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type"
                )

            return token
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token format"
            )

    async def set_tokens_cookie(
        self, response: Response, access_token: str, refresh_token: str
    ) -> None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=1800,
        )

        response.set_cookie(
            key="refresh_token",
            value=f"Bearer {refresh_token}",
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=604800,
        )


async def get_jwt_service(
    user_service: Annotated[UserService, Depends(get_user_service)],
    subscription_service: Annotated[
        SubscriptionService, Depends(get_subscription_service)
    ],
) -> JwtService:
    return JwtService(
        user_service=user_service,
        subscription_service=subscription_service,
    )
