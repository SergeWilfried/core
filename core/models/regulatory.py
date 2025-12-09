"""
Regulatory reporting models for SAR, CTR, and other regulatory filings

SAR: Suspicious Activity Report
CTR: Currency Transaction Report (for transactions >= $10,000)
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class ReportType(str, Enum):
    """Regulatory report types"""

    SAR = "sar"  # Suspicious Activity Report
    CTR = "ctr"  # Currency Transaction Report
    DOEP = "doep"  # Designation of Exempt Person
    STR = "str"  # Suspicious Transaction Report (international)
    FBAR = "fbar"  # Foreign Bank Account Report
    CUSTOM = "custom"  # Custom regulatory report


class ReportStatus(str, Enum):
    """Report filing status"""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    FILED = "filed"
    REJECTED = "rejected"
    AMENDED = "amended"
    CANCELLED = "cancelled"


class ReportPriority(str, Enum):
    """Report urgency priority"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class SuspiciousActivityType(str, Enum):
    """Types of suspicious activity for SAR"""

    STRUCTURING = "structuring"  # Breaking up transactions to avoid reporting
    MONEY_LAUNDERING = "money_laundering"
    TERRORIST_FINANCING = "terrorist_financing"
    FRAUD = "fraud"
    IDENTITY_THEFT = "identity_theft"
    CHECK_FRAUD = "check_fraud"
    CREDIT_CARD_FRAUD = "credit_card_fraud"
    WIRE_TRANSFER_FRAUD = "wire_transfer_fraud"
    MORTGAGE_FRAUD = "mortgage_fraud"
    ELDER_FINANCIAL_ABUSE = "elder_financial_abuse"
    UNAUTHORIZED_ELECTRONIC_INTRUSION = "unauthorized_electronic_intrusion"
    MISUSE_OF_POSITION = "misuse_of_position"
    BRIBERY_CORRUPTION = "bribery_corruption"
    EMBEZZLEMENT = "embezzlement"
    PONZI_SCHEME = "ponzi_scheme"
    TRADE_BASED_LAUNDERING = "trade_based_laundering"
    UNKNOWN_UNUSUAL = "unknown_unusual"
    OTHER = "other"


class FinancialInstitution(BaseModel):
    """Financial institution information for regulatory reports"""

    name: str = Field(..., description="Institution legal name")
    ein: Optional[str] = Field(None, description="Employer Identification Number")
    tin: Optional[str] = Field(None, description="Tax Identification Number")
    rssd_number: Optional[str] = Field(None, description="RSSD number for US banks")

    # Address
    address_street: str = Field(..., description="Street address")
    address_city: str = Field(..., description="City")
    address_state: Optional[str] = Field(None, description="State/Province")
    address_postal_code: str = Field(..., description="Postal code")
    address_country: str = Field(..., description="Country code (ISO 3166-1 alpha-2)")

    # Contact
    phone: str = Field(..., description="Primary phone number")
    email: Optional[str] = Field(None, description="Contact email")

    # Regulatory identifiers
    primary_federal_regulator: Optional[str] = Field(
        None, description="Primary regulator (e.g., OCC, FDIC, FRB)"
    )
    type_of_filing_institution: str = Field(
        default="other",
        description="Type: bank, credit_union, money_service_business, etc."
    )


