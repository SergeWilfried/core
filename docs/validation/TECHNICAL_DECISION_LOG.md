# Technical Decision Log (TDL)

**Purpose:** Document all major technical decisions, rationale, alternatives considered, and implications.

**Status:** Draft - Awaiting Team Validation
**Last Updated:** December 10, 2025

---

## Decision Format

Each decision follows this structure:
- **ID:** Unique identifier
- **Date:** When decision was made
- **Status:** Proposed | Accepted | Rejected | Superseded
- **Context:** What prompted this decision
- **Decision:** What was decided
- **Alternatives:** What else was considered
- **Consequences:** Positive and negative outcomes
- **Validation Needed:** What the team should verify

---

## TDL-001: Python as Primary Language

**Date:** December 2025
**Status:** Proposed
**Decision Maker:** TBD
**Reviewers:** Dev Team

### Context
Need to select primary programming language for core banking system. Requirements:
- Fast development velocity
- Strong async support
- Rich ecosystem for financial services
- Type safety
- Easy to hire developers

### Decision
**Use Python 3.13+ as the primary language**

### Alternatives Considered

#### Option A: Go (Golang)
**Pros:**
- Superior performance
- Built-in concurrency
- Static typing
- Fast compilation

**Cons:**
- Slower development velocity
- Less rich ecosystem for fintech
- More verbose code
- Smaller talent pool

**Verdict:** Better for infrastructure, overkill for business logic layer

#### Option B: Node.js (TypeScript)
**Pros:**
- Excellent async performance
- Large ecosystem
- Good for real-time features
- JSON-native

**Cons:**
- Callback hell potential
- Less mature fintech libraries
- Type system not as strong as Python's
- Runtime errors more common

**Verdict:** Good option, but Python's fintech ecosystem is stronger

#### Option C: Java/Kotlin
**Pros:**
- Enterprise-grade
- Mature banking libraries
- Strong type system
- Battle-tested at scale

**Cons:**
- Verbose
- Slower development
- Heavy runtime
- Less modern

**Verdict:** Too heavyweight for MVP, consider for microservices later

### Consequences

**Positive:**
- Fast development (2-3x faster than Java)
- Rich fintech libraries (Pydantic, FastAPI, etc.)
- Excellent async/await support
- Strong type hints in 3.13+
- Easy to hire Python developers
- Good Formance SDK support

**Negative:**
- Performance ceiling lower than Go
- GIL limitations for CPU-bound tasks
- Runtime type errors possible (mitigated with mypy)
- Packaging/dependency management complexity

### Mitigation Strategies
- Use async/await for I/O-bound operations (main workload)
- Implement mypy for static type checking
- Use Pydantic for runtime validation
- Consider Go microservices for hot paths if needed
- Profile and optimize critical paths

### Validation Questions for Team
- ❓ Do we have Python expertise in-house?
- ❓ Are there performance concerns we haven't addressed?
- ❓ Should we prototype performance-critical paths?
- ❓ What's our strategy for migrating to other languages later if needed?

---

## TDL-002: FastAPI as Web Framework

**Date:** December 2025
**Status:** Proposed
**Decision Maker:** TBD

### Context
Need web framework for REST API. Must support:
- High performance
- Async operations
- Automatic API documentation
- Request/response validation

### Decision
**Use FastAPI for REST API implementation**

### Alternatives Considered

#### Option A: Django + Django REST Framework
**Pros:**
- Mature ecosystem
- Built-in admin panel
- ORM included
- Large community

**Cons:**
- Heavier weight
- Sync-first (async support limited)
- Slower than FastAPI
- More opinionated

**Verdict:** Too heavyweight, async support not first-class

#### Option B: Flask
**Pros:**
- Lightweight
- Flexible
- Large community
- Easy to learn

**Cons:**
- No built-in async support
- Manual API documentation
- No automatic validation
- More boilerplate

**Verdict:** Too basic, would require many extensions

#### Option C: Starlette (FastAPI's base)
**Pros:**
- Minimal overhead
- Pure ASGI
- Very fast

