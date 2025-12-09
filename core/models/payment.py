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
    MOBILE_MONEY = "mobile_money"


class MobileMoneyProvider(str, Enum):
    """Mobile money providers"""

    MPESA = "mpesa"  # Kenya, Tanzania, Mozambique, South Africa
    MTN_MOBILE_MONEY = "mtn"  # Uganda, Ghana, Ivory Coast, Cameroon, Zambia
    AIRTEL_MONEY = "airtel"  # Multiple African countries
    ORANGE_MONEY = "orange"  # West Africa (Senegal, Mali, Burkina Faso, etc.)
    VODACOM = "vodacom"  # South Africa
    TIGO_PESA = "tigo"  # Tanzania
    ECOCASH = "ecocash"  # Zimbabwe
    WAVE = "wave"  # Senegal, Ivory Coast, Burkina Faso, Mali
    CHIPPER_CASH = "chipper"  # Pan-African
    FLUTTERWAVE = "flutterwave"  # Pan-African aggregator


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
    organization_id: str = Field(..., description="Organization identifier")
    branch_id: Optional[str] = Field(
        None, description="Branch that initiated payment (nullable for backward compatibility)"
    )
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


class MobileMoneyDestination(BaseModel):
    """Mobile money destination details"""

    phone_number: str = Field(..., description="Phone number in E.164 format")
    provider: MobileMoneyProvider = Field(..., description="Mobile money provider")
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")

    def to_destination_string(self) -> str:
        """Convert to destination string format: provider:country:phone"""
        return f"{self.provider.value}:{self.country_code}:{self.phone_number}"

    @classmethod
    def from_destination_string(cls, destination: str) -> "MobileMoneyDestination":
        """Parse destination string back to MobileMoneyDestination"""
        parts = destination.split(":")
        if len(parts) != 3:
            raise ValueError(f"Invalid mobile money destination format: {destination}")
        return cls(
            provider=parts[0],
            country_code=parts[1],
            phone_number=parts[2],
        )
