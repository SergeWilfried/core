# Compliance Engine Integration Guide

## Overview

The BaaS Core Banking System now includes a comprehensive compliance engine for KYC/AML, transaction monitoring, and regulatory compliance. This guide explains the architecture, integration, and usage.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  API Layer (FastAPI)                                        │
│  POST /api/v1/payments, POST /api/v1/transactions          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  ComplianceService - Pre-Transaction Checks                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 1. KYC/KYB Verification                               │  │
│  │ 2. Sanctions Screening (OFAC, UN, EU)                │  │
│  │ 3. Organization Settings Validation                   │  │
│  │ 4. Velocity/Pattern Monitoring                        │  │
│  │ 5. Geographic Risk Assessment                         │  │
│  │ 6. Custom Rules Evaluation                            │  │
│  │ 7. Risk Score Calculation                             │  │
│  └───────────────────────────────────────────────────────┘  │
│                 ↓ APPROVED / REVIEW / BLOCKED               │
└─────────────────────────────────────────────────────────────┘
           ↓ If APPROVED                    ↓ If BLOCKED
┌──────────────────────────┐      ┌─────────────────────────┐
│  Payment/Transaction     │      │  Return HTTP 403        │
│  Services Process        │      │  + Compliance Reason    │
└──────────────────────────┘      └─────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│  Formance SDK - Ledger Recording                            │
│  • Create payment in Formance                               │
│  • Post ledger transaction with compliance metadata         │
│  • Immutable audit trail                                    │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Compliance Models

Located in `core/models/compliance.py`:

- **ComplianceCheck**: Record of compliance check performed
- **RiskScore**: Customer/transaction risk scoring
- **SanctionMatch**: Sanctions screening results
- **VelocityCheck**: Transaction velocity monitoring
- **ComplianceAlert**: Suspicious activity alerts
- **ComplianceReport**: Regulatory reporting

### 2. Rule Engine

Located in `core/models/rules.py`:

- **ComplianceRule**: Configurable compliance rules
- **RuleCondition**: Rule evaluation conditions
- **RuleEvaluationResult**: Rule evaluation results
- **RULE_TEMPLATES**: Pre-built rule templates

#### Pre-built Rule Templates

- `high_value_transaction`: Flag transactions above threshold
- `blocked_country`: Block transactions to/from specific countries
- `daily_velocity`: Daily transaction count/amount limits
- `unverified_kyc`: Block transactions without verified KYC

### 3. Compliance Service

Located in `core/services/compliance.py`:

Main orchestration service that performs:
- Pre-transaction compliance checks
- Rule engine evaluation
- Sanctions screening
- Velocity monitoring
- Risk scoring

### 4. Sanctions Screening

Located in `core/utils/sanctions.py`:

- **SanctionsScreening**: Screen names against OFAC, UN, EU lists
- **CountryRiskAssessment**: Country-based risk scoring
- Fuzzy matching for name variations
- Alias checking

### 5. Organization Compliance Settings

Located in `core/models/organization.py`:

```python
class OrganizationSettings:
    # Compliance settings
    compliance_level: str = "standard"  # basic, standard, strict
    enable_sanctions_screening: bool = True
    enable_velocity_monitoring: bool = True
    enable_pep_screening: bool = False
    max_transaction_amount: Optional[float] = None
    restricted_countries: list[str] = []
    require_manual_review_above: Optional[float] = None
    auto_block_high_risk: bool = True
    risk_score_threshold: int = 75
```

### 6. Compliance Permissions

Located in `core/models/user.py`:

- `COMPLIANCE_VIEW`: View compliance checks
- `COMPLIANCE_APPROVE`: Approve manual reviews
- `COMPLIANCE_REJECT`: Reject transactions
- `COMPLIANCE_RULES_MANAGE`: Manage compliance rules
- `COMPLIANCE_OVERRIDE`: Override compliance blocks
- `COMPLIANCE_REPORTS`: Generate compliance reports

## Integration with Payment/Transaction Services

### Example: Payment Service Integration

