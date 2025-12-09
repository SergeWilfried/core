"""
Test data factories for generating test objects

Use these factories in your tests to create consistent test data.
"""

import time
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from faker import Faker

from core.models.account import Account, AccountType, AccountStatus
from core.models.transaction import Transaction, TransactionType, TransactionStatus
from core.models.customer import Customer, CustomerStatus, KYCStatus, Address
from core.models.payment import Payment, PaymentMethod, PaymentStatus
from core.models.card import Card, CardType, CardStatus


fake = Faker()


class CustomerFactory:
    """Factory for creating test customers"""

    @staticmethod
    def create(**kwargs):
        """Create a customer with test data"""
        return Customer(
            id=kwargs.get("id", f"cust_{uuid4().hex[:8]}"),
            email=kwargs.get("email", fake.email()),
            first_name=kwargs.get("first_name", fake.first_name()),
            last_name=kwargs.get("last_name", fake.last_name()),
            phone=kwargs.get("phone", fake.phone_number()[:15]),
            address=kwargs.get("address"),
            status=kwargs.get("status", CustomerStatus.ACTIVE),
            kyc_status=kwargs.get("kyc_status", KYCStatus.NOT_STARTED),
            created_at=kwargs.get("created_at", datetime.utcnow()),
            metadata=kwargs.get("metadata", {}),
        )

    @staticmethod
    def create_with_kyc(**kwargs):
        """Create a KYC-verified customer"""
        return CustomerFactory.create(
            kyc_status=KYCStatus.VERIFIED,
            **kwargs
        )

    @staticmethod
    def create_dict(**kwargs):
        """Create customer as dictionary (for repository mocks)"""
        customer = CustomerFactory.create(**kwargs)
        return {
            "id": customer.id,
            "email": customer.email,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "phone": customer.phone,
            "address": customer.address.model_dump() if customer.address else None,
            "status": customer.status.value,
            "kyc_status": customer.kyc_status.value,
            "metadata": customer.metadata,
        }


class AddressFactory:
    """Factory for creating test addresses"""

    @staticmethod
    def create(**kwargs):
        """Create an address with test data"""
        return Address(
            street=kwargs.get("street", fake.street_address()),
            city=kwargs.get("city", fake.city()),
            state=kwargs.get("state", fake.state_abbr()),
            postal_code=kwargs.get("postal_code", fake.postcode()),
            country=kwargs.get("country", "US"),
        )


class AccountFactory:
    """Factory for creating test accounts"""

    @staticmethod
    def create(customer_id: Optional[str] = None, **kwargs):
        """Create an account with test data"""
        customer_id = customer_id or f"cust_{uuid4().hex[:8]}"
        account_type = kwargs.get("account_type", AccountType.CHECKING)

        return Account(
            id=kwargs.get(
                "id",
                f"customers:{customer_id}:{account_type.value}"
            ),
            customer_id=customer_id,
            account_type=account_type,
            currency=kwargs.get("currency", "USD"),
            balance=kwargs.get("balance", Decimal("0")),
            available_balance=kwargs.get("available_balance", Decimal("0")),
            status=kwargs.get("status", AccountStatus.ACTIVE),
            created_at=kwargs.get("created_at", datetime.utcnow()),
            metadata=kwargs.get("metadata", {}),
        )

    @staticmethod
    def create_with_balance(balance: Decimal, **kwargs):
        """Create an account with specific balance"""
        return AccountFactory.create(
            balance=balance,
            available_balance=balance,
            **kwargs
        )

    @staticmethod
    def create_dict(customer_id: Optional[str] = None, **kwargs):
        """Create account as dictionary (for repository mocks)"""
        account = AccountFactory.create(customer_id, **kwargs)
        return {
            "id": account.id,
            "customer_id": account.customer_id,
            "account_type": account.account_type.value,
            "currency": account.currency,
            "balance": account.balance,
            "available_balance": account.available_balance,
            "status": account.status.value,
            "metadata": account.metadata,
        }


class TransactionFactory:
    """Factory for creating test transactions"""

    @staticmethod
    def create(**kwargs):
        """Create a transaction with test data"""
        return Transaction(
            id=kwargs.get("id", f"txn_{uuid4().hex[:8]}"),
            transaction_type=kwargs.get("transaction_type", TransactionType.TRANSFER),
            from_account_id=kwargs.get("from_account_id"),
            to_account_id=kwargs.get("to_account_id"),
            amount=kwargs.get("amount", Decimal("100.00")),
            currency=kwargs.get("currency", "USD"),
            status=kwargs.get("status", TransactionStatus.COMPLETED),
            description=kwargs.get("description", "Test transaction"),
            reference=kwargs.get("reference"),
            created_at=kwargs.get("created_at", datetime.utcnow()),
            completed_at=kwargs.get("completed_at", datetime.utcnow()),
            metadata=kwargs.get("metadata", {}),
        )

    @staticmethod
    def create_deposit(to_account_id: str, amount: Decimal, **kwargs):
        """Create a deposit transaction"""
        return TransactionFactory.create(
            transaction_type=TransactionType.DEPOSIT,
            from_account_id=None,
            to_account_id=to_account_id,
            amount=amount,
            **kwargs
        )

    @staticmethod
    def create_withdrawal(from_account_id: str, amount: Decimal, **kwargs):
        """Create a withdrawal transaction"""
        return TransactionFactory.create(
            transaction_type=TransactionType.WITHDRAWAL,
            from_account_id=from_account_id,
            to_account_id=None,
            amount=amount,
            **kwargs
        )

    @staticmethod
    def create_transfer(
        from_account_id: str,
        to_account_id: str,
        amount: Decimal,
        **kwargs
    ):
        """Create a transfer transaction"""
        return TransactionFactory.create(
            transaction_type=TransactionType.TRANSFER,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            amount=amount,
            **kwargs
        )

    @staticmethod
    def create_dict(**kwargs):
        """Create transaction as dictionary (for repository mocks)"""
        transaction = TransactionFactory.create(**kwargs)
        return {
            "id": transaction.id,
            "transaction_type": transaction.transaction_type.value,
            "from_account_id": transaction.from_account_id,
            "to_account_id": transaction.to_account_id,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "status": transaction.status.value,
            "description": transaction.description,
            "reference": transaction.reference,
            "metadata": transaction.metadata,
        }


