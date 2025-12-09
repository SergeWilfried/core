# Developer Testing Quick Reference

Quick guide for developers to start writing and running tests.

## Table of Contents

- [Quick Start](#quick-start)
- [Test Types](#test-types)
- [Writing Your First Test](#writing-your-first-test)
- [Using Fixtures](#using-fixtures)
- [Running Tests](#running-tests)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Install Dependencies

```bash
uv sync --group dev
```

### 2. Run Tests

```bash
# All tests
pytest

# With output
pytest -v

# Specific test file
pytest tests/unit/test_validators.py

# Specific test
pytest tests/unit/test_validators.py::test_valid_amount
```

### 3. Check Coverage

```bash
pytest --cov=core --cov-report=html
open htmlcov/index.html
```

---

## Test Types

### Unit Tests (tests/unit/)
**What**: Test individual functions/methods in isolation
**Speed**: Very fast (< 0.01s each)
**Dependencies**: Mocked
**When**: Always write these first

```python
@pytest.mark.unit
def test_validate_amount():
    # Test a single validator function
    validate_amount(Decimal("100.00"))  # Should not raise
```

### Integration Tests (tests/integration/)
**What**: Test service + repository + Formance SDK
**Speed**: Slower (0.1-1s each)
**Dependencies**: Real Formance sandbox
**When**: After implementing repository layer

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_account(formance_client):
    # Test with real Formance API
    repository = FormanceRepository(formance_client)
    service = AccountService(repository)
    account = await service.create_account(...)
```

### E2E Tests (tests/e2e/)
**What**: Test complete API flows
**Speed**: Slowest (1-5s each)
**Dependencies**: Full API + Formance
**When**: For critical user journeys

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_customer_onboarding():
    # Test complete flow via API
    async with AsyncClient(app=app) as client:
        response = await client.post("/api/v1/customers", ...)
```

---

## Writing Your First Test

### Unit Test Example

```python
# tests/unit/test_services/test_my_service.py
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from core.services.accounts import AccountService
from core.models.account import AccountType
from tests.factories import AccountFactory

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_account(mock_formance_repository):
    """Test creating an account"""
    # Arrange - Set up test data and mocks
    service = AccountService(mock_formance_repository)
    customer_id = "cust_123"

    mock_formance_repository.create_ledger_account.return_value = AccountFactory.create_dict(
        customer_id=customer_id
    )

    # Act - Execute the operation
    account = await service.create_account(
        customer_id=customer_id,
        account_type=AccountType.CHECKING,
        currency="USD",
    )

    # Assert - Verify the outcome
    assert account.customer_id == customer_id
    assert account.account_type == AccountType.CHECKING
    mock_formance_repository.create_ledger_account.assert_called_once()
```

### Integration Test Example

```python
# tests/integration/test_account_integration.py
import pytest
from decimal import Decimal

from core.repositories.formance import FormanceRepository
from core.services.accounts import AccountService
from core.models.account import AccountType

@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_creation_end_to_end(formance_client):
    """Test account creation with real Formance"""
    # Arrange
    repository = FormanceRepository(formance_client)
    service = AccountService(repository)

    # Act
    account = await service.create_account(
        customer_id="test_customer_123",
        account_type=AccountType.CHECKING,
        currency="USD",
    )

    # Assert
    assert account.id is not None
    balance = await service.get_balance(account.id)
    assert balance == Decimal("0")
```

---

## Using Fixtures

### Available Fixtures

```python
def test_with_fixtures(
    sample_customer,          # Pre-made customer object
    sample_account,           # Pre-made account object
    mock_formance_repository, # Mocked repository
    account_factory,          # Factory to create test accounts
):
    # Use fixtures in your test
    assert sample_customer.id is not None

    # Create custom test data
    account = account_factory.create(
        customer_id=sample_customer.id,
        balance=Decimal("1000.00")
    )
```

### Common Fixtures

| Fixture | Description | Usage |
|---------|-------------|-------|
| `sample_customer` | Customer object | Direct use |
| `sample_account` | Account object | Direct use |
| `customer_factory` | Create customers | `CustomerFactory.create()` |
| `account_factory` | Create accounts | `AccountFactory.create()` |
| `mock_formance_repository` | Mocked repo | Unit tests |
| `formance_client` | Real client | Integration tests |

### Creating Test Data

```python
# Using factories
from tests.factories import CustomerFactory, AccountFactory

# Create a customer
customer = CustomerFactory.create(
    email="test@example.com",
    first_name="Alice"
)

# Create an account with balance
account = AccountFactory.create_with_balance(
    customer_id=customer.id,
    balance=Decimal("1000.00")
)

# Create as dictionary (for mocks)
account_dict = AccountFactory.create_dict()
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test type
pytest -m unit
pytest -m integration
pytest -m e2e

# Run specific file
pytest tests/unit/test_validators.py

# Run specific test function
pytest tests/unit/test_validators.py::test_valid_amount

# Run tests matching pattern
pytest -k "account"
```

### Coverage

```bash
# Generate coverage report
pytest --cov=core

# With HTML report
pytest --cov=core --cov-report=html

# View coverage
open htmlcov/index.html
```

### Parallel Execution

```bash
# Run tests in parallel (faster)
pytest -n auto
```

### Watch Mode (during development)

```bash
# Install pytest-watch
uv add pytest-watch --group dev

# Run in watch mode
ptw
```

---

## Common Patterns

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await my_async_function()
    assert result == expected
```

### Testing Exceptions

```python
def test_raises_error():
    with pytest.raises(InsufficientFundsError) as exc_info:
        validate_amount(Decimal("-10.00"))

    assert "must be greater than zero" in str(exc_info.value)
```

### Parametrized Tests

```python
@pytest.mark.parametrize("amount,should_raise", [
    (Decimal("100.00"), False),
    (Decimal("-10.00"), True),
    (Decimal("0.00"), True),
])
def test_amount_validation(amount, should_raise):
    if should_raise:
        with pytest.raises(InvalidAmountError):
            validate_amount(amount)
    else:
        validate_amount(amount)  # Should not raise
```

### Mocking Repository Methods

```python
@pytest.mark.asyncio
async def test_with_mock(mock_formance_repository):
    # Setup mock return value
    mock_formance_repository.get_account_balance.return_value = Decimal("1000.00")

    # Use the mock
    service = AccountService(mock_formance_repository)
    balance = await service.get_balance("acc_123")

    # Verify
    assert balance == Decimal("1000.00")
    mock_formance_repository.get_account_balance.assert_called_once_with("acc_123")
```

### Testing API Endpoints

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_api_endpoint():
    from httpx import AsyncClient
    from core.api.app import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/accounts",
            json={"customer_id": "cust_123", "account_type": "checking"},
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == "cust_123"
```

---

## Troubleshooting

### Common Issues

#### "ImportError: No module named 'core'"

**Solution**: Run pytest from project root:
```bash
cd /path/to/project/root
pytest
```

#### "Event loop is closed"

**Solution**: Use `@pytest.mark.asyncio` decorator:
```python
@pytest.mark.asyncio
async def test_my_async_function():
    ...
```

#### "Fixture not found"

**Solution**: Make sure fixture is defined in `conftest.py` or imported:
```python
# Check tests/conftest.py for fixture definitions
```

#### Tests are slow

**Solution**:
1. Run only unit tests: `pytest -m unit`
2. Use parallel execution: `pytest -n auto`
3. Check if you're accidentally running integration tests

#### Mock not working

**Solution**: Check that you're mocking the right location:
```python
# Mock where it's used, not where it's defined
@patch('core.services.accounts.FormanceRepository')
def test_with_mock(mock_repo):
    ...
```

### Debug Tips

```bash
# Run with print statements visible
pytest -s

# Drop into debugger on failure
pytest --pdb

# Run last failed tests
pytest --lf

# See full diff on assertion failure
pytest -vv
```

---

## Best Practices

### ✅ DO

- Write unit tests for all business logic
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Use factories for test data
- Mock external dependencies
- Test both success and error cases
- Keep tests independent
- Run tests before committing

### ❌ DON'T

- Test framework code (FastAPI, Pydantic)
- Test external libraries (Formance SDK)
- Make tests depend on each other
- Use real API calls in unit tests
- Hardcode test data
- Skip testing error cases
- Commit failing tests

---

## Quick Reference Card

```bash
# Run tests
pytest                    # All tests
pytest -v                 # Verbose
pytest -m unit           # Unit tests only
pytest -k "account"      # Tests matching pattern

# Coverage
pytest --cov=core                    # Coverage report
pytest --cov=core --cov-report=html  # HTML report

# Debug
pytest -s                # Show print output
pytest --pdb            # Debug on failure
pytest -vv              # Very verbose

# Speed
pytest -n auto          # Parallel execution
pytest -m unit          # Fast tests only

# Specific tests
pytest tests/unit/test_file.py              # File
pytest tests/unit/test_file.py::test_name   # Specific test
```

---

## Next Steps

1. **Read**: [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive guide
2. **Study**: Existing tests in `tests/unit/test_models.py`
3. **Practice**: Write tests for a new service method
4. **Review**: Check your coverage with `pytest --cov=core`

Happy Testing! 🧪
