"""
Payment processing service
"""

import logging
from decimal import Decimal

from ..models.payment import MobileMoneyProvider, Payment, PaymentMethod, PaymentStatus
from ..repositories.formance import FormanceRepository
from ..utils.validators import (
    validate_country_code,
    validate_e164_phone,
    validate_mobile_money_provider,
)

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for processing payments"""

    def __init__(self, formance_repo: FormanceRepository):
        self.formance_repo = formance_repo

    async def create_payment(
        self,
        from_account_id: str,
        amount: Decimal,
        currency: str,
        payment_method: PaymentMethod,
        destination: str,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> Payment:
        """
        Create a new payment

        Args:
            from_account_id: Source account
            amount: Payment amount
            currency: Payment currency
            payment_method: Payment method (ACH, WIRE, CARD, etc.)
            destination: Payment destination (account number, card, etc.)
            description: Payment description
            metadata: Additional metadata

        Returns:
            Created Payment object
        """
        logger.info(
            f"Creating {payment_method} payment: {amount} {currency} from {from_account_id}"
        )

        payment_data = await self.formance_repo.create_payment(
            from_account_id=from_account_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            destination=destination,
            description=description,
            metadata=metadata or {},
        )

        payment = Payment(**payment_data)
        logger.info(f"Payment created: {payment.id}")
        return payment

    async def get_payment(self, payment_id: str) -> Payment:
        """
        Get payment by ID

        Args:
            payment_id: Payment identifier

        Returns:
            Payment object
        """
        payment_data = await self.formance_repo.get_payment(payment_id)
        return Payment(**payment_data)

    async def list_account_payments(
        self,
        account_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Payment]:
        """
        List payments for an account

        Args:
            account_id: Account identifier
            limit: Maximum number of payments to return
            offset: Number of payments to skip

        Returns:
            List of Payment objects
        """
        payments_data = await self.formance_repo.list_payments(
            account_id=account_id,
            limit=limit,
            offset=offset,
        )
        return [Payment(**data) for data in payments_data]

    async def cancel_payment(self, payment_id: str) -> Payment:
        """
        Cancel a pending payment

        Args:
            payment_id: Payment identifier

        Returns:
            Updated Payment object
        """
        logger.info(f"Cancelling payment {payment_id}")

        payment_data = await self.formance_repo.update_payment_status(
            payment_id, PaymentStatus.CANCELLED
        )

        return Payment(**payment_data)

    async def process_ach_payment(
        self,
        from_account_id: str,
        routing_number: str,
        account_number: str,
        amount: Decimal,
        currency: str = "USD",
        description: str | None = None,
    ) -> Payment:
        """
        Process an ACH payment

        Args:
            from_account_id: Source account
            routing_number: Destination bank routing number
            account_number: Destination account number
            amount: Payment amount
            currency: Payment currency
            description: Payment description

        Returns:
            Created Payment object
        """
        destination = f"{routing_number}:{account_number}"
        return await self.create_payment(
            from_account_id=from_account_id,
            amount=amount,
            currency=currency,
            payment_method=PaymentMethod.ACH,
            destination=destination,
            description=description or "ACH Payment",
        )

    async def process_wire_payment(
        self,
        from_account_id: str,
        beneficiary_account: str,
        swift_code: str,
        amount: Decimal,
        currency: str = "USD",
        description: str | None = None,
    ) -> Payment:
        """
        Process a wire transfer

        Args:
            from_account_id: Source account
            beneficiary_account: Beneficiary account number
            swift_code: SWIFT/BIC code
            amount: Payment amount
            currency: Payment currency
            description: Payment description

        Returns:
            Created Payment object
        """
        destination = f"{swift_code}:{beneficiary_account}"
        return await self.create_payment(
            from_account_id=from_account_id,
            amount=amount,
            currency=currency,
            payment_method=PaymentMethod.WIRE,
            destination=destination,
            description=description or "Wire Transfer",
        )

    async def process_mobile_money_payment(
        self,
        from_account_id: str,
        phone_number: str,
        provider: MobileMoneyProvider,
        country_code: str,
        amount: Decimal,
        currency: str,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> Payment:
        """
        Process a mobile money payment

        Args:
            from_account_id: Source account
            phone_number: Recipient phone number in E.164 format (e.g., +254712345678)
            provider: Mobile money provider (e.g., MPESA, MTN_MOBILE_MONEY)
            country_code: ISO 3166-1 alpha-2 country code (e.g., KE, UG)
            amount: Payment amount
            currency: Payment currency (e.g., KES, UGX)
            description: Payment description
            metadata: Additional metadata

        Returns:
            Created Payment object

        Raises:
            ValidationError: If phone number, provider, or country code is invalid
        """
        # Validate inputs
        validate_e164_phone(phone_number)
        validate_country_code(country_code)
        validate_mobile_money_provider(provider.value, country_code)

        logger.info(
            f"Processing mobile money payment: {amount} {currency} "
            f"to {phone_number} via {provider.value} in {country_code}"
        )

        # Format destination as: provider:country:phone
        # e.g., "mpesa:KE:+254712345678"
        destination = f"{provider.value}:{country_code.upper()}:{phone_number}"

        # Add provider and country to metadata for tracking
        payment_metadata = metadata or {}
        payment_metadata.update(
            {
                "mobile_money_provider": provider.value,
                "country_code": country_code.upper(),
                "phone_number": phone_number,
            }
        )

        return await self.create_payment(
            from_account_id=from_account_id,
            amount=amount,
            currency=currency,
            payment_method=PaymentMethod.MOBILE_MONEY,
            destination=destination,
            description=description or f"Mobile Money Transfer via {provider.value}",
            metadata=payment_metadata,
        )
