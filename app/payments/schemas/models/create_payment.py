from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

from payments.enum.currency import Currency as CurrencyEnum
from payments.enum.provider import PaymentProvider as PaymentProviderEnum
from subscriptions.models.subscription import Subscription
from users.models.user import User


class CreatePayment(BaseModel):
    user: User
    subscription: Subscription
    external_payment_id: str
    provider: PaymentProviderEnum
    amount: Decimal
    currency: CurrencyEnum
    description: str
    payment_method: Optional[str] = None
    metadata: Optional[dict] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
