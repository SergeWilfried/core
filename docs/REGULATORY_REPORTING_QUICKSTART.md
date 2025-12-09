# Regulatory Reporting Quick Start Guide

Get started with automated regulatory reporting (SAR & CTR) in 5 minutes.

## Prerequisites

- Core banking system installed and running
- Organization and customers created
- Compliance engine enabled

## Step 1: Configure Your Organization

Update your organization's regulatory reporting configuration:

```python
from core.services.regulatory import RegulatoryReportingService
from core.models.regulatory import RegulatoryReportingConfig
from decimal import Decimal

# Initialize service
regulatory_service = RegulatoryReportingService(formance_repository)

# Configure reporting
config = RegulatoryReportingConfig(
    organization_id="org_your_bank",

    # CTR settings
    ctr_enabled=True,
    ctr_threshold=Decimal("10000.00"),  # $10,000 threshold
    ctr_auto_generate=True,             # Auto-generate CTRs

    # SAR settings
    sar_enabled=True,
    sar_risk_score_threshold=75,        # Flag for SAR if risk ≥ 75

    # Workflow
    require_dual_approval=True,         # Require two approvals

    # Notifications
    notification_emails=["compliance@yourbank.com"],
)

await regulatory_service.update_reporting_config("org_your_bank", config)
```

## Step 2: Check if CTR is Required

Before processing a high-value transaction:

```python
from decimal import Decimal
from datetime import datetime

# Check CTR requirement
ctr_required = await regulatory_service.check_ctr_required(
    organization_id="org_your_bank",
    customer_id="cust_john_doe",
    transaction_date=datetime.utcnow(),
    amount=Decimal("15000.00"),
    currency="USD"
)

if ctr_required:
    print("⚠️  CTR will be required for this transaction")
```

## Step 3: Generate a CTR

For transactions ≥ $10,000:

```python
# Generate CTR
ctr = await regulatory_service.generate_ctr(
    organization_id="org_your_bank",
    customer_id="cust_john_doe",
    transaction_ids=["txn_001", "txn_002"],  # Related transactions
    prepared_by="user_compliance_officer",
    branch_id="branch_main"
)

print(f"✅ CTR generated: {ctr.id}")
print(f"   Status: {ctr.status}")
print(f"   Total Amount: ${ctr.total_amount}")
```

## Step 4: Generate a SAR

When suspicious activity is detected:

```python
from core.models.regulatory import SuspiciousActivityType, ReportPriority
from datetime import timedelta

# Generate SAR
sar = await regulatory_service.generate_sar(
    organization_id="org_your_bank",
    customer_id="cust_jane_smith",

    # Activity classification
    suspicious_activity_types=[
        SuspiciousActivityType.STRUCTURING,
        SuspiciousActivityType.MONEY_LAUNDERING,
    ],

    # Detailed narrative (minimum 50 characters)
    narrative_summary="""
    Customer conducted six separate cash deposits over a seven-day period,
    with each transaction amount between $9,500 and $9,900 - just below
    the $10,000 CTR reporting threshold. All deposits were made at different
    branch locations with no clear business purpose. When questioned, customer
    provided vague explanations about business expenses. Pattern strongly
    suggests structuring to avoid currency transaction reporting requirements.
    Total amount involved: $57,300.
    """,

    # Related transactions
    transaction_ids=["txn_100", "txn_101", "txn_102", "txn_103", "txn_104", "txn_105"],

    # Activity timeline
    activity_start_date=datetime.utcnow() - timedelta(days=7),
    activity_end_date=datetime.utcnow(),

    # Link to compliance data
    compliance_check_ids=["chk_abc123"],
    alert_ids=["alert_xyz789"],

    # Priority and preparer
    priority=ReportPriority.HIGH,
    prepared_by="user_compliance_officer"
)

print(f"✅ SAR generated: {sar.id}")
print(f"   Priority: {sar.priority}")
print(f"   Status: {sar.status}")
```

## Step 5: Review and Approve Reports

Compliance officers review reports:

```python
# Review CTR
await regulatory_service.review_report(
    report_id=ctr.id,
    report_type=ReportType.CTR,
    reviewed_by="user_compliance_manager",
    approved=True,
    notes="Verified customer identity and transaction details. Approved."
)

print(f"✅ CTR {ctr.id} approved")

# Review SAR (second approval if dual approval required)
await regulatory_service.review_report(
    report_id=sar.id,
    report_type=ReportType.SAR,
    reviewed_by="user_compliance_director",
    approved=True,
    notes="Reviewed narrative and supporting evidence. Approved for filing."
)

print(f"✅ SAR {sar.id} approved")
```