**Cons:**
- Too low-level
- No automatic validation
- No OpenAPI generation
- More work to build features

**Verdict:** FastAPI provides better DX with minimal overhead

### Consequences

**Positive:**
- Automatic OpenAPI/Swagger documentation
- Built-in request/response validation (Pydantic)
- Excellent async performance
- Type hints throughout
- Great developer experience
- Active development and community

**Negative:**
- Younger framework (less battle-tested)
- Smaller ecosystem than Django
- Breaking changes more likely
- Less enterprise adoption (so far)

### Validation Questions for Team
- ❓ Are we comfortable with a younger framework?
- ❓ Do we need Django's admin panel?
- ❓ Is automatic API documentation important?
- ❓ What's our fallback if FastAPI doesn't work out?

---

## TDL-003: Formance as Ledger System

**Date:** December 2025
**Status:** Proposed
**Decision Maker:** TBD

### Context
Core banking requires double-entry accounting ledger. Options:
1. Build custom ledger
2. Use existing ledger service
3. Use traditional accounting software

### Decision
**Use Formance Stack as the ledger system**

### Alternatives Considered

#### Option A: Build Custom Ledger
**Pros:**
- Full control
- No vendor lock-in
- Custom features

**Cons:**
- 12-18 months development time
- Complex accounting logic
- High risk of bugs
- Ongoing maintenance burden
- Need accounting expertise

**Verdict:** Too risky and time-consuming for MVP

#### Option B: TigerBeetle
**Pros:**
- Extremely high performance
- Purpose-built for finance
- Open source
- No vendor lock-in

**Cons:**
- Lower-level (requires more integration work)
- Less ecosystem
- Steeper learning curve
- Self-hosted only

**Verdict:** Great for high-frequency trading, overkill for us

#### Option C: Traditional Database (PostgreSQL)
**Pros:**
- Complete control
- Well understood
- No external dependency

**Cons:**
- No accounting primitives
- Must implement double-entry logic
- No audit trail out-of-box
- Complex transaction handling

**Verdict:** Too much work, high risk of accounting errors

### Consequences

**Positive:**
- Double-entry accounting out of the box
- Immutable audit trail
- Multi-currency support
- Battle-tested in production
- API-first design
- Active development
- Good documentation

**Negative:**
- Vendor dependency
- API rate limits (on free tier)
- Pricing model may change
- Learning curve for team
- Cloud-only (self-hosting not available)

### Migration Strategy
- Abstract Formance behind repository pattern
- Keep business logic separate from ledger operations
- Document all Formance-specific assumptions
- Plan for potential migration in 2-3 years

### Validation Questions for Team
- ❓ Are we comfortable with vendor dependency?
- ❓ What's our budget for Formance at scale?
- ❓ Do we need self-hosting capability?
- ❓ What's our abstraction strategy for potential migration?

---

## TDL-004: Repository Pattern for Data Access

**Date:** December 2025
**Status:** Proposed
**Decision Maker:** TBD

### Context
Need to abstract data access to:
- Isolate business logic from Formance
- Enable testing without external dependencies
- Allow future migration

### Decision
**Implement Repository Pattern with FormanceRepository**

### Rationale
```python
# Service doesn't know about Formance
class TransactionService:
    def __init__(self, repository: Repository):
        self.repository = repository

    async def create_transfer(self, ...):
        # Business logic
        await self.repository.post_transaction(...)

# Can swap implementations
class FormanceRepository(Repository):
    # Formance-specific implementation
    pass

class MockRepository(Repository):
    # Testing implementation
    pass

class PostgresRepository(Repository):
    # Future migration path
    pass
```

### Consequences

**Positive:**
- Testable without Formance
- Migration path preserved
- Clear separation of concerns
- Easier to mock in tests

**Negative:**
- Additional abstraction layer
- Slight performance overhead
- More code to maintain

### Validation Questions for Team
- ❓ Is this the right level of abstraction?
- ❓ Should we abstract further (generic ledger interface)?
- ❓ What other data sources need repositories?

---

## TDL-005: Async/Await Throughout

