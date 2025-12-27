from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from decimal import Decimal

from payment.enum.currency import Currency
from payment.schema.payment_status import PaymentStatus
from payment.schema.payment_result import PaymentResult


class PaymentGateway(ABC):
    @abstractmethod
    async def create_payment(
        self,
        amount: Decimal,
        currency: Currency,
        description: str,
        return_url: str,
        metadata: Dict[str, Any] = None,
    ) -> PaymentResult:
        pass

    @abstractmethod
    async def get_payment_status(
        self,
        payment_id: str
    ) -> PaymentStatus:
        pass

    @abstractmethod
    async def cancel_payment(self, payment_id: str) -> bool:
        pass

    @abstractmethod
    async def create_refund(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        currency: Currency = None,
    ) -> RefundResult:
        pass

    @abstractmethod
    async def verify_webhook(self, data: Dict[str, Any]) -> PaymentStatus:
        pass

    @abstractmethod
    async def create_recurring_payment(
        self,
        payment_token: str,
        amount: Decimal,
        currency: Currency,
        description: str,
        metadata: Dict[str, Any] = None,
    ) -> PaymentResult:
        pass
