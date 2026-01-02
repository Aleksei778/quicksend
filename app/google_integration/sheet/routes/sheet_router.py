from typing import Annotated
from fastapi import HTTPException, Depends, routing

from google_integration.auth.services.google_token_service import GoogleTokenService
from google_integration.sheet.schemas.sheet_request import SheetRequest
from google_integration.sheet.services.google_sheets_service import GoogleSheetsService
from users.dependencies.get_current_user import get_current_user
from users.models.user import User


google_sheets_router = routing.APIRouter(prefix="/sheets", tags=["sheets"])


@google_sheets_router.post("/parse")
async def parse_emails_from_spreadsheet(
    request: SheetRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    google_token_service: Annotated[GoogleTokenService, Depends()],
    google_sheets_service: Annotated[GoogleSheetsService, Depends()],
):
    google_token = await google_token_service.get_google_token_for_user(user=current_user)

    return await google_sheets_service.parse_emails_from_spreadsheet(
        spreadsheet_id=request.spreadsheet_id,
        range=request.range,
        google_token=google_token,
    )


@google_sheets_router.get("/{spreadsheet_id}/metadata")
async def get_sheet_metadata(spreadsheet_id: str):
    try:
        sheets_service = get_sheets_service()
        spreadsheet = (
            sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        )

        sheets = spreadsheet.get("sheets", [])
        sheet_names = [
            {
                "title": sheet["properties"]["title"],
                "sheetId": sheet["properties"]["sheetId"],
            }
            for sheet in sheets
        ]

        return {
            "spreadsheetName": spreadsheet["properties"]["title"],
            "sheets": sheet_names,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
