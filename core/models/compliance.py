"""
Compliance domain models for KYC/AML and transaction monitoring
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ComplianceStatus(str, Enum):
    """Compliance check status"""

    APPROVED = "approved"
    BLOCKED = "blocked"
    REVIEW = "review"
    PENDING = "pending"
    EXPIRED = "expired"


class ComplianceCheckType(str, Enum):
    """Type of compliance check"""

    KYC = "kyc"
    KYB = "kyb"
    SANCTIONS = "sanctions"
    PEP = "pep"  # Politically Exposed Person
    VELOCITY = "velocity"
    AMOUNT_THRESHOLD = "amount_threshold"
    GEO_FENCING = "geo_fencing"
    PATTERN_DETECTION = "pattern_detection"
    RISK_ASSESSMENT = "risk_assessment"
    BENEFICIAL_OWNERSHIP = "beneficial_ownership"
    SOURCE_OF_FUNDS = "source_of_funds"


class RiskLevel(str, Enum):
    """Risk level assessment"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SanctionListType(str, Enum):
    """Sanction list types"""

    OFAC = "ofac"  # US Office of Foreign Assets Control
    UN = "un"  # United Nations
    EU = "eu"  # European Union
    UK = "uk"  # UK HM Treasury
    INTERPOL = "interpol"
    CUSTOM = "custom"  # Organization-specific blacklist


class ComplianceAction(str, Enum):
    """Action taken by compliance system"""

    ALLOW = "allow"
    BLOCK = "block"
    REVIEW = "review"
    ALERT = "alert"
    LOG = "log"


class ComplianceCheck(BaseModel):
    """Record of a compliance check performed"""

    id: str = Field(..., description="Unique compliance check ID")
    organization_id: str = Field(..., description="Organization ID")
    check_type: ComplianceCheckType = Field(..., description="Type of check")
    status: ComplianceStatus = Field(..., description="Check result status")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Risk level assessment")

    # Subject of the check
    customer_id: str | None = Field(None, description="Customer being checked")
    account_id: str | None = Field(None, description="Account being checked")
    transaction_id: str | None = Field(None, description="Transaction being checked")
    payment_id: str | None = Field(None, description="Payment being checked")

    # Check details
    rules_evaluated: list[str] = Field(
        default_factory=list, description="Rules that were evaluated"
    )
    rules_triggered: list[str] = Field(
        default_factory=list, description="Rules that were triggered"
    )
    reason: str | None = Field(None, description="Reason for status")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional check details")

    # Sanctions screening results
    sanctions_matches: list[dict] = Field(
        default_factory=list, description="Any sanction list matches"
    )

    # Scoring
    risk_score: int = Field(default=0, ge=0, le=100, description="Risk score (0-100)")

    # Review tracking
    requires_manual_review: bool = Field(default=False, description="Requires manual review")
    reviewed_by: str | None = Field(None, description="User ID who reviewed")
    reviewed_at: datetime | None = Field(None, description="When it was reviewed")
    review_notes: str | None = Field(None, description="Review notes")

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When check was performed"
    )
    expires_at: datetime | None = Field(None, description="When check expires")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def is_approved(self) -> bool:
        """Check if compliance check approved"""
        return self.status == ComplianceStatus.APPROVED

    def is_blocked(self) -> bool:
        """Check if compliance check blocked"""
        return self.status == ComplianceStatus.BLOCKED

    def needs_review(self) -> bool:
        """Check if compliance check needs review"""
        return self.status == ComplianceStatus.REVIEW or self.requires_manual_review

    def is_high_risk(self) -> bool:
        """Check if high risk"""
        return self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]


class RiskScore(BaseModel):
    """Customer/transaction risk score"""

    id: str = Field(..., description="Unique risk score ID")
    organization_id: str = Field(..., description="Organization ID")

    # Subject
    customer_id: str | None = Field(None, description="Customer ID")
    account_id: str | None = Field(None, description="Account ID")
    transaction_id: str | None = Field(None, description="Transaction ID")

    # Score
    overall_score: int = Field(..., ge=0, le=100, description="Overall risk score (0-100)")
    risk_level: RiskLevel = Field(..., description="Risk level")

    # Score components
    kyc_score: int = Field(default=0, ge=0, le=100, description="KYC score")
    transaction_score: int = Field(default=0, ge=0, le=100, description="Transaction pattern score")
    geographic_score: int = Field(default=0, ge=0, le=100, description="Geographic risk score")
    velocity_score: int = Field(default=0, ge=0, le=100, description="Velocity score")
    sanctions_score: int = Field(default=0, ge=0, le=100, description="Sanctions screening score")

    # Factors
    risk_factors: list[str] = Field(default_factory=list, description="Risk factors identified")

    # Details
    details: dict[str, Any] = Field(default_factory=dict, description="Score calculation details")

    # Timestamps
    calculated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When score was calculated"
    )
    valid_until: datetime | None = Field(None, description="Score validity period")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @classmethod
    def calculate_risk_level(cls, score: int) -> RiskLevel:
        """Calculate risk level from score"""
        if score < 25:
            return RiskLevel.LOW
        elif score < 50:
            return RiskLevel.MEDIUM
        elif score < 75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL


