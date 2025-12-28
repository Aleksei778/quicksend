from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.starlette_client import OAuth
from datetime import datetime

from common.database import get_db
from common.database import DBManager
from auth.dependencies import get_current_user
from auth.jwt_auth import (
    create_access_token,
    verify_token,
    refresh_jwt_token,
    create_refresh_token,
)
from google_token_file import refresh_access_token, is_token_expired
from common.config import BASE_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

auth_router = APIRouter()

oauth = OAuth()
CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    access_token_url="https://accounts.google.com/o/oauth2/token",
    access_token_params=None,
    client_kwargs={
        "scope": "email profile https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/spreadsheets.readonly",
        "redirect_uri": f"{BASE_URL}/api/v1/oauth2callback",
    },
    server_metadata_url=CONF_URL,
)


@auth_router.get("/login")
async def login(request: Request):
    google = oauth.create_client("google")
    redirect_uri = request.url_for("oauth2callback")
    return await google.authorize_redirect(
        request, redirect_uri, access_type="offline", prompt="consent"
    )


@auth_router.get("/oauth2callback", name="oauth2callback")
async def auth(request: Request, db: AsyncSession = Depends(get_db)):
    google = oauth.create_client("google")
    token_data = await google.authorize_access_token(request)

    if not token_data:
        return RedirectResponse(url="/error")

    db_manager = DBManager(session=db)

    resp = await google.get(
        "https://www.googleapis.com/oauth2/v2/userinfo", token=token_data
    )
    user_info = resp.json()

    print(user_info)

    if not user_info or "error" in user_info:
        return RedirectResponse(url="/error")

    user = await db_manager.get_user_by_email(user_info["email"])

    if not user:
        user = await db_manager.create_user(
            email=user_info["email"],
            first_name=user_info["first_name"],
            last_name=user_info["last_name"],
            picture=user_info["picture"],
        )

    user_id = user.id
    user_name = user.first_name + " " + user.last_name
    user_email = user.email
    user_picture = user.picture

    active_sub = await db_manager.get_active_sub(user_id=user_id)

    active_sub_dict = {"plan": "No active sub"}

    if active_sub:
        active_sub_dict["plan"] = active_sub.plan

    oauth_token = await db_manager.get_token(user.id)

    if not oauth_token:
        await db_manager.create_token(
            user_id=user.id,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            expires_at=datetime.fromtimestamp(token_data["expires_at"]),
            scope=token_data["scope"],
        )
    else:
        oauth_token.access_token = token_data["access_token"]
        oauth_token.refresh_token = token_data.get(
            "refresh_token", oauth_token.refresh_token
        )
        oauth_token.expires_in = token_data["expires_in"]
        oauth_token.expires_at = datetime.fromtimestamp(token_data["expires_at"])
        oauth_token.scope = token_data["scope"]

        await db.commit()

    data = {
        "user_info": {"id": user_id, "name": user_name, "email": user_email},
        "subscription_info": {**active_sub_dict},
    }

    access_jwt_token = await create_access_token(data=data)
    refresh_jwt_token = await create_refresh_token(data=data)

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


@auth_router.get("/get_jwt")
async def get_jwt(request: Request, db: AsyncSession = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="token not found")

    try:
        token_type, token = access_token.split()
        if token_type.lower() != "bearer":
            raise HTTPException(status_code=401, detail="The wrong type of token")
    except ValueError:
        raise HTTPException(status_code=401, detail="The wrong format of token")

    payload = await verify_token(token)
    print(payload)

    user_info = payload.get("user_info")

    user_id = user_info.get("id")
    user_email = user_info.get("email")

    print(user_id, user_email)

    if not user_id or not user_email:
        raise HTTPException(status_code=401, detail="The wrong data of token")

    return JSONResponse(content={"access_token": token, "token_type": "bearer"})


# --- ОБНОВЛЕНИЕ ТОКЕНА ---
@auth_router.post("/refresh")
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found")

    try:
        token_type, token = refresh_token.split()
        if token_type.lower() != "bearer":
            raise HTTPException(status_code=401, detail="The wrong type of token")
    except ValueError:
        raise HTTPException(status_code=401, detail="The wrong format of token")

    try:
        token_data = await refresh_jwt_token(refresh_token=token, db=db)

        response = JSONResponse(
            {
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
            }
        )
        response.set_cookie(
            key="access_token",
            httponly=True,
            value=f"Bearer {token_data.get('access_token')}",
            secure=True,
            samesite="lax",
        )
        response.set_cookie(
            key="refresh_token",
            httponly=True,
            value=f"Bearer {token_data.get('refresh_token')}",
            secure=True,
            samesite="lax",
        )

        return response

    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")


@auth_router.get("/check_user")
async def read_user_me(current_user=Depends(get_current_user)):
    return {
        "name": f"{current_user.first_name} {current_user.last_name}",
        "email": current_user.email,
        "picture": current_user.picture,
    }


@auth_router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out successfully"}


@auth_router.post("/get_google_token")
async def get_google_token(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    db_manager = DBManager(session=db)

    token = await db_manager.get_token(current_user.id)

    if not token:
        raise HTTPException(status_code=404, detail="Токен не найден.")

    if is_token_expired(token):
        await refresh_access_token(token, db)

    return {"google_access_token": token.access_token}
