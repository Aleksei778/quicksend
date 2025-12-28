from pydantic import BaseModel
from decimal import Decimal


class RefundResult(BaseModel):
    refund_id: str
    status: str
    amount: Decimal
