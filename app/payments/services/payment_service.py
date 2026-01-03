from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.database import get_db
from payments.models.payment import Payment
from payments.schemas.models.create_payment import CreatePayment


class PaymentService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_payment(self, create_payment: CreatePayment) -> Payment:
        payment = Payment(
            user_id=create_payment.user.id,
            subscription_id=create_payment.subscription.id,
            amount=create_payment.amount,
            currency=create_payment.currency,
            external_payment_id=create_payment.external_payment_id,
            provider=create_payment.provider,
            description=create_payment.description,
            payment_method=create_payment.payment_method,
            payment_metadata=create_payment.metadata,
        )

        self._db.add(payment)
        await self._db.commit()
        await self._db.refresh(payment)

        return payment


async def get_payment_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentService:
    return PaymentService(db=db)
