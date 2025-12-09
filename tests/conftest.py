"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

from core.client import FormanceBankingClient
from core.config import Settings
from core.repositories.formance import FormanceRepository
from core.services import (
    AccountService,
    TransactionService,
    PaymentService,
    CustomerService,
    CardService,
    LedgerService,
)
from tests.factories import (
    CustomerFactory,
    AccountFactory,
    TransactionFactory,
    PaymentFactory,
    CardFactory,
)


# ========================================
# Pytest Configuration
# ========================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (uses Formance sandbox)"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test (full API flow)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (may take >1 second)"
    )


# ========================================
# Event Loop
# ========================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ========================================
# Configuration
# ========================================

@pytest.fixture(scope="session")
def test_settings():
    """Test settings"""
    return Settings(
        app_name="BaaS Core Banking Test",
        environment="test",
        debug=True,
        formance_base_url=os.getenv(
            "FORMANCE_TEST_BASE_URL",
            "https://sandbox.formance.cloud"
        ),
        formance_client_id=os.getenv("FORMANCE_TEST_CLIENT_ID", "test_client_id"),
        formance_client_secret=os.getenv("FORMANCE_TEST_CLIENT_SECRET", "test_secret"),
    )


# ========================================
# Formance Client & Repository
# ========================================

@pytest.fixture
async def formance_client(test_settings) -> AsyncGenerator[FormanceBankingClient, None]:
    """Fixture for Formance client (integration tests)"""
    client = FormanceBankingClient(
        base_url=test_settings.formance_base_url,
        client_id=test_settings.formance_client_id,
        client_secret=test_settings.formance_client_secret,
    )
    yield client
    await client.close()


@pytest.fixture
def mock_formance_client():
    """Mock Formance client for unit tests"""
    client = AsyncMock(spec=FormanceBankingClient)
    client.sdk = Mock()
    return client


@pytest.fixture
def formance_repository(formance_client: FormanceBankingClient) -> FormanceRepository:
    """Fixture for Formance repository (integration tests)"""
    return FormanceRepository(formance_client)


@pytest.fixture
def mock_formance_repository():
    """Mock Formance repository for unit tests"""
    return AsyncMock(spec=FormanceRepository)


# ========================================
# Services (Real)
# ========================================

@pytest.fixture
def account_service(formance_repository: FormanceRepository) -> AccountService:
    """Fixture for Account service"""
    return AccountService(formance_repository)


@pytest.fixture
def transaction_service(formance_repository: FormanceRepository) -> TransactionService:
    """Fixture for Transaction service"""
    return TransactionService(formance_repository)


@pytest.fixture
def payment_service(formance_repository: FormanceRepository) -> PaymentService:
    """Fixture for Payment service"""
    return PaymentService(formance_repository)


@pytest.fixture
def customer_service(formance_repository: FormanceRepository) -> CustomerService:
    """Fixture for Customer service"""
    return CustomerService(formance_repository)


@pytest.fixture
def card_service(formance_repository: FormanceRepository) -> CardService:
    """Fixture for Card service"""
    return CardService(formance_repository)


@pytest.fixture
def ledger_service(formance_repository: FormanceRepository) -> LedgerService:
    """Fixture for Ledger service"""
    return LedgerService(formance_repository)


# ========================================
# Services (Mocked)
# ========================================

@pytest.fixture
def mock_account_service(mock_formance_repository):
    """Mock Account service for unit tests"""
    return AccountService(mock_formance_repository)


@pytest.fixture
def mock_transaction_service(mock_formance_repository):
    """Mock Transaction service for unit tests"""
    return TransactionService(mock_formance_repository)


@pytest.fixture
def mock_payment_service(mock_formance_repository):
    """Mock Payment service for unit tests"""
    return PaymentService(mock_formance_repository)


@pytest.fixture
def mock_customer_service(mock_formance_repository):
    """Mock Customer service for unit tests"""
    return CustomerService(mock_formance_repository)


# ========================================
# Test Data Factories
# ========================================

