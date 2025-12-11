"""
Transaction API endpoints
"""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ...exceptions import AccountNotFoundError, InsufficientFundsError
from ...models.transaction import TransactionStatus, TransactionType
from ...services import TransactionService
from ..dependencies import get_current_user, get_transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


# Request/Response schemas
class DepositRequest(BaseModel):
    to_account_id: str = Field(..., description="Destination account")
    amount: Decimal = Field(..., gt=0, description="Amount to deposit")
    currency: str = Field(default="USD", description="Currency")
    description: str | None = Field(default=None, description="Description")
    metadata: dict = Field(default_factory=dict, description="Metadata")


class WithdrawalRequest(BaseModel):
    from_account_id: str = Field(..., description="Source account")
    amount: Decimal = Field(..., gt=0, description="Amount to withdraw")
    currency: str = Field(default="USD", description="Currency")
    description: str | None = Field(default=None, description="Description")
    metadata: dict = Field(default_factory=dict, description="Metadata")


class TransferRequest(BaseModel):
    from_account_id: str = Field(..., description="Source account")
    to_account_id: str = Field(..., description="Destination account")
    amount: Decimal = Field(..., gt=0, description="Amount to transfer")
    currency: str = Field(default="USD", description="Currency")
    description: str | None = Field(default=None, description="Description")
    metadata: dict = Field(default_factory=dict, description="Metadata")


class TransactionResponse(BaseModel):
    id: str
    transaction_type: TransactionType
    from_account_id: str | None
    to_account_id: str | None
    amount: Decimal
    currency: str
    status: TransactionStatus
    description: str | None
    reference: str | None


@router.post("/deposit", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_deposit(
    request: DepositRequest,
    service: Annotated[TransactionService, Depends(get_transaction_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Deposit funds to an account"""
    try:
        transaction = await service.deposit(
            to_account_id=request.to_account_id,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            metadata=request.metadata,
        )
        return transaction
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create deposit: {str(e)}",
        )


@router.post("/withdraw", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_withdrawal(
    request: WithdrawalRequest,
    service: Annotated[TransactionService, Depends(get_transaction_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Withdraw funds from an account"""
    try:
        transaction = await service.withdraw(
            from_account_id=request.from_account_id,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            metadata=request.metadata,
        )
        return transaction
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientFundsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create withdrawal: {str(e)}",
        )


@router.post("/transfer", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    request: TransferRequest,
    service: Annotated[TransactionService, Depends(get_transaction_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Transfer funds between accounts"""
    try:
        transaction = await service.transfer(
            from_account_id=request.from_account_id,
            to_account_id=request.to_account_id,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            metadata=request.metadata,
        )
        return transaction
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientFundsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transfer: {str(e)}",
        )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    service: Annotated[TransactionService, Depends(get_transaction_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get transaction by ID"""
    try:
        transaction = await service.get_transaction(transaction_id)
        return transaction
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transaction: {str(e)}",
        )


@router.get("/account/{account_id}", response_model=list[TransactionResponse])
async def list_account_transactions(
    account_id: str,
    service: Annotated[TransactionService, Depends(get_transaction_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List transactions for an account"""
    try:
        transactions = await service.list_account_transactions(
            account_id=account_id,
            limit=limit,
            offset=offset,
        )
        return transactions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list transactions: {str(e)}",
        )
