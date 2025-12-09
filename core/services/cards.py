"""
Card management service
"""

from typing import Optional
from decimal import Decimal
import logging

from ..models.card import Card, CardType, CardStatus
from ..repositories.formance import FormanceRepository
from ..exceptions import CardNotFoundError, InvalidCardOperationError


logger = logging.getLogger(__name__)


class CardService:
    """Service for managing payment cards"""

    def __init__(self, formance_repo: FormanceRepository):
        self.formance_repo = formance_repo

    async def create_card(
        self,
        account_id: str,
        customer_id: str,
        card_type: CardType,
        spending_limit: Optional[Decimal] = None,
        metadata: Optional[dict] = None,
    ) -> Card:
        """
        Create a new card (virtual or physical)

        Args:
            account_id: Associated account
            customer_id: Card holder
            card_type: VIRTUAL or PHYSICAL
            spending_limit: Daily spending limit
            metadata: Additional metadata

        Returns:
            Created Card object
        """
        logger.info(f"Creating {card_type} card for customer {customer_id}")

        card_data = await self.formance_repo.create_card(
            account_id=account_id,
            customer_id=customer_id,
            card_type=card_type,
            spending_limit=spending_limit,
            metadata=metadata or {},
        )

        card = Card(**card_data)
        logger.info(f"Card created: {card.id}")
        return card

    async def get_card(self, card_id: str) -> Card:
        """
        Get card by ID

        Args:
            card_id: Card identifier

        Returns:
            Card object

        Raises:
            CardNotFoundError: If card doesn't exist
        """
        card_data = await self.formance_repo.get_card(card_id)
        if not card_data:
            raise CardNotFoundError(f"Card {card_id} not found")

        return Card(**card_data)

    async def list_customer_cards(
        self, customer_id: str, active_only: bool = True
    ) -> list[Card]:
        """
        List all cards for a customer

        Args:
            customer_id: Customer identifier
            active_only: Return only active cards

        Returns:
            List of Card objects
        """
        cards_data = await self.formance_repo.list_cards_by_customer(
            customer_id, active_only
        )
        return [Card(**data) for data in cards_data]

    async def activate_card(self, card_id: str) -> Card:
        """
        Activate a card

        Args:
            card_id: Card identifier

        Returns:
            Updated Card object
        """
        logger.info(f"Activating card {card_id}")

        card_data = await self.formance_repo.update_card_status(
            card_id, CardStatus.ACTIVE
        )

        return Card(**card_data)

    async def freeze_card(self, card_id: str, reason: Optional[str] = None) -> Card:
        """
        Freeze a card (temporary)

        Args:
            card_id: Card identifier
            reason: Reason for freezing

        Returns:
            Updated Card object
        """
        logger.warning(f"Freezing card {card_id}: {reason or 'No reason provided'}")

        card_data = await self.formance_repo.update_card_status(
            card_id, CardStatus.FROZEN
        )

        return Card(**card_data)

    async def unfreeze_card(self, card_id: str) -> Card:
        """
        Unfreeze a frozen card

        Args:
            card_id: Card identifier

        Returns:
            Updated Card object
        """
        logger.info(f"Unfreezing card {card_id}")

        card_data = await self.formance_repo.update_card_status(
            card_id, CardStatus.ACTIVE
        )

        return Card(**card_data)

    async def cancel_card(self, card_id: str, reason: Optional[str] = None) -> Card:
        """
        Cancel a card (permanent)

        Args:
            card_id: Card identifier
            reason: Reason for cancellation

        Returns:
            Updated Card object
        """
        logger.info(f"Cancelling card {card_id}: {reason or 'Customer request'}")

        card_data = await self.formance_repo.update_card_status(
            card_id, CardStatus.CANCELLED
        )

        return Card(**card_data)

    async def update_spending_limit(
        self, card_id: str, new_limit: Decimal
    ) -> Card:
        """
        Update card spending limit

        Args:
            card_id: Card identifier
            new_limit: New daily spending limit

        Returns:
            Updated Card object
        """
        logger.info(f"Updating spending limit for card {card_id} to {new_limit}")

        card_data = await self.formance_repo.update_card_metadata(
            card_id, {"spending_limit": str(new_limit)}
        )

        return Card(**card_data)

    async def get_card_details(self, card_id: str) -> dict:
        """
        Get sensitive card details (PAN, CVV, etc.)
        Should be heavily restricted and logged

        Args:
            card_id: Card identifier

        Returns:
            Card details including sensitive data
        """
        logger.warning(f"Accessing sensitive details for card {card_id}")

        # This should have additional security checks
        card_details = await self.formance_repo.get_card_details(card_id)
        return card_details
