from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Dict


class PaymentStatus(BaseModel):
    payment_id: str
    status: str
    paid_at: Optional[datetime]
    payment_method: Optional[str]
    metadata: Dict[str, Any]
