"""
Branch management service
"""

import logging
import secrets
from datetime import datetime
from typing import Optional
from decimal import Decimal

from ..models.branch import Branch, BranchType, BranchStatus, BranchSettings, BranchPerformanceMetrics
from ..models.organization import Organization
from ..repositories.formance import FormanceRepository
from ..exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)


class BranchService:
    """Service for managing branches"""

    def __init__(self, formance_repo: FormanceRepository):
        self.formance_repo = formance_repo

    async def create_branch(
        self,
        organization_id: str,
        name: str,
        code: str,
        branch_type: BranchType,
        address_country: str,
        parent_branch_id: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address_street: Optional[str] = None,
        address_city: Optional[str] = None,
        address_state: Optional[str] = None,
        address_postal_code: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        manager_user_id: Optional[str] = None,
        settings: Optional[BranchSettings] = None,
        metadata: Optional[dict] = None,
    ) -> Branch:
        """
        Create a new branch

        Args:
            organization_id: Parent organization ID
            name: Branch name
            code: Branch code (must be unique within organization)
            branch_type: Type of branch
            address_country: Country code
            parent_branch_id: Parent branch for hierarchy
            email: Branch email
            phone: Branch phone
            address_street: Street address
            address_city: City
            address_state: State/Province
            address_postal_code: Postal code
            latitude: Latitude for mapping
            longitude: Longitude for mapping
            manager_user_id: Branch manager
            settings: Branch-specific settings
            metadata: Additional metadata

        Returns:
            Created Branch object
        """
        branch_id = f"branch_{secrets.token_hex(12)}"

        logger.info(
            f"Creating branch {code} for organization {organization_id}"
        )

        # Validate organization exists
        org_data = await self.formance_repo.get_organization(organization_id)
        if not org_data:
            raise NotFoundError(f"Organization {organization_id} not found")

        org = Organization(**org_data)

        # Validate parent branch if specified
        if parent_branch_id:
            parent_data = await self.formance_repo.get_branch(parent_branch_id)
            if not parent_data:
                raise NotFoundError(f"Parent branch {parent_branch_id} not found")

            parent = Branch(**parent_data)
            if parent.organization_id != organization_id:
                raise ValidationError(
                    "Parent branch must belong to same organization"
                )

        # Create branch
        branch_data = await self.formance_repo.create_branch(
            id=branch_id,
            organization_id=organization_id,
            parent_branch_id=parent_branch_id,
            name=name,
            code=code,
            branch_type=branch_type,
            email=email,
            phone=phone,
            address_street=address_street,
            address_city=address_city,
            address_state=address_state,
            address_postal_code=address_postal_code,
            address_country=address_country,
            latitude=latitude,
            longitude=longitude,
            manager_user_id=manager_user_id,
            settings=settings or BranchSettings(),
            metadata=metadata or {},
        )

        branch = Branch(**branch_data)
        logger.info(f"Branch created: {branch.id} ({branch.code})")

        return branch

    async def get_branch(self, branch_id: str) -> Branch:
        """
        Get branch by ID

        Args:
            branch_id: Branch identifier

        Returns:
            Branch object
        """
        branch_data = await self.formance_repo.get_branch(branch_id)
        if not branch_data:
            raise NotFoundError(f"Branch {branch_id} not found")

        return Branch(**branch_data)

    async def list_organization_branches(
        self,
        organization_id: str,
        status: Optional[BranchStatus] = None,
        branch_type: Optional[BranchType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Branch]:
        """
        List branches for an organization

        Args:
            organization_id: Organization ID
            status: Filter by status
            branch_type: Filter by branch type
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of Branch objects
        """
        branches_data = await self.formance_repo.list_branches(
            organization_id=organization_id,
            status=status,
            branch_type=branch_type,
            limit=limit,
            offset=offset,
        )

        return [Branch(**data) for data in branches_data]

    async def update_branch(
        self, branch_id: str, update_data: dict
    ) -> Branch:
        """
        Update branch

        Args:
            branch_id: Branch identifier
            update_data: Fields to update

        Returns:
            Updated Branch object
        """
        branch_data = await self.formance_repo.update_branch(
            branch_id, update_data
        )
        return Branch(**branch_data)

    async def activate_branch(self, branch_id: str) -> Branch:
        """Activate a branch"""
        return await self.update_branch(
            branch_id,
            {
                "status": BranchStatus.ACTIVE,
                "opened_at": datetime.utcnow(),
            },
        )

    async def suspend_branch(self, branch_id: str) -> Branch:
        """Suspend a branch"""
        return await self.update_branch(
            branch_id, {"status": BranchStatus.SUSPENDED}
        )

    async def close_branch(self, branch_id: str) -> Branch:
        """Close a branch permanently"""
        return await self.update_branch(
            branch_id,
            {
                "status": BranchStatus.CLOSED,
                "closed_at": datetime.utcnow(),
            },
        )

    async def assign_user_to_branch(
        self,
        user_id: str,
        branch_id: str,
        role_at_branch: Optional[str] = None,
        is_primary: bool = False,
    ) -> dict:
        """
        Assign a user to a branch

        Args:
            user_id: User ID
            branch_id: Branch ID
            role_at_branch: User's role at this branch
            is_primary: Whether this is user's primary branch

        Returns:
            Assignment details
        """
        assignment_id = f"assign_{secrets.token_hex(12)}"

        # TODO: Implement actual storage
        assignment = {
            "id": assignment_id,
            "user_id": user_id,
            "branch_id": branch_id,
            "role_at_branch": role_at_branch,
            "is_primary": is_primary,
            "assigned_at": datetime.utcnow(),
        }

        logger.info(
            f"User {user_id} assigned to branch {branch_id}"
        )

        return assignment

    async def remove_user_from_branch(
        self, user_id: str, branch_id: str
    ) -> None:
        """Remove user assignment from branch"""
        # TODO: Implement actual storage
        logger.info(
            f"User {user_id} removed from branch {branch_id}"
        )

    async def get_branch_users(
        self, branch_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        """Get users assigned to branch"""
        # TODO: Implement actual storage
        return []

    async def get_branch_metrics(
        self,
        branch_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> BranchPerformanceMetrics:
        """
        Get branch performance metrics

        Args:
            branch_id: Branch ID
            period_start: Period start date
            period_end: Period end date

        Returns:
            BranchPerformanceMetrics object
        """
        # TODO: Implement actual metrics calculation from transactions
        # This would query Formance ledger and aggregate data

        metrics = BranchPerformanceMetrics(
            branch_id=branch_id,
            organization_id="org_placeholder",  # Get from branch
            period_start=period_start,
            period_end=period_end,
            total_transactions=0,
            total_transaction_volume=0.0,
            average_transaction_amount=0.0,
            new_accounts_opened=0,
            accounts_closed=0,
            active_accounts=0,
            new_customers=0,
            active_customers=0,
            compliance_checks_performed=0,
            transactions_blocked=0,
            manual_reviews_required=0,
            average_risk_score=0.0,
        )

        return metrics

    async def get_effective_settings(
        self, branch_id: str
    ) -> tuple[BranchSettings, dict]:
        """
        Get effective settings for branch considering org inheritance

        Args:
            branch_id: Branch ID

        Returns:
            Tuple of (branch_settings, effective_compliance_settings)
        """
        branch = await self.get_branch(branch_id)

        org_data = await self.formance_repo.get_organization(
            branch.organization_id
        )
        org = Organization(**org_data)

        # Calculate effective settings
        effective_compliance_level = branch.get_effective_compliance_level(
            org.settings.compliance_level
        )

        effective_max_amount = branch.get_effective_transaction_limit(
            org.settings.max_transaction_amount
        )

        effective_settings = {
            "compliance_level": effective_compliance_level,
            "max_transaction_amount": effective_max_amount,
            "enable_sanctions_screening": org.settings.enable_sanctions_screening,
            "enable_velocity_monitoring": org.settings.enable_velocity_monitoring,
            "enable_pep_screening": org.settings.enable_pep_screening,
            "restricted_countries": org.settings.restricted_countries,
            "risk_score_threshold": org.settings.risk_score_threshold,
            # Branch-specific
            "require_manager_approval_above": branch.settings.require_manager_approval_above,
            "allow_cash_transactions": branch.settings.allow_cash_transactions,
            "allow_account_opening": branch.settings.allow_account_opening,
        }

        return branch.settings, effective_settings
