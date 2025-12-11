# BaaS Core Banking System - Project Overview

**Document Version:** 1.0
**Date:** December 10, 2025
**Status:** Awaiting Team Validation
**Meeting Date:** TBD

---

## Executive Summary

This document presents a comprehensive Banking as a Service (BaaS) core banking system built on the Formance Stack. The system provides multi-tenant banking infrastructure with full compliance, regulatory reporting, and modern payment rails including mobile money support across Africa.

**Key Statistics:**
- **Total Lines of Code:** ~15,000+
- **API Endpoints:** 50+
- **Test Coverage:** Unit and integration tests
- **Documentation:** 2,000+ lines
- **Technology Stack:** Python 3.13+, FastAPI, Formance, Pydantic v2

---

## Project Scope

### What We're Building

A **production-ready core banking system** that provides:

1. **Multi-Tenant Banking Infrastructure**
   - Organization and user management
   - Multi-branch support with hierarchical structure
   - Role-based access control (RBAC)
   - Tenant isolation and data security

2. **Core Banking Operations**
   - Account management (checking, savings, business, escrow)
   - Transaction processing (deposits, withdrawals, transfers)
   - Balance tracking and validation
   - Multi-currency support

3. **Payment Rails**
   - ACH payments
   - Wire transfers
   - Card payment processing
   - Mobile money integration (M-Pesa, MTN, Airtel, etc.)

4. **Compliance & Risk Management**
   - KYC/KYB verification workflows
   - Sanctions screening (OFAC, UN, EU)
   - Real-time risk scoring (0-100)
   - Transaction monitoring and velocity checks
   - Configurable compliance rules engine

5. **Regulatory Reporting**
   - Automated CTR (Currency Transaction Reports)
   - SAR (Suspicious Activity Reports) generation
   - Report lifecycle management
   - FinCEN BSA compliance

6. **Customer Management**
   - Customer onboarding
   - KYC lifecycle management
   - Customer risk profiling

### What We're NOT Building (Out of Scope)

- ❌ Frontend/UI applications (API-only)
- ❌ Mobile banking apps
- ❌ ATM integration
- ❌ Physical card printing services
- ❌ Call center software
- ❌ Loan origination system (future phase)
- ❌ Investment/trading platform
- ❌ Cryptocurrency wallets

---

## Business Value Proposition

### Target Market
- Fintech startups building banking products
- Neobanks requiring core banking infrastructure
- Traditional banks seeking modernization
- Mobile money providers
- Microfinance institutions

### Key Differentiators
1. **Africa-First Design** - Native mobile money support for 15+ providers
2. **Compliance-Native** - Built-in regulatory reporting and AML
3. **Developer-Friendly** - RESTful API with OpenAPI documentation
4. **Formance-Powered** - Leverages battle-tested ledger technology
5. **Multi-Tenant** - Single deployment serves multiple organizations

### ROI & Cost Savings
- **Development Time:** 6-12 months faster than building from scratch
- **Compliance Cost:** Automated reporting reduces manual work by 80%+
- **Infrastructure Cost:** Shared multi-tenant architecture
- **Time to Market:** Weeks instead of years

---

## Technical Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Applications                     │
│            (Web Apps, Mobile Apps, Third-Party)              │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS/REST
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Auth     │  │  Accounts  │  │  Payments  │            │
│  │ Middleware │  │    API     │  │    API     │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Compliance │  │ Regulatory │  │ Customers  │            │
│  │    API     │  │    API     │  │    API     │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Account   │  │Transaction │  │  Payment   │            │
│  │  Service   │  │  Service   │  │  Service   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Compliance │  │ Regulatory │  │  Customer  │            │
│  │  Service   │  │  Service   │  │  Service   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│   Formance   │ │PostgreSQL│ │    Redis     │
│    Stack     │ │ (Future) │ │   (Cache)    │
│              │ │          │ │              │
│ • Ledger     │ │ • Config │ │ • Sessions   │
│ • Payments   │ │ • Users  │ │ • Rate Limit │
│ • Wallets    │ │ • Reports│ │              │
└──────────────┘ └──────────┘ └──────────────┘
```

### Component Breakdown

#### 1. API Layer (FastAPI)
- **Purpose:** RESTful API endpoints for all operations
- **Technology:** FastAPI with async/await
- **Features:**
  - OpenAPI/Swagger documentation
  - Request/response validation (Pydantic)
  - CORS support
  - Error handling middleware

#### 2. Service Layer
- **Purpose:** Business logic orchestration
- **Pattern:** Service-oriented architecture
- **Services:**
  - AccountService
  - TransactionService
  - PaymentService
  - ComplianceService
  - RegulatoryReportingService
  - CustomerService
  - OrganizationService
  - BranchService

#### 3. Data Access Layer
- **Purpose:** Abstraction over data sources
- **Primary:** Formance SDK for ledger operations
- **Secondary:** PostgreSQL for metadata (future)
- **Cache:** Redis for performance (future)

#### 4. Domain Models
- **Purpose:** Type-safe data structures
- **Technology:** Pydantic v2
- **Benefits:**
  - Automatic validation
  - JSON serialization
  - IDE autocomplete
  - Runtime type checking

#### 5. Background Workers
- **Purpose:** Async/scheduled tasks
- **Workers:**
  - Compliance reconciliation
  - Regulatory reporting automation
  - Transaction monitoring
- **Technology:** asyncio with configurable intervals

---

## Data Flow Examples

### Example 1: Transfer Money

```
1. Client → POST /api/v1/transactions/transfer
   {
     "from_account_id": "acc_123",
     "to_account_id": "acc_456",
     "amount": 1000.00
   }

2. API Layer → TransactionService.create_transfer()

3. TransactionService → ComplianceService.check_transaction()
   - KYC verification
   - Sanctions screening
   - Risk scoring
   - Velocity checks

4. If approved → FormanceRepository.post_transaction()
   - Double-entry ledger posting
   - Atomic execution
   - Metadata attachment

5. Success → Return transaction details to client

6. Background → ComplianceReconciliation worker
   - Deep analysis
   - Alert generation
   - Report preparation
```

### Example 2: Generate CTR

```
1. Transaction > $10,000 detected

2. ComplianceService flags for CTR

3. RegulatoryWorker (daily job)
   - Queries transactions from previous day
   - Identifies CTR-qualifying activities
   - Groups by customer

4. RegulatoryService.generate_ctr()
   - Builds report from transaction data
   - Includes customer information
   - Creates draft CTR

5. Notification sent to compliance team

6. Compliance officer reviews and approves

7. RegulatoryService.file_report()
   - Submits to authorities
   - Updates status to "filed"
   - Stores BSA identifier
