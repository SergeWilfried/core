# Architecture Overview

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Apps                          │
│              (Web, Mobile, Third-party APIs)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │             API Layer (v1 Routes)                    │  │
│  │  • /accounts  • /transactions  • /customers          │  │
│  │  • /payments  • /cards         • /webhooks           │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │           Service Layer (Business Logic)             │  │
│  │  • AccountService    • TransactionService            │  │
│  │  • CustomerService   • PaymentService                │  │
│  │  • CardService       • LedgerService                 │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │        Repository Layer (Data Access)                │  │
│  │           FormanceRepository                         │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │      FormanceBankingClient (SDK Wrapper)             │  │
│  │   • Connection pooling  • Retry logic                │  │
│  │   • Logging            • Error handling              │  │
│  └────────────────────┬─────────────────────────────────┘  │
└────────────────────────┼─────────────────────────────────────┘
                         │ Formance SDK
                         ▼
         ┌───────────────────────────────────┐
         │       Formance Cloud API          │
         │  ┌─────────────────────────────┐  │
         │  │    Ledger v2 Module         │  │
         │  │  • Accounts                 │  │
         │  │  • Transactions             │  │
         │  │  • Balances                 │  │
         │  └─────────────────────────────┘  │
         │  ┌─────────────────────────────┐  │
         │  │   Payments v1 Module        │  │
         │  │  • ACH, Wire, Cards         │  │
         │  │  • Connectors (Stripe, etc) │  │
         │  └─────────────────────────────┘  │
         │  ┌─────────────────────────────┐  │
         │  │    Wallets v1 Module        │  │
         │  │  • Wallet management        │  │
         │  └─────────────────────────────┘  │
         └───────────────────────────────────┘
```

## Data Flow: Create Account & Deposit

```
User Request
    │
    ▼
[POST /api/v1/accounts]
    │
    ▼
AccountService.create_account()
    │
    ▼
FormanceRepository.create_ledger_account()
    │
    ▼
FormanceBankingClient.sdk.ledger.v2.create_transaction_async()
    │
    ▼
Formance API: POST /api/ledger/v2/{ledger}/transactions
    │
    ▼
Creates account: "customers:cust_123:checking"
    │
    ▼
Returns account data
    │
    ▼
User receives account object
```

## Formance Ledger Structure

### Account Hierarchy

```
world                           # External world (deposits/withdrawals)
│
├── customers:                  # Customer accounts
│   ├── cust_123:
│   │   ├── checking           # Checking account
│   │   ├── savings            # Savings account
│   │   └── escrow             # Escrow account
│   │
│   └── cust_456:
│       └── checking
│
├── bank:                       # Bank internal accounts
│   ├── fees                   # Fee collection
│   ├── reserve               # Reserve account
│   ├── payments:
│   │   ├── incoming          # Incoming payments
│   │   └── outgoing          # Outgoing payments
│   └── interest              # Interest payments
│
└── partners:                   # Partner accounts
    └── partner_123
```

### Transaction Flow Example

**Deposit $1000 to customer account:**

```
Transaction {
  postings: [
    {
      source: "world"
      destination: "customers:cust_123:checking"
      amount: 100000  // cents
      asset: "USD"
    }
  ]
}
```

**Transfer $100 between accounts:**

```
Transaction {
  postings: [
    {
      source: "customers:cust_123:checking"
      destination: "customers:cust_456:checking"
      amount: 10000
      asset: "USD"
    }
  ]
}
```

**Charge $5 fee:**

```
Transaction {
  postings: [
    {
      source: "customers:cust_123:checking"
      destination: "bank:fees"
      amount: 500
      asset: "USD"
    }
  ]
}
```

## Integration Points

### 1. Ledger Integration

**What it does:**
- Manages all account balances
- Records all transactions
- Maintains audit trail
- Ensures double-entry bookkeeping

**How to integrate:**
```python
# Create account (via transaction)
await client.sdk.ledger.v2.create_transaction_async(
    ledger="main",
    request_body={
        "postings": [{
            "source": "world",
            "destination": "customers:123:checking",
            "amount": 0,
            "asset": "USD"
        }]
    }
)

# Get balance
account = await client.sdk.ledger.v2.get_account_async(
    ledger="main",
    address="customers:123:checking"
)
balance = account.data.balances["USD"]
```

### 2. Payments Integration

**What it does:**
- Processes external payments (ACH, wire, cards)
- Connects to payment providers (Stripe, Wise, etc.)
- Handles payment status updates

**How to integrate:**
```python
# Create payment
payment = await client.sdk.payments.v1.create_payment_async(
    request_body={
        "amount": 10000,
        "asset": "USD",
        "connector_id": "stripe_connector",
        "destination": "external_account_123"
    }
)

