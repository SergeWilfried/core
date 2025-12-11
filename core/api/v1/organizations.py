"""
Organization API endpoints
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

from ...models.organization import (
    OrganizationSettings,
    OrganizationStatus,
    OrganizationType,
)
from ...services.organizations import OrganizationService
from ..dependencies import get_current_user, get_organization_service

router = APIRouter(prefix="/organizations", tags=["organizations"])


# Request/Response schemas
class CreateOrganizationRequest(BaseModel):
    name: str = Field(..., description="Organization name")
    legal_name: str | None = Field(default=None, description="Legal business name")
    organization_type: OrganizationType = Field(..., description="Organization type")
    email: EmailStr = Field(..., description="Contact email")
    phone: str | None = Field(default=None, description="Contact phone")
    website: str | None = Field(default=None, description="Website URL")
    address_street: str | None = Field(default=None, description="Street address")
    address_city: str | None = Field(default=None, description="City")
    address_state: str | None = Field(default=None, description="State/Province")
    address_postal_code: str | None = Field(default=None, description="Postal code")
    address_country: str = Field(..., description="Country code (ISO 3166-1 alpha-2)")
    tax_id: str | None = Field(default=None, description="Tax ID")
    registration_number: str | None = Field(default=None, description="Registration number")
    settings: OrganizationSettings | None = Field(default=None, description="Organization settings")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class UpdateOrganizationRequest(BaseModel):
    name: str | None = Field(default=None, description="Organization name")
    legal_name: str | None = Field(default=None, description="Legal business name")
    email: EmailStr | None = Field(default=None, description="Contact email")
    phone: str | None = Field(default=None, description="Contact phone")
    website: str | None = Field(default=None, description="Website URL")
    address_street: str | None = Field(default=None, description="Street address")
    address_city: str | None = Field(default=None, description="City")
    address_state: str | None = Field(default=None, description="State/Province")
    address_postal_code: str | None = Field(default=None, description="Postal code")
    tax_id: str | None = Field(default=None, description="Tax ID")
    registration_number: str | None = Field(default=None, description="Registration number")
    metadata: dict | None = Field(default=None, description="Additional metadata")


class UpdateOrganizationSettingsRequest(BaseModel):
    allow_mobile_money: bool | None = None
    allow_international: bool | None = None
    require_2fa: bool | None = None
    max_daily_transaction_limit: float | None = None
    allowed_currencies: list[str] | None = None
    webhook_url: str | None = None
    api_callback_url: str | None = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    legal_name: str | None
    organization_type: OrganizationType
    email: str
    phone: str | None
    website: str | None
    address_country: str
    status: OrganizationStatus
    kyb_status: str
    settings: OrganizationSettings


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    request: CreateOrganizationRequest,
    service: Annotated[OrganizationService, Depends(get_organization_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a new organization"""
    try:
        organization = await service.create_organization(
            name=request.name,
            legal_name=request.legal_name,
            organization_type=request.organization_type,
            email=request.email,
            phone=request.phone,
            website=request.website,
            address_street=request.address_street,
            address_city=request.address_city,
            address_state=request.address_state,
            address_postal_code=request.address_postal_code,
            address_country=request.address_country,
            tax_id=request.tax_id,
            registration_number=request.registration_number,
            settings=request.settings,
            created_by=current_user.get("user_id"),
            metadata=request.metadata,
        )
        return organization
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {str(e)}",
        )


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    service: Annotated[OrganizationService, Depends(get_organization_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get organization by ID"""
    try:
        organization = await service.get_organization(organization_id)
        return organization
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization: {str(e)}",
        )


@router.get("/", response_model=list[OrganizationResponse])
async def list_organizations(
    service: Annotated[OrganizationService, Depends(get_organization_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    org_status: OrganizationStatus | None = Query(default=None, alias="status"),
):
    """List organizations"""
    try:
        organizations = await service.list_organizations(
            limit=limit, offset=offset, status=org_status
        )
        return organizations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list organizations: {str(e)}",
        )


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: str,
    request: UpdateOrganizationRequest,
    service: Annotated[OrganizationService, Depends(get_organization_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update organization"""
    try:
        # Only include non-None values
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}

        organization = await service.update_organization(organization_id, update_data)
        return organization
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization: {str(e)}",
        )


@router.patch("/{organization_id}/settings", response_model=OrganizationResponse)
async def update_organization_settings(
    organization_id: str,
    request: UpdateOrganizationSettingsRequest,
    service: Annotated[OrganizationService, Depends(get_organization_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update organization settings"""
    try:
        # Get current organization
        org = await service.get_organization(organization_id)

        # Merge with existing settings
        current_settings = org.settings.model_dump()
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}
        current_settings.update(update_data)

        new_settings = OrganizationSettings(**current_settings)
        organization = await service.update_organization_settings(organization_id, new_settings)
        return organization
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization settings: {str(e)}",
        )


@router.post("/{organization_id}/verify", response_model=OrganizationResponse)
async def verify_organization(
    organization_id: str,
    service: Annotated[OrganizationService, Depends(get_organization_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Verify organization (complete KYB)"""
    try:
        organization = await service.verify_organization(organization_id)
        return organization
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify organization: {str(e)}",
        )


@router.post("/{organization_id}/activate", response_model=OrganizationResponse)
async def activate_organization(
    organization_id: str,
    service: Annotated[OrganizationService, Depends(get_organization_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Activate organization"""
    try:
        organization = await service.update_organization_status(
            organization_id, OrganizationStatus.ACTIVE
        )
        return organization
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate organization: {str(e)}",
        )


@router.post("/{organization_id}/suspend", response_model=OrganizationResponse)
async def suspend_organization(
    organization_id: str,
    service: Annotated[OrganizationService, Depends(get_organization_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Suspend organization"""
    try:
        organization = await service.update_organization_status(
            organization_id, OrganizationStatus.SUSPENDED
        )
        return organization
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suspend organization: {str(e)}",
        )


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: str,
    service: Annotated[OrganizationService, Depends(get_organization_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Delete organization (soft delete)"""
    try:
        await service.delete_organization(organization_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete organization: {str(e)}",
        )
