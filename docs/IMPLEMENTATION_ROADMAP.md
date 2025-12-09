# Implementation Roadmap

Step-by-step guide to implementing your Formance-based BaaS Core Banking system.

## Phase 1: Formance Setup (1-2 days)

### Step 1.1: Create Formance Account
1. Sign up at [formance.com](https://formance.com)
2. Create a new stack (e.g., "baas-core-dev")
3. Note your stack ID and organization ID

### Step 1.2: Generate API Credentials
1. Go to Settings > API Keys
2. Create a new API key pair
3. Save client ID and client secret securely
4. Update `.env` file:
   ```bash
   FORMANCE_BASE_URL=https://api.formance.cloud
   FORMANCE_CLIENT_ID=your_client_id_here
   FORMANCE_CLIENT_SECRET=your_client_secret_here
   FORMANCE_STACK_ID=your_stack_id
   ```

### Step 1.3: Create Default Ledger
```bash
# Using Formance CLI or API
curl -X POST "https://api.formance.cloud/api/ledger/v2/ledgers" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "main"}'
```

Or programmatically:
```python
# In a setup script
from core.client import get_formance_client

async def setup_ledger():
    async with get_formance_client() as client:
        await client.sdk.ledger.v2.create_ledger_async(
            ledger="main",
            request_body={"metadata": {"env": "production"}}
        )
```

## Phase 2: Basic Account Operations (2-3 days)

### Step 2.1: Implement Account Creation
1. Copy the example from `docs/examples/formance_repository_example.py`
2. Update `core/repositories/formance.py`:
   - Replace `create_ledger_account()` placeholder
   - Replace `get_account()` placeholder
   - Replace `get_account_balance()` placeholder

### Step 2.2: Test Account Creation
```python
# Create test script: scripts/test_accounts.py
import asyncio
from core.client import get_formance_client
from core.repositories.formance import FormanceRepository
from core.services.accounts import AccountService
from core.models.account import AccountType

async def test_account_creation():
    async with get_formance_client() as client:
        repo = FormanceRepository(client)
        service = AccountService(repo)

        # Create account
        account = await service.create_account(
            customer_id="test_customer_001",
            account_type=AccountType.CHECKING,
            currency="USD",
        )

        print(f"Created account: {account.id}")

        # Get balance
        balance = await service.get_balance(account.id)
        print(f"Balance: {balance}")

if __name__ == "__main__":
    asyncio.run(test_account_creation())
```

Run test:
```bash
python scripts/test_accounts.py
```

### Step 2.3: Verify in Formance Dashboard
1. Go to your Formance dashboard
2. Navigate to Ledger > Accounts
3. Verify the account was created
4. Check the metadata

## Phase 3: Transaction Processing (3-4 days)

### Step 3.1: Implement Transactions
Update `core/repositories/formance.py`:
- `create_transaction()`
- `get_transaction()`
- `list_transactions()`

### Step 3.2: Test Transactions
```python
# scripts/test_transactions.py
async def test_transactions():
    # Create two accounts
    account1 = await service.create_account(...)
    account2 = await service.create_account(...)

    # Deposit to account1
    txn1 = await txn_service.deposit(
        to_account_id=account1.id,
        amount=Decimal("1000.00"),
        currency="USD",
    )
    print(f"Deposit: {txn1.id}")

    # Transfer between accounts
    txn2 = await txn_service.transfer(
        from_account_id=account1.id,
        to_account_id=account2.id,
        amount=Decimal("100.00"),
        currency="USD",
    )
    print(f"Transfer: {txn2.id}")

    # Check balances
    balance1 = await service.get_balance(account1.id)
    balance2 = await service.get_balance(account2.id)
    print(f"Account1: ${balance1}, Account2: ${balance2}")
```

### Step 3.3: Edge Cases Testing
- Test insufficient funds
- Test negative amounts
- Test zero amounts
- Test concurrent transactions
- Test idempotency

## Phase 4: Customer Management (1-2 days)

### Step 4.1: Choose Storage Strategy

**Option A: PostgreSQL (Recommended)**
```bash
# Add to dependencies
uv add sqlalchemy asyncpg alembic
```

Create models:
```python
# core/database/models.py
from sqlalchemy import Column, String, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CustomerDB(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String)
    address = Column(JSON)
    status = Column(String, default="active")
    kyc_status = Column(String, default="not_started")
    metadata = Column(JSON)
```

**Option B: Formance Metadata**
Store in ledger metadata (simpler but limited querying)

### Step 4.2: Implement Customer Operations
Choose based on your storage strategy:
- PostgreSQL: Create database repository
- Metadata: Use ledger metadata operations

## Phase 5: Payment Integration (3-5 days)

### Step 5.1: Set Up Payment Connectors
1. Go to Formance Dashboard > Payments
2. Add connectors:
   - Stripe (for cards, ACH)
   - Wise (for international wire)
   - Or your preferred providers

3. Note connector IDs

### Step 5.2: Configure Connectors
```python
# In your repository
CONNECTOR_MAP = {
    PaymentMethod.ACH: "your_stripe_connector_id",
    PaymentMethod.WIRE: "your_wise_connector_id",
    PaymentMethod.CARD: "your_stripe_connector_id",
}
```

### Step 5.3: Implement Payments
Update repository with payment methods

### Step 5.4: Set Up Webhooks
```python
# core/api/v1/webhooks.py
from fastapi import APIRouter, Request

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/formance/payments")
async def payment_webhook(request: Request):
    """Handle Formance payment status updates"""
    payload = await request.json()

    # Verify webhook signature
    # Update payment status in your system
    # Trigger notifications

    return {"status": "received"}
```

## Phase 6: API Testing (2-3 days)

### Step 6.1: Install Dependencies
```bash
uv sync --group dev
```

### Step 6.2: Start API Server
```bash
uvicorn core.api.app:app --reload
```

### Step 6.3: Test with cURL

**Create customer:**
```bash
curl -X POST http://localhost:8000/api/v1/customers \
  -H "Authorization: Bearer test_token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890"
  }'
```

**Create account:**
```bash
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Authorization: Bearer test_token" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_123",
    "account_type": "checking",
    "currency": "USD"
  }'
```

**Make deposit:**
```bash
curl -X POST http://localhost:8000/api/v1/transactions/deposit \
  -H "Authorization: Bearer test_token" \
  -H "Content-Type: application/json" \
  -d '{
    "to_account_id": "customers:cust_123:checking",
    "amount": 1000.00,
    "currency": "USD"
  }'
```

### Step 6.4: Test with Swagger UI
1. Go to http://localhost:8000/docs
2. Test each endpoint interactively

## Phase 7: Authentication & Security (2-3 days)

### Step 7.1: Implement JWT Authentication
```python
# core/auth/jwt.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### Step 7.2: Update Dependencies
Update `core/api/dependencies.py` with real JWT validation

### Step 7.3: Add Rate Limiting
```bash
uv add slowapi
```

```python
# core/api/app.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/accounts")
@limiter.limit("10/minute")
async def create_account(...):
    ...
```

## Phase 8: Testing & QA (3-5 days)

### Step 8.1: Write Unit Tests
```bash
pytest tests/unit/ -v
```

### Step 8.2: Write Integration Tests
```bash
pytest tests/integration/ -v
```

### Step 8.3: End-to-End Testing
Test complete flows:
- Customer onboarding → Account creation → Deposit → Transfer
- Payment processing flow
- Account freezing/closure
- Error scenarios

## Phase 9: Deployment (2-3 days)

### Step 9.1: Production Checklist
- [ ] Update all secrets in production `.env`
- [ ] Configure CORS for production domains
- [ ] Set up SSL certificates
- [ ] Configure database backups
- [ ] Set up logging aggregation (e.g., Datadog, CloudWatch)
- [ ] Configure monitoring/alerting
- [ ] Set up Sentry for error tracking
- [ ] Enable rate limiting
- [ ] Configure webhook signatures
- [ ] Set up CI/CD pipeline

### Step 9.2: Deploy with Docker
```bash
# Build
docker build -t baas-core-banking:latest .

# Run
docker run -d \
  -p 8000:8000 \
  --env-file .env.production \
  --name baas-api \
  baas-core-banking:latest
```

### Step 9.3: Deploy with Docker Compose
```bash
docker-compose -f docker/docker-compose.yml up -d
```

### Step 9.4: Health Checks
```bash
curl http://your-domain.com/health
```

## Timeline Summary

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| 1. Formance Setup | 1-2 days | None |
| 2. Account Operations | 2-3 days | Phase 1 |
| 3. Transactions | 3-4 days | Phase 2 |
| 4. Customers | 1-2 days | Phase 1 |
| 5. Payments | 3-5 days | Phase 3 |
| 6. API Testing | 2-3 days | Phases 2-5 |
| 7. Auth & Security | 2-3 days | Phase 6 |
| 8. Testing & QA | 3-5 days | All phases |
| 9. Deployment | 2-3 days | Phase 8 |

**Total Estimated Time: 3-5 weeks**

## Next Immediate Steps

1. **TODAY**:
   - Set up Formance account
   - Get API credentials
   - Create default ledger
   - Update `.env` file

2. **TOMORROW**:
   - Implement `create_ledger_account()`
   - Test account creation
   - Verify in Formance dashboard

3. **THIS WEEK**:
   - Complete Phase 2 (Account Operations)
   - Start Phase 3 (Transactions)

## Getting Help

- **Formance Docs**: https://docs.formance.com
- **Formance Discord**: https://discord.gg/formance
- **GitHub Issues**: Create issues in your repo for tracking
- **Example Code**: Check `docs/examples/` directory

## Tips for Success

1. **Start Small**: Get one feature working end-to-end before moving on
2. **Test Early**: Test each integration as you build it
3. **Use Formance Sandbox**: Test in sandbox before production
4. **Read SDK Code**: The Formance SDK is open source - read it when stuck
5. **Version Control**: Commit frequently with clear messages
6. **Monitor Logs**: Watch both your logs and Formance dashboard
7. **Handle Errors**: Add comprehensive error handling from the start
8. **Document**: Keep notes on decisions and gotchas

Good luck with your implementation!
