"""
FastAPI dependencies
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..client import FormanceBankingClient
from ..config import get_settings
from ..repositories.formance import FormanceRepository
from ..services import (
    AccountService,
    CardService,
    CustomerService,
    LedgerService,
    PaymentService,
    TransactionService,
)
from ..services.organizations import OrganizationService
from ..services.users import UserService

# Security
security = HTTPBearer()


async def get_formance_client() -> FormanceBankingClient:
    """Get Formance client instance"""
    settings = get_settings()

    client = FormanceBankingClient(
        base_url=settings.formance_base_url,
        client_id=settings.formance_client_id,
        client_secret=settings.formance_client_secret,
    )

    try:
        yield client
    finally:
        await client.close()


async def get_formance_repository(
    client: Annotated[FormanceBankingClient, Depends(get_formance_client)],
) -> FormanceRepository:
    """Get Formance repository instance"""
    return FormanceRepository(client)


async def get_account_service(
    repo: Annotated[FormanceRepository, Depends(get_formance_repository)],
) -> AccountService:
    """Get Account service instance"""
    return AccountService(repo)


async def get_transaction_service(
    repo: Annotated[FormanceRepository, Depends(get_formance_repository)],
) -> TransactionService:
    """Get Transaction service instance"""
    return TransactionService(repo)


async def get_payment_service(
    repo: Annotated[FormanceRepository, Depends(get_formance_repository)],
) -> PaymentService:
    """Get Payment service instance"""
    return PaymentService(repo)


async def get_customer_service(
    repo: Annotated[FormanceRepository, Depends(get_formance_repository)],
) -> CustomerService:
    """Get Customer service instance"""
    return CustomerService(repo)


async def get_card_service(
    repo: Annotated[FormanceRepository, Depends(get_formance_repository)],
) -> CardService:
    """Get Card service instance"""
    return CardService(repo)


async def get_ledger_service(
    repo: Annotated[FormanceRepository, Depends(get_formance_repository)],
) -> LedgerService:
    """Get Ledger service instance"""
    return LedgerService(repo)


async def get_organization_service(
    repo: Annotated[FormanceRepository, Depends(get_formance_repository)],
) -> OrganizationService:
    """Get Organization service instance"""
    return OrganizationService(repo)


async def get_user_service(
    repo: Annotated[FormanceRepository, Depends(get_formance_repository)],
) -> UserService:
    """Get User service instance"""
    return UserService(repo)


async def verify_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """
    Verify API key from Bearer token

    This is a placeholder - implement proper authentication
    """
    token = credentials.credentials

    # TODO: Implement proper token validation
    # - Validate JWT token
    # - Check token expiry
    # - Verify user permissions

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


async def get_current_user(token: Annotated[str, Depends(verify_api_key)]) -> dict:
    """
    Get current authenticated user

    This is a placeholder - implement proper user retrieval
    """
    # TODO: Implement user retrieval from token
    # - Decode JWT
    # - Fetch user from database
    # - Return user object

    return {"user_id": "placeholder", "token": token}