**Date:** December 2025
**Status:** Proposed
**Decision Maker:** TBD

### Context
Core banking involves many I/O operations:
- API calls to Formance
- Database queries
- External API calls (sanctions screening)
- Webhook deliveries

### Decision
**Use async/await for all I/O operations**

### Alternatives Considered

#### Option A: Synchronous Code
**Pros:**
- Simpler to understand
- Easier to debug
- More libraries available

**Cons:**
- Poor performance under load
- One request blocks others
- Lower throughput

**Verdict:** Unacceptable for API serving many concurrent requests

#### Option B: Threading
**Pros:**
- More intuitive than async
- Good for CPU-bound tasks

**Cons:**
- GIL limitations in Python
- Higher memory overhead
- Complex synchronization
- Race conditions

**Verdict:** Async is more efficient for I/O-bound workload

#### Option C: Celery for Everything
**Pros:**
- Distributed task execution
- Battle-tested

**Cons:**
- Adds complexity
- Requires message broker
- Overkill for synchronous API requests
- Latency overhead

**Verdict:** Use for background jobs only, not request handling

### Consequences

**Positive:**
- High concurrency (thousands of requests)
- Efficient resource usage
- Fast response times
- Modern Python best practice

**Negative:**
- More complex than sync code
- Async/sync mixing issues
- Debugging can be harder
- Not all libraries support async

### Coding Standards
```python
# Good: Async throughout
async def transfer_money(from_id: str, to_id: str, amount: Decimal):
    compliance = await check_compliance(...)
    await post_to_ledger(...)

# Bad: Mixing sync and async
async def transfer_money(from_id: str, to_id: str, amount: Decimal):
    compliance = check_compliance_sync(...)  # Blocks event loop!
    await post_to_ledger(...)
```

### Validation Questions for Team
- ❓ Does team have async/await experience?
- ❓ What's our strategy for sync libraries?
- ❓ How do we handle blocking operations?

---

## TDL-006: Pydantic v2 for Validation

**Date:** December 2025
**Status:** Proposed
**Decision Maker:** TBD

### Context
Need data validation for:
- API requests/responses
- Configuration
- Domain models
- Type safety

### Decision
**Use Pydantic v2 for all data validation and modeling**

### Alternatives Considered

#### Option A: Marshmallow
**Pros:**
- Mature library
- Separate serialization/deserialization
- Framework-agnostic

**Cons:**
- Slower than Pydantic v2
- More verbose
- No type hints integration

**Verdict:** Pydantic v2 is 10x faster, better integrated

#### Option B: Dataclasses + Manual Validation
**Pros:**
- Standard library
- Lightweight
- No dependencies

**Cons:**
- No automatic validation
- Manual serialization
- No automatic OpenAPI schema

**Verdict:** Too much manual work

#### Option C: Attrs
**Pros:**
- More features than dataclasses
- Good performance

**Cons:**
- No automatic validation
- Less FastAPI integration
- Smaller community

**Verdict:** Pydantic has better FastAPI integration

### Consequences

**Positive:**
- Type safety throughout application
- Automatic validation
- JSON serialization/deserialization
- OpenAPI schema generation
- Excellent IDE support
- 10x faster than Pydantic v1

**Negative:**
- Breaking changes from v1 (if migrating)
- Custom validators can be complex
- Learning curve for advanced features

### Example Usage
```python
class TransferRequest(BaseModel):
    from_account_id: str = Field(..., pattern=r"^acc_\w+$")
    to_account_id: str = Field(..., pattern=r"^acc_\w+$")
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    description: Optional[str] = Field(None, max_length=500)

    @model_validator(mode='after')
    def validate_different_accounts(self) -> 'TransferRequest':
        if self.from_account_id == self.to_account_id:
            raise ValueError("Cannot transfer to same account")
        return self
```

### Validation Questions for Team
- ❓ Is Pydantic v2 mature enough?
- ❓ Do we need custom validators?
- ❓ What's our migration strategy from v1 (if applicable)?

---

## TDL-007: No Frontend (API-Only)

