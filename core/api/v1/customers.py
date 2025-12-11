"""
Customer API endpoints
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from ...exceptions import CustomerNotFoundError
from ...models.customer import Address, CustomerStatus, KYCStatus
from ...services import CustomerService
from ..dependencies import get_current_user, get_customer_service

router = APIRouter(prefix="/customers", tags=["customers"])


# Request/Response schemas
class CreateCustomerRequest(BaseModel):
    email: EmailStr = Field(..., description="Customer email")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    phone: str | None = Field(default=None, description="Phone number")
    address: Address | None = Field(default=None, description="Address")
    metadata: dict = Field(default_factory=dict, description="Metadata")


class UpdateCustomerRequest(BaseModel):
    email: EmailStr | None = Field(default=None, description="Email")
    first_name: str | None = Field(default=None, description="First name")
    last_name: str | None = Field(default=None, description="Last name")
    phone: str | None = Field(default=None, description="Phone number")
    address: Address | None = Field(default=None, description="Address")
    metadata: dict | None = Field(default=None, description="Metadata")


class UpdateKYCRequest(BaseModel):
    kyc_status: KYCStatus = Field(..., description="KYC status")
    kyc_data: dict | None = Field(default=None, description="KYC data")


class CustomerResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None
    address: Address | None
    status: CustomerStatus
    kyc_status: KYCStatus


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    request: CreateCustomerRequest,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a new customer"""
    try:
        customer = await service.create_customer(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            address=request.address.model_dump() if request.address else None,
            metadata=request.metadata,
        )
        return customer
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create customer: {str(e)}",
        )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get customer by ID"""
    try:
        customer = await service.get_customer(customer_id)
        return customer
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer: {str(e)}",
        )


@router.get("/email/{email}", response_model=CustomerResponse)
async def get_customer_by_email(
    email: str,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get customer by email"""
    try:
        customer = await service.get_customer_by_email(email)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with email {email} not found",
            )
        return customer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer: {str(e)}",
        )


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    request: UpdateCustomerRequest,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update customer information"""
    try:
        customer = await service.update_customer(
            customer_id=customer_id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            address=request.address.model_dump() if request.address else None,
            metadata=request.metadata,
        )
        return customer
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update customer: {str(e)}",
        )


@router.post("/{customer_id}/kyc", response_model=CustomerResponse)
async def update_kyc_status(
    customer_id: str,
    request: UpdateKYCRequest,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update customer KYC status"""
    try:
        customer = await service.update_kyc_status(
            customer_id=customer_id,
            kyc_status=request.kyc_status,
            kyc_data=request.kyc_data,
        )
        return customer
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update KYC status: {str(e)}",
        )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_customer(
    customer_id: str,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Deactivate a customer"""
    try:
        await service.deactivate_customer(customer_id)
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate customer: {str(e)}",
        )
