"""
Organization management service
"""

from typing import Optional
import logging

from ..models.organization import (
    Organization,
    OrganizationType,
    OrganizationStatus,
    OrganizationSettings,
)
from ..models.branch import BranchType, Branch
from ..repositories.formance import FormanceRepository
from ..exceptions import ValidationError


logger = logging.getLogger(__name__)


class OrganizationService:
    """Service for managing organizations"""

    def __init__(self, formance_repo: FormanceRepository):
        self.formance_repo = formance_repo

    async def create_organization(
        self,
        name: str,
        organization_type: OrganizationType,
        email: str,
        address_country: str,
        legal_name: Optional[str] = None,
        phone: Optional[str] = None,
        website: Optional[str] = None,
        address_street: Optional[str] = None,
        address_city: Optional[str] = None,
        address_state: Optional[str] = None,
        address_postal_code: Optional[str] = None,
        tax_id: Optional[str] = None,
        registration_number: Optional[str] = None,
        settings: Optional[OrganizationSettings] = None,
        created_by: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Organization:
        """
        Create a new organization

        Args:
            name: Organization name
            organization_type: Type of organization
            email: Contact email
            address_country: Country code
            legal_name: Legal business name
            phone: Contact phone
            website: Website URL
            address_street: Street address
            address_city: City
            address_state: State/Province
            address_postal_code: Postal code
            tax_id: Tax identification number
            registration_number: Business registration number
            settings: Organization settings
            created_by: User ID who created the organization
            metadata: Additional metadata

        Returns:
            Created Organization object
        """
        logger.info(f"Creating organization: {name}")

        org_data = await self.formance_repo.create_organization(
            name=name,
            legal_name=legal_name,
            organization_type=organization_type,
            email=email,
            phone=phone,
            website=website,
            address_street=address_street,
            address_city=address_city,
            address_state=address_state,
            address_postal_code=address_postal_code,
            address_country=address_country,
            tax_id=tax_id,
            registration_number=registration_number,
            settings=settings or OrganizationSettings(),
            created_by=created_by,
            metadata=metadata or {},
        )

        organization = Organization(**org_data)
        logger.info(f"Organization created: {organization.id}")

        # Auto-create headquarters branch
        from .branches import BranchService
        branch_service = BranchService(self.formance_repo)

        hq_branch = await branch_service.create_branch(
            organization_id=organization.id,
            name=f"{name} - Headquarters",
            code="HQ",
            branch_type=BranchType.HEADQUARTERS,
            address_country=address_country,
            address_street=address_street,
            address_city=address_city,
            address_state=address_state,
            address_postal_code=address_postal_code,
            email=email,
            phone=phone,
            metadata={"auto_created": True, "created_with_organization": True},
        )

        logger.info(f"Auto-created HQ branch {hq_branch.id} for organization {organization.id}")

        return organization

    async def get_organization(self, organization_id: str) -> Organization:
        """
        Get organization by ID

        Args:
            organization_id: Organization identifier

        Returns:
            Organization object
        """
        org_data = await self.formance_repo.get_organization(organization_id)
        return Organization(**org_data)

    async def update_organization(
        self,
        organization_id: str,
        update_data: dict,
    ) -> Organization:
        """
        Update organization

        Args:
            organization_id: Organization identifier
            update_data: Dictionary of fields to update

        Returns:
            Updated Organization object
        """
        logger.info(f"Updating organization: {organization_id}")

        org_data = await self.formance_repo.update_organization(
            organization_id, update_data
        )

        return Organization(**org_data)

    async def update_organization_status(
        self,
        organization_id: str,
        status: OrganizationStatus,
    ) -> Organization:
        """
        Update organization status

        Args:
            organization_id: Organization identifier
            status: New organization status

        Returns:
            Updated Organization object
        """
        logger.info(f"Updating organization {organization_id} status to {status}")

        return await self.update_organization(
            organization_id, {"status": status.value}
        )

    async def update_organization_settings(
        self,
        organization_id: str,
        settings: OrganizationSettings,
    ) -> Organization:
        """
        Update organization settings

        Args:
            organization_id: Organization identifier
            settings: New organization settings

        Returns:
            Updated Organization object
        """
        logger.info(f"Updating organization {organization_id} settings")

        return await self.update_organization(
            organization_id, {"settings": settings.model_dump()}
        )

    async def verify_organization(
        self,
        organization_id: str,
    ) -> Organization:
        """
        Mark organization as verified (KYB complete)

        Args:
            organization_id: Organization identifier

        Returns:
            Updated Organization object
        """
        from datetime import datetime

        logger.info(f"Verifying organization: {organization_id}")

        return await self.update_organization(
            organization_id,
            {"kyb_status": "verified", "verified_at": datetime.utcnow()},
        )

    async def list_organizations(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[OrganizationStatus] = None,
    ) -> list[Organization]:
        """
        List organizations

        Args:
            limit: Maximum number of organizations to return
            offset: Number of organizations to skip
            status: Filter by status

        Returns:
            List of Organization objects
        """
        orgs_data = await self.formance_repo.list_organizations(
            limit=limit,
            offset=offset,
            status=status.value if status else None,
        )
        return [Organization(**data) for data in orgs_data]

    async def delete_organization(self, organization_id: str) -> None:
        """
        Delete (soft delete) an organization

        Args:
            organization_id: Organization identifier
        """
        logger.info(f"Deleting organization: {organization_id}")

        await self.update_organization_status(
            organization_id, OrganizationStatus.CLOSED
        )