## Step 6: File Reports with Authorities

File approved reports:

```python
from core.models.regulatory import ReportType

# File CTR
bsa_id = await regulatory_service.file_report(
    report_id=ctr.id,
    report_type=ReportType.CTR,
    filed_by="user_compliance_officer"
)

print(f"✅ CTR filed successfully")
print(f"   BSA Identifier: {bsa_id}")

# File SAR
bsa_id = await regulatory_service.file_report(
    report_id=sar.id,
    report_type=ReportType.SAR,
    filed_by="user_compliance_officer"
)

print(f"✅ SAR filed successfully")
print(f"   BSA Identifier: {bsa_id}")
```

## Step 7: List and Monitor Reports

Track your reports:

```python
from core.models.regulatory import ReportStatus

# List all draft CTRs
reports = await regulatory_service.list_reports(
    organization_id="org_your_bank",
    report_type=ReportType.CTR,
    status=ReportStatus.DRAFT,
    limit=50
)

print(f"📋 Draft CTRs: {len(reports)}")
for report in reports:
    print(f"   {report.id}: ${report.total_amount} - {report.created_at}")

# List pending SARs
reports = await regulatory_service.list_reports(
    organization_id="org_your_bank",
    report_type=ReportType.SAR,
    status=ReportStatus.PENDING_REVIEW,
    limit=50
)

print(f"📋 Pending SARs: {len(reports)}")
```

## Using the REST API

### Check CTR Requirement
```bash
curl -X POST "http://localhost:8000/api/v1/regulatory/ctr/check?organization_id=org_your_bank" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "customer_id": "cust_john_doe",
    "transaction_date": "2025-12-09T10:00:00Z",
    "amount": 15000.00,
    "currency": "USD"
  }'
```

### Generate CTR
```bash
curl -X POST "http://localhost:8000/api/v1/regulatory/ctr?organization_id=org_your_bank&prepared_by=user_compliance" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "customer_id": "cust_john_doe",
    "transaction_ids": ["txn_001"],
    "branch_id": "branch_main"
  }'
```

### Generate SAR
```bash
curl -X POST "http://localhost:8000/api/v1/regulatory/sar?organization_id=org_your_bank&prepared_by=user_compliance" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "customer_id": "cust_jane_smith",
    "suspicious_activity_types": ["structuring"],
    "narrative_summary": "Customer conducted multiple transactions just below threshold...",
    "transaction_ids": ["txn_100", "txn_101"],
    "activity_start_date": "2025-12-01T00:00:00Z",
    "priority": "high"
  }'
```

### List Reports
```bash
curl "http://localhost:8000/api/v1/regulatory/reports?organization_id=org_your_bank&status=draft&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Review Report
```bash
curl -X POST "http://localhost:8000/api/v1/regulatory/reports/ctr_abc123/review?report_type=ctr&reviewed_by=user_manager" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "approved": true,
    "notes": "Approved"
  }'
```

### File Report
```bash
curl -X POST "http://localhost:8000/api/v1/regulatory/reports/ctr_abc123/file?report_type=ctr&filed_by=user_compliance" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Integrate with Compliance Checks

Automatically check regulatory reporting requirements during compliance checks:

```python
from core.services.compliance import ComplianceService

# Run compliance check
compliance_check = await compliance_service.check_transaction(
    organization_id="org_your_bank",
    customer_id="cust_john_doe",
    account_id="acc_checking_001",
    amount=Decimal("15000.00"),
    currency="USD",
    transaction_type="deposit"
)

# Check if regulatory reporting required
reporting = await compliance_service.check_regulatory_reporting_required(
    organization_id="org_your_bank",
    compliance_check=compliance_check,
    transaction_amount=Decimal("15000.00"),
    transaction_date=datetime.utcnow()
)

if reporting["ctr_required"]:
    print("⚠️  CTR generation required")
    # Auto-generate CTR or notify compliance team

if reporting["sar_required"]:
    print("⚠️  SAR review required")
    # Flag for manual SAR preparation
```

## Run Background Worker

Start the automated regulatory reporting worker:

```python
from core.workers.regulatory_reporting import run_regulatory_reporting_worker
from core.repositories.formance import FormanceRepository

# Initialize repository
repository = FormanceRepository(...)

# Run worker (checks every 60 minutes)
await run_regulatory_reporting_worker(
    formance_repository=repository,
    check_interval_minutes=60
)
```

