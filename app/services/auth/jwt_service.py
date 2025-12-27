from datetime import datetime, timedelta
import jwt
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from config import (
    JWT_ACCESS_SECRET_FOR_AUTH,
    JWT_REFRESH_SECRET_FOR_AUTH,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRES_MINUTES,
    REFRESH_TOKEN_EXPIRES_DAYS
)
from services.subscription_service import SubscriptionService
from services.user_service import UserService
from logger import logger


class JwtService:
    def __init__(self, user_service: UserService, subscription_service: SubscriptionService):
        self.access_secret = JWT_ACCESS_SECRET_FOR_AUTH
        self.refresh_secret = JWT_REFRESH_SECRET_FOR_AUTH
        self.algorithm = JWT_ALGORITHM

        self.subscription_service = subscription_service
        self.user_service = user_service

    async def create_access_token(self, user_data: Dict[str, Any]) -> str:
        to_encode = user_data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        return jwt.encode(to_encode, self.access_secret, self.algorithm)

    async def create_refresh_token(self, user_data: Dict[str, Any]) -> str:
        to_encode = user_data.copy()
        expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRES_DAYS)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })

        return jwt.encode(to_encode, self.refresh_secret, algorithm=self.algorithm)

    async def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        return await self._verify_token(token, "access", self.access_secret)

    async def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        return await self._verify_token(token, "refresh", self.refresh_secret)

    async def _verify_token(
        self,
        token: str,
        expected_type: str,
        secret: str,
    ) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, secret, algorithms=[self.algorithm])

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
                 detail=f"Invalid token: {str(e)}"
            )

    async def refresh_token(
        self,
        refresh_token: str
    ) -> Dict[str, str]:
        payload = await self.verify_refresh_token(refresh_token)
        user_data = payload.get("user_info")

        if not user_data:
            logger.info(f'No user data {user_data}')

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"No user data"
            )

        user_email = user_data.get("email")
        user = await self.user_service.find_user_by_email(user_email)

        if not user:
            logger.info(f'No user for email {user_email}')

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"No such user: {user_email}"
            )

        active_sub = await self.subscription_service.get_user_active_sub(user)
        user_id = user.id
        user_name = user.first_name + " " + user.last_name
        user_email = user.email

        active_sub_dict = {"plan": "No active sub"}

        if active_sub:
            active_sub_dict["plan"] = active_sub.plan

        new_data = {
            "user_info": {
                "id": user_id,
                "name": user_name,
                "email": user_email,
            },
            "subscription_info": {**active_sub_dict},
        }

        new_access_token = await self.create_access_token(new_data)
        new_refresh_token = await self.create_refresh_token(new_data)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
        }
