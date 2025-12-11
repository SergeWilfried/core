"""
Unit tests for domain models
"""

from decimal import Decimal

from core.models.account import Account, AccountStatus, AccountType
from core.models.customer import Customer, CustomerStatus, KYCStatus
from core.models.transaction import Transaction, TransactionStatus, TransactionType


class TestAccountModel:
    """Tests for Account model"""

    def test_account_creation(self):
        """Test creating an account"""
        account = Account(
            id="acc_123",
            customer_id="cust_123",
            account_type=AccountType.CHECKING,
            currency="USD",
            balance=Decimal("1000.00"),
            available_balance=Decimal("1000.00"),
        )

        assert account.id == "acc_123"
        assert account.customer_id == "cust_123"
        assert account.account_type == AccountType.CHECKING
        assert account.balance == Decimal("1000.00")

    def test_account_is_active(self):
        """Test account active status"""
        account = Account(
            id="acc_123",
            customer_id="cust_123",
            account_type=AccountType.CHECKING,
            status=AccountStatus.ACTIVE,
        )

        assert account.is_active() is True
        assert account.can_transact() is True

    def test_account_is_frozen(self):
        """Test account frozen status"""
        account = Account(
            id="acc_123",
            customer_id="cust_123",
            account_type=AccountType.CHECKING,
            status=AccountStatus.FROZEN,
        )

        assert account.is_frozen() is True
        assert account.can_transact() is False


class TestTransactionModel:
    """Tests for Transaction model"""

    def test_transaction_creation(self):
        """Test creating a transaction"""
        transaction = Transaction(
            id="txn_123",
            transaction_type=TransactionType.TRANSFER,
            from_account_id="acc_source",
            to_account_id="acc_dest",
            amount=Decimal("100.00"),
            currency="USD",
        )

        assert transaction.id == "txn_123"
        assert transaction.transaction_type == TransactionType.TRANSFER
        assert transaction.amount == Decimal("100.00")

    def test_transaction_is_completed(self):
        """Test transaction completed status"""
        transaction = Transaction(
            id="txn_123",
            transaction_type=TransactionType.DEPOSIT,
            to_account_id="acc_dest",
            amount=Decimal("100.00"),
            status=TransactionStatus.COMPLETED,
        )

        assert transaction.is_completed() is True
        assert transaction.is_pending() is False


class TestCustomerModel:
    """Tests for Customer model"""

    def test_customer_creation(self):
        """Test creating a customer"""
        customer = Customer(
            id="cust_123",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
        )

        assert customer.id == "cust_123"
        assert customer.email == "test@example.com"
        assert customer.full_name == "John Doe"

    def test_customer_can_transact(self):
        """Test customer transaction eligibility"""
        customer = Customer(
            id="cust_123",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            status=CustomerStatus.ACTIVE,
            kyc_status=KYCStatus.VERIFIED,
        )

        assert customer.can_transact() is True

    def test_customer_cannot_transact_without_kyc(self):
        """Test customer cannot transact without KYC"""
        customer = Customer(
            id="cust_123",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            status=CustomerStatus.ACTIVE,
            kyc_status=KYCStatus.PENDING,
        )

        assert customer.can_transact() is False
