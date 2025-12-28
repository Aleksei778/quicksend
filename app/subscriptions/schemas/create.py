from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    user_id: int
    type: str
    started_at: datetime
    end_at: datetime
    price: Decimal
