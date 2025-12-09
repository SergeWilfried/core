"""
Example implementation of FormanceRepository with actual SDK calls

This shows how to implement the repository methods using the real Formance SDK.
Copy these implementations to core/repositories/formance.py
"""

from typing import Optional, Any
from decimal import Decimal
import logging
import time
from uuid import uuid4

from formance_sdk_python.models import errors

from core.client import FormanceBankingClient
from core.models.account import AccountType
from core.models.transaction import TransactionType
from core.models.payment import PaymentMethod, PaymentStatus
from core.exceptions import FormanceAPIError, AccountNotFoundError


logger = logging.getLogger(__name__)


class FormanceRepositoryExample:
    """Example implementation with real Formance SDK calls"""

    def __init__(self, client: FormanceBankingClient):
        self.client = client
        self.default_ledger = "main"  # Your ledger name

    # ========================================
    # ACCOUNT OPERATIONS
    # ========================================

    async def create_ledger_account(
        self,
        customer_id: str,
        account_type: AccountType,
        currency: str,
        metadata: dict,
    ) -> dict:
        """
        Create an account in Formance ledger

        Formance creates accounts implicitly through transactions.
        We create a zero-value transaction to establish the account.
        """
        account_address = f"customers:{customer_id}:{account_type.value}"

        try:
            # Create initial transaction to establish account
            response = await self.client.sdk.ledger.v2.create_transaction_async(
                ledger=self.default_ledger,
                request_body={
                    "metadata": {
                        "customer_id": customer_id,
                        "account_type": account_type.value,
                        "currency": currency,
                        "status": "active",
                        "created_at": time.time(),
                        **metadata,
                    },
                    "postings": [
                        {
                            "amount": 0,
                            "asset": currency,
                            "destination": account_address,
                            "source": "world",
                        }
                    ],
                }
            )

            logger.info(f"Created account: {account_address}")

            return {
                "id": account_address,
                "customer_id": customer_id,
                "account_type": account_type,
                "currency": currency,
                "balance": Decimal("0"),
                "available_balance": Decimal("0"),
                "status": "active",
                "metadata": metadata,
            }

        except errors.ErrorResponse as e:
            logger.error(f"Formance API error creating account: {e}")
            raise FormanceAPIError(f"Failed to create account: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating account: {e}")
            raise FormanceAPIError(f"Account creation failed: {e}")

    async def get_account(self, account_id: str) -> Optional[dict]:
        """Get account by ID"""
        try:
            response = await self.client.sdk.ledger.v2.get_account_async(
                ledger=self.default_ledger,
                address=account_id,
            )

            if not response.data:
                return None

            account = response.data
            metadata = account.metadata or {}

            # Extract balance (first currency)
            balance = Decimal("0")
            currency = "USD"
            if account.balances:
                currency = list(account.balances.keys())[0]
                balance = Decimal(str(account.balances[currency])) / 100

            return {
                "id": account.address,
                "customer_id": metadata.get("customer_id"),
                "account_type": metadata.get("account_type"),
                "currency": currency,
                "balance": balance,
                "available_balance": balance,
                "status": metadata.get("status", "active"),
                "metadata": metadata,
            }

        except errors.ErrorResponse as e:
            if e.status_code == 404:
                return None
            logger.error(f"Formance API error: {e}")
            raise FormanceAPIError(f"Failed to get account: {e}")
        except Exception as e:
            logger.error(f"Error getting account: {e}")
            return None

    async def get_account_balance(self, account_id: str) -> Decimal:
        """Get account balance"""
        try:
            response = await self.client.sdk.ledger.v2.get_account_async(
                ledger=self.default_ledger,
                address=account_id,
            )

            if response.data and response.data.balances:
                # Return first currency balance
                for currency, amount in response.data.balances.items():
                    return Decimal(str(amount)) / 100

            return Decimal("0")

        except errors.ErrorResponse as e:
            logger.error(f"Failed to get balance: {e}")
            raise FormanceAPIError(f"Balance retrieval failed: {e}")

    async def list_accounts_by_customer(self, customer_id: str) -> list[dict]:
        """List all accounts for a customer"""
        try:
            # Search for accounts matching customer pattern
            response = await self.client.sdk.ledger.v2.list_accounts_async(
                ledger=self.default_ledger,
                address=f"customers:{customer_id}:*",  # Wildcard search
                page_size=100,
            )

            accounts = []
            if response.data and response.data.data:
                for account in response.data.data:
                    metadata = account.metadata or {}

                    balance = Decimal("0")
                    currency = "USD"
                    if account.balances:
                        currency = list(account.balances.keys())[0]
                        balance = Decimal(str(account.balances[currency])) / 100

                    accounts.append({
                        "id": account.address,
                        "customer_id": customer_id,
                        "account_type": metadata.get("account_type"),
                        "currency": currency,
                        "balance": balance,
                        "available_balance": balance,
                        "status": metadata.get("status", "active"),
                        "metadata": metadata,
                    })

            return accounts

        except errors.ErrorResponse as e:
            logger.error(f"Failed to list accounts: {e}")
            raise FormanceAPIError(f"Account listing failed: {e}")

    async def update_account_metadata(
        self, account_id: str, metadata: dict
    ) -> dict:
        """Update account metadata"""
        try:
            await self.client.sdk.ledger.v2.add_metadata_to_account_async(
                ledger=self.default_ledger,
                address=account_id,
                request_body=metadata,
            )

            # Fetch updated account
            return await self.get_account(account_id)

        except errors.ErrorResponse as e:
            logger.error(f"Failed to update metadata: {e}")
            raise FormanceAPIError(f"Metadata update failed: {e}")

    async def account_exists(self, account_id: str) -> bool:
        """Check if account exists"""
        account = await self.get_account(account_id)
        return account is not None

    # ========================================
    # TRANSACTION OPERATIONS
    # ========================================

    async def create_transaction(
        self,
        transaction_type: TransactionType,
        from_account: Optional[str],
        to_account: Optional[str],
        amount: Decimal,
        currency: str,
        description: Optional[str],
        metadata: dict,
    ) -> dict:
        """Create a transaction"""

        # Determine source and destination
        if transaction_type == TransactionType.DEPOSIT:
            source = "world"
            destination = to_account
        elif transaction_type == TransactionType.WITHDRAWAL:
            source = from_account
            destination = "world"
        elif transaction_type == TransactionType.TRANSFER:
            source = from_account
            destination = to_account
        elif transaction_type == TransactionType.PAYMENT:
            source = from_account
            destination = "bank:payments:outgoing"
        else:
            source = from_account or "world"
            destination = to_account or "world"

        # Generate idempotency key
        idempotency_key = metadata.get("idempotency_key") or str(uuid4())

        try:
            response = await self.client.sdk.ledger.v2.create_transaction_async(
                ledger=self.default_ledger,
                idempotency_key=idempotency_key,
                request_body={
                    "metadata": {
                        "transaction_type": transaction_type.value,
                        "description": description,
                        "timestamp": time.time(),
                        **metadata,
                    },
                    "postings": [
                        {
                            "amount": int(amount * 100),  # Convert to cents
                            "asset": currency,
                            "source": source,
                            "destination": destination,
                        }
                    ],
                }
            )

            txn = response.data

            return {
                "id": str(txn.id),
                "transaction_type": transaction_type,
                "from_account_id": from_account,
                "to_account_id": to_account,
                "amount": amount,
                "currency": currency,
                "status": "completed",
                "description": description,
                "reference": txn.reference,
                "metadata": txn.metadata or {},
                "created_at": txn.timestamp,
            }

        except errors.ErrorResponse as e:
            logger.error(f"Transaction failed: {e}")
            raise FormanceAPIError(f"Transaction creation failed: {e}")

    async def get_transaction(self, transaction_id: str) -> dict:
        """Get transaction by ID"""
        try:
            response = await self.client.sdk.ledger.v2.get_transaction_async(
                ledger=self.default_ledger,
                id=int(transaction_id),
            )

            txn = response.data
            posting = txn.postings[0] if txn.postings else None

            return {
                "id": str(txn.id),
                "transaction_type": txn.metadata.get("transaction_type", "unknown"),
                "from_account_id": posting.source if posting else None,
                "to_account_id": posting.destination if posting else None,
                "amount": Decimal(str(posting.amount)) / 100 if posting else 0,
                "currency": posting.asset if posting else "USD",
                "status": "completed",
                "description": txn.metadata.get("description"),
                "reference": txn.reference,
                "metadata": txn.metadata or {},
            }

        except errors.ErrorResponse as e:
            logger.error(f"Failed to get transaction: {e}")
            raise FormanceAPIError(f"Transaction retrieval failed: {e}")

    async def list_transactions(
        self,
        account_id: str,
        limit: int,
        offset: int
    ) -> list[dict]:
        """List transactions for account"""
        try:
            response = await self.client.sdk.ledger.v2.list_transactions_async(
                ledger=self.default_ledger,
                account=account_id,
                page_size=limit,
            )

            transactions = []
            if response.data and response.data.data:
                for txn in response.data.data:
                    posting = txn.postings[0] if txn.postings else None

                    transactions.append({
                        "id": str(txn.id),
                        "transaction_type": txn.metadata.get("transaction_type", "unknown"),
                        "from_account_id": posting.source if posting else None,
                        "to_account_id": posting.destination if posting else None,
                        "amount": Decimal(str(posting.amount)) / 100 if posting else 0,
                        "currency": posting.asset if posting else "USD",
                        "status": "completed",
                        "description": txn.metadata.get("description"),
                        "reference": txn.reference,
                        "metadata": txn.metadata or {},
                        "created_at": txn.timestamp,
                    })

            return transactions

        except errors.ErrorResponse as e:
            logger.error(f"Failed to list transactions: {e}")
            return []

    # ========================================
    # PAYMENT OPERATIONS
    # ========================================

    async def create_payment(
        self,
        from_account_id: str,
        amount: Decimal,
        currency: str,
        payment_method: PaymentMethod,
        destination: str,
        description: Optional[str],
        metadata: dict,
    ) -> dict:
        """Create a payment via Formance Payments module"""

        try:
            # First, move funds from account to payments outgoing
            await self.create_transaction(
                transaction_type=TransactionType.PAYMENT,
                from_account=from_account_id,
                to_account="bank:payments:outgoing",
                amount=amount,
                currency=currency,
                description=description,
                metadata=metadata,
            )

            # Then create external payment
            response = await self.client.sdk.payments.v1.create_payment_async(
                request_body={
                    "amount": int(amount * 100),
                    "asset": currency,
                    "connector_id": self._get_connector_id(payment_method),
                    "destination": destination,
                    "metadata": {
                        "from_account": from_account_id,
                        "description": description,
                        **metadata,
                    },
                }
            )

            payment = response.data
            payment_id = str(uuid4())

            return {
                "id": payment_id,
                "from_account_id": from_account_id,
                "amount": amount,
                "currency": currency,
                "payment_method": payment_method,
                "destination": destination,
                "status": PaymentStatus.PENDING,
                "description": description,
                "metadata": metadata,
            }

        except errors.ErrorResponse as e:
            logger.error(f"Payment failed: {e}")
            raise FormanceAPIError(f"Payment creation failed: {e}")

    def _get_connector_id(self, payment_method: PaymentMethod) -> str:
        """Map payment method to Formance connector"""
        connector_map = {
            PaymentMethod.ACH: "stripe",
            PaymentMethod.WIRE: "wise",
            PaymentMethod.CARD: "stripe",
        }
        return connector_map.get(payment_method, "stripe")

    # ========================================
    # HELPER METHODS
    # ========================================

    async def revert_transaction(
        self, ledger_id: str, transaction_id: str
    ) -> dict:
        """Revert a transaction"""
        try:
            response = await self.client.sdk.ledger.v2.revert_transaction_async(
                ledger=self.default_ledger,
                id=int(transaction_id),
            )

            return {
                "id": str(response.data.id),
                "reverted_transaction_id": transaction_id,
                "status": "completed",
            }

        except errors.ErrorResponse as e:
            logger.error(f"Failed to revert transaction: {e}")
            raise FormanceAPIError(f"Transaction reversal failed: {e}")
