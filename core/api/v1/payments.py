"""
Payment API endpoints
"""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ...models.payment import MobileMoneyProvider, PaymentMethod, PaymentStatus
from ...services import PaymentService
from ..dependencies import get_current_user, get_payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


# Request/Response schemas
class CreatePaymentRequest(BaseModel):
    from_account_id: str = Field(..., description="Source account")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="USD", description="Currency")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    destination: str = Field(..., description="Payment destination")
    description: str | None = Field(default=None, description="Description")
    metadata: dict = Field(default_factory=dict, description="Metadata")


class ACHPaymentRequest(BaseModel):
    from_account_id: str = Field(..., description="Source account")
    routing_number: str = Field(..., description="Routing number")
    account_number: str = Field(..., description="Account number")
    amount: Decimal = Field(..., gt=0, description="Amount")
    currency: str = Field(default="USD", description="Currency")
    description: str | None = Field(default=None, description="Description")


class WirePaymentRequest(BaseModel):
    from_account_id: str = Field(..., description="Source account")
    beneficiary_account: str = Field(..., description="Beneficiary account")
    swift_code: str = Field(..., description="SWIFT/BIC code")
    amount: Decimal = Field(..., gt=0, description="Amount")
    currency: str = Field(default="USD", description="Currency")
    description: str | None = Field(default=None, description="Description")


class MobileMoneyPaymentRequest(BaseModel):
    from_account_id: str = Field(..., description="Source account")
    phone_number: str = Field(
        ..., description="Recipient phone number in E.164 format (e.g., +254712345678)"
    )
    provider: MobileMoneyProvider = Field(..., description="Mobile money provider")
    country_code: str = Field(
        ...,
        description="ISO 3166-1 alpha-2 country code (e.g., KE, UG)",
        min_length=2,
        max_length=2,
    )
    amount: Decimal = Field(..., gt=0, description="Amount")
    currency: str = Field(..., description="Currency (e.g., KES, UGX, TZS)")
    description: str | None = Field(default=None, description="Description")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class PaymentResponse(BaseModel):
    id: str
    from_account_id: str
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    destination: str
    status: PaymentStatus
    description: str | None
    reference: str | None


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    request: CreatePaymentRequest,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a new payment"""
    try:
        payment = await service.create_payment(
            from_account_id=request.from_account_id,
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method,
            destination=request.destination,
            description=request.description,
            metadata=request.metadata,
        )
        return payment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}",
        )


@router.post("/ach", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_ach_payment(
    request: ACHPaymentRequest,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create an ACH payment"""
    try:
        payment = await service.process_ach_payment(
            from_account_id=request.from_account_id,
            routing_number=request.routing_number,
            account_number=request.account_number,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
        )
        return payment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ACH payment: {str(e)}",
        )


@router.post("/wire", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_wire_payment(
    request: WirePaymentRequest,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a wire transfer"""
    try:
        payment = await service.process_wire_payment(
            from_account_id=request.from_account_id,
            beneficiary_account=request.beneficiary_account,
            swift_code=request.swift_code,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
        )
        return payment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create wire payment: {str(e)}",
        )


@router.post("/mobile-money", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_mobile_money_payment(
    request: MobileMoneyPaymentRequest,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a mobile money payment"""
    try:
        payment = await service.process_mobile_money_payment(
            from_account_id=request.from_account_id,
            phone_number=request.phone_number,
            provider=request.provider,
            country_code=request.country_code,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            metadata=request.metadata,
        )
        return payment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create mobile money payment: {str(e)}",
        )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get payment by ID"""
    try:
        payment = await service.get_payment(payment_id)
        return payment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment: {str(e)}",
        )


@router.get("/account/{account_id}", response_model=list[PaymentResponse])
async def list_account_payments(
    account_id: str,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List payments for an account"""
    try:
        payments = await service.list_account_payments(
            account_id=account_id,
            limit=limit,
            offset=offset,
        )
        return payments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list payments: {str(e)}",
        )


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
async def cancel_payment(
    payment_id: str,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Cancel a pending payment"""
    try:
        payment = await service.cancel_payment(payment_id)
        return payment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel payment: {str(e)}",
        )
