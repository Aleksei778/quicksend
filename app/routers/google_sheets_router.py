from fastapi import routing, Depends

from app.schemas.google_sheets import ParseEmailsRequest, ParseEmailsResponse
from dependencies.get_current_user import get_current_user
from models.user import User


sheets_router = routing.APIRouter(prefix="/sheets", tags=["sheets"])

@sheets_router.post("/parse/emails", response_model=ParseEmailsResponse)
async def parse_emails_from_google_sheets(
    request: ParseEmailsRequest,
    current_user: User = Depends(get_current_user),
) -> ParseEmailsResponse: