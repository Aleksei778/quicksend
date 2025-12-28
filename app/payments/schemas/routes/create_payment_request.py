from decimal import Decimal
from typing import Optional
from pydantic import Field

from payments.enum.currency import Currency


class CreatePaymentRequest:
    amount: Decimal = Field(..., gt=0, description="Amount to be paid")
    currency: Currency = Field(default=Currency.RUB)
    description: str = Field(..., max_length=255)
    metadata: Optional[dict] = None
