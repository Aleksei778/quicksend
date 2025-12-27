from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

from services.user_service import UserService
from utils.security import security
from services.auth.jwt_service import JwtService
from models.user import User


async def get_current_user_from_access(
    user_service: UserService = Depends(UserService),
    jwt_service: JwtService = Depends(JwtService),
    credentials: HTTPBearer = Depends(security),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="No credentials provided")

    payload = await jwt_service.ver(token=credentials)
    user_info = payload.get("user_info")
    user_id = user_info.get("id")

    if not user_id:
        raise HTTPException(
            status_code=401, detail="No authentication information provided"
        )

    user = await user_repository.get_by_id(user_id=user_id)

    return user
