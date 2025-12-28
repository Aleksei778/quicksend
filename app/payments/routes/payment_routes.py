from fastapi import APIRouter, Depends, HTTPException, status

from payments.schema.routes.create_payment_request import CreatePaymentRequest
from payments.schema.routes.payment_response import PaymentResponse


router = APIRouter(prefix="/payments", tags=["payments"])

@router.post(
    path="/create",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_payment(
    request: CreatePaymentRequest,
    current_user:
)