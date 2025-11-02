from fastapi import HTTPException, Depends, routing
from sqlalchemy.ext.asyncio import AsyncSession

from google_token_file import get_sheets_service
from database.models import User
from schemas.google_sheets import EmailList, SheetRequest


class GoogleSheetsService:
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db

    async def get_sheets_google_service(user: UserOrm):
        stmt = select(TokenOrm).where(TokenOrm.user_id == user.id)
        result = await self.db.execute(stmt)
        token = result.scalar_one_or_none()

        if not token:
            raise HTTPException(status_code=404, detail="Token not found")

        if is_token_expired(token):
            await refresh_access_token(token, db)

        creds = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri="https://accounts.google.com/o/oauth2/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )

        return build("sheets", "v4", credentials=creds)

    async def get_emails_from_spreadsheet(
        spreadsheet_id: str,
        range: str,
        current_user: User,
    ):
        try:
            sheets_service = await get_sheets_service(current_user)

            spreadsheet = (
                sheets_service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id)
                .execute()
            )

            if not spreadsheet:
                raise HTTPException(status_code=404, detail="No such spreadsheet")

            spreadsheet_name = spreadsheet.get("properties", {}).get("title", "")

            result = (
                sheets_service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range)
                .execute()
            )

            values = result.get("values", [])

            if not values:
                raise HTTPException(status_code=404, detail="No data found")

            emails = [item[0] for item in values if item and "@" in item[0]]

            email_list = EmailList(emails=emails, spreadsheet_name=spreadsheet_name)
            email_list.remove_dups()

            return email_list
        except Exception as e:
            print(str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def get_spreadsheet_metadata(spreadsheet_id: str):
        try:
            sheets_service = await self.get_sheets_google_service(spreadsheet_id)
            spreadsheet = (
                sheets_service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id)
                .execute()
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
