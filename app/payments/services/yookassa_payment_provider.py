from yookassa import Configuration, Payment as YooPayment, Refund
from yookassa.domain.notification import WebhookNotification
from yookassa.domain.response import PaymentResponse as YooPaymentResponse
from decimal import Decimal
from datetime import datetime
import uuid
from typing import Dict, Any, Optional

from payments.schemas.base.payment_result import PaymentResult
from payments.schemas.base.payment_status import PaymentStatus
from payments.schemas.base.refund_result import RefundResult
from payments.services.base_payment_provider import BasePaymentProvider
from payments.enum.currency import Currency
from common.log.logger import logger


class YookassaPaymentProvider(BasePaymentProvider):
    def __init__(self, shop_id: str, secret_key: str):
        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key

    async def create_payment(
        self,
        amount: Decimal,
        currency: Currency,
        description: str,
        return_url: str,
        metadata: Dict[str, Any] = None,
        **kwargs,
    ) -> PaymentResult:
        capture = kwargs.get("capture", True)

        yoo_payment = YooPayment.create(
            {
                "amount": {
                    "value": amount,
                    "currency": currency.value,
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url,
                },
                "capture": capture,
                "metadata": metadata or {},
            },
            str(uuid.uuid4()),
        )

        return PaymentResult(
            payment_id=yoo_payment.id,
            payment_method=yoo_payment.payment_method,
            confirmation_url=yoo_payment.confirmation_url,
            status=yoo_payment.status,
            amount=Decimal(yoo_payment.amount),
            currency=yoo_payment.amount.currency,
            metadata=yoo_payment.metadata,
        )

    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        yoo_payment = YooPayment.find_one(payment_id)

        return await self._get_payment_info(yoo_payment)

    async def cancel_payment(self, payment_id: str) -> bool:
        try:
            yoo_payment = YooPayment.find_one(payment_id)
            YooPayment.cancel(yoo_payment.id, str(uuid.uuid4()))

            return True
        except Exception as e:
            logger.info(f"Failed to cancel payment {payment_id}: {e}")

            return False

    async def create_refund(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        currency: Currency = None,
    ) -> RefundResult:
        if amount is None:
            yoo_payment = YooPayment.find_one(payment_id)
            amount = Decimal(yoo_payment.amount)
            currency = yoo_payment.amount.currency
        else:
            currency = currency.value

        refund = Refund.create(
            {
                "amount": {
                    "value": amount,
                    "currency": currency,
                },
            },
            str(uuid.uuid4()),
        )

        return RefundResult(
            refund_id=refund.id,
            status=refund.status,
            amount=Decimal(refund.amount.value),
        )

    async def verify_webhook(self, data: Dict[str, Any]) -> PaymentStatus:
        notification = WebhookNotification(data)
        yoo_payment = notification.object

        return await self._get_payment_info(yoo_payment)

    async def create_recurring_payment(
        self,
        payment_token: str,
        amount: Decimal,
        currency: Currency,
        description: str,
        metadata: Dict[str, Any] = None,
    ) -> PaymentResult:
        yoo_payment = YooPayment.create(
            {
                "amount": {
                    "value": str(amount),
                    "currency": currency.value,
                },
                "capture": True,
                "payment_method_id": payment_token,
                "description": description,
                "metadata": metadata or {},
            },
            str(uuid.uuid4()),
        )

        return PaymentResult(
            payment_id=yoo_payment.id,
            confirmation_url=None,
            status=await self._map_payment_statuses(yoo_payment.status),
            currency=currency,
            amount=Decimal(yoo_payment.amount),
            metadata=yoo_payment.metadata,
        )

    async def _get_payment_info(self, yoo_payment: YooPaymentResponse) -> PaymentStatus:
        paid_at = None
        if yoo_payment.status == "succeeded" and yoo_payment.captured_at:
            paid_at = datetime.fromisoformat(str(yoo_payment.captured_at))

        payment_method = None
        if yoo_payment.payment_method:
            payment_method = yoo_payment.payment_method

        return PaymentStatus(
            payment_id=yoo_payment.id,
            status=yoo_payment.status,
            payment_method=payment_method,
            paid_at=paid_at,
            metadata=yoo_payment.metadata or {},
        )

    async def _map_payment_statuses(self, yoo_status: str) -> str:
        status_map = {
            "waiting_for_capture": "pending",
            "succeeded": "succeeded",
            "canceled": "canceled",
        }

        return status_map[yoo_status]
