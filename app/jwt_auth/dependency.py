from typing import Annotated
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from app.jwt_auth.service import JwtService, get_jwt_service
from common.users.service import UserService, get_user_service
from common.utils.security import security
from common.utils.logger import logger
from common.users.model import User


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
) -> User:
    access_token: str | None = None

    if credentials and credentials.scheme.lower() == "bearer":
        access_token = credentials.credentials

    if not access_token:
        access_token = request.cookies.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = await jwt_service.verify_access_token(token=access_token)
        logger.info(payload)

        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user id provided",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await user_service.find_by_id(user_id=user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except Exception as e:
        logger.error(f"get_current_user: Some problems while extracting user: {e}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_for_refresh(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
) -> tuple[User, str]:
    refresh_token: str | None = None

    if credentials and credentials.scheme.lower() == "bearer":
        refresh_token = credentials.credentials

    if not refresh_token:
        refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = await jwt_service.verify_refresh_token(token=refresh_token)
        user_id = payload.get("user_id")

        logger.info(payload)

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user id provided",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await user_service.find_by_id(user_id=user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user, refresh_token

    except Exception as e:
        logger.error(f"get_current_user: Some problems while extracting user: {e}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