class PaymentFactory:
    """Factory for creating test payments"""

    @staticmethod
    def create(**kwargs):
        """Create a payment with test data"""
        return Payment(
            id=kwargs.get("id", f"pay_{uuid4().hex[:8]}"),
            from_account_id=kwargs.get("from_account_id", "acc_test"),
            amount=kwargs.get("amount", Decimal("100.00")),
            currency=kwargs.get("currency", "USD"),
            payment_method=kwargs.get("payment_method", PaymentMethod.ACH),
            destination=kwargs.get("destination", "dest_test"),
            status=kwargs.get("status", PaymentStatus.PENDING),
            description=kwargs.get("description", "Test payment"),
            reference=kwargs.get("reference"),
            transaction_id=kwargs.get("transaction_id"),
            created_at=kwargs.get("created_at", datetime.utcnow()),
            metadata=kwargs.get("metadata", {}),
        )

    @staticmethod
    def create_ach(from_account_id: str, amount: Decimal, **kwargs):
        """Create an ACH payment"""
        return PaymentFactory.create(
            from_account_id=from_account_id,
            amount=amount,
            payment_method=PaymentMethod.ACH,
            **kwargs
        )

    @staticmethod
    def create_wire(from_account_id: str, amount: Decimal, **kwargs):
        """Create a wire transfer payment"""
        return PaymentFactory.create(
            from_account_id=from_account_id,
            amount=amount,
            payment_method=PaymentMethod.WIRE,
            **kwargs
        )

    @staticmethod
    def create_dict(**kwargs):
        """Create payment as dictionary (for repository mocks)"""
        payment = PaymentFactory.create(**kwargs)
        return {
            "id": payment.id,
            "from_account_id": payment.from_account_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "payment_method": payment.payment_method.value,
            "destination": payment.destination,
            "status": payment.status.value,
            "description": payment.description,
            "reference": payment.reference,
            "transaction_id": payment.transaction_id,
            "metadata": payment.metadata,
        }


class CardFactory:
    """Factory for creating test cards"""

    @staticmethod
    def create(**kwargs):
        """Create a card with test data"""
        return Card(
            id=kwargs.get("id", f"card_{uuid4().hex[:8]}"),
            account_id=kwargs.get("account_id", "acc_test"),
            customer_id=kwargs.get("customer_id", "cust_test"),
            card_type=kwargs.get("card_type", CardType.VIRTUAL),
            last_four=kwargs.get("last_four", "1234"),
            brand=kwargs.get("brand", "VISA"),
            expiry_month=kwargs.get("expiry_month", 12),
            expiry_year=kwargs.get("expiry_year", datetime.now().year + 2),
            status=kwargs.get("status", CardStatus.ACTIVE),
            spending_limit=kwargs.get("spending_limit"),
            created_at=kwargs.get("created_at", datetime.utcnow()),
            metadata=kwargs.get("metadata", {}),
        )

    @staticmethod
    def create_virtual(**kwargs):
        """Create a virtual card"""
        return CardFactory.create(card_type=CardType.VIRTUAL, **kwargs)

    @staticmethod
    def create_physical(**kwargs):
        """Create a physical card"""
        return CardFactory.create(card_type=CardType.PHYSICAL, **kwargs)

    @staticmethod
    def create_dict(**kwargs):
        """Create card as dictionary (for repository mocks)"""
        card = CardFactory.create(**kwargs)
        return {
            "id": card.id,
            "account_id": card.account_id,
            "customer_id": card.customer_id,
            "card_type": card.card_type.value,
            "last_four": card.last_four,
            "brand": card.brand,
            "expiry_month": card.expiry_month,
            "expiry_year": card.expiry_year,
            "status": card.status.value,
            "spending_limit": card.spending_limit,
            "metadata": card.metadata,
        }


# Timestamp for unique test IDs
def get_test_timestamp():
    """Get current timestamp for unique test IDs"""
    return int(time.time() * 1000)


# Pytest integration
def pytest_configure(config):
    """Add timestamp to pytest namespace"""
    import pytest
    pytest.timestamp = get_test_timestamp()
