# Tools and Infrastructure Requirements

**Document Version:** 1.0
**Date:** December 10, 2025
**Purpose:** Define all tools, services, and infrastructure needed for development, deployment, and operation

---

## Overview

This document outlines the complete tooling and infrastructure ecosystem required to build, deploy, and operate the BaaS core banking system.

---

## Development Environment

### Required Tools

| Tool | Version | Purpose | Cost | Priority |
|------|---------|---------|------|----------|
| **Python** | 3.13+ | Runtime | Free | Critical |
| **uv** or **pip** | Latest | Package management | Free | Critical |
| **Git** | 2.x+ | Version control | Free | Critical |
| **Docker** | Latest | Containerization | Free | Critical |
| **Docker Compose** | Latest | Local multi-service | Free | Critical |
| **VS Code** or **PyCharm** | Latest | IDE | Free/Paid | High |
| **Postman** or **Insomnia** | Latest | API testing | Free | High |

### Installation Commands

```bash
# Python (macOS)
brew install python@3.13

# uv (recommended package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Docker
brew install --cask docker

# Git
brew install git

# VS Code
brew install --cask visual-studio-code
```

### Python Package Requirements

```toml
# pyproject.toml
[project]
name = "baas-core-banking"
version = "0.1.0"
requires-python = ">=3.13"

dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "formance-sdk>=1.0.0",
    "httpx>=0.26.0",
    "python-multipart>=0.0.6",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
    "black>=23.12.0",
]
```

---

## External Services

### Core Services (Critical)

#### 1. Formance Stack
- **Purpose:** Ledger system, payment orchestration
- **Components:**
  - Formance Ledger (double-entry accounting)
  - Formance Payments (payment processing)
  - Formance Wallets (balance management)
- **Pricing:**
  - Free tier: Development/testing
  - Pro tier: $299/month (estimated)
  - Enterprise: Custom pricing
