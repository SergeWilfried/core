"""
Account management service
"""

import logging
from decimal import Decimal

from ..exceptions import AccountNotFoundError, InsufficientFundsError
from ..models.account import Account, AccountStatus, AccountType
from ..repositories.formance import FormanceRepository

logger = logging.getLogger(__name__)


class AccountService:
    """Service for managing customer accounts"""

    def __init__(self, formance_repo: FormanceRepository):
        self.formance_repo = formance_repo

    async def create_account(
        self,
        customer_id: str,
        account_type: AccountType,
        currency: str = "USD",
        metadata: dict | None = None,
    ) -> Account:
        """
        Create a new customer account

        Args:
            customer_id: Customer identifier
            account_type: Type of account (CHECKING, SAVINGS, etc.)
            currency: Account currency (default: USD)
            metadata: Additional account metadata

        Returns:
            Created Account object
        """
        logger.info(f"Creating {account_type} account for customer {customer_id}")

        # Create account in Formance ledger
        account_data = await self.formance_repo.create_ledger_account(
            customer_id=customer_id,
            account_type=account_type,
            currency=currency,
            metadata=metadata or {},
        )

        account = Account(**account_data)
        logger.info(f"Account created: {account.id}")
        return account

    async def get_account(self, account_id: str) -> Account:
        """
        Get account by ID

        Args:
            account_id: Account identifier

        Returns:
            Account object

        Raises:
            AccountNotFoundError: If account doesn't exist
        """
        account_data = await self.formance_repo.get_account(account_id)
        if not account_data:
            raise AccountNotFoundError(f"Account {account_id} not found")

        return Account(**account_data)

    async def get_balance(self, account_id: str) -> Decimal:
        """
        Get account balance

        Args:
            account_id: Account identifier

        Returns:
            Current account balance
        """
        balance = await self.formance_repo.get_account_balance(account_id)
        return Decimal(str(balance))

    async def list_customer_accounts(self, customer_id: str) -> list[Account]:
        """
        List all accounts for a customer

        Args:
            customer_id: Customer identifier

        Returns:
            List of Account objects
        """
        accounts_data = await self.formance_repo.list_accounts_by_customer(customer_id)
        return [Account(**data) for data in accounts_data]

    async def update_account_status(self, account_id: str, status: AccountStatus) -> Account:
        """
        Update account status (ACTIVE, FROZEN, CLOSED)

        Args:
            account_id: Account identifier
            status: New account status

        Returns:
            Updated Account object
        """
        logger.info(f"Updating account {account_id} status to {status}")

        account_data = await self.formance_repo.update_account_metadata(
            account_id, {"status": status.value}
        )

        return Account(**account_data)

    async def freeze_account(self, account_id: str, reason: str) -> Account:
        """
        Freeze an account

        Args:
            account_id: Account identifier
            reason: Reason for freezing

        Returns:
            Updated Account object
        """
        logger.warning(f"Freezing account {account_id}: {reason}")
        return await self.update_account_status(account_id, AccountStatus.FROZEN)

    async def close_account(self, account_id: str) -> Account:
        """
        Close an account (requires zero balance)

        Args:
            account_id: Account identifier

        Returns:
            Updated Account object

        Raises:
            InsufficientFundsError: If account has non-zero balance
        """
        balance = await self.get_balance(account_id)
        if balance != 0:
            raise InsufficientFundsError(
                f"Cannot close account {account_id} with non-zero balance: {balance}"
            )

        logger.info(f"Closing account {account_id}")
        return await self.update_account_status(account_id, AccountStatus.CLOSED)
