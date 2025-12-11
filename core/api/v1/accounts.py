"""
Account API endpoints
"""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ...exceptions import AccountNotFoundError, InsufficientFundsError
from ...models.account import AccountStatus, AccountType
from ...services import AccountService
from ..dependencies import get_account_service, get_current_user

router = APIRouter(prefix="/accounts", tags=["accounts"])


# Request/Response schemas
class CreateAccountRequest(BaseModel):
    customer_id: str = Field(..., description="Customer identifier")
    account_type: AccountType = Field(..., description="Account type")
    currency: str = Field(default="USD", description="Account currency")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class AccountResponse(BaseModel):
    id: str
    customer_id: str
    account_type: AccountType
    currency: str
    balance: Decimal
    available_balance: Decimal
    status: AccountStatus


class BalanceResponse(BaseModel):
    account_id: str
    balance: Decimal
    currency: str


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: CreateAccountRequest,
    service: Annotated[AccountService, Depends(get_account_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a new customer account"""
    try:
        account = await service.create_account(
            customer_id=request.customer_id,
            account_type=request.account_type,
            currency=request.currency,
            metadata=request.metadata,
        )
        return account
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create account: {str(e)}",
        )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    service: Annotated[AccountService, Depends(get_account_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get account by ID"""
    try:
        account = await service.get_account(account_id)
        return account
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account: {str(e)}",
        )


@router.get("/{account_id}/balance", response_model=BalanceResponse)
async def get_account_balance(
    account_id: str,
    service: Annotated[AccountService, Depends(get_account_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get account balance"""
    try:
        account = await service.get_account(account_id)
        balance = await service.get_balance(account_id)
        return BalanceResponse(
            account_id=account_id,
            balance=balance,
            currency=account.currency,
        )
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get balance: {str(e)}",
        )


@router.get("/customer/{customer_id}", response_model=list[AccountResponse])
async def list_customer_accounts(
    customer_id: str,
    service: Annotated[AccountService, Depends(get_account_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """List all accounts for a customer"""
    try:
        accounts = await service.list_customer_accounts(customer_id)
        return accounts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list accounts: {str(e)}",
        )


@router.post("/{account_id}/freeze", response_model=AccountResponse)
async def freeze_account(
    account_id: str,
    service: Annotated[AccountService, Depends(get_account_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    reason: str = "Customer request",
):
    """Freeze an account"""
    try:
        account = await service.freeze_account(account_id, reason)
        return account
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to freeze account: {str(e)}",
        )


@router.post("/{account_id}/close", response_model=AccountResponse)
async def close_account(
    account_id: str,
    service: Annotated[AccountService, Depends(get_account_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Close an account"""
    try:
        account = await service.close_account(account_id)
        return account
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientFundsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close account: {str(e)}",
        )