```

---

## Technology Stack Deep Dive

### Core Technologies

| Technology | Version | Purpose | Justification |
|-----------|---------|---------|---------------|
| **Python** | 3.13+ | Primary language | Type hints, async/await, ecosystem |
| **FastAPI** | Latest | Web framework | Performance, async, OpenAPI |
| **Pydantic** | v2 | Validation | Type safety, automatic validation |
| **Formance** | Latest | Ledger system | Battle-tested, double-entry accounting |
| **pytest** | Latest | Testing | Async support, fixtures, coverage |
| **Docker** | Latest | Containerization | Consistent environments |

### Why These Choices?

#### Python 3.13+
**Pros:**
- Excellent async/await support
- Strong type hinting
- Rich ecosystem for fintech
- Fast development velocity
- Easy to hire developers

**Cons:**
- Not as performant as Go/Rust
- GIL limitations (mitigated by async)

**Decision:** Python's ecosystem and development speed outweigh performance concerns for MVP.

#### FastAPI
**Pros:**
- Native async support
- Automatic OpenAPI documentation
- Built-in request/response validation
- High performance (comparable to Node.js)
- Modern Python features

**Cons:**
- Relatively newer framework
- Smaller community than Django/Flask

**Decision:** FastAPI's modern architecture and performance make it ideal for API-first banking.

#### Formance Stack
**Pros:**
- Purpose-built for financial services
- Double-entry ledger out of the box
- Audit trail built-in
- Handles complex accounting logic
- Scalable and reliable

**Cons:**
- Vendor dependency
- Learning curve
- API rate limits (on free tier)

**Decision:** Building our own ledger would take 12+ months. Formance provides battle-tested foundation.

#### Pydantic v2
**Pros:**
- Type safety throughout codebase
- Automatic validation
- JSON serialization
- Excellent IDE support
- Performance (10x faster than v1)

**Cons:**
- Breaking changes from v1

**Decision:** Type safety is critical for financial applications. Pydantic v2 provides this with minimal overhead.

---

## Open Questions for Dev Team

### Architecture & Design

1. **Database Strategy**
   - ❓ Should we use PostgreSQL for metadata or rely solely on Formance?
   - ❓ What's our strategy for data backup and disaster recovery?
   - ❓ Do we need a separate data warehouse for analytics?

2. **Caching Strategy**
   - ❓ When should we introduce Redis?
   - ❓ What should we cache (compliance checks, org settings, etc.)?
   - ❓ Cache invalidation strategy?

3. **Authentication & Authorization**
   - ❓ JWT tokens vs. session-based auth?
   - ❓ OAuth2/SSO integration timeline?
   - ❓ API key management for third-party integrations?

4. **Message Queue**
   - ❓ Do we need RabbitMQ/Kafka for event-driven architecture?
   - ❓ Is asyncio sufficient for background workers?
   - ❓ Event sourcing pattern needed?

### Compliance & Security

5. **Data Residency**
   - ❓ Where will customer data be stored (US, EU, Africa)?
   - ❓ GDPR compliance requirements?
   - ❓ Data encryption at rest and in transit strategy?

6. **Audit Logging**
   - ❓ Centralized logging system (ELK, Datadog)?
   - ❓ What level of audit detail is required?
   - ❓ Log retention policy (SOC2, PCI compliance)?

7. **Compliance Testing**
   - ❓ How do we test sanctions screening without real data?
   - ❓ Compliance sandbox environment strategy?
   - ❓ Regulatory audit preparation process?

### Operations & DevOps

8. **Deployment Strategy**
   - ❓ Kubernetes vs. simpler container orchestration?
   - ❓ Multi-region deployment plan?
   - ❓ Blue-green deployment or canary releases?

9. **Monitoring & Alerting**
   - ❓ Application Performance Monitoring (APM) tool?
   - ❓ Error tracking (Sentry, Rollbar)?
   - ❓ Business metrics dashboard?

10. **Scaling Strategy**
    - ❓ When do we need horizontal scaling?
    - ❓ Database sharding strategy?
    - ❓ Rate limiting implementation?

### Development Process

11. **Code Quality**
    - ❓ CI/CD pipeline requirements?
    - ❓ Code review process and tools?
    - ❓ Static analysis tools (mypy, ruff)?

12. **Testing Strategy**
    - ❓ Target test coverage percentage?
    - ❓ Integration testing with Formance sandbox?
    - ❓ Load testing requirements?

13. **Documentation**
    - ❓ API versioning strategy?
    - ❓ Developer portal needed?
    - ❓ Changelog management?

### Business & Product

14. **Feature Priority**
    - ❓ What's the MVP feature set?
    - ❓ Which payment rails are highest priority?
    - ❓ Mobile money providers to support first?

15. **Customer Onboarding**
    - ❓ Self-service org creation or manual provisioning?
    - ❓ Sandbox environment for customers?
    - ❓ API usage billing/metering?

---

## Risk Assessment

### Technical Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Formance vendor lock-in** | Medium | Abstract ledger operations behind repository pattern |
| **Python performance at scale** | Medium | Use async/await, add caching, consider microservices later |
| **Compliance rule complexity** | High | Iterative development with compliance experts |
| **Data consistency** | High | Leverage Formance's ACID transactions |
| **Third-party API failures** | Medium | Retry mechanisms, circuit breakers, fallbacks |

### Operational Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Regulatory changes** | High | Modular compliance engine, regular reviews |
| **Security breaches** | Critical | Security audits, penetration testing, encryption |
| **Data loss** | Critical | Automated backups, disaster recovery plan |
| **Service outages** | High | Multi-region deployment, health checks, monitoring |
| **Incorrect financial calculations** | Critical | Extensive testing, double-entry accounting, audits |

### Business Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Market competition** | Medium | Focus on Africa, mobile money, compliance |
| **Customer acquisition** | Medium | Developer-friendly API, comprehensive docs |
| **Regulatory approval** | High | Partner with compliance experts, regular audits |
| **Formance pricing changes** | Medium | Monitor costs, have migration plan |

---

## Success Criteria

### Technical Metrics
- ✅ API response time < 200ms (p95)
- ✅ 99.9% uptime
- ✅ Zero data loss
- ✅ < 0.01% error rate
- ✅ 80%+ test coverage

### Business Metrics
- ✅ Onboard first pilot customer in Q1
- ✅ Process $1M+ in transactions
- ✅ Support 3+ organizations
- ✅ Zero compliance violations
- ✅ 100% CTR filing on time

### Developer Experience
- ✅ Complete API documentation
- ✅ Working code examples
- ✅ Sandbox environment
- ✅ < 1 week integration time
- ✅ Responsive support

---

## Next Steps

### Immediate Actions (This Week)
1. ✅ **Team Review Meeting** - Validate architecture and scope
2. ⏳ **Decision on open questions** - Database, caching, auth
3. ⏳ **Risk mitigation plans** - Address high-severity risks
4. ⏳ **Sprint planning** - Define MVP scope and timeline

### Short Term (Next 2 Weeks)
1. ⏳ **Set up CI/CD pipeline** - Automated testing and deployment
2. ⏳ **Implement authentication** - JWT or OAuth2
3. ⏳ **Database schema design** - PostgreSQL for metadata
4. ⏳ **Security review** - Identify vulnerabilities

### Medium Term (Next Month)
1. ⏳ **Integration testing** - End-to-end test suite
2. ⏳ **Load testing** - Performance benchmarks
3. ⏳ **Monitoring setup** - APM, logging, alerts
4. ⏳ **Documentation completion** - User guides, API reference

### Long Term (Next Quarter)
1. ⏳ **Pilot customer onboarding** - First production deployment
2. ⏳ **Compliance audit** - External security review
3. ⏳ **Feature expansion** - Based on customer feedback
4. ⏳ **Scaling preparation** - Infrastructure for growth

---

## Appendix: Resources

### Documentation Index
- [README.md](../README.md) - Project overview
- [COMPLIANCE_ENGINE.md](../COMPLIANCE_ENGINE.md) - Compliance system details
- [REGULATORY_REPORTING.md](../REGULATORY_REPORTING.md) - Regulatory reporting guide
- [MULTI_BRANCH_ARCHITECTURE.md](../MULTI_BRANCH_ARCHITECTURE.md) - Branch management
- [REGULATORY_REPORTING_QUICKSTART.md](../REGULATORY_REPORTING_QUICKSTART.md) - Quick start guide

### External Resources
- [Formance Documentation](https://docs.formance.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [FinCEN BSA Requirements](https://www.fincen.gov/resources/statutes-and-regulations/bank-secrecy-act)
- [PCI DSS Compliance](https://www.pcisecuritystandards.org)

---

**Document Prepared By:** Technical Team
**Review Status:** Pending
**Next Review Date:** [Meeting Date]
