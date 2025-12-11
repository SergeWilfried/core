"""
Ledger operations service
"""

import logging
from decimal import Decimal

from ..repositories.formance import FormanceRepository

logger = logging.getLogger(__name__)


class LedgerService:
    """Service for direct ledger operations"""

    def __init__(self, formance_repo: FormanceRepository):
        self.formance_repo = formance_repo

    async def create_ledger(
        self,
        name: str,
        metadata: dict | None = None,
    ) -> dict:
        """
        Create a new ledger

        Args:
            name: Ledger name
            metadata: Ledger metadata

        Returns:
            Created ledger data
        """
        logger.info(f"Creating ledger: {name}")

        ledger_data = await self.formance_repo.create_ledger(name=name, metadata=metadata or {})

        logger.info(f"Ledger created: {ledger_data.get('id')}")
        return ledger_data

    async def get_ledger(self, ledger_id: str) -> dict:
        """
        Get ledger by ID

        Args:
            ledger_id: Ledger identifier

        Returns:
            Ledger data
        """
        return await self.formance_repo.get_ledger(ledger_id)

    async def list_ledgers(self) -> list[dict]:
        """
        List all ledgers

        Returns:
            List of ledger data
        """
        return await self.formance_repo.list_ledgers()

    async def post_transaction(
        self,
        ledger_id: str,
        postings: list[dict],
        reference: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """
        Post a transaction with custom postings

        Args:
            ledger_id: Ledger identifier
            postings: List of posting objects
            reference: Transaction reference
            metadata: Transaction metadata

        Returns:
            Transaction data
        """
        logger.info(f"Posting transaction to ledger {ledger_id}")

        transaction_data = await self.formance_repo.post_transaction(
            ledger_id=ledger_id,
            postings=postings,
            reference=reference,
            metadata=metadata or {},
        )

        return transaction_data

    async def get_account_balances(self, ledger_id: str, account_id: str) -> dict[str, Decimal]:
        """
        Get balances for an account across all currencies

        Args:
            ledger_id: Ledger identifier
            account_id: Account identifier

        Returns:
            Dictionary of currency -> balance
        """
        balances = await self.formance_repo.get_account_balances(ledger_id, account_id)

        return {currency: Decimal(str(amount)) for currency, amount in balances.items()}

    async def get_aggregated_balances(
        self, ledger_id: str, address_pattern: str
    ) -> dict[str, Decimal]:
        """
        Get aggregated balances for accounts matching a pattern

        Args:
            ledger_id: Ledger identifier
            address_pattern: Account address pattern (e.g., "customers:*")

        Returns:
            Dictionary of currency -> total balance
        """
        balances = await self.formance_repo.get_aggregated_balances(ledger_id, address_pattern)

        return {currency: Decimal(str(amount)) for currency, amount in balances.items()}

    async def revert_transaction(self, ledger_id: str, transaction_id: str) -> dict:
        """
        Revert a transaction

        Args:
            ledger_id: Ledger identifier
            transaction_id: Transaction to revert

        Returns:
            Reversal transaction data
        """
        logger.warning(f"Reverting transaction {transaction_id} in ledger {ledger_id}")

        reversal_data = await self.formance_repo.revert_transaction(ledger_id, transaction_id)

        return reversal_data

    async def add_metadata(
        self,
        ledger_id: str,
        target_type: str,
        target_id: str,
        metadata: dict,
    ) -> dict:
        """
        Add metadata to a ledger object

        Args:
            ledger_id: Ledger identifier
            target_type: Type of object (account, transaction)
            target_id: Object identifier
            metadata: Metadata to add

        Returns:
            Updated object data
        """
        logger.info(f"Adding metadata to {target_type} {target_id}")

        return await self.formance_repo.add_metadata(ledger_id, target_type, target_id, metadata)