class SubjectInformation(BaseModel):
    """Subject (person or entity) information for reports"""

    # Identity
    entity_type: str = Field(
        ..., description="Type: individual, entity, unknown"
    )

    # Individual information
    first_name: Optional[str] = Field(None, description="First name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    last_name: Optional[str] = Field(None, description="Last name")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    ssn: Optional[str] = Field(None, description="Social Security Number")
    ein: Optional[str] = Field(None, description="Employer Identification Number")

    # Entity information
    entity_name: Optional[str] = Field(None, description="Legal entity name")
    dba_name: Optional[str] = Field(None, description="Doing Business As name")

    # Contact
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")

    # Address
    address_street: Optional[str] = Field(None, description="Street address")
    address_city: Optional[str] = Field(None, description="City")
    address_state: Optional[str] = Field(None, description="State/Province")
    address_postal_code: Optional[str] = Field(None, description="Postal code")
    address_country: Optional[str] = Field(None, description="Country code")

    # Identification documents
    identification_type: Optional[str] = Field(
        None, description="ID type: passport, drivers_license, national_id"
    )
    identification_number: Optional[str] = Field(None, description="ID number")
    identification_country: Optional[str] = Field(None, description="Issuing country")

    # Account information
    account_numbers: list[str] = Field(
        default_factory=list, description="Associated account numbers"
    )

    # Relationship to institution
    relationship: Optional[str] = Field(
        None, description="Relationship: customer, employee, agent, other"
    )

    # Occupation/Business
    occupation: Optional[str] = Field(None, description="Occupation or business type")
    employer: Optional[str] = Field(None, description="Employer name")

    # Risk indicators
    is_politically_exposed: bool = Field(
        default=False, description="Whether subject is a PEP"
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class TransactionDetails(BaseModel):
    """Transaction details for regulatory reports"""

    transaction_id: str = Field(..., description="Transaction ID")
    transaction_date: datetime = Field(..., description="Transaction date")
    transaction_type: str = Field(..., description="Transaction type")

    # Amounts
    amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field(default="USD", description="Currency code")

    # Accounts involved
    from_account_number: Optional[str] = Field(None, description="Source account")
    to_account_number: Optional[str] = Field(None, description="Destination account")

    # Location
    branch_id: Optional[str] = Field(None, description="Branch ID")
    branch_name: Optional[str] = Field(None, description="Branch name")

    # Method
    payment_method: Optional[str] = Field(None, description="Payment method")
    payment_instrument: Optional[str] = Field(
        None, description="Instrument: cash, check, wire, ach, card, mobile_money"
    )

    # Additional details
    description: Optional[str] = Field(None, description="Transaction description")
    reference_number: Optional[str] = Field(None, description="Reference number")

    # Related transactions
    related_transaction_ids: list[str] = Field(
        default_factory=list, description="Related transaction IDs"
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class SuspiciousActivityReport(BaseModel):
    """
    SAR - Suspicious Activity Report

    Filed when financial institution detects suspicious activity that might
    indicate money laundering, fraud, or other criminal activity.

    US: FinCEN Form 111
    """

    id: str = Field(..., description="Report ID")
    organization_id: str = Field(..., description="Organization ID")
    report_type: ReportType = Field(default=ReportType.SAR, description="Report type")
    status: ReportStatus = Field(default=ReportStatus.DRAFT, description="Filing status")
    priority: ReportPriority = Field(
        default=ReportPriority.NORMAL, description="Report priority"
    )

    # Filing institution
    filing_institution: FinancialInstitution = Field(
        ..., description="Financial institution filing the report"
    )

    # Activity information
    activity_start_date: datetime = Field(..., description="Start date of suspicious activity")
    activity_end_date: Optional[datetime] = Field(
        None, description="End date if ongoing or multiple instances"
    )
    activity_detected_date: datetime = Field(
        ..., description="When activity was detected"
    )

    # Subject(s) involved
    subjects: list[SubjectInformation] = Field(
        ..., description="Subjects involved in suspicious activity"
    )

    # Activity classification
    suspicious_activity_types: list[SuspiciousActivityType] = Field(
        ..., description="Types of suspicious activity"
    )

    # Transaction details
    transactions: list[TransactionDetails] = Field(
        ..., description="Transactions involved"
    )

    # Total amounts
    total_amount: Decimal = Field(..., description="Total amount involved")
    total_currency: str = Field(default="USD", description="Currency")

    # Narrative
    narrative_summary: str = Field(
        ...,
        min_length=50,
        description="Detailed narrative explaining the suspicious activity"
    )

    # Supporting information
    ip_addresses: list[str] = Field(
        default_factory=list, description="IP addresses involved"
    )
    email_addresses: list[str] = Field(
        default_factory=list, description="Email addresses involved"
    )
    phone_numbers: list[str] = Field(
        default_factory=list, description="Phone numbers involved"
    )

    # Law enforcement
    law_enforcement_contacted: bool = Field(
        default=False, description="Whether law enforcement was contacted"
    )
    law_enforcement_agency: Optional[str] = Field(
        None, description="Law enforcement agency name"
    )
    law_enforcement_contact_date: Optional[datetime] = Field(
        None, description="Date law enforcement was contacted"
    )

    # Internal tracking
    compliance_check_ids: list[str] = Field(
        default_factory=list, description="Related compliance check IDs"
    )
    alert_ids: list[str] = Field(
        default_factory=list, description="Related alert IDs"
    )

    # Filing information
    prepared_by: str = Field(..., description="User ID who prepared report")
    reviewed_by: Optional[str] = Field(None, description="User ID who reviewed")
    approved_by: Optional[str] = Field(None, description="User ID who approved")
    filed_by: Optional[str] = Field(None, description="User ID who filed")

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When report was created"
    )
    reviewed_at: Optional[datetime] = Field(None, description="Review timestamp")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    filed_at: Optional[datetime] = Field(None, description="Filing timestamp")

    # Regulatory submission
    bsa_identifier: Optional[str] = Field(
        None, description="BSA E-Filing System identifier"
    )
    fincen_ack_number: Optional[str] = Field(
        None, description="FinCEN acknowledgment number"
    )

    # Amendment information
    is_amendment: bool = Field(default=False, description="Is this an amendment")
    prior_report_id: Optional[str] = Field(
        None, description="ID of report being amended"
    )
    prior_bsa_identifier: Optional[str] = Field(
        None, description="Prior BSA identifier"
    )

    # Attachments
    attachment_urls: list[str] = Field(
        default_factory=list, description="URLs to supporting documents"
    )

    # Metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class CurrencyTransactionReport(BaseModel):
    """
    CTR - Currency Transaction Report

    Filed for currency transactions exceeding $10,000 in a single day.

    US: FinCEN Form 112
    """

    id: str = Field(..., description="Report ID")
    organization_id: str = Field(..., description="Organization ID")
    report_type: ReportType = Field(default=ReportType.CTR, description="Report type")
    status: ReportStatus = Field(default=ReportStatus.DRAFT, description="Filing status")

    # Filing institution
    filing_institution: FinancialInstitution = Field(
        ..., description="Financial institution filing the report"
    )

    # Transaction date
    transaction_date: datetime = Field(..., description="Transaction date")

    # Person(s) on whose behalf transaction was conducted
    person_on_behalf: SubjectInformation = Field(
        ..., description="Person on whose behalf transaction was conducted"
    )

    # Person(s) conducting transaction (if different)
    person_conducting: Optional[SubjectInformation] = Field(
        None, description="Person physically conducting transaction"
    )

    # Transaction details
    transactions: list[TransactionDetails] = Field(
        ..., description="Currency transactions"
    )

    # Total amounts (separate for cash in/out)
    total_cash_in: Decimal = Field(
        default=Decimal("0"), description="Total cash received"
    )
    total_cash_out: Decimal = Field(
        default=Decimal("0"), description="Total cash paid out"
    )
    total_amount: Decimal = Field(..., description="Total amount (in + out)")
    currency: str = Field(default="USD", description="Currency")

    # Transaction type
    transaction_type: str = Field(
        ...,
        description="Type: deposit, withdrawal, exchange, payment, other"
    )

    # Multiple transactions
    multiple_transactions: bool = Field(
        default=False,
        description="Multiple transactions aggregated"
    )

    # Branch/location information
    branch_id: str = Field(..., description="Branch where transaction occurred")
    branch_name: str = Field(..., description="Branch name")

    # Armored car service
    armored_car_service: bool = Field(
        default=False, description="Involved armored car service"
    )
    armored_car_company: Optional[str] = Field(
        None, description="Armored car company name"
    )

    # ATM involvement
    atm_involved: bool = Field(default=False, description="ATM involved")
    atm_location: Optional[str] = Field(None, description="ATM location")

    # Account information
    account_numbers: list[str] = Field(
        default_factory=list, description="Account numbers involved"
    )

    # Verification
    identification_verified: bool = Field(
        default=False, description="Identification was verified"
    )
    verification_method: Optional[str] = Field(
        None, description="Method of verification"
    )

    # Internal tracking
    compliance_check_ids: list[str] = Field(
        default_factory=list, description="Related compliance check IDs"
    )

    # Filing information
    prepared_by: str = Field(..., description="User ID who prepared report")
    reviewed_by: Optional[str] = Field(None, description="User ID who reviewed")
    filed_by: Optional[str] = Field(None, description="User ID who filed")

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When report was created"
    )
    reviewed_at: Optional[datetime] = Field(None, description="Review timestamp")
    filed_at: Optional[datetime] = Field(None, description="Filing timestamp")

    # Regulatory submission
    bsa_identifier: Optional[str] = Field(
        None, description="BSA E-Filing System identifier"
    )
    fincen_ack_number: Optional[str] = Field(
        None, description="FinCEN acknowledgment number"
    )

    # Amendment information
    is_amendment: bool = Field(default=False, description="Is this an amendment")
    prior_report_id: Optional[str] = Field(
        None, description="ID of report being amended"
    )
    prior_bsa_identifier: Optional[str] = Field(
        None, description="Prior BSA identifier"
    )

    # Exemption
    is_exempt: bool = Field(default=False, description="Transaction exempt from reporting")
    exemption_type: Optional[str] = Field(None, description="Type of exemption")

    # Metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class RegulatoryReportSummary(BaseModel):
    """Summary view of regulatory report for listing"""

    id: str = Field(..., description="Report ID")
    organization_id: str = Field(..., description="Organization ID")
    report_type: ReportType = Field(..., description="Report type")
    status: ReportStatus = Field(..., description="Filing status")
    priority: Optional[ReportPriority] = Field(None, description="Priority")

    # Key amounts
    total_amount: Decimal = Field(..., description="Total amount")
    currency: str = Field(..., description="Currency")

    # Key dates
    transaction_date: Optional[datetime] = Field(None, description="Transaction date")
    activity_start_date: Optional[datetime] = Field(None, description="Activity start")
    created_at: datetime = Field(..., description="Creation timestamp")
    filed_at: Optional[datetime] = Field(None, description="Filing timestamp")

    # Key people
    prepared_by: str = Field(..., description="Preparer user ID")
    filed_by: Optional[str] = Field(None, description="Filer user ID")

    # Regulatory submission
    bsa_identifier: Optional[str] = Field(None, description="BSA identifier")
    fincen_ack_number: Optional[str] = Field(None, description="FinCEN ack number")

    # Counts
    subject_count: int = Field(default=0, description="Number of subjects")
    transaction_count: int = Field(default=0, description="Number of transactions")


class RegulatoryReportingConfig(BaseModel):
    """Configuration for automated regulatory reporting"""

    organization_id: str = Field(..., description="Organization ID")

    # CTR configuration
    ctr_enabled: bool = Field(default=True, description="Enable CTR reporting")
    ctr_threshold: Decimal = Field(
        default=Decimal("10000.00"),
        description="CTR reporting threshold"
    )
    ctr_auto_generate: bool = Field(
        default=True, description="Automatically generate CTRs"
    )
    ctr_aggregation_window_hours: int = Field(
        default=24, description="Hours to aggregate transactions"
    )

    # SAR configuration
    sar_enabled: bool = Field(default=True, description="Enable SAR reporting")
    sar_auto_generate: bool = Field(
        default=False,
        description="Automatically generate SARs (requires manual review)"
    )
    sar_risk_score_threshold: int = Field(
        default=75,
        description="Risk score threshold for auto SAR generation"
    )

    # Filing schedule
    auto_file_reports: bool = Field(
        default=False, description="Automatically file approved reports"
    )
    require_dual_approval: bool = Field(
        default=True, description="Require two approvals before filing"
    )

    # Notifications
    notify_on_report_generation: bool = Field(
        default=True, description="Notify on report generation"
    )
    notification_emails: list[str] = Field(
        default_factory=list, description="Email addresses for notifications"
    )
    notification_user_ids: list[str] = Field(
        default_factory=list, description="User IDs to notify"
    )

    # Retention
    report_retention_days: int = Field(
        default=1825, description="Report retention period (default 5 years)"
    )

    # Integration
    fincen_api_enabled: bool = Field(
        default=False, description="Enable FinCEN BSA E-Filing integration"
    )
    fincen_filing_type: Optional[str] = Field(
        None, description="FinCEN filing type identifier"
    )

    # Metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional configuration"
    )
