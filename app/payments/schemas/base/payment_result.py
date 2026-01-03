from pydantic import BaseModel
from decimal import Decimal
from typing import Optional, Dict, Any

from payments.enum.currency import Currency


class PaymentResult(BaseModel):
    payment_id: str
    confirmation_url: Optional[str]
    status: str
    amount: Decimal
    currency: Currency
    metadata: Dict[str, Any]
    payment_method: str
