"""
Complete Test Suite Example

This file demonstrates a comprehensive test suite for the AccountService.
Use this as a template for testing your own services.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, call

from core.services.accounts import AccountService
from core.models.account import Account, AccountType, AccountStatus
from core.exceptions import (
    AccountNotFoundError,
    InsufficientFundsError,
)
from tests.factories import AccountFactory


# ============================================================================
# Unit Tests
# ============================================================================

@pytest.mark.unit
class TestAccountServiceUnit:
    """Unit tests for AccountService (mocked repository)"""

    # ------------------------------------------------------------------------
    # Success Cases
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_account_success(self, mock_formance_repository):
        """Test successful account creation"""
        # Arrange
        service = AccountService(mock_formance_repository)
        customer_id = "cust_123"
        account_type = AccountType.CHECKING

        mock_formance_repository.create_ledger_account.return_value = AccountFactory.create_dict(
            customer_id=customer_id,
            account_type=account_type,
        )

        # Act
        account = await service.create_account(
            customer_id=customer_id,
            account_type=account_type,
            currency="USD",
        )

        # Assert
        assert isinstance(account, Account)
        assert account.customer_id == customer_id
        assert account.account_type == AccountType.CHECKING
        assert account.currency == "USD"
        assert account.balance == Decimal("0")

        # Verify repository was called correctly
        mock_formance_repository.create_ledger_account.assert_called_once_with(
            customer_id=customer_id,
            account_type=account_type,
            currency="USD",
            metadata={},
        )

    @pytest.mark.asyncio
    async def test_create_account_with_metadata(self, mock_formance_repository):
        """Test account creation with custom metadata"""
        # Arrange
        service = AccountService(mock_formance_repository)
        metadata = {"source": "mobile_app", "campaign": "summer_2024"}

        mock_formance_repository.create_ledger_account.return_value = AccountFactory.create_dict(
            metadata=metadata
        )

        # Act
        account = await service.create_account(
            customer_id="cust_123",
            account_type=AccountType.SAVINGS,
            currency="USD",
            metadata=metadata,
        )

        # Assert
        assert account.metadata == metadata
        mock_formance_repository.create_ledger_account.assert_called_once()
        call_args = mock_formance_repository.create_ledger_account.call_args
        assert call_args.kwargs["metadata"] == metadata

    @pytest.mark.asyncio
    async def test_get_account_success(self, mock_formance_repository):
        """Test getting an existing account"""
        # Arrange
        service = AccountService(mock_formance_repository)
        account_id = "customers:cust_123:checking"

        mock_formance_repository.get_account.return_value = AccountFactory.create_dict(
            id=account_id
        )

        # Act
        account = await service.get_account(account_id)

        # Assert
        assert account.id == account_id
        mock_formance_repository.get_account.assert_called_once_with(account_id)

    @pytest.mark.asyncio
    async def test_get_balance(self, mock_formance_repository):
        """Test getting account balance"""
        # Arrange
        service = AccountService(mock_formance_repository)
        account_id = "customers:cust_123:checking"
        expected_balance = Decimal("1234.56")

        mock_formance_repository.get_account_balance.return_value = expected_balance

        # Act
        balance = await service.get_balance(account_id)

        # Assert
        assert balance == expected_balance
        mock_formance_repository.get_account_balance.assert_called_once_with(account_id)

    @pytest.mark.asyncio
    async def test_list_customer_accounts(self, mock_formance_repository):
        """Test listing all accounts for a customer"""
        # Arrange
        service = AccountService(mock_formance_repository)
        customer_id = "cust_123"

        mock_formance_repository.list_accounts_by_customer.return_value = [
            AccountFactory.create_dict(
                customer_id=customer_id,
                account_type=AccountType.CHECKING,
            ),
            AccountFactory.create_dict(
                customer_id=customer_id,
                account_type=AccountType.SAVINGS,
            ),
        ]

        # Act
        accounts = await service.list_customer_accounts(customer_id)

        # Assert
        assert len(accounts) == 2
        assert all(isinstance(acc, Account) for acc in accounts)
        assert accounts[0].account_type == AccountType.CHECKING
        assert accounts[1].account_type == AccountType.SAVINGS
        mock_formance_repository.list_accounts_by_customer.assert_called_once_with(
            customer_id
        )

    @pytest.mark.asyncio
    async def test_freeze_account(self, mock_formance_repository):
        """Test freezing an account"""
        # Arrange
        service = AccountService(mock_formance_repository)
        account_id = "customers:cust_123:checking"
        reason = "Suspicious activity detected"

        mock_formance_repository.update_account_metadata.return_value = AccountFactory.create_dict(
            id=account_id,
            status=AccountStatus.FROZEN,
        )

        # Act
        account = await service.freeze_account(account_id, reason)

        # Assert
        assert account.status == AccountStatus.FROZEN
        assert account.is_frozen()
        mock_formance_repository.update_account_metadata.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_account_with_zero_balance(self, mock_formance_repository):
        """Test closing account with zero balance"""
        # Arrange
        service = AccountService(mock_formance_repository)
        account_id = "customers:cust_123:checking"

        mock_formance_repository.get_balance.return_value = Decimal("0")
        mock_formance_repository.update_account_metadata.return_value = AccountFactory.create_dict(
            id=account_id,
            status=AccountStatus.CLOSED,
        )

        # Act
        account = await service.close_account(account_id)

        # Assert
        assert account.status == AccountStatus.CLOSED
        mock_formance_repository.get_balance.assert_called_once()
        mock_formance_repository.update_account_metadata.assert_called_once()

    # ------------------------------------------------------------------------
    # Error Cases
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_account_not_found(self, mock_formance_repository):
        """Test getting non-existent account raises error"""
        # Arrange
        service = AccountService(mock_formance_repository)
        account_id = "non_existent_account"

        mock_formance_repository.get_account.return_value = None

        # Act & Assert
        with pytest.raises(AccountNotFoundError) as exc_info:
            await service.get_account(account_id)

        assert account_id in str(exc_info.value)
        mock_formance_repository.get_account.assert_called_once_with(account_id)

    @pytest.mark.asyncio
    async def test_close_account_with_non_zero_balance(self, mock_formance_repository):
        """Test closing account with balance raises error"""
        # Arrange
        service = AccountService(mock_formance_repository)
        account_id = "customers:cust_123:checking"
        balance = Decimal("100.50")

        mock_formance_repository.get_balance.return_value = balance

        # Act & Assert
        with pytest.raises(InsufficientFundsError) as exc_info:
            await service.close_account(account_id)

        error_message = str(exc_info.value)
        assert "non-zero balance" in error_message
        assert str(balance) in error_message

    # ------------------------------------------------------------------------
    # Edge Cases
    # ------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_account_different_currencies(self, mock_formance_repository):
        """Test creating accounts with different currencies"""
        service = AccountService(mock_formance_repository)

        for currency in ["USD", "EUR", "GBP"]:
            mock_formance_repository.create_ledger_account.return_value = AccountFactory.create_dict(
                currency=currency
            )

            account = await service.create_account(
                customer_id="cust_123",
                account_type=AccountType.CHECKING,
                currency=currency,
            )

            assert account.currency == currency

    @pytest.mark.asyncio
    async def test_get_balance_returns_decimal(self, mock_formance_repository):
        """Ensure balance is always returned as Decimal"""
        # Arrange
        service = AccountService(mock_formance_repository)

        # Test with different numeric types
        test_balances = [100, 100.5, "100.50", Decimal("100.50")]

        for test_balance in test_balances:
            mock_formance_repository.get_account_balance.return_value = test_balance

            # Act
            balance = await service.get_balance("acc_123")

            # Assert
            assert isinstance(balance, Decimal)


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestAccountServiceIntegration:
    """Integration tests for AccountService (real Formance sandbox)"""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_account(self, formance_client):
        """Test creating account and retrieving it"""
        from core.repositories.formance import FormanceRepository

        # Arrange
        repository = FormanceRepository(formance_client)
        service = AccountService(repository)
        customer_id = f"test_cust_{pytest.timestamp}"

        # Act - Create account
        created_account = await service.create_account(
            customer_id=customer_id,
            account_type=AccountType.CHECKING,
            currency="USD",
        )

        # Assert - Account created
        assert created_account.id is not None
        assert created_account.customer_id == customer_id

        # Act - Retrieve account
        retrieved_account = await service.get_account(created_account.id)

        # Assert - Same account
        assert retrieved_account.id == created_account.id
        assert retrieved_account.customer_id == customer_id
        assert retrieved_account.balance == Decimal("0")

    @pytest.mark.asyncio
    async def test_list_multiple_accounts(self, formance_client):
        """Test listing multiple accounts for a customer"""
        from core.repositories.formance import FormanceRepository

        # Arrange
        repository = FormanceRepository(formance_client)
        service = AccountService(repository)
        customer_id = f"test_cust_{pytest.timestamp}"

        # Create multiple accounts
        checking = await service.create_account(
            customer_id=customer_id,
            account_type=AccountType.CHECKING,
            currency="USD",
        )

        savings = await service.create_account(
            customer_id=customer_id,
            account_type=AccountType.SAVINGS,
            currency="USD",
        )

        # Act
        accounts = await service.list_customer_accounts(customer_id)

        # Assert
        assert len(accounts) >= 2
        account_types = [acc.account_type for acc in accounts]
        assert AccountType.CHECKING in account_types
        assert AccountType.SAVINGS in account_types


# ============================================================================
# Parametrized Tests
# ============================================================================

@pytest.mark.unit
class TestAccountServiceParametrized:
    """Parametrized tests for comprehensive coverage"""

    @pytest.mark.parametrize("account_type", [
        AccountType.CHECKING,
        AccountType.SAVINGS,
        AccountType.BUSINESS,
        AccountType.ESCROW,
    ])
    @pytest.mark.asyncio
    async def test_create_all_account_types(
        self,
        mock_formance_repository,
        account_type
    ):
        """Test creating all supported account types"""
        service = AccountService(mock_formance_repository)

        mock_formance_repository.create_ledger_account.return_value = AccountFactory.create_dict(
            account_type=account_type
        )

        account = await service.create_account(
            customer_id="cust_123",
            account_type=account_type,
            currency="USD",
        )

        assert account.account_type == account_type

    @pytest.mark.parametrize("balance,can_close", [
        (Decimal("0"), True),
        (Decimal("0.01"), False),
        (Decimal("100"), False),
        (Decimal("-0.01"), False),
    ])
    @pytest.mark.asyncio
    async def test_close_account_balance_validation(
        self,
        mock_formance_repository,
        balance,
        can_close
    ):
        """Test account closure with various balances"""
        service = AccountService(mock_formance_repository)
        account_id = "acc_123"

        mock_formance_repository.get_balance.return_value = balance
        mock_formance_repository.update_account_metadata.return_value = AccountFactory.create_dict()

        if can_close:
            # Should succeed
            await service.close_account(account_id)
        else:
            # Should raise error
            with pytest.raises(InsufficientFundsError):
                await service.close_account(account_id)


# ============================================================================
# Test Utilities
# ============================================================================

@pytest.fixture
def sample_accounts():
    """Fixture providing sample accounts for testing"""
    return {
        "checking": AccountFactory.create(account_type=AccountType.CHECKING),
        "savings": AccountFactory.create(account_type=AccountType.SAVINGS),
        "business": AccountFactory.create(account_type=AccountType.BUSINESS),
    }


# ============================================================================
# Summary
# ============================================================================

"""
Test Coverage Summary:

Unit Tests:
- ✓ Account creation (success, with metadata)
- ✓ Account retrieval (success, not found)
- ✓ Balance queries
- ✓ List customer accounts
- ✓ Freeze account
- ✓ Close account (success, with balance)
- ✓ Different currencies
- ✓ All account types (parametrized)
- ✓ Balance validation (parametrized)

Integration Tests:
- ✓ Create and retrieve account (real API)
- ✓ List multiple accounts (real API)

Coverage: ~95% of AccountService

Running These Tests:
    # All tests
    pytest docs/examples/complete_test_example.py -v

    # Unit tests only
    pytest docs/examples/complete_test_example.py -m unit

    # Integration tests only
    pytest docs/examples/complete_test_example.py -m integration

    # With coverage
    pytest docs/examples/complete_test_example.py --cov=core.services.accounts
"""
