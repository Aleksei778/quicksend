from decimal import Decimal
from typing import Optional
from pydantic import Field, BaseModel

from payments.enum.currency import Currency
from payments.enum.provider import PaymentProvider
from subscriptions.enum.plan import SubscriptionPlan


class CreatePaymentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount to be paid")
    currency: Currency = Field(default=Currency.RUB)
    description: str = Field(..., max_length=255)
    payment_provider: PaymentProvider = Field(...)
    plan: SubscriptionPlan = Field(...)
    metadata: Optional[dict] = None
