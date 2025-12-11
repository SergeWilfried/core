"""
Customer domain models
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerStatus(str, Enum):
    """Customer status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class KYCStatus(str, Enum):
    """KYC verification status"""

    NOT_STARTED = "not_started"
    PENDING = "pending"
    IN_REVIEW = "in_review"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Address(BaseModel):
    """Customer address"""

    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/Province")
    postal_code: str = Field(..., description="Postal code")
    country: str = Field(..., description="Country code (ISO 3166-1 alpha-2)")


class Customer(BaseModel):
    """Customer model"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: str = Field(..., description="Customer identifier")
    organization_id: str = Field(..., description="Organization identifier")
    branch_id: str = Field(..., description="Branch where customer was registered")
    email: EmailStr = Field(..., description="Customer email")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    phone: str | None = Field(default=None, description="Phone number")
    address: Address | None = Field(default=None, description="Customer address")
    status: CustomerStatus = Field(default=CustomerStatus.ACTIVE, description="Customer status")
    kyc_status: KYCStatus = Field(
        default=KYCStatus.NOT_STARTED, description="KYC verification status"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    @property
    def full_name(self) -> str:
        """Get full name"""
        return f"{self.first_name} {self.last_name}"

    def is_active(self) -> bool:
        """Check if customer is active"""
        return self.status == CustomerStatus.ACTIVE

    def is_kyc_verified(self) -> bool:
        """Check if customer KYC is verified"""
        return self.kyc_status == KYCStatus.VERIFIED

    def can_transact(self) -> bool:
        """Check if customer can perform transactions"""
        return self.is_active() and self.is_kyc_verified()
