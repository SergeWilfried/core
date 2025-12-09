"""
Account domain models
"""

from enum import Enum
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AccountType(str, Enum):
    """Account types"""

    CHECKING = "checking"
    SAVINGS = "savings"
    BUSINESS = "business"
    ESCROW = "escrow"


class AccountStatus(str, Enum):
    """Account status"""

    PENDING = "pending"
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class Account(BaseModel):
    """Account model"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: str = Field(..., description="Account identifier")
    customer_id: str = Field(..., description="Customer identifier")
    account_type: AccountType = Field(..., description="Account type")
    currency: str = Field(default="USD", description="Account currency")
    balance: Decimal = Field(default=Decimal("0"), description="Current balance")
    available_balance: Decimal = Field(
        default=Decimal("0"), description="Available balance"
    )
    status: AccountStatus = Field(
        default=AccountStatus.ACTIVE, description="Account status"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    def is_active(self) -> bool:
        """Check if account is active"""
        return self.status == AccountStatus.ACTIVE

    def is_frozen(self) -> bool:
        """Check if account is frozen"""
        return self.status == AccountStatus.FROZEN

    def can_transact(self) -> bool:
        """Check if account can perform transactions"""
        return self.status == AccountStatus.ACTIVE
