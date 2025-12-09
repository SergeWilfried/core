# Formance Integration Implementation Guide

This guide explains how to implement the actual Formance SDK integration in the repository layer.

## Overview

The Formance SDK provides several modules for banking operations:

1. **Ledger (v2)**: Double-entry bookkeeping, accounts, transactions
2. **Payments (v1)**: Payment processing, connectors
3. **Wallets (v1)**: Wallet management
4. **Auth (v1)**: Authentication and authorization

## Architecture Flow

```
API Layer (FastAPI)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Formance SDK Integration) ← YOU ARE HERE
    ↓
FormanceBankingClient (SDK Wrapper)
    ↓
Formance API
```

## Implementation Strategy

### Step 1: Understanding Formance Ledger Structure

Formance uses a **double-entry bookkeeping** system with:

- **Ledgers**: Isolated accounting environments
- **Accounts**: Account addresses (e.g., `users:john`, `bank:main`)
- **Transactions**: Postings that move money between accounts
- **Metadata**: Additional data attached to objects

#### Account Naming Convention

```
{namespace}:{identifier}
```

Examples:
- `customers:cust_123:checking` - Customer checking account
- `customers:cust_123:savings` - Customer savings account
- `bank:fees` - Bank fee collection account
- `bank:reserve` - Bank reserve account
- `world` - Special account representing external world (for deposits/withdrawals)
```

### Step 2: Ledger Operations Implementation

#### Create a Ledger (One-time setup)

```python
async def create_ledger(self, name: str, metadata: dict) -> dict:
    """Create a new ledger"""
    try:
        response = await self.client.sdk.ledger.v2.create_ledger_async(
            ledger=name,
            request_body={
                "metadata": metadata
            }
        )

        return {
            "id": response.data.name if response.data else name,
            "name": name,
            "metadata": metadata,
        }
    except Exception as e:
        logger.error(f"Failed to create ledger: {e}")
        raise FormanceAPIError(f"Ledger creation failed: {e}")
