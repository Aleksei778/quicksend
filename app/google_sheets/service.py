import asyncio
from typing import Any
from fastapi import HTTPException
from googleapiclient.discovery import build
from starlette import status

from common.google.token.model import GoogleToken
from common.google.token.credentials import create_credentials


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
    ) -> list[str]:
        try:
            sheets_service = await self.get_google_sheets_service(google_token)

            result = await asyncio.to_thread(
                lambda: sheets_service
                    .spreadsheets()
                    .values()
                    .get(
                        spreadsheetId=spreadsheet_id,
                        range=range
                    )
                    .execute()
            )

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

            return list(dict.fromkeys(emails))
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Some problems while processing spreadsheet {spreadsheet_id}: {str(e)}",
            )


async def get_google_sheets_service() -> GoogleSheetsService:
    return GoogleSheetsService()
