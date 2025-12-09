# Regulatory Reporting Integration

Automated regulatory reporting system for SAR (Suspicious Activity Reports) and CTR (Currency Transaction Reports) compliance.

## Overview

This module provides comprehensive regulatory reporting capabilities for financial institutions, ensuring compliance with US Bank Secrecy Act (BSA) and FinCEN requirements.

### Supported Report Types

- **CTR (Currency Transaction Report)** - FinCEN Form 112
  - Required for currency transactions ≥ $10,000 in a single business day
  - Automatic detection and generation
  - Aggregation of multiple transactions per customer

- **SAR (Suspicious Activity Report)** - FinCEN Form 111
  - Filed when suspicious activity is detected
  - Integrated with compliance engine
  - Manual review and approval workflow

- **Future Support**
  - STR (Suspicious Transaction Report) - International
  - DOEP (Designation of Exempt Person)
  - FBAR (Foreign Bank Account Report)

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Compliance Engine                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Sanctions Screening │ Risk Scoring │ Velocity    │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│            Regulatory Reporting Service                      │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │  CTR Detection │  │  SAR Detection │  │  Report Gen  │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Regulatory Reporting Worker                     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Automated CTR │ SAR Flagging │ Notifications    │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 FinCEN BSA E-Filing                          │
│                   (Optional Integration)                     │
└─────────────────────────────────────────────────────────────┘
```

## Data Models

### Currency Transaction Report (CTR)

```python
CurrencyTransactionReport(
    id="ctr_abc123",
    organization_id="org_bank",
    report_type=ReportType.CTR,
    status=ReportStatus.DRAFT,

    # Filing institution
    filing_institution=FinancialInstitution(
        name="Acme Bank",
        ein="12-3456789",
        address_street="123 Bank St",
        address_city="New York",
        address_state="NY",
        address_postal_code="10001",
        address_country="US",
        phone="+12125551234",
    ),

    # Transaction details
    transaction_date=datetime(2025, 12, 9),
    person_on_behalf=SubjectInformation(...),
    transactions=[TransactionDetails(...)],

    # Amounts
    total_cash_in=Decimal("15000.00"),
    total_cash_out=Decimal("0"),
    total_amount=Decimal("15000.00"),
    currency="USD",

    # Filing info
    prepared_by="user_compliance",
    branch_id="branch_main",
)
```

### Suspicious Activity Report (SAR)

```python
SuspiciousActivityReport(
    id="sar_xyz789",
    organization_id="org_bank",
    report_type=ReportType.SAR,
    status=ReportStatus.DRAFT,
    priority=ReportPriority.HIGH,

    # Activity details
    activity_start_date=datetime(2025, 12, 1),
    activity_end_date=datetime(2025, 12, 9),
    activity_detected_date=datetime(2025, 12, 9),

    # Subjects
    subjects=[SubjectInformation(...)],

    # Classification
    suspicious_activity_types=[
        SuspiciousActivityType.STRUCTURING,
        SuspiciousActivityType.MONEY_LAUNDERING,
    ],

    # Transactions
    transactions=[TransactionDetails(...)],
    total_amount=Decimal("45000.00"),

    # Narrative (minimum 50 characters)
    narrative_summary="""
    Customer conducted multiple transactions over 7-day period,
    each just below $10,000 CTR threshold. Pattern suggests
    structuring to avoid reporting requirements. Transactions
    originated from multiple branches with no clear business purpose.
    """,

    # Related compliance data
    compliance_check_ids=["chk_123", "chk_456"],
    alert_ids=["alert_789"],

    # Filing info
    prepared_by="user_compliance",
)
```

## API Endpoints

### CTR Operations

#### Check CTR Requirement
```http
POST /api/v1/regulatory/ctr/check?organization_id=org_test
Content-Type: application/json