```python
from core.services.compliance import ComplianceService
from core.services.payments import PaymentService
from core.exceptions import TransactionBlockedError, KYCRequiredError

class PaymentService:
    def __init__(self, formance_repo: FormanceRepository):
        self.formance_repo = formance_repo
        self.compliance_service = ComplianceService(formance_repo)

    async def process_mobile_money_payment(
        self,
        organization_id: str,
        customer_id: str,
        from_account_id: str,
        phone_number: str,
        provider: MobileMoneyProvider,
        country_code: str,
        amount: Decimal,
        currency: str,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Payment:
        """Process mobile money payment with compliance checks"""

        # 1️⃣ Run compliance checks BEFORE processing payment
        try:
            compliance_check = await self.compliance_service.check_transaction(
                organization_id=organization_id,
                customer_id=customer_id,
                account_id=from_account_id,
                amount=amount,
                currency=currency,
                transaction_type="mobile_money_payment",
                payment_method=PaymentMethod.MOBILE_MONEY,
                destination_country=country_code,
                metadata={
                    "mobile_money_provider": provider.value,
                    "phone_number": phone_number,
                    **(metadata or {}),
                },
            )
        except (TransactionBlockedError, KYCRequiredError) as e:
            logger.error(f"Compliance check failed: {e}")
            raise

        # Check if requires manual review
        if compliance_check.needs_review():
            logger.info(f"Transaction requires manual review: {compliance_check.reason}")
            # Return pending payment awaiting review
            # In production, store in review queue

        # 2️⃣ If compliance APPROVED, process payment
        if compliance_check.is_approved():
            # Create payment metadata with compliance info
            payment_metadata = {
                "compliance_check_id": compliance_check.id,
                "compliance_status": compliance_check.status.value,
                "risk_score": compliance_check.risk_score,
                "rules_evaluated": compliance_check.rules_evaluated,
                "mobile_money_provider": provider.value,
                "country_code": country_code,
                "phone_number": phone_number,
                **(metadata or {}),
            }

            # Create payment in Formance
            payment_data = await self.formance_repo.create_payment(
                from_account_id=from_account_id,
                amount=amount,
                currency=currency,
                payment_method=PaymentMethod.MOBILE_MONEY,
                destination=f"{provider.value}:{country_code}:{phone_number}",
                description=description,
                metadata=payment_metadata,
            )

            # 3️⃣ Post to Formance ledger for audit trail
            await self._post_compliance_transaction(
                organization_id=organization_id,
                payment_data=payment_data,
                compliance_check=compliance_check,
            )

            return Payment(**payment_data)

    async def _post_compliance_transaction(
        self,
        organization_id: str,
        payment_data: dict,
        compliance_check: ComplianceCheck,
    ):
        """Post transaction to Formance ledger with compliance metadata"""

        ledger_id = f"org_{organization_id}"
        payment_id = payment_data["id"]
        amount_cents = int(payment_data["amount"] * 100)

        # Create postings
        postings = [
            {
                "source": f"org:{organization_id}:accounts:{payment_data['from_account_id']}",
                "destination": f"compliance:approved:{payment_id}",
                "amount": amount_cents,
                "asset": f"{payment_data['currency']}/2",
            }
        ]

        # Compliance metadata for immutable ledger
        ledger_metadata = {
            "compliance_check_id": compliance_check.id,
            "compliance_status": compliance_check.status.value,
            "risk_score": compliance_check.risk_score,
            "risk_level": compliance_check.risk_level.value,
            "rules_evaluated": compliance_check.rules_evaluated,
            "rules_triggered": compliance_check.rules_triggered,
            "organization_id": organization_id,
            "customer_id": compliance_check.customer_id,
            "payment_id": payment_id,
            "payment_method": payment_data["payment_method"].value,
        }

        # Post to ledger
        await self.formance_repo.post_transaction(
            ledger_id=ledger_id,
            postings=postings,
            reference=payment_id,
            metadata=ledger_metadata,
        )

        logger.info(f"Posted compliance transaction to ledger for payment {payment_id}")
```

## Usage Examples

### 1. Create Organization with Compliance Settings

