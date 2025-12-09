"""
Transaction processing service
"""

from typing import Optional
from decimal import Decimal
from datetime import datetime
import logging

from ..models.transaction import Transaction, TransactionType, TransactionStatus
from ..repositories.formance import FormanceRepository
from ..exceptions import (
    InsufficientFundsError,
    TransactionLimitExceeded,
    AccountNotFoundError,
)


logger = logging.getLogger(__name__)


class TransactionService:
    """Service for processing transactions"""

    def __init__(self, formance_repo: FormanceRepository):
        self.formance_repo = formance_repo
        self.daily_limit = Decimal("10000.00")  # Default daily limit

    async def create_transaction(
        self,
        transaction_type: TransactionType,
        from_account_id: Optional[str],
        to_account_id: Optional[str],
        amount: Decimal,
        currency: str = "USD",
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Transaction:
        """
        Create a new transaction

        Args:
            transaction_type: Type of transaction
            from_account_id: Source account (None for deposits)
            to_account_id: Destination account (None for withdrawals)
            amount: Transaction amount
            currency: Transaction currency
            description: Transaction description
            metadata: Additional metadata

        Returns:
            Created Transaction object

        Raises:
            InsufficientFundsError: If source account has insufficient funds
            AccountNotFoundError: If account doesn't exist
        """
        logger.info(
            f"Processing {transaction_type} transaction: {amount} {currency}"
        )

        # Validate accounts exist
        if from_account_id:
            await self._validate_account_exists(from_account_id)
        if to_account_id:
            await self._validate_account_exists(to_account_id)

        # Check sufficient funds for debits
        if from_account_id and transaction_type in [
            TransactionType.TRANSFER,
            TransactionType.WITHDRAWAL,
            TransactionType.PAYMENT,
        ]:
            await self._validate_sufficient_funds(from_account_id, amount)

        # Create transaction in Formance
        transaction_data = await self.formance_repo.create_transaction(
            transaction_type=transaction_type,
            from_account=from_account_id,
            to_account=to_account_id,
            amount=amount,
            currency=currency,
            description=description,
            metadata=metadata or {},
        )

        transaction = Transaction(**transaction_data)
        logger.info(f"Transaction created: {transaction.id}")
        return transaction

    async def get_transaction(self, transaction_id: str) -> Transaction:
        """
        Get transaction by ID

        Args:
            transaction_id: Transaction identifier

        Returns:
            Transaction object
        """
        transaction_data = await self.formance_repo.get_transaction(transaction_id)
        return Transaction(**transaction_data)

    async def list_account_transactions(
        self,
        account_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        """
        List transactions for an account

        Args:
            account_id: Account identifier
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip

        Returns:
            List of Transaction objects
        """
        transactions_data = await self.formance_repo.list_transactions(
            account_id=account_id,
            limit=limit,
            offset=offset,
        )
        return [Transaction(**data) for data in transactions_data]

    async def deposit(
        self,
        to_account_id: str,
        amount: Decimal,
        currency: str = "USD",
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Transaction:
        """
        Deposit funds to an account

        Args:
            to_account_id: Destination account
            amount: Amount to deposit
            currency: Currency
            description: Deposit description
            metadata: Additional metadata

        Returns:
            Created Transaction object
        """
        return await self.create_transaction(
            transaction_type=TransactionType.DEPOSIT,
            from_account_id=None,
            to_account_id=to_account_id,
            amount=amount,
            currency=currency,
            description=description or "Deposit",
            metadata=metadata,
        )

    async def withdraw(
        self,
        from_account_id: str,
        amount: Decimal,
        currency: str = "USD",
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Transaction:
        """
        Withdraw funds from an account

        Args:
            from_account_id: Source account
            amount: Amount to withdraw
            currency: Currency
            description: Withdrawal description
            metadata: Additional metadata

        Returns:
            Created Transaction object
        """
        return await self.create_transaction(
            transaction_type=TransactionType.WITHDRAWAL,
            from_account_id=from_account_id,
            to_account_id=None,
            amount=amount,
            currency=currency,
            description=description or "Withdrawal",
            metadata=metadata,
        )

    async def transfer(
        self,
        from_account_id: str,
        to_account_id: str,
        amount: Decimal,
        currency: str = "USD",
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Transaction:
        """
        Transfer funds between accounts

        Args:
            from_account_id: Source account
            to_account_id: Destination account
            amount: Amount to transfer
            currency: Currency
            description: Transfer description
            metadata: Additional metadata

        Returns:
            Created Transaction object
        """
        return await self.create_transaction(
            transaction_type=TransactionType.TRANSFER,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            amount=amount,
            currency=currency,
            description=description or "Transfer",
            metadata=metadata,
        )

    async def _validate_account_exists(self, account_id: str) -> None:
        """Validate that an account exists"""
        exists = await self.formance_repo.account_exists(account_id)
        if not exists:
            raise AccountNotFoundError(f"Account {account_id} not found")

    async def _validate_sufficient_funds(
        self, account_id: str, amount: Decimal
    ) -> None:
        """Validate account has sufficient funds"""
        balance = await self.formance_repo.get_account_balance(account_id)
        if Decimal(str(balance)) < amount:
            raise InsufficientFundsError(
                f"Insufficient funds in account {account_id}. "
                f"Balance: {balance}, Required: {amount}"
            )
