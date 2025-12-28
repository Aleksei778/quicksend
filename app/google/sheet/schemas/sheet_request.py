from pydantic import BaseModel


class SheetRequest(BaseModel):
    spreadsheet_id: str
    range: str
