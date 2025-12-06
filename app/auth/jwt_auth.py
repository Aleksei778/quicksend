from datetime import timedelta, datetime
from jose import jwt, JWTError
from fastapi import HTTPException
from typing import Dict, Any
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_manager import DBManager
from config import (
    JWT_ACCESS_SECRET_FOR_AUTH,
    JWT_ALGORITHM,
    JWT_REFRESH_SECRET_FOR_AUTH,
    JWT,
)


class TokenError(Exception):
    pass


class JWTHandler:
    def __init__(self):
        self.access_secret = JWT_ACCESS_SECRET_FOR_AUTH
        self.refresh_secret = JWT_REFRESH_SECRET_FOR_AUTH
        self.algorithm = JWT_ALGORITHM

    async def create_access_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})

        try:
            encoded_jwt = jwt.encode(
                to_encode, self.access_secret, algorithm=self.algorithm
            )
            return encoded_jwt
        except Exception as e:
            raise TokenError(f"Error creating access token: {str(e)}")

    async def create_refresh_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
        to_encode.update({"exp": expire, "type": "refresh"})

        try:
            encoded_jwt = jwt.encode(
                to_encode, self.refresh_secret, algorithm=self.algorithm
            )
            return encoded_jwt
        except Exception as e:
            raise TokenError(f"Error creating refresh token: {str(e)}")

    async def verify_token(
        self, token: str, token_type: str = "access"
    ) -> Dict[str, Any]:
        try:
            secret = (
                self.access_secret if token_type == "access" else self.refresh_secret
            )

            payload = jwt.decode(token, secret, algorithms=[self.algorithm])

            if payload.get("type") != token_type:
                raise TokenError("Invalid token type")

            exp = payload.get("exp")
            if not exp or datetime.fromtimestamp(exp) < datetime.utcnow():
                raise TokenError("Token has expired")

            return payload

        except JWTError as jwt_e:
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(jwt_e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
            raise credentials_exception

        except TokenError as token_e:
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(token_e),
                headers={"WWW-Authenticate": "Bearer"},
            )
            raise credentials_exception

    async def refresh_token(
        self, refresh_token: str, db: AsyncSession
    ) -> Dict[str, str]:
        try:
            db_manager = DBManager(session=db)

            payload = await self.verify_token(refresh_token, "refresh")
            user_data = payload.get("user_info")

            if not user_data:
                raise TokenError("Invalid token data")
            print(user_data)

            # Проверяем пользователя в БД
            user = await db_manager.get_user_by_email(user_data["email"])
            print(user.id)

            if not user:
                print("not user")
                raise TokenError("User not found")
                # Создаем новую информацию для токенов
                active_sub = await db_manager.get_active_sub(user
            user_id = user.id
            user_name = user.first_name + " " + user.last_name
            user_email = user.email

         _id=user_id)

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

            # Создаем новую пару токенов
            new_access_token = await self.create_access_token(new_data)
            new_refresh_token = await self.create_refresh_token(new_data)

            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "Bearer",
            }

        except TokenError as e:
            print(str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            print(str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error refreshing token: {str(e)}",
            )


jwt_handler = JWTHandler()


async def create_access_token(data: Dict[str, Any]) -> str:
    return await jwt_handler.create_access_token(data)


async def create_refresh_token(data: Dict[str, Any]) -> str:
    return await jwt_handler.create_refresh_token(data)


async def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    return await jwt_handler.verify_token(token, token_type)


async def refresh_jwt_token(refresh_token: str, db: AsyncSession) -> Dict[str, str]:
    return await jwt_handler.refresh_token(refresh_token, db)
