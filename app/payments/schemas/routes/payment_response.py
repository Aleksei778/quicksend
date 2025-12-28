from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from payments.enum.currency import Currency
from payments.enum.payment_status import PaymentStatus


class PaymentResponse(BaseModel):
    payment_id: int
    external_payment_id: str
    amount: Decimal
    currency: Currency
    status: PaymentStatus
    confirmation_url: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None
    payment_method: Optional[str] = None