# Listen for webhooks
@app.post("/webhooks/payments")
async def payment_webhook(payload: dict):
    # Update payment status
    # Trigger notifications
    pass
```

### 3. Wallets Integration (Optional)

**What it does:**
- Higher-level wallet abstraction
- Multi-account management
- Spending controls

**When to use:**
- Need wallet-based features
- Want simplified balance management
- Building consumer wallets

## Service Layer Responsibilities

### AccountService
- **Input**: Customer ID, account type, currency
- **Business Logic**:
  - Validate customer exists (if using KYC)
  - Check account limits
  - Generate account address
- **Output**: Account object
- **Calls**: FormanceRepository.create_ledger_account()

### TransactionService
- **Input**: Source, destination, amount, currency
- **Business Logic**:
  - Validate sufficient funds
  - Check transaction limits
  - Validate accounts exist
  - Generate idempotency key
- **Output**: Transaction object
- **Calls**: FormanceRepository.create_transaction()

### PaymentService
- **Input**: Account, amount, payment method, destination
- **Business Logic**:
  - Validate payment method
  - Check daily limits
  - Debit account in ledger
  - Initiate external payment
- **Output**: Payment object
- **Calls**:
  - FormanceRepository.create_transaction() (ledger debit)
  - FormanceRepository.create_payment() (external payment)

### CustomerService
- **Input**: Customer data (email, name, etc.)
- **Business Logic**:
  - Validate email uniqueness
  - Check KYC requirements
  - Store customer data
- **Output**: Customer object
- **Calls**: Database or FormanceRepository (metadata)

## Error Handling Flow

```
API Request
    │
    ▼
Try: Service Method
    │
    ├─[Success]─────────────────► Return Result
    │
    └─[Error]
        │
        ├─[InsufficientFundsError]─► HTTP 400
        ├─[AccountNotFoundError]───► HTTP 404
        ├─[FormanceAPIError]────────► HTTP 502
        ├─[ValidationError]─────────► HTTP 422
        └─[UnknownError]────────────► HTTP 500
```

## Security Layers

```
┌─────────────────────────────────────────┐
│  1. API Gateway (Rate Limiting)         │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  2. JWT Authentication                  │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  3. Input Validation (Pydantic)         │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  4. Business Logic Validation           │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  5. Formance API (OAuth2 + TLS)         │
└─────────────────────────────────────────┘
```

## Deployment Architecture

### Development
```
localhost:8000 ──► Formance Sandbox
```

### Production
```
                    ┌─── Load Balancer ───┐
                    │                      │
         ┌──────────▼──────────┐  ┌───────▼────────┐
         │   API Instance 1    │  │  API Instance 2 │
         └──────────┬──────────┘  └───────┬─────────┘
                    │                      │
         ┌──────────▼──────────────────────▼─────────┐
         │         Redis (Session/Cache)             │
         └──────────┬────────────────────────────────┘
                    │
         ┌──────────▼────────────────────────────────┐
         │    PostgreSQL (Customer Data)             │
         └──────────┬────────────────────────────────┘
                    │
         ┌──────────▼────────────────────────────────┐
         │         Formance Production               │
         └───────────────────────────────────────────┘
```

## Monitoring & Observability

```
Application Logs
    │
    ├─► Structlog ─► JSON Format
    │
    ├─► CloudWatch / Datadog
    │
    └─► Error Tracking (Sentry)

Metrics
    │
    ├─► Request latency
    ├─► Transaction volume
    ├─► Error rates
    └─► Account balances

Alerts
    │
    ├─► High error rate
    ├─► Slow responses
    ├─► Failed payments
    └─► Balance discrepancies
```

## Key Design Decisions

1. **Async by Default**: All I/O operations are async for high concurrency
2. **Service Layer**: Business logic separated from API and data access
3. **Repository Pattern**: Formance integration isolated in repository layer
4. **Pydantic Models**: Strong typing and validation throughout
5. **Ledger-First**: Formance Ledger is source of truth for balances
6. **Idempotency**: All transactions use idempotency keys
7. **Metadata Storage**: Flexible metadata for extensibility

## Next Steps

1. Review [FORMANCE_INTEGRATION.md](FORMANCE_INTEGRATION.md) for SDK details
2. Check [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) for step-by-step plan
3. See [examples/formance_repository_example.py](examples/formance_repository_example.py) for code