{
  "customer_id": "cust_123",
  "transaction_date": "2025-12-09T10:00:00Z",
  "amount": 15000.00,
  "currency": "USD"
}
```

Response:
```json
{
  "required": true,
  "threshold": 10000.00,
  "amount": 15000.00,
  "reason": "Transaction amount 15000.00 exceeds threshold 10000.00"
}
```

#### Generate CTR
```http
POST /api/v1/regulatory/ctr?organization_id=org_test&prepared_by=user_compliance
Content-Type: application/json

{
  "customer_id": "cust_123",
  "transaction_ids": ["txn_001", "txn_002"],
  "branch_id": "branch_main"
}
```

Response: Full `CurrencyTransactionReport` object

### SAR Operations

#### Generate SAR
```http
POST /api/v1/regulatory/sar?organization_id=org_test&prepared_by=user_compliance
Content-Type: application/json

{
  "customer_id": "cust_456",
  "suspicious_activity_types": ["structuring", "money_laundering"],
  "narrative_summary": "Customer appears to be structuring transactions...",
  "transaction_ids": ["txn_100", "txn_101", "txn_102"],
  "activity_start_date": "2025-12-01T00:00:00Z",
  "activity_end_date": "2025-12-09T23:59:59Z",
  "compliance_check_ids": ["chk_789"],
  "alert_ids": ["alert_123"],
  "priority": "high"
}
```

Response: Full `SuspiciousActivityReport` object

### Report Lifecycle

#### List Reports
```http
GET /api/v1/regulatory/reports?organization_id=org_test&report_type=ctr&status=draft&limit=50
```

Response:
```json
[
  {
    "id": "ctr_abc123",
    "organization_id": "org_test",
    "report_type": "ctr",
    "status": "draft",
    "total_amount": 15000.00,
    "currency": "USD",
    "transaction_date": "2025-12-09T00:00:00Z",
    "created_at": "2025-12-09T10:30:00Z",
    "prepared_by": "user_compliance"
  }
]
```

#### Get Report
```http
GET /api/v1/regulatory/reports/ctr_abc123?report_type=ctr
```

Response: Full report object

#### Review Report
```http
POST /api/v1/regulatory/reports/ctr_abc123/review?report_type=ctr&reviewed_by=user_manager
Content-Type: application/json

{
  "approved": true,
  "notes": "Verified all transaction details. Approved for filing."
}
```

Response:
```json
{
  "report_id": "ctr_abc123",
  "report_type": "ctr",
  "status": "approved",
  "reviewed_by": "user_manager",
  "success": true
}
```

#### File Report
```http
POST /api/v1/regulatory/reports/ctr_abc123/file?report_type=ctr&filed_by=user_compliance
```

Response:
```json
{
  "report_id": "ctr_abc123",
  "report_type": "ctr",
  "status": "filed",
  "bsa_identifier": "BSA1234567890ABCD",
  "filed_at": "2025-12-09T15:00:00Z"
}
```

### Configuration

#### Get Configuration
```http
GET /api/v1/regulatory/config?organization_id=org_test
```

Response:
```json
{
  "organization_id": "org_test",
  "ctr_enabled": true,
  "ctr_threshold": 10000.00,
  "ctr_auto_generate": true,
  "ctr_aggregation_window_hours": 24,
  "sar_enabled": true,
  "sar_auto_generate": false,
  "sar_risk_score_threshold": 75,
  "require_dual_approval": true,
  "report_retention_days": 1825
}
```

#### Update Configuration
```http
PUT /api/v1/regulatory/config
Content-Type: application/json

{
  "organization_id": "org_test",
  "ctr_threshold": 15000.00,
  "sar_risk_score_threshold": 80,
  "require_dual_approval": false
}
```

## Automated Detection

### CTR Detection Rules

1. **Single Transaction Rule**
   - Any currency transaction ≥ $10,000
   - Triggers immediate CTR generation

2. **Aggregation Rule**
   - Multiple transactions from same customer
   - Within 24-hour window
   - Combined total ≥ $10,000
   - Automatically aggregated into single CTR

3. **Exemption Check**
   - Check if customer has exemption designation
   - Skip CTR generation if exempt

### SAR Detection Triggers

1. **High Risk Score**
   - Compliance check risk score ≥ threshold (default: 75)
   - Flags for manual SAR review

2. **Sanctions Match**
   - Any sanctions screening hit
   - Immediate SAR flagging

3. **Pattern Detection**
   - Structuring behavior
   - Rapid movement of funds
   - Unusual transaction patterns
   - Geographic anomalies

4. **Manual Flag**
   - Compliance officer flags transaction
   - Elevated for SAR preparation

## Background Worker

The regulatory reporting worker runs continuously in the background:

```python
from core.workers.regulatory_reporting import run_regulatory_reporting_worker
from core.repositories.formance import FormanceRepository