**Date:** December 2025
**Status:** Proposed
**Decision Maker:** TBD

### Context
Need to decide whether to build frontend or focus on API.

### Decision
**Build API-only system, no frontend included**

### Rationale
- Focus on core banking logic
- Let customers build their own UIs
- Faster development (no UI complexity)
- B2B/developer-focused product
- API-first enables any client (web, mobile, etc.)

### Alternatives Considered

#### Option A: Admin Dashboard
**Pros:**
- Easier customer evaluation
- Internal operations support
- Common in enterprise software

**Cons:**
- 3-6 months additional development
- Maintenance burden
- Different technology stack
- May not fit all customers

**Verdict:** Can add later if needed, not critical for MVP

#### Option B: React Admin Panel
**Pros:**
- Quick to build with libraries
- Professional appearance

**Cons:**
- Still 2-3 months work
- Security considerations
- Deployment complexity

**Verdict:** Defer to post-MVP

### Consequences

**Positive:**
- Faster time to market
- Focus on core functionality
- Better API design (dogfooding not possible)
- Customers can build custom UIs
- Lower maintenance burden

**Negative:**
- Harder to demo
- Internal operations need API tools
- Customer onboarding less visual
- Testing requires API clients

### Mitigation
- Excellent API documentation
- Postman/Insomnia collections
- Code examples in multiple languages
- Video tutorials
- Swagger UI for testing

### Validation Questions for Team
- ❓ Can we effectively sell an API-only product?
- ❓ Do we need admin dashboard for internal use?
- ❓ What's our timeline for adding UI later?
- ❓ How will we demo to non-technical stakeholders?

---

## TDL-008: Multi-Tenancy Architecture

**Date:** December 2025
**Status:** Proposed
**Decision Maker:** TBD

### Context
Need to support multiple organizations on single deployment.

### Decision
**Implement multi-tenancy with organization-based isolation**

### Architecture
```
Single Deployment
├── Organization A (Acme Bank)
│   ├── Users (isolated)
│   ├── Customers (isolated)
│   ├── Accounts (isolated)
│   ├── Ledger: org_acme_bank
│   └── Configuration (isolated)
└── Organization B (Beta FinTech)
    ├── Users (isolated)
    ├── Customers (isolated)
    ├── Accounts (isolated)
    ├── Ledger: org_beta_fintech
    └── Configuration (isolated)
```

### Alternatives Considered

#### Option A: Separate Deployments Per Customer
**Pros:**
- Complete isolation
- Custom configurations
- Easier to debug

**Cons:**
- High operational overhead
- Expensive infrastructure
- Slow customer onboarding
- Hard to maintain

**Verdict:** Not scalable

#### Option B: Database-Per-Tenant
**Pros:**
- Good isolation
- Easy backup/restore per tenant
- Performance isolation

**Cons:**
- Complex management
- Schema migrations difficult
- Connection pool limits

**Verdict:** Over-engineered for MVP

#### Option C: Shared Database, Row-Level Security
**Pros:**
- Efficient resource usage
- Single schema to maintain
- Fast queries with proper indexes

**Cons:**
- Risk of data leakage
- Complex security model
- Query performance concerns

**Verdict:** Good for MVP, current approach

### Security Considerations
```python
# Every query must filter by organization_id
async def get_account(account_id: str, organization_id: str):
    # ALWAYS include organization_id in query
    account = await repository.get_account(account_id)
    if account.organization_id != organization_id:
        raise ForbiddenError()
    return account
```

### Consequences

**Positive:**
- Cost-effective
- Fast customer onboarding
- Shared infrastructure
- Easy updates

**Negative:**
- Security is critical
- "Noisy neighbor" potential
- Complex testing
- Data segregation required

### Validation Questions for Team
- ❓ Is our isolation strategy sufficient?
- ❓ What if a customer needs dedicated infrastructure?
- ❓ How do we prevent data leakage?
- ❓ What's our migration path to separate deployments?

---

## TDL-009: Testing Strategy

**Date:** December 2025
**Status:** Proposed
**Decision Maker:** TBD