- **Setup:**
  1. Sign up at [formance.com](https://formance.com)
  2. Create new stack
  3. Generate API credentials
  4. Configure `.env` file
- **Alternatives if not approved:**
  - TigerBeetle (open source, more work)
  - Custom ledger (12-18 months development)
  - PostgreSQL with custom accounting logic (high risk)

**Formance Configuration:**
```bash
# .env
FORMANCE_BASE_URL=https://api.formance.cloud
FORMANCE_CLIENT_ID=your_client_id_here
FORMANCE_CLIENT_SECRET=your_secret_here
FORMANCE_ORGANIZATION_ID=your_org_id_here
```

**Monthly Cost Estimate:**
- Development: $0 (free tier)
- Staging: $299/month
- Production: $299-999/month (depends on volume)

### Database (Pending Decision)

#### Option A: PostgreSQL (Recommended for MVP)
- **Purpose:** Metadata storage (users, organizations, compliance reports)
- **Hosting Options:**
  - Self-hosted (Docker): Free
  - AWS RDS: ~$50-200/month
  - DigitalOcean Managed: ~$15-60/month
  - Supabase: Free tier, then ~$25/month
- **Setup:**
  ```bash
  docker run -d \
    --name postgres \
    -e POSTGRES_PASSWORD=secret \
    -e POSTGRES_DB=banking \
    -p 5432:5432 \
    postgres:16-alpine
  ```
- **Decision Needed:** Do we need this for MVP or rely on Formance only?

#### Option B: Formance Only
- **Pros:** Simpler architecture, one less service
- **Cons:** Limited query capabilities, may need database later
- **Verdict:** Start here, add PostgreSQL when needed

### Caching (Future - Not MVP)

#### Redis
- **Purpose:** Session storage, rate limiting, cache
- **When Needed:** When we see performance issues
- **Hosting:**
  - Self-hosted: Free
  - Redis Cloud: Free tier, then ~$7/month
  - AWS ElastiCache: ~$15/month
- **Decision:** Defer to post-MVP

---

## Development Tools

### Code Quality

| Tool | Purpose | Configuration | When to Run |
|------|---------|---------------|-------------|
| **Ruff** | Linting & formatting | `ruff.toml` | Pre-commit |
| **mypy** | Static type checking | `mypy.ini` | Pre-commit |
| **pytest** | Testing | `pytest.ini` | Pre-commit |
| **pytest-cov** | Coverage reporting | In pytest | CI/CD |

### Ruff Configuration

```toml
# ruff.toml
line-length = 100
target-version = "py313"

[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
]
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic>=2.5.0]

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

**Setup:**
```bash
pip install pre-commit
pre-commit install
```

---

## CI/CD Pipeline

### GitHub Actions (Recommended)

**Why:** Free for public repos, easy integration, good Python support

**.github/workflows/ci.yml:**
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Lint
        run: uv run ruff check .

      - name: Type check
        run: uv run mypy core

      - name: Test
        run: uv run pytest --cov=core --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Alternative: GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  image: python:3.13
  script:
    - pip install uv
    - uv sync
    - uv run pytest --cov=core
```

### Decision Needed
- ❓ GitHub Actions or GitLab CI?
- ❓ What triggers deployment?
- ❓ Do we need staging environment?

---

## Deployment Infrastructure

### Option A: AWS (Enterprise Grade)

**Services Needed:**
- **ECS Fargate** - Container orchestration (~$30-100/month)
- **RDS PostgreSQL** - Database (~$50-200/month)
- **ElastiCache Redis** - Caching (~$15-50/month)
- **CloudWatch** - Logging/monitoring (~$10-30/month)
- **ALB** - Load balancer (~$20/month)
- **Route53** - DNS (~$1/month)
- **ACM** - SSL certificates (Free)

**Total: ~$126-401/month**

**Pros:**
- Enterprise-grade
- Excellent tooling
- Auto-scaling
- Good compliance options

**Cons:**
- Complex setup
- Higher cost
- Steeper learning curve

### Option B: DigitalOcean (Cost-Effective)

**Services Needed:**
- **App Platform** - Container hosting (~$12-24/month)
- **Managed Database** - PostgreSQL (~$15-60/month)
- **Managed Redis** - Caching (~$15/month)
- **Spaces** - Object storage (~$5/month)

**Total: ~$47-104/month**

**Pros:**
- Simple setup
- Lower cost
- Good documentation
- Managed services

**Cons:**
- Less enterprise features
- Limited regions
- Smaller ecosystem

### Option C: Railway (Fastest Setup)

**Services:**
- **Railway** - All-in-one platform (~$20-50/month)
  - Automatic deploys from Git
  - Built-in PostgreSQL
  - Built-in Redis
  - SSL included

**Pros:**
- Fastest to deploy
- Git-based deploys
- Very simple
- Good for MVP

**Cons:**
- Less control
- Limited scaling
- Vendor lock-in

### Recommendation
**MVP:** Railway or DigitalOcean App Platform
**Production:** AWS or GCP with proper redundancy

---

## Monitoring & Observability

### Required for Production

#### Application Performance Monitoring (APM)

**Option A: Sentry (Recommended)**
- **Purpose:** Error tracking, performance monitoring
- **Pricing:** Free (5K errors/month), then $26/month
- **Setup:**
  ```python
  import sentry_sdk

  sentry_sdk.init(
      dsn="your-dsn",
      traces_sample_rate=1.0,
  )
  ```

**Option B: DataDog**
- **Purpose:** Full observability platform
- **Pricing:** $15/host/month
- **Pros:** Comprehensive, excellent dashboards
- **Cons:** More expensive

**Option C: New Relic**
- **Purpose:** APM and monitoring
- **Pricing:** Free tier, then $49/month
- **Pros:** Powerful, good Python support

**Decision:** Start with Sentry (cheaper), consider DataDog for production

#### Logging

**Option A: Structured Logging (stdlib)**
```python
import logging
import json

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
```

**Option B: Loguru (Better DX)**
```python
from loguru import logger

logger.add("app.log", rotation="500 MB")
logger.info("Transaction processed", transaction_id="txn_123")
```

**Option C: ELK Stack (Enterprise)**
- Elasticsearch + Logstash + Kibana
- Expensive and complex
- Only for large scale

**Recommendation:** Loguru for MVP, ELK later if needed

#### Metrics

**Prometheus + Grafana (Standard)**
- **Prometheus:** Metrics collection
- **Grafana:** Visualization
- **Cost:** Self-hosted (free) or cloud (~$49/month)
- **Setup:**
  ```python
  from prometheus_client import Counter, Histogram

  transaction_counter = Counter('transactions_total', 'Total transactions')
  transaction_duration = Histogram('transaction_duration_seconds', 'Transaction duration')
  ```

---

## Security Tools

### Required

| Tool | Purpose | Cost | When |
|------|---------|------|------|
| **SSL/TLS Certificates** | HTTPS | Free (Let's Encrypt) | Production |
| **Secrets Management** | Environment variables | Free (cloud native) | MVP |
| **SAST (Bandit)** | Security scanning | Free | CI/CD |
| **Dependency Scanning** | Vulnerable packages | Free (Dependabot) | CI/CD |
| **Vault** (future) | Secrets management | Self-host or $0.03/hour | Post-MVP |

### Security Scanning

```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r core/ -ll

      - name: Check dependencies
        run: |
          pip install safety
          safety check
```

---

## Compliance & Regulatory Tools

### Sanctions Screening

**Current:** Built-in (simplified for MVP)
**Future Options:**
- **Dow Jones Risk & Compliance** - $$$
- **Refinitiv World-Check** - $$$
- **ComplyAdvantage** - $$$
- **Decision:** Build basic version, integrate paid service later

### KYC/Identity Verification

**Options:**
- **Stripe Identity** - $1.50/verification
- **Onfido** - $1-3/check
- **Persona** - $1/verification
- **Jumio** - Enterprise pricing
- **Decision:** Future integration, manual KYC for MVP

### Document Storage (Compliance Documents)

**Options:**
- **AWS S3** - ~$0.023/GB/month
- **DigitalOcean Spaces** - $5/month (250GB)
- **Backblaze B2** - $5/TB/month
- **Decision:** Needed when storing CTR/SAR documents

---

## Communication & Collaboration Tools

### Team Tools

| Tool | Purpose | Cost | Priority |
|------|---------|------|----------|
| **Slack/Discord** | Team communication | Free | High |
| **GitHub** | Code repository | Free | Critical |
| **Notion/Confluence** | Documentation | Free/Paid | Medium |
| **Linear/Jira** | Project management | Free/Paid | Medium |
| **Figma** | Design (if UI needed) | Free | Low |

### Customer Communication

| Tool | Purpose | Cost | When |
|------|---------|------|------|
| **Intercom** | Support chat | $39/month | Launch |
| **SendGrid** | Transactional email | Free (100/day) | MVP |
| **Twilio** | SMS notifications | Pay-as-you-go | Post-MVP |

---

## Development Workflow Tools

### Local Development

```bash
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FORMANCE_BASE_URL=${FORMANCE_BASE_URL}
      - FORMANCE_CLIENT_ID=${FORMANCE_CLIENT_ID}
      - FORMANCE_CLIENT_SECRET=${FORMANCE_CLIENT_SECRET}
    volumes:
      - ./core:/app/core
    command: uvicorn core.api.app:app --reload --host 0.0.0.0

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=banking
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=secret
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

**Start everything:**
```bash
docker-compose up -d
```

### API Documentation

**Swagger UI** (Built-in with FastAPI)
- URL: `http://localhost:8000/docs`
- Auto-generated from code
- Interactive API testing

**ReDoc** (Also built-in)
- URL: `http://localhost:8000/redoc`
- Better for reading

**Postman Collections** (Manual)
- Export from Swagger
- Share with team/customers

---

## Cost Summary

### MVP (First 3 Months)

| Service | Cost/Month | Notes |
|---------|------------|-------|
| **Formance** | $0 | Free tier |
| **Hosting (Railway)** | $20 | MVP hosting |
| **Domain** | $1 | .com domain |
| **GitHub** | $0 | Public repo |
| **Sentry** | $0 | Free tier |
| **SendGrid** | $0 | 100 emails/day |
| **Development Tools** | $0 | All open source |
| **Total MVP** | **$21/month** | Very affordable |

### Production (Scaling)

| Service | Cost/Month | Notes |
|---------|------------|-------|
| **Formance** | $299 | Pro tier |
| **AWS/DigitalOcean** | $150 | Hosting + DB |
| **Sentry** | $26 | Paid tier |
| **Domain + SSL** | $1 | Certificates |
| **Monitoring (DataDog)** | $49 | Optional |
| **SendGrid** | $20 | 50K emails |
| **Support Tools** | $39 | Intercom |
| **Total Production** | **$584/month** | With all services |

### Enterprise (At Scale)

| Service | Cost/Month | Notes |
|---------|------------|-------|
| **Formance** | $999 | Enterprise |
| **AWS** | $1000+ | Multi-region |
| **DataDog** | $150 | Full observability |
| **Compliance Services** | $500+ | KYC, Sanctions |
| **Support** | $200 | Multiple tools |
| **Total Enterprise** | **$2,849+/month** | Full production stack |

---

## Tool Selection Checklist

For each tool, evaluate:

- [ ] **Cost:** Within budget?
- [ ] **Complexity:** Can team operate it?
- [ ] **Support:** Good documentation and community?
- [ ] **Integration:** Works with our stack?
- [ ] **Scalability:** Handles growth?
- [ ] **Vendor Risk:** What if they shut down?
- [ ] **Compliance:** Meets regulatory requirements?
- [ ] **Migration:** Can we switch later if needed?

---

## Infrastructure Decisions Needed

### Immediate (Before Starting)
1. ✅ **Python & FastAPI** - Confirmed
2. ✅ **Formance** - Confirmed
3. ❓ **Hosting Platform** - Railway vs DigitalOcean vs AWS?
4. ❓ **CI/CD** - GitHub Actions or GitLab CI?
5. ❓ **Error Tracking** - Sentry or alternative?

### Short Term (First Month)
6. ❓ **Database** - PostgreSQL now or later?
7. ❓ **Caching** - Redis now or defer?
8. ❓ **Logging** - Loguru vs stdlib?
9. ❓ **Monitoring** - Start with basics or full observability?

### Medium Term (First Quarter)
10. ❓ **Secrets Management** - When to add Vault?
11. ❓ **Message Queue** - RabbitMQ/Kafka or async only?
12. ❓ **KYC Integration** - Which provider?
13. ❓ **Email Service** - SendGrid or alternative?

---

## Setup Checklist for New Developer

```bash
# 1. Install prerequisites
brew install python@3.13 git docker

# 2. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Clone repository
git clone <repo-url>
cd core

# 4. Install dependencies
uv sync

# 5. Set up environment
cp .env.example .env
# Edit .env with your Formance credentials

# 6. Run tests
uv run pytest

# 7. Start development server
uv run uvicorn core.api.app:app --reload

# 8. Open API docs
open http://localhost:8000/docs
```

**Time to first API call:** < 10 minutes

---

## Questions for Team

### Infrastructure
- ❓ What's our cloud platform preference (AWS/GCP/Azure/DO)?
- ❓ Do we need multi-region deployment for MVP?
- ❓ What's our budget for external services?
- ❓ Who manages infrastructure (DevOps role)?

### Tools
- ❓ Which monitoring/APM tool should we use?
- ❓ Do we need paid database hosting or self-host?
- ❓ What's our stance on vendor dependencies?
- ❓ Which compliance services should we integrate?

### Process
- ❓ What's our deployment frequency (continuous, weekly, monthly)?
- ❓ Who approves production deployments?
- ❓ Do we need staging environment?
- ❓ What's our incident response plan?

---

## Next Steps

1. **Review This Document** - Team validates tool choices
2. **Make Decisions** - Answer all open questions
3. **Set Up Accounts** - Create accounts for selected services
4. **Configure Environment** - Set up development environment
5. **Test Integration** - Verify all tools work together
6. **Document Process** - Update runbooks and guides

---

**Prepared By:** Technical Team
**Review Status:** Awaiting Validation
**Last Updated:** December 10, 2025