# Initialize
repository = FormanceRepository(...)

# Run worker (checks every 60 minutes)
await run_regulatory_reporting_worker(
    formance_repository=repository,
    check_interval_minutes=60
)
```

### Worker Responsibilities

1. **CTR Generation** (Daily)
   - Queries previous day's transactions
   - Identifies CTR-qualifying activities
   - Auto-generates CTR reports
   - Notifies compliance team

2. **SAR Flagging** (Continuous)
   - Monitors compliance alerts
   - Identifies potential SAR cases
   - Flags for manual review
   - Escalates high-priority cases

3. **Notifications**
   - Email alerts for new reports
   - In-app notifications
   - Escalation for overdue reviews

4. **Report Lifecycle**
   - Tracks report aging
   - Escalates pending reviews
   - Monitors filing deadlines

## Integration with Compliance Engine

The regulatory reporting system integrates seamlessly with the compliance engine:

```python
from core.services.compliance import ComplianceService
from core.services.regulatory import RegulatoryReportingService

# Initialize services
compliance_service = ComplianceService(repository)
regulatory_service = RegulatoryReportingService(repository)

# Run compliance check
compliance_check = await compliance_service.check_transaction(
    organization_id="org_test",
    customer_id="cust_123",
    account_id="acc_456",
    amount=Decimal("15000.00"),
    currency="USD",
    transaction_type="deposit"
)

# Check if regulatory reporting required
reporting = await compliance_service.check_regulatory_reporting_required(
    organization_id="org_test",
    compliance_check=compliance_check,
    transaction_amount=Decimal("15000.00"),
    transaction_date=datetime.utcnow()
)

if reporting["ctr_required"]:
    # Generate CTR
    ctr = await regulatory_service.generate_ctr(...)

if reporting["sar_required"]:
    # Flag for SAR review
    logger.warning("SAR review required")
```

## Report Workflow

### CTR Workflow

```
┌──────────────┐
│ Transaction  │
│  ≥ $10,000   │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│   Auto or    │────▶│   CTR DRAFT  │
│   Manual     │     └──────┬───────┘
│  Detection   │            │
└──────────────┘            │
                            ▼
                     ┌──────────────┐
                     │   REVIEW     │
                     │  (Optional)  │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   APPROVED   │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    FILED     │
                     │ (FinCEN BSA) │
                     └──────────────┘
```

### SAR Workflow

```
┌──────────────┐
│  Compliance  │
│    Alert     │
│ (High Risk)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│   Manual     │────▶│   SAR DRAFT  │
│  Preparation │     └──────┬───────┘
│  (Required)  │            │
└──────────────┘            │
                            ▼
                     ┌──────────────┐
                     │ PENDING      │
                     │ REVIEW       │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   APPROVED   │
                     │ (Dual Auth)  │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    FILED     │
                     │ (FinCEN BSA) │
                     └──────────────┘
