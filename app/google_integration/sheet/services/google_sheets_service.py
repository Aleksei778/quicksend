from typing import Any
from fastapi import HTTPException
from googleapiclient.discovery import build
from starlette import status

from google_integration.auth.models.google_token import GoogleToken
from google_integration.auth.utils.credentials import create_credentials


class GoogleSheetsService:
    async def get_google_sheets_service(self, google_token: GoogleToken) -> Any:
        credentials = await create_credentials(
            google_token=google_token,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )

        return build(
            serviceName="sheets",
            version="v4",
            credentials=credentials,
        )

    async def parse_emails_from_spreadsheet(
        self,
        spreadsheet_id: str,
        range: str,
        google_token: GoogleToken,
    ) -> set[str]:
        try:
            sheets_service = await self.get_google_sheets_service(google_token)
            spreadsheet_base = await sheets_service.spreadsheets().values()

            spreadsheet = spreadsheet_base.get(spreadsheetId=spreadsheet_id).execute()

            if not spreadsheet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No such spreadsheet found {spreadsheet_id}",
                )

            result = spreadsheet_base.get(
                spreadsheetId=spreadsheet_id, range=range
            ).execute()

            values = result.get("values", [])

            if not values:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No data for spreadsheet {spreadsheet_id}",
                )

            emails = [item[0] for item in values if item and "@" in item[0]]

            if not emails:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No valid emails found in spreadsheet {spreadsheet_id}",
                )

            return set(emails)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Some problems while processing spreadsheet {spreadsheet_id}: {str(e)}",
            )

    async def get_spreadsheet_metadata(
        self,
        spreadsheet_id: str,
        google_token: GoogleToken,
    ) -> dict[str, Any]:
        try:
            sheets_service = await self.get_google_sheets_service(google_token)
            spreadsheet_base = await sheets_service.spreadsheets()

            spreadsheet = spreadsheet_base.get(spreadsheetId=spreadsheet_id).execute()

            sheets = spreadsheet.get("sheets", [])

            if len(sheets) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No sheets found for spreadsheet {spreadsheet_id}",
                )

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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Some problems while processing spreadsheet {spreadsheet_id}: {str(e)}",
            )


async def get_google_sheets_service() -> GoogleSheetsService:
    return GoogleSheetsService()
