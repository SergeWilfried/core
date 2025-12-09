"""
Payment domain models
"""

from enum import Enum
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PaymentMethod(str, Enum):
    """Payment methods"""

    ACH = "ach"
    WIRE = "wire"
    CARD = "card"
    CHECK = "check"
    CRYPTO = "crypto"
    INTERNAL = "internal"


class PaymentStatus(str, Enum):
    """Payment status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class Payment(BaseModel):
    """Payment model"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: str = Field(..., description="Payment identifier")
    from_account_id: str = Field(..., description="Source account")
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field(default="USD", description="Payment currency")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    destination: str = Field(..., description="Payment destination")
    status: PaymentStatus = Field(
        default=PaymentStatus.PENDING, description="Payment status"
    )
    description: Optional[str] = Field(
        default=None, description="Payment description"
    )
    reference: Optional[str] = Field(
        default=None, description="External reference"
    )
    transaction_id: Optional[str] = Field(
        default=None, description="Associated transaction ID"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Completion timestamp"
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    def is_completed(self) -> bool:
        """Check if payment is completed"""
        return self.status == PaymentStatus.COMPLETED

    def is_pending(self) -> bool:
        """Check if payment is pending"""
        return self.status in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]

    def can_cancel(self) -> bool:
        """Check if payment can be cancelled"""
        return self.status in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]
