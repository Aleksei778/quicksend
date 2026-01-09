from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from typing import Annotated

from app.google_integration.auth.enum.source import Source
from app.users.config.jwt_config import jwt_settings
from app.users.models.user import User
from app.users.dependencies.get_current_user import get_current_user, get_current_user_for_refresh
from app.users.services.jwt_service import JwtService, get_jwt_service

jwt_router = APIRouter(prefix="/auth/jwt", tags=["auth_jwt"])


@jwt_router.post("/refresh", response_model=None)
async def refresh_token(
    source: Source,
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    user_and_token: Annotated[tuple[User, str], Depends(get_current_user_for_refresh)],
) -> Response | JSONResponse:
    try:
        _, refresh_token = user_and_token

        token_data = await jwt_service.refresh_jwt_token(refresh_token)
        new_access_token, new_refresh_token = token_data

        if source == Source.Website:
            response = Response()

            response.set_cookie(
                key="access_jwt_token",
                value=f"Bearer {new_access_token}",
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=jwt_settings.JWT_ACCESS_TOKEN_EXPIRATION_HOURS * 3600,
            )

            response.set_cookie(
                key="refresh_jwt_token",
                value=f"Bearer {new_refresh_token}",
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=jwt_settings.JWT_REFRESH_TOKEN_EXPIRATION_DAYS * 3600 * 24,
            )
        else:
            response = JSONResponse({
                "access_jwt_token": new_access_token,
                "refresh_jwt_token": new_refresh_token,
            })

        return response

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
        )


@jwt_router.post("/logout", response_model=None)
async def logout(_: User = Depends(get_current_user)) -> JSONResponse:
    response = JSONResponse(content={"message": "Successfully logged out"})

    response.delete_cookie(key="access_jwt_token")
    response.delete_cookie(key="refresh_jwt_token")

    return response