### Context
Need comprehensive testing for financial system.

### Decision
**Multi-layered testing approach:**
1. Unit tests (80%+ coverage)
2. Integration tests
3. E2E tests
4. Load tests
5. Compliance test suite

### Test Structure
```
tests/
├── unit/               # Fast, isolated
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_validators.py
│   └── test_regulatory.py
├── integration/        # With external services
│   ├── test_formance_integration.py
│   ├── test_api_endpoints.py
│   └── test_compliance_flow.py
├── e2e/               # Full workflows
│   ├── test_account_lifecycle.py
│   ├── test_payment_flows.py
│   └── test_compliance_scenarios.py
└── load/              # Performance
    └── locustfile.py
```

### Testing Principles
1. **Unit Tests** - Fast, isolated, no external dependencies
2. **Mocking** - Mock Formance, external APIs
3. **Fixtures** - Reusable test data
4. **Async Tests** - pytest-asyncio for async code
5. **Coverage** - Minimum 80% for business logic

### Validation Questions for Team
- ❓ What's our target test coverage?
- ❓ How do we test compliance rules?
- ❓ Do we need contract testing?
- ❓ What's our load testing strategy?

---

## TDL-010: Error Handling Strategy

**Date:** December 2025
**Status:** Proposed
**Decision Maker:** TBD

### Context
Banking systems require robust error handling.

### Decision
**Structured exception hierarchy with proper HTTP mappings**

### Exception Hierarchy
```python
BankingException (base)
├── AccountNotFoundError (404)
├── InsufficientFundsError (400)
├── ComplianceError (400)
│   ├── KYCRequiredError
│   └── TransactionBlockedError
├── RegulatoryReportError (400)
├── ValidationError (422)
└── FormanceAPIError (502)
```

### Error Response Format
```json
{
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "Account balance too low for withdrawal",
    "details": {
      "account_id": "acc_123",
      "balance": "50.00",
      "requested": "100.00"
    },
    "timestamp": "2025-12-10T10:00:00Z",
    "request_id": "req_abc123"
  }
}
```

### Validation Questions for Team
- ❓ Is this error structure appropriate?
- ❓ How much detail should we expose?
- ❓ Do we need error codes catalog?
- ❓ What's our logging strategy for errors?

---

## Decisions Pending Team Input

### Database Selection
- **Status:** Open
- **Options:** PostgreSQL, Formance-only, CockroachDB
- **Context:** Need to decide on metadata storage

### Authentication Method
- **Status:** Open
- **Options:** JWT, OAuth2, API Keys, Session-based
- **Context:** How do customers authenticate?

### Caching Strategy
- **Status:** Open
- **Options:** Redis, In-memory, None
- **Context:** When to introduce caching?

### Message Queue
- **Status:** Open
- **Options:** RabbitMQ, Kafka, None (asyncio only)
- **Context:** Do we need message queue?

### Deployment Platform
- **Status:** Open
- **Options:** AWS, GCP, Azure, DigitalOcean
- **Context:** Where to host?

---

## Review Checklist

For each decision, the team should evaluate:

- [ ] **Understand the context** - Why is this decision needed?
- [ ] **Review alternatives** - Were other options properly considered?
- [ ] **Assess risks** - What could go wrong?
- [ ] **Check mitigation** - Are risks addressed?
- [ ] **Validate assumptions** - Are underlying assumptions correct?
- [ ] **Consider future** - Will this scale? Can we change it later?
- [ ] **Team capability** - Do we have skills to execute?
- [ ] **Cost implications** - What's the financial impact?

---

## Next Steps

1. **Schedule Decision Review Meeting**
   - Go through each decision
   - Discuss concerns and alternatives
   - Vote on acceptance/rejection

2. **Document Outcomes**
   - Update status for each decision
   - Record team consensus
   - Note any modifications

3. **Create Action Items**
   - Assign owners for implementation
   - Set timelines
   - Track progress

---

**Prepared By:** Technical Team
**Review Status:** Awaiting Team Validation
**Next Review:** Team Meeting
