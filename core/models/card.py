"""
Card domain models
"""

from enum import Enum
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CardType(str, Enum):
    """Card types"""

    VIRTUAL = "virtual"
    PHYSICAL = "physical"


class CardStatus(str, Enum):
    """Card status"""

    PENDING = "pending"
    ACTIVE = "active"
    FROZEN = "frozen"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Card(BaseModel):
    """Card model"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: str = Field(..., description="Card identifier")
    account_id: str = Field(..., description="Associated account")
    customer_id: str = Field(..., description="Card holder")
    card_type: CardType = Field(..., description="Card type")
    last_four: Optional[str] = Field(
        default=None, description="Last 4 digits of card"
    )
    brand: Optional[str] = Field(
        default="VISA", description="Card brand (VISA, MASTERCARD, etc.)"
    )
    expiry_month: Optional[int] = Field(
        default=None, description="Expiry month"
    )
    expiry_year: Optional[int] = Field(
        default=None, description="Expiry year"
    )
    status: CardStatus = Field(
        default=CardStatus.PENDING, description="Card status"
    )
    spending_limit: Optional[Decimal] = Field(
        default=None, description="Daily spending limit"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    activated_at: Optional[datetime] = Field(
        default=None, description="Activation timestamp"
    )
    cancelled_at: Optional[datetime] = Field(
        default=None, description="Cancellation timestamp"
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    def is_active(self) -> bool:
        """Check if card is active"""
        return self.status == CardStatus.ACTIVE

    def is_frozen(self) -> bool:
        """Check if card is frozen"""
        return self.status == CardStatus.FROZEN

    def can_transact(self) -> bool:
        """Check if card can be used for transactions"""
        return self.status == CardStatus.ACTIVE

    def is_expired(self) -> bool:
        """Check if card is expired"""
        if not self.expiry_month or not self.expiry_year:
            return False

        now = datetime.utcnow()
        return (
            self.expiry_year < now.year
            or (self.expiry_year == now.year and self.expiry_month < now.month)
        )