```

#### Create an Account via Transaction

In Formance, accounts are created implicitly through transactions. Here's how:

```python
async def create_ledger_account(
    self,
    customer_id: str,
    account_type: AccountType,
    currency: str,
    metadata: dict,
) -> dict:
    """Create an account in Formance ledger"""

    # Account address format: customers:{customer_id}:{account_type}
    account_address = f"customers:{customer_id}:{account_type.value}"
    ledger_name = "main"  # Your default ledger name

    try:
        # Create initial transaction to establish the account
        # This is a zero-value transaction that creates the account with metadata
        response = await self.client.sdk.ledger.v2.create_transaction_async(
            ledger=ledger_name,
            request_body={
                "metadata": {
                    "customer_id": customer_id,
                    "account_type": account_type.value,
                    "currency": currency,
                    "status": "active",
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

        # Return account data in our expected format
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

    except Exception as e:
        logger.error(f"Failed to create account: {e}")
        raise FormanceAPIError(f"Account creation failed: {e}")
```

#### Get Account Balance

```python
async def get_account_balance(self, account_id: str) -> Decimal:
    """Get account balance"""
    ledger_name = "main"

    try:
        response = await self.client.sdk.ledger.v2.get_account_async(
            ledger=ledger_name,
            address=account_id,
        )

        if response.data and response.data.balances:
            # Balances are returned as {currency: amount}
            # For simplicity, we assume single currency per account
            for currency, balance in response.data.balances.items():
                return Decimal(str(balance))

        return Decimal("0")

    except Exception as e:
        logger.error(f"Failed to get balance for {account_id}: {e}")
        raise FormanceAPIError(f"Balance retrieval failed: {e}")
```

#### Get Account Details

```python
async def get_account(self, account_id: str) -> Optional[dict]:
    """Get account by ID"""
    ledger_name = "main"

    try:
        response = await self.client.sdk.ledger.v2.get_account_async(
            ledger=ledger_name,
            address=account_id,
        )

        if not response.data:
            return None

        account = response.data
        metadata = account.metadata or {}

        # Extract balance
        balance = Decimal("0")
        if account.balances:
            for currency, amount in account.balances.items():
                balance = Decimal(str(amount))
                break  # Take first currency

        return {
            "id": account.address,
            "customer_id": metadata.get("customer_id"),
            "account_type": metadata.get("account_type"),
            "currency": list(account.balances.keys())[0] if account.balances else "USD",
            "balance": balance,
            "available_balance": balance,  # TODO: Calculate holds
            "status": metadata.get("status", "active"),
            "metadata": metadata,
        }

    except Exception as e:
        logger.error(f"Failed to get account {account_id}: {e}")
        return None
```

### Step 3: Transaction Operations

#### Create a Transaction (Transfer)

```python
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
    ledger_name = "main"

    # Determine source and destination based on transaction type
    if transaction_type == TransactionType.DEPOSIT:
        source = "world"
        destination = to_account
    elif transaction_type == TransactionType.WITHDRAWAL:
        source = from_account
        destination = "world"
    elif transaction_type == TransactionType.TRANSFER:
        source = from_account
        destination = to_account
    else:
        source = from_account or "world"
        destination = to_account or "world"

    try:
        response = await self.client.sdk.ledger.v2.create_transaction_async(
            ledger=ledger_name,
            request_body={
                "metadata": {
                    "transaction_type": transaction_type.value,
                    "description": description,
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
                "reference": metadata.get("reference"),
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
        }

    except Exception as e:
        logger.error(f"Failed to create transaction: {e}")
        raise FormanceAPIError(f"Transaction failed: {e}")
```

#### List Account Transactions

```python
async def list_transactions(
    self,
    account_id: str,
    limit: int,
    offset: int
) -> list[dict]:
    """List transactions for account"""
    ledger_name = "main"

    try:
        response = await self.client.sdk.ledger.v2.list_transactions_async(
            ledger=ledger_name,
            account=account_id,
            page_size=limit,
            # Note: Formance uses cursor-based pagination, not offset
        )

        transactions = []
        if response.data and response.data.data:
            for txn in response.data.data:
                # Parse postings to determine type and amounts
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
                })

        return transactions

    except Exception as e:
        logger.error(f"Failed to list transactions: {e}")
        return []
```

### Step 4: Payment Operations

Formance Payments module handles external payment rails (ACH, wire, etc.):

```python
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
    """Create a payment via Formance Payments"""

    try:
        # Formance Payments v1 API
        response = await self.client.sdk.payments.v1.create_payment_async(
            request_body={
                "amount": int(amount * 100),
                "asset": currency,
                "connector_id": self._get_connector_id(payment_method),
                "destination": destination,
                "reference": metadata.get("reference"),
                "metadata": {
                    "from_account": from_account_id,
                    "description": description,
                    **metadata,
                },
            }
        )

        payment = response.data

        return {
            "id": payment.id,
            "from_account_id": from_account_id,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "destination": destination,
            "status": payment.status,
            "description": description,
            "metadata": payment.metadata or {},
        }

    except Exception as e:
        logger.error(f"Failed to create payment: {e}")
        raise FormanceAPIError(f"Payment creation failed: {e}")

def _get_connector_id(self, payment_method: PaymentMethod) -> str:
    """Map payment method to Formance connector"""
    connector_map = {
        PaymentMethod.ACH: "stripe",  # or your ACH provider
        PaymentMethod.WIRE: "wise",   # or your wire provider
        PaymentMethod.CARD: "stripe",
    }
    return connector_map.get(payment_method, "stripe")
```

### Step 5: Customer Storage

Since Formance doesn't have a built-in customer management system, you have two options:

**Option 1: Store in Ledger Metadata**

```python
async def create_customer(
    self,
    email: str,
    first_name: str,
    last_name: str,
    phone: Optional[str],
    address: Optional[dict],
    metadata: dict,
) -> dict:
    """Store customer data in ledger metadata"""

    customer_id = f"cust_{email.split('@')[0]}_{int(time.time())}"

    # Create a customer "account" to hold metadata
    await self.client.sdk.ledger.v2.add_metadata_to_account_async(
        ledger="main",
        address=f"customers:{customer_id}",
        request_body={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "address": address,
            "status": "active",
            "kyc_status": "not_started",
            **metadata,
        }
    )

    return {
        "id": customer_id,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "address": address,
        "status": "active",
        "kyc_status": "not_started",
        "metadata": metadata,
    }
```

**Option 2: Use External Database (Recommended)**

Store customers in PostgreSQL for better querying:

```python
# Add to your repository or create a separate CustomerRepository
async def create_customer(
    self,
    email: str,
    first_name: str,
    last_name: str,
    phone: Optional[str],
    address: Optional[dict],
    metadata: dict,
) -> dict:
    """Store customer in PostgreSQL"""

    # Use SQLAlchemy or similar
    customer = Customer(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        address=address,
        metadata=metadata,
    )

    async with self.db_session() as session:
        session.add(customer)
        await session.commit()
        await session.refresh(customer)

    return customer.to_dict()
```

## Implementation Checklist

- [ ] Set up Formance account and get credentials
- [ ] Create a ledger via Formance dashboard or API
- [ ] Implement ledger account operations
- [ ] Implement transaction operations
- [ ] Set up payment connectors (Stripe, Wise, etc.)
- [ ] Implement payment operations
- [ ] Decide on customer storage strategy
- [ ] Implement customer operations
- [ ] Add retry logic for API failures
- [ ] Add comprehensive error handling
- [ ] Write integration tests
- [ ] Set up webhooks for payment status updates

## Testing Strategy

1. **Unit Tests**: Mock the Formance SDK responses
2. **Integration Tests**: Use Formance sandbox environment
3. **E2E Tests**: Full flow testing with test accounts

## Common Patterns

### Error Handling

```python
from formance_sdk_python.models import errors

try:
    response = await self.client.sdk.ledger.v2.create_transaction_async(...)
except errors.ErrorResponse as e:
    logger.error(f"Formance API error: {e.error_code} - {e.error_message}")
    raise FormanceAPIError(f"API Error: {e.error_message}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### Idempotency

Use transaction references for idempotency:

```python
reference = f"txn_{customer_id}_{timestamp}_{uuid4()}"

await self.client.sdk.ledger.v2.create_transaction_async(
    ledger="main",
    idempotency_key=reference,  # Prevents duplicate transactions
    request_body={...}
)
```

### Pagination

```python
cursor = None
all_transactions = []

while True:
    response = await self.client.sdk.ledger.v2.list_transactions_async(
        ledger="main",
        cursor=cursor,
        page_size=100,
    )

    all_transactions.extend(response.data.data)

    if not response.data.has_more:
        break

    cursor = response.data.next
```

## Next Steps

1. Start with implementing ledger account operations
2. Test with Formance sandbox
3. Implement transaction operations
4. Add payment connectors
5. Implement customer storage
6. Add comprehensive error handling
7. Write tests
8. Deploy to production

## Resources

- [Formance Ledger v2 Docs](https://docs.formance.com/ledger/v2)
- [Formance Payments Docs](https://docs.formance.com/payments)
- [Formance Python SDK](https://github.com/formancehq/formance-sdk-python)
- [Formance API Reference](https://docs.formance.com/api)