The worker will:
- 🔄 Generate CTRs daily for qualifying transactions
- 🔄 Flag potential SARs based on compliance alerts
- 📧 Send notifications to compliance officers
- ⏰ Monitor and escalate overdue reports

## API Documentation

View complete API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Look for the **regulatory** tag to see all endpoints.

## Configuration Reference

```python
RegulatoryReportingConfig(
    organization_id="org_your_bank",

    # CTR Configuration
    ctr_enabled=True,                      # Enable CTR reporting
    ctr_threshold=Decimal("10000.00"),     # Reporting threshold
    ctr_auto_generate=True,                # Auto-generate CTRs
    ctr_aggregation_window_hours=24,       # Aggregate within 24 hours

    # SAR Configuration
    sar_enabled=True,                      # Enable SAR reporting
    sar_auto_generate=False,               # Manual SAR preparation
    sar_risk_score_threshold=75,           # Risk score trigger

    # Workflow
    require_dual_approval=True,            # Two approvals required
    auto_file_reports=False,               # Manual filing

    # Notifications
    notify_on_report_generation=True,      # Notify on generation
    notification_emails=[                  # Email recipients
        "compliance@yourbank.com",
        "aml@yourbank.com"
    ],

    # Retention
    report_retention_days=1825,            # 5 years (required)

    # Integration
    fincen_api_enabled=False,              # FinCEN API (future)
)
```

## Suspicious Activity Type Reference

Common SAR classifications:

```python
from core.models.regulatory import SuspiciousActivityType

# Most common
SuspiciousActivityType.STRUCTURING          # Breaking up transactions
SuspiciousActivityType.MONEY_LAUNDERING     # Money laundering
SuspiciousActivityType.FRAUD                # General fraud
SuspiciousActivityType.IDENTITY_THEFT       # Identity crimes

# Fraud types
SuspiciousActivityType.CHECK_FRAUD          # Check-related
SuspiciousActivityType.CREDIT_CARD_FRAUD    # Card fraud
SuspiciousActivityType.WIRE_TRANSFER_FRAUD  # Wire fraud
SuspiciousActivityType.MORTGAGE_FRAUD       # Property fraud

# Other
SuspiciousActivityType.TERRORIST_FINANCING  # Terrorism
SuspiciousActivityType.ELDER_FINANCIAL_ABUSE # Senior exploitation
SuspiciousActivityType.EMBEZZLEMENT         # Internal theft
SuspiciousActivityType.PONZI_SCHEME         # Investment fraud
SuspiciousActivityType.UNKNOWN_UNUSUAL      # Unknown/other
```

## Best Practices

### CTR Best Practices
1. ✅ File within 15 days
2. ✅ Verify customer identity
3. ✅ Document all cash transactions
4. ✅ Aggregate related transactions
5. ✅ Maintain 5-year records

### SAR Best Practices
1. ✅ Write detailed narratives (200+ characters)
2. ✅ Include all supporting evidence
3. ✅ File within 30 days of detection
4. ✅ Never disclose to customer
5. ✅ Dual approval for high-risk cases
6. ✅ Document decision process

## Troubleshooting

### "Narrative too short" error
**Solution:** SAR narratives must be at least 50 characters. Provide detailed explanation.

### CTR not auto-generating
**Solution:** Check configuration:
```python
config = await regulatory_service._get_reporting_config("org_your_bank")
print(f"CTR enabled: {config.ctr_enabled}")
print(f"Auto-generate: {config.ctr_auto_generate}")
```

### Reports not appearing in list
**Solution:** Check filters and pagination:
```python
reports = await regulatory_service.list_reports(
    organization_id="org_your_bank",
    report_type=None,  # All types
    status=None,       # All statuses
    limit=100
)
```

## Next Steps

1. 📖 Read [REGULATORY_REPORTING.md](REGULATORY_REPORTING.md) for comprehensive guide
2. 🧪 Run tests: `pytest tests/unit/test_regulatory.py`
3. 🔧 Configure your organization settings
4. 🚀 Start the background worker
5. 📊 Monitor reports in dashboard

## Support

- **Documentation:** `/docs/REGULATORY_REPORTING.md`
- **API Docs:** http://localhost:8000/docs
- **Tests:** `tests/unit/test_regulatory.py`

## Resources

- [FinCEN BSA E-Filing](https://bsaefiling.fincen.treas.gov/)
- [FinCEN SAR Guidance](https://www.fincen.gov/resources/filing-information)
- [Bank Secrecy Act](https://www.fincen.gov/resources/statutes-and-regulations/bank-secrecy-act)