class SanctionMatch(BaseModel):
    """Sanction list match result"""

    id: str = Field(..., description="Match ID")
    organization_id: str = Field(..., description="Organization ID")
    compliance_check_id: str = Field(..., description="Associated compliance check ID")

    # Match subject
    customer_id: str | None = Field(None, description="Customer ID")
    entity_name: str = Field(..., description="Name that was screened")

    # Match details
    list_type: SanctionListType = Field(..., description="Sanction list type")
    match_name: str = Field(..., description="Name from sanction list")
    match_score: float = Field(..., ge=0, le=1, description="Match confidence score (0-1)")
    match_type: str = Field(default="exact", description="Match type: exact, fuzzy, alias")

    # Sanction details
    sanction_id: str = Field(..., description="ID from sanction list")
    program: str | None = Field(None, description="Sanctions program (e.g., SDGT, IRAN)")
    country: str | None = Field(None, description="Country associated with sanction")
    aliases: list[str] = Field(default_factory=list, description="Known aliases")
    remarks: str | None = Field(None, description="Additional remarks")

    # Status
    is_false_positive: bool = Field(default=False, description="Marked as false positive")
    reviewed_by: str | None = Field(None, description="User who reviewed")
    reviewed_at: datetime | None = Field(None, description="When reviewed")

    # Timestamps
    detected_at: datetime = Field(
        default_factory=datetime.utcnow, description="When match was detected"
    )

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class VelocityCheck(BaseModel):
    """Velocity/pattern monitoring result"""

    id: str = Field(..., description="Velocity check ID")
    organization_id: str = Field(..., description="Organization ID")
    customer_id: str = Field(..., description="Customer ID")
    account_id: str | None = Field(None, description="Account ID")

    # Time period
    period: str = Field(..., description="Time period: hourly, daily, weekly, monthly")
    start_time: datetime = Field(..., description="Period start")
    end_time: datetime = Field(..., description="Period end")

    # Metrics
    transaction_count: int = Field(default=0, description="Number of transactions")
    total_amount: Decimal = Field(default=Decimal("0"), description="Total amount")
    average_amount: Decimal = Field(default=Decimal("0"), description="Average amount")
    max_amount: Decimal = Field(default=Decimal("0"), description="Maximum amount")

    # Limits
    count_limit: int | None = Field(None, description="Transaction count limit")
    amount_limit: Decimal | None = Field(None, description="Amount limit")

    # Status
    limit_exceeded: bool = Field(default=False, description="Whether limit was exceeded")
    exceeded_limits: list[str] = Field(
        default_factory=list, description="Which limits were exceeded"
    )

    # Timestamps
    checked_at: datetime = Field(
        default_factory=datetime.utcnow, description="When check was performed"
    )

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ComplianceAlert(BaseModel):
    """Compliance alert for suspicious activity"""

    id: str = Field(..., description="Alert ID")
    organization_id: str = Field(..., description="Organization ID")
    alert_type: str = Field(..., description="Alert type")
    severity: RiskLevel = Field(..., description="Alert severity")

    # Subject
    customer_id: str | None = Field(None, description="Customer ID")
    account_id: str | None = Field(None, description="Account ID")
    transaction_id: str | None = Field(None, description="Transaction ID")
    payment_id: str | None = Field(None, description="Payment ID")

    # Alert details
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")
    indicators: list[str] = Field(default_factory=list, description="Risk indicators")

    # Status
    status: str = Field(
        default="open", description="Status: open, investigating, resolved, false_positive"
    )
    assigned_to: str | None = Field(None, description="User assigned to investigate")
    resolved_by: str | None = Field(None, description="User who resolved")
    resolved_at: datetime | None = Field(None, description="When resolved")
    resolution_notes: str | None = Field(None, description="Resolution notes")

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When alert was created"
    )

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ComplianceReport(BaseModel):
    """Compliance reporting for regulatory requirements"""

    id: str = Field(..., description="Report ID")
    organization_id: str = Field(..., description="Organization ID")
    report_type: str = Field(..., description="Report type: SAR, CTR, STR, etc.")

    # Period
    start_date: datetime = Field(..., description="Report period start")
    end_date: datetime = Field(..., description="Report period end")

    # Summary
    total_transactions: int = Field(default=0, description="Total transactions")
    flagged_transactions: int = Field(default=0, description="Flagged transactions")
    blocked_transactions: int = Field(default=0, description="Blocked transactions")
    total_amount: Decimal = Field(default=Decimal("0"), description="Total amount")

    # Details
    details: dict[str, Any] = Field(default_factory=dict, description="Report details")

    # Status
    status: str = Field(default="draft", description="Status: draft, submitted, filed")
    filed_by: str | None = Field(None, description="User who filed")
    filed_at: datetime | None = Field(None, description="When filed")

    # Timestamps
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When report was generated"
    )

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
