# BaaS Core Banking System

A production-ready Banking as a Service (BaaS) core banking system built on the [Formance](https://formance.com) stack using Python, FastAPI, and async architecture.

## Overview

This project provides a complete banking infrastructure including:

- **Multi-Tenancy**: Organizations and users with role-based access control
- **Account Management**: Create and manage checking, savings, business, and escrow accounts
- **Transaction Processing**: Handle deposits, withdrawals, and transfers with full audit trails
- **Payment Rails**: ACH, wire transfers, card payment processing, and mobile money
- **Mobile Money Support**: M-Pesa, MTN Mobile Money, Airtel Money, and other providers across Africa
- **User Management**: Authentication, authorization, and team collaboration
- **Customer Management**: KYC/AML compliance and customer lifecycle management
- **Card Issuance**: Virtual and physical card management
- **Real-time Ledger**: Double-entry bookkeeping via Formance Ledger

## Architecture

### Technology Stack

- **Framework**: FastAPI (async REST API)
- **Database**: Formance Ledger (primary) + PostgreSQL (optional local storage)
- **Caching**: Redis
- **SDK**: Formance Python SDK
- **Validation**: Pydantic v2
- **Testing**: Pytest with async support
- **Deployment**: Docker + Docker Compose

### Project Structure

```
core/
├── core/
│   ├── __init__.py
│   ├── client.py              # Formance client wrapper
│   ├── config.py              # Configuration management
│   ├── exceptions.py          # Custom banking exceptions
│   │
│   ├── services/              # Business logic layer
│   │   ├── accounts.py
│   │   ├── transactions.py
│   │   ├── payments.py
│   │   ├── customers.py
│   │   ├── cards.py
│   │   └── ledger.py
│   │
│   ├── models/                # Domain models (Pydantic)
│   │   ├── account.py
│   │   ├── transaction.py
│   │   ├── customer.py
│   │   ├── payment.py
│   │   └── card.py
│   │
│   ├── api/                   # FastAPI routes
│   │   ├── app.py
│   │   ├── dependencies.py
│   │   └── v1/
│   │       ├── accounts.py
│   │       ├── transactions.py
│   │       ├── payments.py
│   │       └── customers.py
│   │
│   ├── repositories/          # Data access layer
│   │   └── formance.py
│   │
│   └── utils/
│       ├── logging.py
│       ├── retry.py
│       └── validators.py
│
├── tests/                     # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docker/                    # Docker configs
├── pyproject.toml
├── Dockerfile
└── README.md
```

## Setup

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Formance account and API credentials
- Docker (optional, for local development)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd core
   ```

2. **Install dependencies**:
   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -e .
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Formance credentials
   ```

4. **Set up Formance credentials**:
   - Sign up at [formance.com](https://formance.com)
   - Create a new stack
   - Generate API credentials
   - Update `.env` with your credentials

### Configuration

Edit `.env` with your settings:

```bash
# Required
FORMANCE_BASE_URL=https://api.formance.cloud
FORMANCE_CLIENT_ID=your_client_id
FORMANCE_CLIENT_SECRET=your_client_secret

# Optional
DATABASE_URL=postgresql://user:password@localhost:5432/banking
REDIS_URL=redis://localhost:6379/0
```

## Running the Application

### Local Development

**Run the API server**:
```bash
uvicorn core.api.app:app --reload --port 8000
```

**Run with Docker Compose**:
```bash
docker-compose -f docker/docker-compose.yml up
```

Access the API:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Testing

**Run all tests**:
```bash
pytest
```

**Run with coverage**:
```bash
pytest --cov=core --cov-report=html
```

**Run specific test types**:
```bash
# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/
```

## API Usage

### Authentication

All endpoints require Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/accounts
```

### Example API Calls

**Create a customer**:
```bash
POST /api/v1/customers
{
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

**Create an account**:
```bash
POST /api/v1/accounts
{
  "customer_id": "cust_123",
  "account_type": "checking",
  "currency": "USD"
}
```

**Deposit funds**:
```bash
POST /api/v1/transactions/deposit
{
  "to_account_id": "acc_123",
  "amount": 1000.00,
  "currency": "USD",
  "description": "Initial deposit"
}
```

**Transfer between accounts**:
```bash
POST /api/v1/transactions/transfer
{
  "from_account_id": "acc_123",
  "to_account_id": "acc_456",
  "amount": 100.00,
  "currency": "USD",
  "description": "Transfer to savings"
}
```

**Send mobile money payment**:
```bash
POST /api/v1/payments/mobile-money
{
  "from_account_id": "acc_123",
  "phone_number": "+254712345678",
  "provider": "mpesa",
  "country_code": "KE",
  "amount": 1000.00,
  "currency": "KES",
  "description": "Payment to merchant"
}
```

## Key Features

### 1. Async Architecture

Built with async/await for high concurrency:
- Non-blocking I/O operations
- Handles thousands of concurrent requests
- Optimized connection pooling

### 2. Banking Services

**Account Service** ([core/services/accounts.py](core/services/accounts.py)):
- Account creation and management
- Balance queries
- Account freezing/closure
- Multi-currency support

**Transaction Service** ([core/services/transactions.py](core/services/transactions.py)):
- Deposits and withdrawals
- Internal transfers
- Transaction history
- Balance validation

**Payment Service** ([core/services/payments.py](core/services/payments.py)):
- ACH payments
- Wire transfers
- Mobile money transfers
- Payment tracking
- Payment cancellation

**Customer Service** ([core/services/customers.py](core/services/customers.py)):
- Customer onboarding
- KYC management
- Customer lifecycle

**Card Service** ([core/services/cards.py](core/services/cards.py)):
- Virtual card issuance
- Physical card management
- Spending limits
- Card controls

### 3. Mobile Money Integration

Comprehensive support for mobile money providers across Africa and beyond:

**Supported Providers**:
- **M-Pesa**: Kenya, Tanzania, Mozambique, South Africa
- **MTN Mobile Money**: Uganda, Ghana, Ivory Coast, Cameroon, Zambia, and more
- **Airtel Money**: Kenya, Tanzania, Uganda, Zambia, Malawi, Nigeria, and more
- **Orange Money**: Senegal, Mali, Burkina Faso, Ivory Coast, Cameroon
- **Vodacom**: South Africa, Tanzania, Mozambique
- **Tigo Pesa**: Tanzania, Rwanda, Ghana
- **EcoCash**: Zimbabwe, Zambia
- **Wave**: Senegal, Ivory Coast, Burkina Faso, Mali
- **Chipper Cash**: Pan-African
- **Flutterwave**: Pan-African aggregator

**Features**:
- E.164 phone number validation
- Provider-country validation
- Multi-currency support (KES, TZS, UGX, GHS, ZAR, XOF, XAF, etc.)
- Structured metadata for tracking
- Formance ledger integration ready

**API Endpoint**: `POST /api/v1/payments/mobile-money`

**Example**:
```python
# Send M-Pesa payment in Kenya
payment = await payment_service.process_mobile_money_payment(
    from_account_id="acc_123",
    phone_number="+254712345678",
    provider=MobileMoneyProvider.MPESA,
    country_code="KE",
    amount=Decimal("1000.00"),
    currency="KES",
    description="Payment to merchant"
)
```

### 4. Robust Error Handling

Custom exceptions for banking operations:
- `InsufficientFundsError`
- `AccountNotFoundError`
- `KYCRequiredError`
- `TransactionLimitExceeded`
- And more...

### 5. Validation

Business rule validators:
- Amount validation
- Currency validation
- Routing number verification
- SWIFT code validation
- E.164 phone number validation
- Mobile money provider-country validation
- Email and phone validation

### 6. Observability

- Structured logging with `structlog`
- Request/response logging
- Error tracking
- Health check endpoint

## Development

### Code Quality

**Linting**:
```bash
ruff check .
```

**Type checking**:
```bash
mypy core
```

**Formatting**:
```bash
ruff format .
```

### Adding New Features

1. Create domain model in `core/models/`
2. Add service logic in `core/services/`
3. Create API endpoints in `core/api/v1/`
4. Write tests in `tests/`
5. Update repository layer in `core/repositories/`

## Deployment

### Docker

**Build image**:
```bash
docker build -t baas-core-banking .
```

**Run container**:
```bash
docker run -p 8000:8000 --env-file .env baas-core-banking
```

### Production Checklist

- [ ] Update `SECRET_KEY` in production
- [ ] Configure proper CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Enable rate limiting
- [ ] Configure monitoring (Sentry, etc.)
- [ ] Set up proper logging aggregation
- [ ] Implement proper authentication
- [ ] Configure database backups
- [ ] Set up CI/CD pipeline

## Roadmap

### Phase 1: Foundation ✓
- [x] Account management
- [x] Basic transactions
- [x] Customer management
- [x] API structure

### Phase 2: Payments (In Progress)
- [ ] ACH processing
- [ ] Wire transfers
- [ ] Payment reconciliation
- [ ] Webhook handling

### Phase 3: Cards
- [ ] Card issuance
- [ ] Card transactions
- [ ] Card controls
- [ ] 3DS authentication

### Phase 4: Compliance
- [ ] KYC/AML automation
- [ ] Transaction monitoring
- [ ] Regulatory reporting
- [ ] Audit trails

### Phase 5: Advanced Features
- [x] Mobile money integration
- [x] Organizations and users management
- [x] Role-based access control (RBAC)
- [x] Multi-tenancy support
- [ ] Multi-currency accounts
- [ ] FX trading
- [ ] Recurring payments
- [ ] Mobile money webhook handling
- [ ] OAuth2/SSO integration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

Apache-2.0 - See LICENSE file for details

## Resources

- [Formance Documentation](https://docs.formance.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Pydantic Documentation](https://docs.pydantic.dev)

---

Built with Formance and FastAPI
