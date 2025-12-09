"""
Transaction domain models
"""

from enum import Enum
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TransactionType(str, Enum):
    """Transaction types"""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    FEE = "fee"
    REFUND = "refund"
    REVERSAL = "reversal"


class TransactionStatus(str, Enum):
    """Transaction status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class Transaction(BaseModel):
    """Transaction model"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: str = Field(..., description="Transaction identifier")
    organization_id: str = Field(..., description="Organization identifier")
    branch_id: Optional[str] = Field(
        None, description="Branch that processed transaction (nullable for backward compatibility)"
    )
    processed_by_user_id: Optional[str] = Field(
        None, description="User ID who processed the transaction"
    )
    transaction_type: TransactionType = Field(..., description="Transaction type")
    from_account_id: Optional[str] = Field(
        default=None, description="Source account"
    )
    to_account_id: Optional[str] = Field(
        default=None, description="Destination account"
    )
    amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field(default="USD", description="Transaction currency")
    status: TransactionStatus = Field(
        default=TransactionStatus.PENDING, description="Transaction status"
    )
    description: Optional[str] = Field(default=None, description="Transaction description")
    reference: Optional[str] = Field(
        default=None, description="External reference"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Completion timestamp"
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    def is_completed(self) -> bool:
        """Check if transaction is completed"""
        return self.status == TransactionStatus.COMPLETED

    def is_pending(self) -> bool:
        """Check if transaction is pending"""
        return self.status in [TransactionStatus.PENDING, TransactionStatus.PROCESSING]

    def is_reversible(self) -> bool:
        """Check if transaction can be reversed"""
        return (
            self.status == TransactionStatus.COMPLETED
            and self.transaction_type != TransactionType.REVERSAL
        )
