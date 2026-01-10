from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, status
from starlette.responses import JSONResponse

from app.google_sheets.schema import SheetRequest
from app.google_sheets.service import GoogleSheetsService, get_google_sheets_service
from app.jwt_auth.dependency import get_current_user
from common.google.token.service import GoogleTokenService, get_google_token_service
from common.users.model import User
from common.utils.logger import logger


router = APIRouter(prefix="/googlesheet", tags=["sheets"])


@router.post("/parse", response_model=None)
async def parse_emails_from_spreadsheet(
    request: SheetRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    google_token_service: Annotated[
        GoogleTokenService, Depends(get_google_token_service)
    ],
    google_sheets_service: Annotated[
        GoogleSheetsService, Depends(get_google_sheets_service)
    ],
) -> JSONResponse | None:
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No current user",
            )

        google_token = await google_token_service.find_google_token_by_user(current_user)

        if not google_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Google token not found for user {current_user}",
            )

        if google_token.is_expired:
            await google_token_service.refresh_google_token(google_token)

        emails = await google_sheets_service.parse_emails_from_spreadsheet(
            spreadsheet_id=request.spreadsheet_id,
            range=request.range,
            google_token=google_token,
        )
        logger.info(f'Parsed emails: {emails}')

        return JSONResponse({
            "emails": emails,
        })

    except Exception as e:
        logger.info(e)
