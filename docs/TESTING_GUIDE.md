# Testing Guide for BaaS Core Banking

Comprehensive guide for writing unit tests, integration tests, and end-to-end tests.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Structure](#test-structure)
- [Unit Tests](#unit-tests)
- [Integration Tests](#integration-tests)
- [End-to-End Tests](#end-to-end-tests)
- [Testing Best Practices](#testing-best-practices)
- [Mocking Strategies](#mocking-strategies)
- [Test Data Management](#test-data-management)
- [Running Tests](#running-tests)

---

## Testing Philosophy

### Test Pyramid

```
           /\
          /  \
         / E2E \          ← Few (10%)
        /______\
       /        \
      / Integration\      ← Some (30%)
     /____________\
    /              \
   /   Unit Tests   \    ← Many (60%)
  /________________\
```

**Our Approach:**
- **60% Unit Tests**: Fast, isolated, test business logic
- **30% Integration Tests**: Test service + repository + Formance SDK
- **10% E2E Tests**: Test complete API flows

### Testing Goals

1. **Confidence**: Catch bugs before production
2. **Documentation**: Tests serve as usage examples
3. **Refactoring Safety**: Change code without fear
4. **Fast Feedback**: Most tests run in < 1 second

---

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/                       # Unit tests (60%)
│   ├── test_models.py
│   ├── test_services/
│   │   ├── test_account_service.py
│   │   ├── test_transaction_service.py
│   │   ├── test_payment_service.py
│   │   └── test_customer_service.py
│   ├── test_validators.py
│   └── test_utils.py
├── integration/                # Integration tests (30%)
│   ├── test_formance_integration.py
│   ├── test_account_flows.py
│   ├── test_transaction_flows.py
│   └── test_payment_flows.py
└── e2e/                       # End-to-end tests (10%)
    ├── test_api_endpoints.py
    └── test_complete_flows.py
```

---

## Unit Tests

### What to Test

- **Business Logic**: Service methods
- **Validation**: Pydantic models, custom validators
- **Calculations**: Balance calculations, fee calculations
- **Edge Cases**: Negative amounts, zero balances, etc.

### What NOT to Test

- External dependencies (Formance SDK calls)
- Database operations
- HTTP requests/responses
- Third-party libraries

### Example: Testing Account Service

```python
# tests/unit/test_services/test_account_service.py
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

from core.services.accounts import AccountService
from core.models.account import Account, AccountType, AccountStatus
from core.exceptions import InsufficientFundsError, AccountNotFoundError


@pytest.fixture
def mock_repository():
    """Create a mock repository"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def account_service(mock_repository):
    """Create account service with mocked repository"""
    return AccountService(mock_repository)


class TestAccountService:
    """Unit tests for AccountService"""

    @pytest.mark.asyncio
    async def test_create_account_success(self, account_service, mock_repository):
        """Test successful account creation"""
        # Arrange
        customer_id = "cust_123"
        account_type = AccountType.CHECKING
        currency = "USD"

        mock_repository.create_ledger_account.return_value = {
            "id": "customers:cust_123:checking",
            "customer_id": customer_id,
            "account_type": account_type,
            "currency": currency,
            "balance": Decimal("0"),
            "available_balance": Decimal("0"),
            "status": "active",
            "metadata": {},
        }

        # Act
        account = await account_service.create_account(
            customer_id=customer_id,
            account_type=account_type,
            currency=currency,
        )

        # Assert
        assert account.id == "customers:cust_123:checking"
        assert account.customer_id == customer_id
        assert account.account_type == AccountType.CHECKING
        assert account.balance == Decimal("0")

        # Verify repository was called correctly
        mock_repository.create_ledger_account.assert_called_once_with(
            customer_id=customer_id,
            account_type=account_type,
            currency=currency,
            metadata={},
        )

    @pytest.mark.asyncio
    async def test_get_account_not_found(self, account_service, mock_repository):
        """Test getting non-existent account raises error"""
        # Arrange
        mock_repository.get_account.return_value = None

        # Act & Assert
        with pytest.raises(AccountNotFoundError):
            await account_service.get_account("non_existent_account")

    @pytest.mark.asyncio
    async def test_close_account_with_balance(self, account_service, mock_repository):
        """Test closing account with non-zero balance raises error"""
        # Arrange
        account_id = "customers:cust_123:checking"
        mock_repository.get_balance.return_value = Decimal("100.00")

        # Act & Assert
        with pytest.raises(InsufficientFundsError) as exc_info:
            await account_service.close_account(account_id)

        assert "non-zero balance" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_close_account_success(self, account_service, mock_repository):
        """Test successful account closure"""
        # Arrange
        account_id = "customers:cust_123:checking"
        mock_repository.get_balance.return_value = Decimal("0")
        mock_repository.update_account_metadata.return_value = {
            "id": account_id,
            "status": "closed",
        }

        # Act
        account = await account_service.close_account(account_id)

        # Assert
        assert account.status == AccountStatus.CLOSED
        mock_repository.update_account_metadata.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_customer_accounts(self, account_service, mock_repository):
        """Test listing all customer accounts"""
        # Arrange
        customer_id = "cust_123"
        mock_repository.list_accounts_by_customer.return_value = [
            {
                "id": "customers:cust_123:checking",
                "customer_id": customer_id,
                "account_type": "checking",
                "currency": "USD",
                "balance": Decimal("1000"),
                "available_balance": Decimal("1000"),
                "status": "active",
                "metadata": {},
            },
            {
                "id": "customers:cust_123:savings",
                "customer_id": customer_id,
                "account_type": "savings",
                "currency": "USD",
                "balance": Decimal("5000"),
                "available_balance": Decimal("5000"),
                "status": "active",
                "metadata": {},
            },
        ]

        # Act
        accounts = await account_service.list_customer_accounts(customer_id)

        # Assert
        assert len(accounts) == 2
        assert accounts[0].account_type == AccountType.CHECKING
        assert accounts[1].account_type == AccountType.SAVINGS
```

### Example: Testing Transaction Service

```python
# tests/unit/test_services/test_transaction_service.py
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from core.services.transactions import TransactionService
from core.models.transaction import TransactionType, TransactionStatus
from core.exceptions import InsufficientFundsError, AccountNotFoundError


@pytest.fixture
def mock_repository():
    repository = AsyncMock()
    return repository


@pytest.fixture
def transaction_service(mock_repository):
    return TransactionService(mock_repository)


class TestTransactionService:
    """Unit tests for TransactionService"""

    @pytest.mark.asyncio
    async def test_deposit_success(self, transaction_service, mock_repository):
        """Test successful deposit"""
        # Arrange
        to_account_id = "customers:cust_123:checking"
        amount = Decimal("1000.00")

        mock_repository.account_exists.return_value = True
        mock_repository.create_transaction.return_value = {
            "id": "txn_123",
            "transaction_type": TransactionType.DEPOSIT,
            "from_account_id": None,
            "to_account_id": to_account_id,
            "amount": amount,
            "currency": "USD",
            "status": "completed",
            "description": "Deposit",
            "metadata": {},
        }

        # Act
        transaction = await transaction_service.deposit(
            to_account_id=to_account_id,
            amount=amount,
            currency="USD",
        )

        # Assert
        assert transaction.transaction_type == TransactionType.DEPOSIT
        assert transaction.amount == amount
        assert transaction.to_account_id == to_account_id

    @pytest.mark.asyncio
    async def test_transfer_insufficient_funds(
        self, transaction_service, mock_repository
    ):
        """Test transfer with insufficient funds"""
        # Arrange
        from_account = "customers:alice:checking"
        to_account = "customers:bob:checking"
        amount = Decimal("1000.00")

        mock_repository.account_exists.return_value = True
        mock_repository.get_account_balance.return_value = Decimal("500.00")

        # Act & Assert
        with pytest.raises(InsufficientFundsError):
            await transaction_service.transfer(
                from_account_id=from_account,
                to_account_id=to_account,
                amount=amount,
                currency="USD",
            )

    @pytest.mark.asyncio
    async def test_transfer_account_not_found(
        self, transaction_service, mock_repository
    ):
        """Test transfer to non-existent account"""
        # Arrange
        from_account = "customers:alice:checking"
        to_account = "non_existent_account"
        amount = Decimal("100.00")

        mock_repository.account_exists.side_effect = [True, False]

        # Act & Assert
        with pytest.raises(AccountNotFoundError):
            await transaction_service.transfer(
                from_account_id=from_account,
                to_account_id=to_account,
                amount=amount,
                currency="USD",
            )
```

### Example: Testing Validators

```python
# tests/unit/test_validators.py
import pytest
from decimal import Decimal

from core.utils.validators import (
    validate_amount,
    validate_currency,
    validate_routing_number,
    validate_swift_code,
)
from core.exceptions import InvalidAmountError, InvalidCurrencyError, ValidationError


class TestAmountValidator:
    """Test amount validation"""

    def test_valid_amount(self):
        """Valid amounts should not raise"""
        validate_amount(Decimal("100.00"))
        validate_amount(Decimal("0.01"))
        validate_amount(Decimal("999999.99"))

    def test_zero_amount(self):
        """Zero amount should raise error"""
        with pytest.raises(InvalidAmountError):
            validate_amount(Decimal("0.00"))

    def test_negative_amount(self):
        """Negative amount should raise error"""
        with pytest.raises(InvalidAmountError):
            validate_amount(Decimal("-10.00"))

    def test_too_many_decimals(self):
        """More than 2 decimal places should raise error"""
        with pytest.raises(InvalidAmountError):
            validate_amount(Decimal("10.123"))

    def test_min_amount(self):
        """Amount below minimum should raise error"""
        with pytest.raises(InvalidAmountError):
            validate_amount(Decimal("5.00"), min_amount=Decimal("10.00"))


class TestCurrencyValidator:
    """Test currency validation"""

    def test_valid_currencies(self):
        """Valid currency codes should not raise"""
        for currency in ["USD", "EUR", "GBP", "JPY"]:
            validate_currency(currency)

    def test_invalid_length(self):
        """Invalid length should raise error"""
        with pytest.raises(InvalidCurrencyError):
            validate_currency("US")

    def test_unsupported_currency(self):
        """Unsupported currency should raise error"""
        with pytest.raises(InvalidCurrencyError):
            validate_currency("XYZ")


class TestRoutingNumberValidator:
    """Test routing number validation"""

    def test_valid_routing_number(self):
        """Valid routing number should not raise"""
        validate_routing_number("121000248")

    def test_invalid_length(self):
        """Invalid length should raise error"""
        with pytest.raises(ValidationError):
            validate_routing_number("12345678")

    def test_invalid_checksum(self):
        """Invalid checksum should raise error"""
        with pytest.raises(ValidationError):
            validate_routing_number("123456789")


class TestSwiftCodeValidator:
    """Test SWIFT code validation"""

    def test_valid_8_char(self):
        """Valid 8 character SWIFT code"""
        validate_swift_code("DEUTDEFF")

    def test_valid_11_char(self):
        """Valid 11 character SWIFT code"""
        validate_swift_code("DEUTDEFF500")

    def test_invalid_length(self):
        """Invalid length should raise error"""
        with pytest.raises(ValidationError):
            validate_swift_code("DEUT")

    def test_invalid_format(self):
        """Invalid format should raise error"""
        with pytest.raises(ValidationError):
            validate_swift_code("1234DEFF")
```

---

## Integration Tests

### What to Test

- Service + Repository + Formance SDK interaction
- Database operations (if using PostgreSQL)
- External API calls (mocked or sandboxed)
- Error handling across layers

### Setup Requirements

```python
# tests/integration/conftest.py
import pytest
import asyncio
from httpx import AsyncClient

from core.client import FormanceBankingClient
from core.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Test settings using sandbox environment"""
    return Settings(
        formance_base_url="https://sandbox.formance.cloud",
        formance_client_id="test_client_id",
        formance_client_secret="test_client_secret",
        environment="test",
    )


@pytest.fixture
async def formance_client(test_settings):
    """Real Formance client for integration tests"""
    client = FormanceBankingClient(
        base_url=test_settings.formance_base_url,
        client_id=test_settings.formance_client_id,
        client_secret=test_settings.formance_client_secret,
    )
    yield client
    await client.close()
```

### Example: Integration Test for Account Flow

```python
# tests/integration/test_account_flows.py
import pytest
from decimal import Decimal

from core.repositories.formance import FormanceRepository
from core.services.accounts import AccountService
from core.models.account import AccountType


@pytest.mark.integration
@pytest.mark.asyncio
class TestAccountIntegration:
    """Integration tests for account operations"""

    async def test_create_and_get_account(self, formance_client):
        """Test creating and retrieving an account"""
        # Arrange
        repository = FormanceRepository(formance_client)
        service = AccountService(repository)
        customer_id = f"test_customer_{pytest.timestamp}"

        # Act - Create account
        account = await service.create_account(
            customer_id=customer_id,
            account_type=AccountType.CHECKING,
            currency="USD",
        )

        # Assert - Account created
        assert account.id is not None
        assert account.customer_id == customer_id
        assert account.balance == Decimal("0")

        # Act - Get account
        retrieved_account = await service.get_account(account.id)

        # Assert - Same account retrieved
        assert retrieved_account.id == account.id
        assert retrieved_account.customer_id == customer_id

    async def test_account_lifecycle(self, formance_client):
        """Test complete account lifecycle"""
        repository = FormanceRepository(formance_client)
        service = AccountService(repository)
        customer_id = f"test_customer_{pytest.timestamp}"

        # Create account
        account = await service.create_account(
            customer_id=customer_id,
            account_type=AccountType.CHECKING,
            currency="USD",
        )

        # Freeze account
        frozen = await service.freeze_account(
            account.id,
            reason="Suspicious activity"
        )
        assert frozen.is_frozen()

        # Close account (requires zero balance)
        closed = await service.close_account(account.id)
        assert closed.status == "closed"
```

### Example: Integration Test for Transaction Flow

```python
# tests/integration/test_transaction_flows.py
import pytest
from decimal import Decimal

from core.repositories.formance import FormanceRepository
from core.services.accounts import AccountService
from core.services.transactions import TransactionService
from core.models.account import AccountType
from core.models.transaction import TransactionType


@pytest.mark.integration
@pytest.mark.asyncio
class TestTransactionIntegration:
    """Integration tests for transaction operations"""

    async def test_deposit_and_balance(self, formance_client):
        """Test deposit updates balance correctly"""
        # Arrange
        repository = FormanceRepository(formance_client)
        account_service = AccountService(repository)
        txn_service = TransactionService(repository)

        account = await account_service.create_account(
            customer_id=f"test_customer_{pytest.timestamp}",
            account_type=AccountType.CHECKING,
            currency="USD",
        )

        # Act - Deposit
        deposit_amount = Decimal("1000.00")
        transaction = await txn_service.deposit(
            to_account_id=account.id,
            amount=deposit_amount,
            currency="USD",
        )

        # Assert
        assert transaction.transaction_type == TransactionType.DEPOSIT
        assert transaction.amount == deposit_amount

        # Verify balance updated
        balance = await account_service.get_balance(account.id)
        assert balance == deposit_amount

    async def test_transfer_between_accounts(self, formance_client):
        """Test transfer between two accounts"""
        # Arrange
        repository = FormanceRepository(formance_client)
        account_service = AccountService(repository)
        txn_service = TransactionService(repository)

        # Create two accounts
        account1 = await account_service.create_account(
            customer_id=f"alice_{pytest.timestamp}",
            account_type=AccountType.CHECKING,
            currency="USD",
        )
        account2 = await account_service.create_account(
            customer_id=f"bob_{pytest.timestamp}",
            account_type=AccountType.CHECKING,
            currency="USD",
        )

        # Deposit to account1
        await txn_service.deposit(
            to_account_id=account1.id,
            amount=Decimal("1000.00"),
            currency="USD",
        )

        # Act - Transfer
        transfer_amount = Decimal("250.00")
        transfer = await txn_service.transfer(
            from_account_id=account1.id,
            to_account_id=account2.id,
            amount=transfer_amount,
            currency="USD",
        )

        # Assert
        assert transfer.transaction_type == TransactionType.TRANSFER
        assert transfer.amount == transfer_amount

        # Verify balances
        balance1 = await account_service.get_balance(account1.id)
        balance2 = await account_service.get_balance(account2.id)

        assert balance1 == Decimal("750.00")
        assert balance2 == Decimal("250.00")

    async def test_transaction_history(self, formance_client):
        """Test retrieving transaction history"""
        # Arrange
        repository = FormanceRepository(formance_client)
        account_service = AccountService(repository)
        txn_service = TransactionService(repository)

        account = await account_service.create_account(
            customer_id=f"test_customer_{pytest.timestamp}",
            account_type=AccountType.CHECKING,
            currency="USD",
        )

        # Create multiple transactions
        await txn_service.deposit(account.id, Decimal("1000.00"), "USD")
        await txn_service.withdraw(account.id, Decimal("100.00"), "USD")
        await txn_service.deposit(account.id, Decimal("500.00"), "USD")

        # Act
        transactions = await txn_service.list_account_transactions(
            account_id=account.id,
            limit=10,
            offset=0,
        )

        # Assert
        assert len(transactions) == 3
        assert transactions[0].transaction_type == TransactionType.DEPOSIT
```

---

## End-to-End Tests

### What to Test

- Complete API workflows
- User journeys
- Error scenarios
- Authentication flows

### Example: E2E Test for Complete User Journey

```python
# tests/e2e/test_complete_flows.py
import pytest
from httpx import AsyncClient
from decimal import Decimal

from core.api.app import app


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCompleteUserJourney:
    """End-to-end tests for complete user journeys"""

    async def test_customer_onboarding_and_first_transaction(self):
        """Test complete flow from customer creation to first transaction"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Step 1: Create customer
            customer_response = await client.post(
                "/api/v1/customers",
                json={
                    "email": "john.doe@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "phone": "+1234567890",
                },
                headers={"Authorization": "Bearer test_token"},
            )
            assert customer_response.status_code == 201
            customer = customer_response.json()
            customer_id = customer["id"]

            # Step 2: Create checking account
            account_response = await client.post(
                "/api/v1/accounts",
                json={
                    "customer_id": customer_id,
                    "account_type": "checking",
                    "currency": "USD",
                },
                headers={"Authorization": "Bearer test_token"},
            )
            assert account_response.status_code == 201
            account = account_response.json()
            account_id = account["id"]

            # Step 3: Make initial deposit
            deposit_response = await client.post(
                "/api/v1/transactions/deposit",
                json={
                    "to_account_id": account_id,
                    "amount": 1000.00,
                    "currency": "USD",
                    "description": "Initial deposit",
                },
                headers={"Authorization": "Bearer test_token"},
            )
            assert deposit_response.status_code == 201

            # Step 4: Check balance
            balance_response = await client.get(
                f"/api/v1/accounts/{account_id}/balance",
                headers={"Authorization": "Bearer test_token"},
            )
            assert balance_response.status_code == 200
            balance = balance_response.json()
            assert Decimal(str(balance["balance"])) == Decimal("1000.00")

            # Step 5: Get transaction history
            history_response = await client.get(
                f"/api/v1/transactions/account/{account_id}",
                headers={"Authorization": "Bearer test_token"},
            )
            assert history_response.status_code == 200
            transactions = history_response.json()
            assert len(transactions) >= 1

    async def test_transfer_between_customers(self):
        """Test transfer between two customers"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create two customers and accounts
            # ... (similar setup as above)

            # Transfer between accounts
            transfer_response = await client.post(
                "/api/v1/transactions/transfer",
                json={
                    "from_account_id": account1_id,
                    "to_account_id": account2_id,
                    "amount": 250.00,
                    "currency": "USD",
                    "description": "Payment to Bob",
                },
                headers={"Authorization": "Bearer test_token"},
            )
            assert transfer_response.status_code == 201

            # Verify both balances updated
            # ... (balance checks)
```

---

## Testing Best Practices

### 1. Test Naming Convention

```python
def test_<what>_<condition>_<expected_result>():
    """
    Good:
    - test_deposit_valid_amount_increases_balance()
    - test_transfer_insufficient_funds_raises_error()
    - test_create_account_duplicate_email_returns_400()

    Bad:
    - test_deposit()
    - test_error()
    - test_account_creation()
    """
    pass
```

### 2. AAA Pattern (Arrange, Act, Assert)

```python
async def test_transfer_success():
    # Arrange - Set up test data
    from_account = create_test_account()
    to_account = create_test_account()
    amount = Decimal("100.00")

    # Act - Execute the operation
    result = await service.transfer(from_account, to_account, amount)

    # Assert - Verify the outcome
    assert result.status == "completed"
    assert result.amount == amount
```

### 3. Use Fixtures for Common Setup

```python
@pytest.fixture
def customer_with_account():
    """Fixture providing customer with checking account"""
    customer = create_customer()
    account = create_account(customer.id, AccountType.CHECKING)
    return {"customer": customer, "account": account}


def test_deposit(customer_with_account):
    account = customer_with_account["account"]
    # Test deposit logic
```

### 4. Parametrize for Multiple Scenarios

```python
@pytest.mark.parametrize("amount,expected_error", [
    (Decimal("-10.00"), InvalidAmountError),
    (Decimal("0.00"), InvalidAmountError),
    (Decimal("10.123"), InvalidAmountError),
])
def test_invalid_amounts(amount, expected_error):
    with pytest.raises(expected_error):
        validate_amount(amount)
```

### 5. Test Error Messages

```python
def test_insufficient_funds_error_message():
    with pytest.raises(InsufficientFundsError) as exc_info:
        # ... trigger error

    assert "Insufficient funds" in str(exc_info.value)
    assert "Balance: 50.00" in str(exc_info.value)
    assert "Required: 100.00" in str(exc_info.value)
```

---

## Mocking Strategies

### Mock External Dependencies

```python
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_formance_sdk():
    """Mock Formance SDK responses"""
    with patch("core.client.SDK") as mock_sdk:
        mock_sdk.ledger.v2.create_transaction_async.return_value = AsyncMock(
            data=Mock(id=123, postings=[...])
        )
        yield mock_sdk
```

### Mock Repository Layer

```python
@pytest.fixture
def mock_repository():
    """Mock repository for service tests"""
    repo = AsyncMock()
    repo.create_ledger_account.return_value = {...}
    repo.get_account_balance.return_value = Decimal("1000.00")
    return repo
```

### Partial Mocking

```python
def test_with_partial_mock():
    """Mock only specific methods"""
    service = AccountService(real_repository)

    with patch.object(service, '_validate_customer') as mock_validate:
        mock_validate.return_value = True
        # Test logic
```

---

## Test Data Management

### Use Factories

```python
# tests/factories.py
from decimal import Decimal
from faker import Faker

fake = Faker()


def create_test_customer(**kwargs):
    """Create test customer data"""
    return {
        "id": kwargs.get("id", f"cust_{fake.uuid4()}"),
        "email": kwargs.get("email", fake.email()),
        "first_name": kwargs.get("first_name", fake.first_name()),
        "last_name": kwargs.get("last_name", fake.last_name()),
        "phone": kwargs.get("phone", fake.phone_number()),
    }


def create_test_account(customer_id, account_type=AccountType.CHECKING, **kwargs):
    """Create test account data"""
    return {
        "id": kwargs.get("id", f"customers:{customer_id}:{account_type.value}"),
        "customer_id": customer_id,
        "account_type": account_type,
        "currency": kwargs.get("currency", "USD"),
        "balance": kwargs.get("balance", Decimal("0")),
        "status": kwargs.get("status", "active"),
    }
```

### Use Fixtures for Test Data

```python
@pytest.fixture
def sample_customer_data():
    return create_test_customer()


@pytest.fixture
def sample_account_data(sample_customer_data):
    return create_test_account(sample_customer_data["id"])
```

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Types

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v

# Run by marker
pytest -m unit
pytest -m integration
pytest -m e2e
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=core --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Run specific file
pytest tests/unit/test_services/test_account_service.py

# Run specific test
pytest tests/unit/test_services/test_account_service.py::TestAccountService::test_create_account_success

# Run tests matching pattern
pytest -k "account"
```

### Run with Different Verbosity

```bash
# Quiet mode
pytest -q

# Verbose mode
pytest -v

# Very verbose mode
pytest -vv
```

### Run Failed Tests Only

```bash
# Run last failed tests
pytest --lf

# Run last failed, then all
pytest --ff
```

### Parallel Execution

```bash
# Install pytest-xdist
uv add pytest-xdist --group dev

# Run tests in parallel
pytest -n auto
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=core

      - name: Run integration tests
        run: pytest tests/integration/ -v
        env:
          FORMANCE_BASE_URL: ${{ secrets.FORMANCE_SANDBOX_URL }}
          FORMANCE_CLIENT_ID: ${{ secrets.FORMANCE_TEST_CLIENT_ID }}
          FORMANCE_CLIENT_SECRET: ${{ secrets.FORMANCE_TEST_CLIENT_SECRET }}

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Common Testing Patterns

### Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

### Testing Exceptions

```python
def test_raises_exception():
    with pytest.raises(CustomException) as exc_info:
        function_that_raises()

    assert "error message" in str(exc_info.value)
```

### Testing With Timeouts

```python
@pytest.mark.timeout(5)
async def test_with_timeout():
    # Test must complete in 5 seconds
    await slow_operation()
```

### Cleanup After Tests

```python
@pytest.fixture
async def test_account():
    # Setup
    account = await create_test_account()

    yield account

    # Cleanup
    await delete_test_account(account.id)
```

---

## Summary Checklist

### Before Writing Tests
- [ ] Understand what you're testing
- [ ] Identify test boundaries (unit/integration/e2e)
- [ ] Determine what to mock vs. what to test real

### Writing Tests
- [ ] Use descriptive test names
- [ ] Follow AAA pattern
- [ ] Test both success and failure cases
- [ ] Test edge cases
- [ ] Use fixtures for setup
- [ ] Mock external dependencies

### After Writing Tests
- [ ] Run tests locally
- [ ] Check coverage
- [ ] Review test quality
- [ ] Update documentation

### Code Coverage Goals
- [ ] **80%+ overall coverage**
- [ ] **90%+ for services layer**
- [ ] **100% for critical paths** (money movement)

---

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)
- [Example Tests](../tests/)

Happy Testing! 🧪
