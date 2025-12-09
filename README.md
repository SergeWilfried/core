# BaaS Core Banking System

A production-ready Banking as a Service (BaaS) core banking system built on the [Formance](https://formance.com) stack using Python, FastAPI, and async architecture.

## Overview

This project provides a complete banking infrastructure including:

- **Multi-Tenancy**: Organizations and users with role-based access control
- **Multi-Branch Support**: Hierarchical branch structure for organizations with multiple locations
- **Account Management**: Create and manage checking, savings, business, and escrow accounts
- **Transaction Processing**: Handle deposits, withdrawals, and transfers with full audit trails
- **Payment Rails**: ACH, wire transfers, card payment processing, and mobile money
- **Mobile Money Support**: M-Pesa, MTN Mobile Money, Airtel Money, and other providers across Africa
- **User Management**: Authentication, authorization, and team collaboration
- **Customer Management**: KYC/AML compliance and customer lifecycle management
- **Card Issuance**: Virtual and physical card management
- **Real-time Ledger**: Double-entry bookkeeping via Formance Ledger
- **Compliance Engine**: Automated KYC/AML, sanctions screening, transaction monitoring, and risk scoring

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
│   │   ├── compliance.py      # NEW: Compliance engine
│   │   └── ledger.py
│   │
│   ├── models/                # Domain models (Pydantic)
│   │   ├── account.py
│   │   ├── transaction.py
│   │   ├── customer.py
│   │   ├── payment.py
│   │   ├── card.py
│   │   ├── compliance.py      # NEW: Compliance models
│   │   └── rules.py           # NEW: Rule engine models
│   │
│   ├── api/                   # FastAPI routes
│   │   ├── app.py
│   │   ├── dependencies.py
│   │   └── v1/
│   │       ├── accounts.py
│   │       ├── transactions.py
│   │       ├── payments.py
│   │       ├── customers.py
│   │       ├── organizations.py
│   │       ├── users.py
│   │       └── compliance.py  # NEW: Compliance API
│   │
│   ├── repositories/          # Data access layer
│   │   └── formance.py
│   │
│   ├── workers/               # NEW: Background workers
│   │   └── compliance_reconciliation.py
│   │
│   └── utils/
│       ├── logging.py
│       ├── retry.py
│       ├── validators.py
│       └── sanctions.py       # NEW: Sanctions screening
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

### 7. Compliance Engine ⭐

**ComplianceService** ([core/services/compliance.py](core/services/compliance.py)):

Comprehensive compliance engine for KYC/AML and transaction monitoring:

**Pre-Transaction Checks:**
- KYC/KYB verification status validation
- Sanctions screening (OFAC, UN, EU lists)
- Organization compliance settings validation
- Transaction velocity monitoring
- Geographic risk assessment
- Custom compliance rules evaluation
- Real-time risk scoring (0-100)

**Sanctions Screening** ([core/utils/sanctions.py](core/utils/sanctions.py)):
- Name matching against OFAC, UN, EU sanctions lists
- Fuzzy matching for name variations
- Alias checking
- Country-level sanctions validation
- Country risk scoring (FATF-aligned)

**Configurable Rules Engine** ([core/models/rules.py](core/models/rules.py)):
- Custom compliance rules per organization
- Pre-built rule templates (high value, blocked countries, velocity, KYC)
- Flexible condition operators (equals, greater than, in, contains, regex)
- Actions: ALLOW, BLOCK, REVIEW, ALERT, LOG
- Priority-based evaluation
- Risk score impact weighting

**Organization Compliance Settings**:
```python
OrganizationSettings:
  compliance_level: "basic" | "standard" | "strict"
  enable_sanctions_screening: bool
  enable_velocity_monitoring: bool
  enable_pep_screening: bool
  max_transaction_amount: Optional[Decimal]
  restricted_countries: list[str]
  require_manual_review_above: Optional[Decimal]
  risk_score_threshold: int (0-100)
```

**Risk Scoring Components** (weighted):
- KYC Score (25%): Verification status
- Sanctions Score (30%): Screening match confidence
- Transaction Score (20%): Amount-based risk
- Geographic Score (15%): Country risk assessment
- Velocity Score (10%): Pattern analysis

**Audit Trail Integration**:
All approved transactions are posted to Formance ledger with comprehensive compliance metadata:
```
Metadata:
  - compliance_check_id
  - compliance_status: approved/blocked/review
  - risk_score: 0-100
  - risk_level: low/medium/high/critical
  - rules_evaluated: [...]
  - organization_id, customer_id
```

**API Endpoints** ([core/api/v1/compliance.py](core/api/v1/compliance.py)):
- `POST /api/v1/compliance/check` - Run compliance check
- `GET /api/v1/compliance/checks/{id}` - Get check details
- `POST /api/v1/compliance/checks/{id}/approve` - Approve review
- `POST /api/v1/compliance/checks/{id}/reject` - Reject transaction
- `POST /api/v1/compliance/rules` - Create compliance rule
- `GET /api/v1/compliance/rules` - List rules
- `GET /api/v1/compliance/sanctions/screen` - Screen name
- `GET /api/v1/compliance/country-risk/{code}` - Get country risk

**Background Workers** ([core/workers/compliance_reconciliation.py](core/workers/compliance_reconciliation.py)):
- Async reconciliation with Formance ledger
- Deep AML analysis
- Risk score updates
- Compliance alert generation
- Regulatory report preparation

**RBAC Permissions**:
- `COMPLIANCE_VIEW` - View compliance checks
- `COMPLIANCE_APPROVE` - Approve manual reviews
- `COMPLIANCE_REJECT` - Reject transactions
- `COMPLIANCE_RULES_MANAGE` - Manage rules
- `COMPLIANCE_OVERRIDE` - Override blocks
- `COMPLIANCE_REPORTS` - Generate reports

**Example Integration**:
```python
from core.services.compliance import ComplianceService

# Run compliance check before payment
compliance_check = await compliance_service.check_transaction(
    organization_id="org_acme",
    customer_id="cust_john",
    account_id="acc_123",
    amount=Decimal("5000.00"),
    currency="USD",
    transaction_type="mobile_money_payment",
    payment_method=PaymentMethod.MOBILE_MONEY,
    destination_country="KE",
)

if compliance_check.is_approved():
    # Process payment
    payment = await payment_service.create_payment(...)

    # Post to Formance ledger with compliance metadata
    await formance_repo.post_transaction(
        ledger_id=f"org_{organization_id}",
        postings=[...],
        metadata={
            "compliance_check_id": compliance_check.id,
            "risk_score": compliance_check.risk_score,
            ...
        }
    )
elif compliance_check.needs_review():
    # Queue for manual review
    pass
else:
    # Transaction blocked
    raise TransactionBlockedError(compliance_check.reason)
```

**Documentation**: See [COMPLIANCE_ENGINE.md](docs/COMPLIANCE_ENGINE.md) for detailed integration guide.

### 8. Regulatory Reporting ⭐

**RegulatoryReportingService** ([core/services/regulatory.py](core/services/regulatory.py)):

Automated regulatory reporting for SAR and CTR compliance:

**Report Types:**
- **CTR (Currency Transaction Report)** - FinCEN Form 112
  - Automatic detection for transactions ≥ $10,000
  - Daily aggregation of currency transactions
  - Auto-generation with compliance officer review
- **SAR (Suspicious Activity Report)** - FinCEN Form 111
  - Based on compliance alerts and risk scores
  - Manual preparation with detailed narratives
  - Dual approval workflow for high-risk cases

**Key Features:**
- Automated CTR detection and generation
- SAR flagging based on compliance triggers
- Report lifecycle management (draft → review → approve → file)
- Integration with FinCEN BSA E-Filing (optional)
- Configurable thresholds and workflows
- Background worker for continuous monitoring
- Comprehensive audit trails

**Configuration** ([core/models/regulatory.py](core/models/regulatory.py)):
```python
RegulatoryReportingConfig:
  ctr_enabled: bool  # Enable CTR reporting
  ctr_threshold: Decimal  # Threshold (default: $10,000)
  ctr_auto_generate: bool  # Auto-generate CTRs
  ctr_aggregation_window_hours: int  # Aggregation window

  sar_enabled: bool  # Enable SAR reporting
  sar_auto_generate: bool  # Auto-flag SARs
  sar_risk_score_threshold: int  # Risk score trigger (default: 75)

  require_dual_approval: bool  # Require two approvals
  auto_file_reports: bool  # Auto-file approved reports
  report_retention_days: int  # Retention period (default: 5 years)
```

**API Endpoints** ([core/api/v1/regulatory.py](core/api/v1/regulatory.py)):
- `POST /api/v1/regulatory/ctr/check` - Check if CTR required
- `POST /api/v1/regulatory/ctr` - Generate CTR
- `POST /api/v1/regulatory/sar` - Generate SAR
- `GET /api/v1/regulatory/reports` - List reports
- `GET /api/v1/regulatory/reports/{id}` - Get report details
- `POST /api/v1/regulatory/reports/{id}/review` - Review report
- `POST /api/v1/regulatory/reports/{id}/file` - File with authorities
- `GET /api/v1/regulatory/config` - Get configuration
- `PUT /api/v1/regulatory/config` - Update configuration

**Background Worker** ([core/workers/regulatory_reporting.py](core/workers/regulatory_reporting.py)):
- Daily CTR generation for qualifying transactions
- Continuous SAR flagging based on alerts
- Notification to compliance officers
- Report lifecycle monitoring and escalation

**Suspicious Activity Types:**
- Structuring (avoiding CTR reporting)
- Money laundering
- Terrorist financing
- Fraud (check, card, wire, mortgage)
- Identity theft
- Elder financial abuse
- Embezzlement
- Ponzi schemes
- And 10+ more classifications

**Example Usage:**
```python
from core.services.regulatory import RegulatoryReportingService

# Check if CTR required
ctr_required = await regulatory_service.check_ctr_required(
    organization_id="org_bank",
    customer_id="cust_123",
    transaction_date=datetime.utcnow(),
    amount=Decimal("15000.00"),
    currency="USD"
)

if ctr_required:
    # Generate CTR
    ctr = await regulatory_service.generate_ctr(
        organization_id="org_bank",
        customer_id="cust_123",
        transaction_ids=["txn_1", "txn_2"],
        prepared_by="user_compliance",
        branch_id="branch_main"
    )

# Generate SAR for suspicious activity
sar = await regulatory_service.generate_sar(
    organization_id="org_bank",
    customer_id="cust_456",
    suspicious_activity_types=[SuspiciousActivityType.STRUCTURING],
    narrative_summary="Customer conducted multiple transactions just below $10K threshold over 7 days, suggesting structuring behavior to avoid CTR reporting.",
    transaction_ids=["txn_10", "txn_11", "txn_12"],
    prepared_by="user_compliance",
    activity_start_date=datetime.utcnow() - timedelta(days=7),
    priority=ReportPriority.HIGH
)

# Review and approve report
await regulatory_service.review_report(
    report_id=ctr.id,
    report_type=ReportType.CTR,
    reviewed_by="user_manager",
    approved=True
)

# File with authorities
bsa_id = await regulatory_service.file_report(
    report_id=ctr.id,
    report_type=ReportType.CTR,
    filed_by="user_compliance"
)
```

**Integration with Compliance:**
```python
# Check if regulatory reporting required
reporting = await compliance_service.check_regulatory_reporting_required(
    organization_id="org_bank",
    compliance_check=compliance_check,
    transaction_amount=Decimal("15000.00"),
    transaction_date=datetime.utcnow()
)

if reporting["ctr_required"]:
    logger.info("CTR generation required")

if reporting["sar_required"]:
    logger.warning("SAR review required")
```

**Documentation**: See [REGULATORY_REPORTING.md](docs/REGULATORY_REPORTING.md) for comprehensive guide.

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

### Phase 4: Compliance ✓
- [x] KYC/AML automation
- [x] Transaction monitoring with risk scoring
- [x] Sanctions screening (OFAC, UN, EU)
- [x] Configurable compliance rules engine
- [x] Geographic risk assessment
- [x] Velocity/pattern monitoring
- [x] Formance ledger audit trails
- [x] Organization-level compliance policies
- [x] RBAC compliance permissions
- [x] Compliance API endpoints
- [x] Background reconciliation worker
- [x] Automated regulatory reporting (SAR, CTR)
- [ ] FinCEN BSA E-Filing integration
- [ ] PEP screening integration
- [ ] ML-based anomaly detection

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
