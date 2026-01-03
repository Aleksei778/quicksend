from typing import Annotated
from fastapi import HTTPException, Depends, routing
from starlette import status

from google_integration.auth.services.google_auth_service import (
    GoogleAuthService,
    get_google_auth_service,
)
from google_integration.auth.services.google_token_service import (
    GoogleTokenService,
    get_google_token_service,
)
from google_integration.sheet.schemas.sheet_request import SheetRequest
from google_integration.sheet.services.google_sheets_service import (
    GoogleSheetsService,
    get_google_sheets_service,
)
from users.dependencies.get_current_user import get_current_user
from users.models.user import User


google_sheets_router = routing.APIRouter(prefix="/sheets", tags=["sheets"])


@google_sheets_router.post("/parse")
async def parse_emails_from_spreadsheet(
    request: SheetRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    google_token_service: Annotated[
        GoogleTokenService, Depends(get_google_token_service)
    ],
    google_sheets_service: Annotated[
        GoogleSheetsService, Depends(get_google_sheets_service)
    ],
    google_auth_service: Annotated[GoogleAuthService, Depends(get_google_auth_service)],
):
    google_token = await google_token_service.get_google_token_for_user(
        user=current_user
    )

    if not google_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google token not found for user {current_user}",
        )

    if google_token.is_expired:
        await google_auth_service.refresh_google_token(google_token)

    return await google_sheets_service.parse_emails_from_spreadsheet(
        spreadsheet_id=request.spreadsheet_id,
        range=request.range,
        google_token=google_token,
    )


@google_sheets_router.get("/{spreadsheet_id}/metadata")
async def get_sheet_metadata(
    spreadsheet_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    google_token_service: Annotated[
        GoogleTokenService, Depends(get_google_token_service)
    ],
    google_sheets_service: Annotated[
        GoogleSheetsService, Depends(get_google_sheets_service)
    ],
    google_auth_service: Annotated[GoogleAuthService, Depends(get_google_auth_service)],
):
    current_user = User()

    google_token = await google_token_service.get_google_token_for_user(
        user=current_user
    )

    if google_token.is_expired:
        await google_auth_service.refresh_google_token(google_token)

    if not google_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google token not found for user {current_user}",
        )

    return await google_sheets_service.get_spreadsheet_metadata(
        spreadsheet_id=spreadsheet_id,
        google_token=google_token,
    )