```

## Suspicious Activity Types

The system supports comprehensive SAR classification:

- **Structuring** - Breaking transactions to avoid reporting
- **Money Laundering** - Suspicious fund movement
- **Terrorist Financing** - Potential terrorism links
- **Fraud** - Fraudulent activity
- **Identity Theft** - Identity-related crimes
- **Check Fraud** - Check-related fraud
- **Credit Card Fraud** - Card payment fraud
- **Wire Transfer Fraud** - Wire fraud
- **Mortgage Fraud** - Property-related fraud
- **Elder Financial Abuse** - Senior exploitation
- **Unauthorized Electronic Intrusion** - Cyber crimes
- **Misuse of Position** - Insider abuse
- **Bribery/Corruption** - Bribery schemes
- **Embezzlement** - Theft by employees
- **Ponzi Scheme** - Investment fraud
- **Trade-Based Laundering** - Invoice manipulation
- **Unknown/Unusual** - Unexplained activity

## Compliance Requirements

### CTR Filing Requirements (US)

- **Threshold**: $10,000 in currency
- **Timeframe**: 15 days from transaction date
- **Form**: FinCEN Form 112
- **Retention**: 5 years minimum

### SAR Filing Requirements (US)

- **Threshold**: $5,000+ for most activities
- **Timeframe**: 30 days from detection (60 days if no subject ID)
- **Form**: FinCEN Form 111
- **Retention**: 5 years minimum
- **No Disclosure**: Cannot inform subject of SAR filing

## Security & Access Control

### RBAC Permissions

```python
# View reports
Permission.REGULATORY_REPORTS_VIEW

# Prepare reports
Permission.REGULATORY_REPORTS_PREPARE

# Review and approve reports
Permission.REGULATORY_REPORTS_APPROVE

# File reports with authorities
Permission.REGULATORY_REPORTS_FILE

# Manage configuration
Permission.REGULATORY_REPORTS_CONFIG
```

### Audit Trail

All regulatory reporting activities are logged:
- Report generation
- Reviews and approvals
- Filing submissions
- Configuration changes
- Access to report data

## Best Practices

### CTR Best Practices

1. **Timely Filing** - File within 15 days
2. **Accuracy** - Verify all customer information
3. **Aggregation** - Properly aggregate related transactions
4. **Documentation** - Maintain supporting documentation
5. **Exemptions** - Properly document exempt customers

### SAR Best Practices

1. **Thorough Narrative** - Provide detailed description (minimum 50 characters, recommended 200+)
2. **Complete Information** - Include all relevant transaction details
3. **Timely Filing** - File within 30 days of detection
4. **Confidentiality** - Never disclose SAR filing to subject
5. **Supporting Documentation** - Maintain evidence and analysis
6. **Management Review** - Dual approval for high-risk SARs

## Testing

Run regulatory reporting tests:

```bash
# Unit tests
pytest tests/unit/test_regulatory.py -v

# Integration tests
pytest tests/integration/test_regulatory_integration.py -v

# Specific test
pytest tests/unit/test_regulatory.py::test_generate_ctr_success -v
```

## Monitoring & Alerts

### Key Metrics

- CTRs generated (daily)
- SARs filed (monthly)
- Average report preparation time
- Reports pending review
- Reports overdue for filing
- False positive rate

### Alerting

- New CTR generated
- SAR flagged for review
- Report pending > 48 hours
- Filing deadline approaching
- Configuration changes

## Future Enhancements

- [ ] FinCEN BSA E-Filing API integration
- [ ] ML-based SAR prediction
- [ ] Enhanced pattern detection algorithms
- [ ] International reporting formats (STR, etc.)
- [ ] Automated narrative generation assistance
- [ ] Report templates and customization
- [ ] Bulk report operations
- [ ] Advanced analytics and reporting
- [ ] Integration with case management systems

## References

- [FinCEN BSA E-Filing System](https://bsaefiling.fincen.treas.gov/)
- [FinCEN Form 112 (CTR)](https://www.fincen.gov/sites/default/files/shared/CTR.pdf)
- [FinCEN Form 111 (SAR)](https://www.fincen.gov/sites/default/files/shared/FinCEN_SAR_ElectronicFiling.pdf)
- [Bank Secrecy Act Requirements](https://www.fincen.gov/resources/statutes-and-regulations/bank-secrecy-act)

## Support

For questions or issues with regulatory reporting:
- Check system logs for error details
- Review compliance check history
- Verify organization configuration
- Contact compliance team for policy questions
