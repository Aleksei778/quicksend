from pydantic import BaseModel

from typing import Set


class ParseEmailsRequest(BaseModel):
    spreadsheet_id: str
    range: str


class ParseEmailsResponse(BaseModel):
    emails: Set[str]
    spreadsheet_name: str
