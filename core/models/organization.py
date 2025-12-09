"""
Organization domain models
"""

from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class OrganizationType(str, Enum):
    """Organization type"""

    INDIVIDUAL = "individual"  # Single person business
    BUSINESS = "business"  # Small business
    ENTERPRISE = "enterprise"  # Large enterprise
    FINTECH = "fintech"  # Financial technology company
    MARKETPLACE = "marketplace"  # Marketplace platform
    NON_PROFIT = "non_profit"  # Non-profit organization


class OrganizationStatus(str, Enum):
    """Organization status"""

    PENDING = "pending"  # Registration pending
    ACTIVE = "active"  # Active organization
    SUSPENDED = "suspended"  # Temporarily suspended
    INACTIVE = "inactive"  # Deactivated
    CLOSED = "closed"  # Permanently closed


class OrganizationSettings(BaseModel):
    """Organization settings and preferences"""

    allow_mobile_money: bool = Field(default=True, description="Enable mobile money")
    allow_international: bool = Field(default=False, description="Enable international payments")
    require_2fa: bool = Field(default=False, description="Require 2FA for all users")
    max_daily_transaction_limit: Optional[float] = Field(
        default=None, description="Maximum daily transaction limit"
    )
    allowed_currencies: list[str] = Field(
        default_factory=lambda: ["USD"], description="Allowed currencies"
    )
    webhook_url: Optional[str] = Field(default=None, description="Webhook URL for events")
    api_callback_url: Optional[str] = Field(default=None, description="API callback URL")


class Organization(BaseModel):
    """Organization model"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: str = Field(..., description="Organization identifier")
    name: str = Field(..., description="Organization name")
    legal_name: Optional[str] = Field(default=None, description="Legal business name")
    organization_type: OrganizationType = Field(..., description="Type of organization")
    email: EmailStr = Field(..., description="Organization contact email")
    phone: Optional[str] = Field(default=None, description="Organization phone")
    website: Optional[str] = Field(default=None, description="Organization website")

    # Address
    address_street: Optional[str] = Field(default=None, description="Street address")
    address_city: Optional[str] = Field(default=None, description="City")
    address_state: Optional[str] = Field(default=None, description="State/Province")
    address_postal_code: Optional[str] = Field(default=None, description="Postal code")
    address_country: str = Field(..., description="Country code (ISO 3166-1 alpha-2)")

    # Business details
    tax_id: Optional[str] = Field(default=None, description="Tax identification number")
    registration_number: Optional[str] = Field(
        default=None, description="Business registration number"
    )

    # Status and verification
    status: OrganizationStatus = Field(
        default=OrganizationStatus.PENDING, description="Organization status"
    )
    kyb_status: str = Field(
        default="not_started", description="KYB (Know Your Business) status"
    )
    verified_at: Optional[datetime] = Field(
        default=None, description="Verification timestamp"
    )

    # Settings
    settings: OrganizationSettings = Field(
        default_factory=OrganizationSettings, description="Organization settings"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )
    created_by: Optional[str] = Field(default=None, description="Created by user ID")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    def is_active(self) -> bool:
        """Check if organization is active"""
        return self.status == OrganizationStatus.ACTIVE

    def is_verified(self) -> bool:
        """Check if organization KYB is verified"""
        return self.kyb_status == "verified" and self.verified_at is not None

    def can_operate(self) -> bool:
        """Check if organization can perform operations"""
        return self.is_active() and self.is_verified()