```python
from core.services.organizations import OrganizationService
from core.models.organization import OrganizationType, OrganizationSettings

org_service = OrganizationService(formance_repo)

# Create organization with strict compliance
org = await org_service.create_organization(
    name="Acme Fintech",
    organization_type=OrganizationType.FINTECH,
    email="compliance@acme.com",
    address_country="US",
    settings=OrganizationSettings(
        compliance_level="strict",
        enable_sanctions_screening=True,
        enable_velocity_monitoring=True,
        enable_pep_screening=True,
        max_transaction_amount=50000.00,
        restricted_countries=["IR", "KP", "SY"],  # Sanctioned countries
        require_manual_review_above=10000.00,
        auto_block_high_risk=True,
        risk_score_threshold=70,
        allowed_currencies=["USD", "EUR"],
        allow_international=True,
    ),
)
```

### 2. Process Payment with Compliance

```python
from core.services.payments import PaymentService
from core.models.payment import MobileMoneyProvider

payment_service = PaymentService(formance_repo)

try:
    payment = await payment_service.process_mobile_money_payment(
        organization_id="org_acme",
        customer_id="cust_john",
        from_account_id="acc_checking_123",
        phone_number="+254712345678",
        provider=MobileMoneyProvider.MPESA,
        country_code="KE",
        amount=Decimal("5000.00"),
        currency="KES",
        description="Payment to merchant",
    )
    print(f"Payment created: {payment.id}, Status: {payment.status}")

except TransactionBlockedError as e:
    print(f"Transaction blocked: {e}")

except KYCRequiredError as e:
    print(f"KYC required: {e}")
```

### 3. Create Custom Compliance Rule

```python
from core.services.compliance import ComplianceService
from core.models.rules import (
    ComplianceRule,
    RuleType,
    RuleAction,
    RuleSeverity,
    RuleCondition,
    RuleConditionOperator,
)

compliance_service = ComplianceService(formance_repo)

# Create rule: Block transactions over $25k to high-risk countries
rule = ComplianceRule(
    id="rule_high_value_high_risk",
    organization_id="org_acme",
    name="High Value to High Risk Country",
    description="Block large transactions to high-risk countries",
    rule_type=RuleType.GEO_FENCING,
    conditions=[
        RuleCondition(
            field="amount",
            operator=RuleConditionOperator.GREATER_THAN,
            value=25000,
            value_type="number",
        ),
        RuleCondition(
            field="destination_country",
            operator=RuleConditionOperator.IN,
            value=["AF", "IQ", "LY", "SO", "SD", "YE"],
            value_type="list",
        ),
    ],
    conditions_logic="AND",
    action=RuleAction.BLOCK,
    severity=RuleSeverity.CRITICAL,
    risk_score_impact=50,
    message="High-value transaction to high-risk country blocked",
    enabled=True,
    priority=10,  # High priority
)

await compliance_service.create_rule("org_acme", rule)
```

### 4. Manual Review Workflow

```python
from core.services.compliance import ComplianceService

compliance_service = ComplianceService(formance_repo)

# Get compliance check requiring review
check = await compliance_service.get_compliance_check("chk_xyz123")

if check.needs_review():
    # Compliance officer reviews
    if approved:
        await compliance_service.approve_manual_review(
            check_id=check.id,
            reviewed_by="usr_compliance_officer",
            notes="Verified legitimate business transaction",
        )
    else:
        await compliance_service.reject_manual_review(
            check_id=check.id,
            reviewed_by="usr_compliance_officer",
            reason="Unable to verify source of funds",
        )
```

## Compliance Check Results

### Status Values

- **APPROVED**: Transaction approved, can proceed
- **BLOCKED**: Transaction blocked, cannot proceed
- **REVIEW**: Requires manual review
- **PENDING**: Check in progress
- **EXPIRED**: Check expired, need new check

### Risk Levels

- **LOW**: Risk score 0-24
- **MEDIUM**: Risk score 25-49
- **HIGH**: Risk score 50-74
- **CRITICAL**: Risk score 75-100

### Risk Score Components

1. **KYC Score** (25% weight): Based on verification status
2. **Sanctions Score** (30% weight): Sanctions screening match confidence
3. **Transaction Score** (20% weight): Amount-based risk
4. **Geographic Score** (15% weight): Country risk assessment
5. **Velocity Score** (10% weight): Transaction pattern analysis

## Formance Ledger Integration

### Ledger Posting Structure

All compliance-approved transactions are posted to the Formance ledger with comprehensive metadata:

