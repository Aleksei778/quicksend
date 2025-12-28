from pydantic import BaseModel
from typing import List
from fastapi import HTTPException, Depends, routing
from sqlalchemy.ext.asyncio import AsyncSession
from collections import OrderedDict


sheet_router = routing.APIRouter()


@sheets_router.post("/get-emails", response_model=EmailList)
async def get_emails(
    request: SheetRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        print(request.spreadsheet_id, request.range)
        sheets_service = await get_sheets_service(current_user, db)
        print("НЕТ ОШИБКИ")
        # Получаем информацию о таблице
        spreadsheet = (
            sheets_service.spreadsheets()
            .get(spreadsheetId=request.spreadsheet_id)
            .execute()
        )

        if not spreadsheet:
            raise HTTPException(status_code=404, detail="No such spreadsheet")

        print("НЕТ ОШИБКИ2")
        spreadsheet_name = spreadsheet.get("properties", {}).get("title", "")
        print("НЕТ ОШИБКИ3")

        # Получаем данные из указанного диапазона
        result = (
            sheets_service.spreadsheets()
            .values()
            .get(spreadsheetId=request.spreadsheet_id, range=request.range)
            .execute()
        )
        print("НЕТ ОШИБКИ4")

        values = result.get("values", [])
        if not values:
            raise HTTPException(status_code=404, detail="No data found")

        # Извлекаем email адреса
        emails = [item[0] for item in values if item and "@" in item[0]]

        email_list = EmailList(emails=emails, spreadsheet_name=spreadsheet_name)
        email_list.remove_dups()

        return email_list
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@sheets_router.get("/{spreadsheet_id}/metadata")
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
