"""
Branch domain models for multi-branch organizations
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class BranchType(str, Enum):
    """Branch type"""

    HEADQUARTERS = "headquarters"  # Main/head office
    REGIONAL = "regional"  # Regional office
    BRANCH = "branch"  # Standard branch
    SUB_BRANCH = "sub_branch"  # Sub-branch
    AGENCY = "agency"  # Agency/kiosk
    VIRTUAL = "virtual"  # Virtual/online-only branch


class BranchStatus(str, Enum):
    """Branch status"""

    PENDING = "pending"  # Setup pending
    ACTIVE = "active"  # Operational
    SUSPENDED = "suspended"  # Temporarily suspended
    INACTIVE = "inactive"  # Deactivated
    CLOSED = "closed"  # Permanently closed


class BranchSettings(BaseModel):
    """Branch-specific settings"""

    # Transaction limits (can override org settings)
    max_daily_transaction_limit: float | None = Field(
        None, description="Branch-specific daily limit"
    )
    max_transaction_amount: float | None = Field(
        None, description="Branch-specific transaction limit"
    )

    # Branch capabilities
    allow_cash_transactions: bool = Field(
        default=True, description="Allow cash deposits/withdrawals"
    )
    allow_account_opening: bool = Field(default=True, description="Allow new account opening")
    allow_loan_processing: bool = Field(default=False, description="Allow loan processing")

    # Compliance settings (inherits from org, can be stricter)
    require_manager_approval_above: float | None = Field(
        None, description="Amount requiring branch manager approval"
    )
    compliance_level_override: str | None = Field(
        None, description="Override org compliance level (must be stricter)"
    )

    # Operating hours
    operating_hours: dict | None = Field(
        None, description="Operating hours by day: {'monday': {'open': '09:00', 'close': '17:00'}}"
    )
    timezone: str = Field(default="UTC", description="Branch timezone")


class Branch(BaseModel):
    """Branch model for multi-branch organizations"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: str = Field(..., description="Branch identifier")
    organization_id: str = Field(..., description="Parent organization ID")

    # Parent branch for hierarchy
    parent_branch_id: str | None = Field(
        None, description="Parent branch ID (for regional hierarchy)"
    )

    # Branch details
    name: str = Field(..., description="Branch name")
    code: str = Field(..., description="Branch code (e.g., BR001)")
    branch_type: BranchType = Field(..., description="Type of branch")

    # Contact information
    email: str | None = Field(None, description="Branch email")
    phone: str | None = Field(None, description="Branch phone")

    # Address
    address_street: str | None = Field(None, description="Street address")
    address_city: str | None = Field(None, description="City")
    address_state: str | None = Field(None, description="State/Province")
    address_postal_code: str | None = Field(None, description="Postal code")
    address_country: str = Field(..., description="Country code (ISO 3166-1)")

    # Geolocation (for mapping/routing)
    latitude: float | None = Field(None, description="Latitude")
    longitude: float | None = Field(None, description="Longitude")

    # Branch manager
    manager_user_id: str | None = Field(None, description="Branch manager user ID")

    # Status
    status: BranchStatus = Field(default=BranchStatus.PENDING, description="Branch status")

    # Settings
    settings: BranchSettings = Field(
        default_factory=BranchSettings, description="Branch-specific settings"
    )

    # Statistics (cached)
    total_accounts: int = Field(default=0, description="Number of accounts")
    total_customers: int = Field(default=0, description="Number of customers")
    total_users: int = Field(default=0, description="Number of staff users")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    opened_at: datetime | None = Field(None, description="When branch opened for business")
    closed_at: datetime | None = Field(None, description="When branch closed")

    # Metadata
    created_by: str | None = Field(None, description="Created by user ID")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    def is_active(self) -> bool:
        """Check if branch is active"""
        return self.status == BranchStatus.ACTIVE

    def is_headquarters(self) -> bool:
        """Check if this is the headquarters"""
        return self.branch_type == BranchType.HEADQUARTERS

    def can_operate(self) -> bool:
        """Check if branch can perform operations"""
        return self.is_active()

    def get_effective_transaction_limit(self, org_limit: float | None) -> float | None:
        """
        Get effective transaction limit considering both org and branch limits

        Returns the more restrictive (lower) limit
        """
        if self.settings.max_transaction_amount and org_limit:
            return min(self.settings.max_transaction_amount, org_limit)
        return self.settings.max_transaction_amount or org_limit

    def get_effective_compliance_level(self, org_compliance_level: str) -> str:
        """
        Get effective compliance level

        Branch can only be stricter, not more lenient
        """
        if self.settings.compliance_level_override:
            # Map to strictness levels
            strictness = {"basic": 1, "standard": 2, "strict": 3}
            org_level = strictness.get(org_compliance_level, 2)
            branch_level = strictness.get(self.settings.compliance_level_override, 2)

            # Use stricter level
            if branch_level >= org_level:
                return self.settings.compliance_level_override

        return org_compliance_level


class BranchAssignment(BaseModel):
    """User or resource assignment to branch"""

    id: str = Field(..., description="Assignment ID")
    organization_id: str = Field(..., description="Organization ID")
    branch_id: str = Field(..., description="Branch ID")

    # What is being assigned
    user_id: str | None = Field(None, description="User ID if assigning user")
    resource_type: str | None = Field(None, description="Resource type: account, customer, etc.")
    resource_id: str | None = Field(None, description="Resource ID")

    # Assignment details
    role_at_branch: str | None = Field(
        None, description="User's role at this branch (if user assignment)"
    )
    is_primary: bool = Field(default=True, description="Primary assignment for this user/resource")

    # Timestamps
    assigned_at: datetime = Field(
        default_factory=datetime.utcnow, description="Assignment timestamp"
    )
    assigned_by: str | None = Field(None, description="Assigned by user ID")

    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class BranchPerformanceMetrics(BaseModel):
    """Branch performance metrics for reporting"""

    branch_id: str = Field(..., description="Branch ID")
    organization_id: str = Field(..., description="Organization ID")

    # Time period
    period_start: datetime = Field(..., description="Period start")
    period_end: datetime = Field(..., description="Period end")

    # Transaction metrics
    total_transactions: int = Field(default=0, description="Total transactions")
    total_transaction_volume: float = Field(default=0.0, description="Total transaction volume")
    average_transaction_amount: float = Field(default=0.0, description="Average transaction amount")

    # Account metrics
    new_accounts_opened: int = Field(default=0, description="New accounts")
    accounts_closed: int = Field(default=0, description="Accounts closed")
    active_accounts: int = Field(default=0, description="Active accounts")

    # Customer metrics
    new_customers: int = Field(default=0, description="New customers onboarded")
    active_customers: int = Field(default=0, description="Active customers")

    # Compliance metrics
    compliance_checks_performed: int = Field(default=0, description="Compliance checks")
    transactions_blocked: int = Field(default=0, description="Transactions blocked")
    manual_reviews_required: int = Field(default=0, description="Manual reviews required")
    average_risk_score: float = Field(default=0.0, description="Average risk score")

    # Timestamps
    calculated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Calculation timestamp"
    )

    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional metrics")