```
Source: org:{org_id}:accounts:{account_id}
Destination: compliance:approved:{payment_id}
Amount: {amount_in_cents}
Asset: {currency}/2

Metadata:
  - compliance_check_id: chk_xyz123
  - compliance_status: approved
  - risk_score: 25
  - risk_level: low
  - rules_evaluated: [kyc_verification, sanctions_screening, velocity_check]
  - rules_triggered: []
  - organization_id: org_acme
  - customer_id: cust_john
  - payment_id: pay_abc456
```

This creates an **immutable audit trail** for regulatory compliance and internal auditing.

## Sanctions Screening

### Supported Lists

- **OFAC** (US Office of Foreign Assets Control)
- **UN** (United Nations Security Council)
- **EU** (European Union Sanctions)
- **UK** (UK HM Treasury)

### Integration Notes

In production, integrate with:
- Dow Jones Risk & Compliance
- Refinitiv World-Check One
- ComplyAdvantage
- Accuity
- LexisNexis Bridger Insight XG

## Best Practices

### 1. Organization-Level Configuration

Configure compliance settings at the organization level to support multi-tenancy:

```python
# Fintech platform with strict compliance
settings = OrganizationSettings(
    compliance_level="strict",
    enable_sanctions_screening=True,
    enable_pep_screening=True,
    risk_score_threshold=70,
)

# SMB with standard compliance
settings = OrganizationSettings(
    compliance_level="standard",
    enable_sanctions_screening=True,
    risk_score_threshold=75,
)
```

### 2. Rule Prioritization

Rules are evaluated by priority (lower number = higher priority):

- Critical rules: priority 1-25
- High priority: 26-50
- Medium priority: 51-75
- Low priority: 76-100

### 3. Performance Optimization

- Cache rules per organization (15-minute TTL)
- Use Redis for session storage and rule caching
- Asynchronous sanctions list updates
- Index compliance checks by customer_id and organization_id

### 4. Audit Trail

Always post transactions to Formance ledger with compliance metadata for:
- Regulatory reporting (SAR, CTR)
- Internal audits
- Investigation support
- Dispute resolution

## API Endpoints

Compliance API endpoints will be available at:

- `POST /api/v1/compliance/check` - Run compliance check
- `GET /api/v1/compliance/checks/{check_id}` - Get compliance check
- `GET /api/v1/compliance/checks` - List compliance checks
- `POST /api/v1/compliance/checks/{check_id}/approve` - Approve review
- `POST /api/v1/compliance/checks/{check_id}/reject` - Reject transaction
- `POST /api/v1/compliance/rules` - Create compliance rule
- `GET /api/v1/compliance/rules` - List rules
- `PATCH /api/v1/compliance/rules/{rule_id}` - Update rule
- `DELETE /api/v1/compliance/rules/{rule_id}` - Delete rule
- `GET /api/v1/compliance/reports` - Generate compliance reports

## Future Enhancements

### Phase 1 (Implemented)
- ✅ Compliance domain models
- ✅ Rule engine
- ✅ Sanctions screening
- ✅ Risk scoring
- ✅ Organization compliance settings
- ✅ RBAC permissions

### Phase 2 (In Progress)
- ⏳ Compliance API endpoints
- ⏳ Manual review queue
- ⏳ Async reconciliation workers

### Phase 3 (Planned)
- ⏰ PEP (Politically Exposed Person) screening
- ⏰ Beneficial ownership analysis
- ⏰ Enhanced transaction monitoring
- ⏰ ML-based anomaly detection
- ⏰ Automated regulatory reporting (SAR, CTR, STR)
- ⏰ Real-time sanction list updates
- ⏰ Case management system
- ⏰ Compliance dashboard

## Resources

- [FATF Recommendations](https://www.fatf-gafi.org/publications/fatfrecommendations/)
- [OFAC Sanctions Lists](https://www.treasury.gov/resource-center/sanctions/SDN-List/Pages/default.aspx)
- [UN Security Council Sanctions](https://www.un.org/securitycouncil/sanctions/information)
- [EU Sanctions Map](https://www.sanctionsmap.eu/)
- [FinCEN BSA Requirements](https://www.fincen.gov/resources/statutes-and-regulations/bank-secrecy-act)

---

Built with Formance Stack and FastAPI
