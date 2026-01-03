from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse

from payments.schemas.models.create_payment import CreatePayment
from payments.schemas.routes.create_payment_request import CreatePaymentRequest
from payments.services.payment_service import PaymentService, get_payment_service
from payments.services.provider_factory import (
    PaymentProviderFactory,
    get_payment_provider_factory,
)
from payments.config.payment_config import payment_settings
from subscriptions.enum.plan import SubscriptionPlan
from subscriptions.services.subscription_service import (
    SubscriptionService,
    get_subscription_service,
)
from users.dependencies.get_current_user import get_current_user
from users.models.user import User


subscription_router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@subscription_router.post(path="/subscribe")
async def start_base_premium_subscription(
    request: CreatePaymentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    payment_provider_factory: Annotated[
        PaymentProviderFactory, Depends(get_payment_provider_factory)
    ],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
    subscription_service: Annotated[
        SubscriptionService, Depends(get_subscription_service)
    ],
) -> JSONResponse:
    if request.plan == SubscriptionPlan.TRIAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trial plan is another route",
        )

    subscription = await subscription_service.get_user_active_subscription(current_user)

    if subscription:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Already subscribed",
        )

    payment_provider_service = payment_provider_factory.create(request.payment_provider)

    payment_result = await payment_provider_service.create_payment(
        amount=request.amount,
        currency=request.currency,
        description=request.description,
        return_url=payment_settings.PAYMENT_RETURN_URL,
        metadata=request.metadata,
    )

    subscription = await subscription_service.create_subscription(
        user=current_user,
        plan=request.plan,
        end_at=datetime.utcnow() + timedelta(days=request.plan.get_days_count()),
    )

    payment = await payment_service.create_payment(
        CreatePayment(
            user=current_user,
            subscription=subscription,
            external_payment_id=payment_result.payment_id,
            provider=request.payment_provider,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            payment_method=payment_result.payment_method,
            metadata=payment_result.metadata,
        )
    )

    await subscription_service.set_last_payment_for_subscription(subscription, payment)

    return JSONResponse(
        content={
            "subscription": subscription,
            "payment": payment,
            "provider_payment_result": payment_result,
        },
        status_code=status.HTTP_201_CREATED,
    )


@subscription_router.post(path="/trial")
async def start_trial_subscription(
    current_user: Annotated[User, Depends(get_current_user)],
    subscription_service: Annotated[
        SubscriptionService, Depends(get_subscription_service)
    ],
) -> JSONResponse:
    if subscription_service.is_user_already_used_trial(user=current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Already used your trial"
        )

    subscription = await subscription_service.create_subscription(
        user=current_user,
        plan=SubscriptionPlan.TRIAL,
        end_at=datetime.utcnow()
        + timedelta(days=SubscriptionPlan.TRIAL.get_days_count()),
    )

    return JSONResponse(
        content={
            "subscription": subscription,
        },
        status_code=status.HTTP_201_CREATED,
    )