@pytest.fixture
def customer_factory():
    """Customer factory"""
    return CustomerFactory


@pytest.fixture
def account_factory():
    """Account factory"""
    return AccountFactory


@pytest.fixture
def transaction_factory():
    """Transaction factory"""
    return TransactionFactory


@pytest.fixture
def payment_factory():
    """Payment factory"""
    return PaymentFactory


@pytest.fixture
def card_factory():
    """Card factory"""
    return CardFactory


# ========================================
# Sample Test Data
# ========================================

@pytest.fixture
def sample_customer():
    """Sample customer object"""
    return CustomerFactory.create()


@pytest.fixture
def sample_customer_dict():
    """Sample customer as dictionary"""
    return CustomerFactory.create_dict()


@pytest.fixture
def sample_account(sample_customer):
    """Sample account object"""
    return AccountFactory.create(customer_id=sample_customer.id)


@pytest.fixture
def sample_account_dict(sample_customer):
    """Sample account as dictionary"""
    return AccountFactory.create_dict(customer_id=sample_customer.id)


@pytest.fixture
def sample_account_with_balance():
    """Sample account with balance"""
    return AccountFactory.create_with_balance(Decimal("1000.00"))


@pytest.fixture
def sample_transaction():
    """Sample transaction object"""
    return TransactionFactory.create()


@pytest.fixture
def sample_transaction_dict():
    """Sample transaction as dictionary"""
    return TransactionFactory.create_dict()


@pytest.fixture
def sample_payment():
    """Sample payment object"""
    return PaymentFactory.create()


@pytest.fixture
def sample_payment_dict():
    """Sample payment as dictionary"""
    return PaymentFactory.create_dict()


@pytest.fixture
def sample_card():
    """Sample card object"""
    return CardFactory.create()


@pytest.fixture
def sample_card_dict():
    """Sample card as dictionary"""
    return CardFactory.create_dict()


# ========================================
# Common Test Scenarios
# ========================================

@pytest.fixture
def customer_with_accounts(sample_customer):
    """Customer with checking and savings accounts"""
    from core.models.account import AccountType

    checking = AccountFactory.create(
        customer_id=sample_customer.id,
        account_type=AccountType.CHECKING,
        balance=Decimal("1000.00"),
    )
    savings = AccountFactory.create(
        customer_id=sample_customer.id,
        account_type=AccountType.SAVINGS,
        balance=Decimal("5000.00"),
    )

    return {
        "customer": sample_customer,
        "checking": checking,
        "savings": savings,
    }


@pytest.fixture
def two_customers_with_accounts():
    """Two customers each with a checking account"""
    alice = CustomerFactory.create(first_name="Alice")
    bob = CustomerFactory.create(first_name="Bob")

    alice_account = AccountFactory.create(
        customer_id=alice.id,
        balance=Decimal("1000.00"),
    )
    bob_account = AccountFactory.create(
        customer_id=bob.id,
        balance=Decimal("500.00"),
    )

    return {
        "alice": alice,
        "bob": bob,
        "alice_account": alice_account,
        "bob_account": bob_account,
    }


# ========================================
# API Testing
# ========================================

@pytest.fixture
def api_headers():
    """Standard API headers for testing"""
    return {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json",
    }


@pytest.fixture
def api_client():
    """HTTP client for API testing"""
    from httpx import AsyncClient
    from core.api.app import app

    async def _client():
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    return _client


# ========================================
# Cleanup Helpers
# ========================================

@pytest.fixture
def cleanup_list():
    """List of resources to cleanup after test"""
    resources = []

    yield resources

    # Cleanup happens automatically after test
    # Can be extended with actual cleanup logic if needed


# ========================================
# Assertion Helpers
# ========================================

@pytest.fixture
def assert_decimal_equal():
    """Helper to assert decimal equality"""
    def _assert(actual: Decimal, expected: Decimal, places: int = 2):
        assert round(actual, places) == round(expected, places)

    return _assert
