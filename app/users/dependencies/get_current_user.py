from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from users.services.user_service import UserService, get_user_service
from common.security.security import security
from common.log.logger import logger
from users.services.jwt_service import JwtService, get_jwt_service
from users.models.user import User


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    user_service: UserService = Depends(get_user_service),
    jwt_service: JwtService = Depends(get_jwt_service),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No credentials provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_str: str = credentials.credentials

    try:
        payload = await jwt_service.verify_access_token(token=token_str)
        user_id = payload.get("user_info", {}).get("id")

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
