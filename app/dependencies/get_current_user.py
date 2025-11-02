from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

from repositories.user import UserRepository
from dependencies.get_db import get_user_repository
from core.security import security


async def get_current_user(
    credentials: HTTPBearer = Depends(security),
    user_repository: UserRepository = Depends(get_user_repository),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="No credentials provided")

    payload = await verify_token(token=credentials)
    user_info = payload.get("user_info")
    user_id = user_info.get("id")

    if not user_id:
        raise HTTPException(
            status_code=401, detail="No authentication information provided"
        )

    user = await user_repository.get_by_id(user_id=user_id)

    return user
