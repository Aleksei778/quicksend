from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Annotated

from users.dependencies.get_current_user import get_current_user
from users.models.user import User
from users.services.jwt_service import JwtService, get_jwt_service

jwt_router = APIRouter(prefix="/auth/jwt", tags=["auth_jwt"])


@jwt_router.get("/token")
async def get_jwt(
    request: Request, jwt_service: Annotated[JwtService, Depends(get_jwt_service)]
):
    access_token = request.cookies.get("access_token")

    token = await jwt_service.extract_token(access_token)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token format"
        )

    payload = await jwt_service.verify_access_token(token)

    user_info = payload.get("user_info")
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token data"
        )

    user_id = user_info.get("id")
    user_email = user_info.get("email")

    if not user_id or not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user data in token",
        )

    return JSONResponse(
        content={"access_token": token, "token_type": "bearer", "user_info": user_info}
    )


@jwt_router.post("/refresh")
async def refresh_token(
    request: Request,
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    current_user: User = Depends(get_current_user),
):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found"
        )

    try:
        token_type, token = refresh_token.split()
        if token_type.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token format"
        )

    try:
        token_data = await jwt_service.refresh_token(token)

        response = JSONResponse(
            content={
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "token_type": token_data["token_type"],
            }
        )

        await jwt_service.set_tokens_cookie(
            response=response,
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
        )

        return response

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
        )


@jwt_router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    response = JSONResponse(content={"message": "Successfully logged out"})

    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return response
