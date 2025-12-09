"""
Customer management service
"""

from typing import Optional
import logging

from ..models.customer import Customer, CustomerStatus, KYCStatus
from ..repositories.formance import FormanceRepository
from ..exceptions import CustomerNotFoundError, KYCRequiredError


logger = logging.getLogger(__name__)


class CustomerService:
    """Service for managing customers"""

    def __init__(self, formance_repo: FormanceRepository):
        self.formance_repo = formance_repo

    async def create_customer(
        self,
        email: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        address: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> Customer:
        """
        Create a new customer

        Args:
            email: Customer email
            first_name: First name
            last_name: Last name
            phone: Phone number
            address: Customer address
            metadata: Additional metadata

        Returns:
            Created Customer object
        """
        logger.info(f"Creating customer: {email}")

        customer_data = await self.formance_repo.create_customer(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            address=address,
            metadata=metadata or {},
        )

        customer = Customer(**customer_data)
        logger.info(f"Customer created: {customer.id}")
        return customer

    async def get_customer(self, customer_id: str) -> Customer:
        """
        Get customer by ID

        Args:
            customer_id: Customer identifier

        Returns:
            Customer object

        Raises:
            CustomerNotFoundError: If customer doesn't exist
        """
        customer_data = await self.formance_repo.get_customer(customer_id)
        if not customer_data:
            raise CustomerNotFoundError(f"Customer {customer_id} not found")

        return Customer(**customer_data)

    async def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """
        Get customer by email

        Args:
            email: Customer email

        Returns:
            Customer object or None
        """
        customer_data = await self.formance_repo.get_customer_by_email(email)
        if not customer_data:
            return None

        return Customer(**customer_data)

    async def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> Customer:
        """
        Update customer information

        Args:
            customer_id: Customer identifier
            email: New email
            first_name: New first name
            last_name: New last name
            phone: New phone number
            address: New address
            metadata: Additional metadata

        Returns:
            Updated Customer object
        """
        logger.info(f"Updating customer {customer_id}")

        update_data = {}
        if email:
            update_data["email"] = email
        if first_name:
            update_data["first_name"] = first_name
        if last_name:
            update_data["last_name"] = last_name
        if phone:
            update_data["phone"] = phone
        if address:
            update_data["address"] = address
        if metadata:
            update_data["metadata"] = metadata

        customer_data = await self.formance_repo.update_customer(
            customer_id, update_data
        )

        return Customer(**customer_data)

    async def update_kyc_status(
        self, customer_id: str, kyc_status: KYCStatus, kyc_data: Optional[dict] = None
    ) -> Customer:
        """
        Update customer KYC status

        Args:
            customer_id: Customer identifier
            kyc_status: New KYC status
            kyc_data: KYC verification data

        Returns:
            Updated Customer object
        """
        logger.info(f"Updating KYC status for customer {customer_id} to {kyc_status}")

        customer_data = await self.formance_repo.update_customer_metadata(
            customer_id,
            {
                "kyc_status": kyc_status.value,
                "kyc_data": kyc_data or {},
            },
        )

        return Customer(**customer_data)

    async def verify_customer_kyc(self, customer_id: str) -> bool:
        """
        Check if customer has completed KYC

        Args:
            customer_id: Customer identifier

        Returns:
            True if KYC is verified

        Raises:
            KYCRequiredError: If KYC is not verified
        """
        customer = await self.get_customer(customer_id)

        if customer.kyc_status != KYCStatus.VERIFIED:
            raise KYCRequiredError(
                f"Customer {customer_id} KYC status: {customer.kyc_status}"
            )

        return True

    async def deactivate_customer(self, customer_id: str) -> Customer:
        """
        Deactivate a customer

        Args:
            customer_id: Customer identifier

        Returns:
            Updated Customer object
        """
        logger.info(f"Deactivating customer {customer_id}")

        customer_data = await self.formance_repo.update_customer_metadata(
            customer_id, {"status": CustomerStatus.INACTIVE.value}
        )

        return Customer(**customer_data)
