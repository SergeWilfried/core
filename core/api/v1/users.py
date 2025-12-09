"""
User management API endpoints
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, EmailStr

from ...models.user import User, UserRole, UserStatus, Permission
from ...services.users import UserService
from ..dependencies import get_user_service, get_current_user


router = APIRouter(prefix="/users", tags=["users"])


# Request/Response schemas
class CreateUserRequest(BaseModel):
    organization_id: str = Field(..., description="Organization ID")
    email: EmailStr = Field(..., description="User email")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    role: UserRole = Field(..., description="User role")
    password: Optional[str] = Field(default=None, description="User password")
    phone: Optional[str] = Field(default=None, description="Phone number")
    permissions: list[Permission] = Field(
        default_factory=list, description="Additional permissions"
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = Field(default=None, description="First name")
    last_name: Optional[str] = Field(default=None, description="Last name")
    phone: Optional[str] = Field(default=None, description="Phone number")
    role: Optional[UserRole] = Field(default=None, description="User role")
    permissions: Optional[list[Permission]] = Field(
        default=None, description="Additional permissions"
    )
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, description="New password")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")
    organization_id: Optional[str] = Field(
        default=None, description="Organization ID (optional)"
    )


class UserResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    role: UserRole
    permissions: list[Permission]
    status: UserStatus
    email_verified: bool
    two_factor_enabled: bool


class LoginResponse(BaseModel):
    user: UserResponse
    token: str
    refresh_token: str
    expires_at: str


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a new user"""
    try:
        user = await service.create_user(
            organization_id=request.organization_id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            role=request.role,
            password=request.password,
            phone=request.phone,
            permissions=request.permissions,
            created_by=current_user.get("user_id"),
            metadata=request.metadata,
        )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """User login"""
    try:
        user, session = await service.authenticate(
            email=request.email,
            password=request.password,
            organization_id=request.organization_id,
        )

        return LoginResponse(
            user=UserResponse(**user.model_dump()),
            token=session.token,
            refresh_token=session.refresh_token or "",
            expires_at=session.expires_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """User logout"""
    try:
        token = current_user.get("token")
        if token:
            await service.logout(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to logout: {str(e)}",
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get user by ID"""
    try:
        user = await service.get_user(user_id)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}",
        )


@router.get("/organization/{organization_id}", response_model=list[UserResponse])
async def list_organization_users(
    organization_id: str,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user_status: Optional[UserStatus] = Query(default=None, alias="status"),
    user_role: Optional[UserRole] = Query(default=None, alias="role"),
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """List users in an organization"""
    try:
        users = await service.list_organization_users(
            organization_id=organization_id,
            limit=limit,
            offset=offset,
            status=user_status,
            role=user_role,
        )
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}",
        )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update user"""
    try:
        # Only include non-None values
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}

        user = await service.update_user(user_id, update_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}",
        )


@router.post("/{user_id}/verify-email", response_model=UserResponse)
async def verify_email(
    user_id: str,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Verify user email"""
    try:
        user = await service.verify_email(user_id)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify email: {str(e)}",
        )


@router.post("/{user_id}/change-password", response_model=UserResponse)
async def change_password(
    user_id: str,
    request: ChangePasswordRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Change user password"""
    try:
        user = await service.change_password(
            user_id=user_id,
            old_password=request.old_password,
            new_password=request.new_password,
        )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{user_id}/reset-password", response_model=UserResponse)
async def reset_password(
    user_id: str,
    request: ResetPasswordRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Reset user password (admin action)"""
    try:
        user = await service.reset_password(user_id=user_id, new_password=request.new_password)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}",
        )


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: str,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Activate user"""
    try:
        user = await service.update_user_status(user_id, UserStatus.ACTIVE)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}",
        )


@router.post("/{user_id}/suspend", response_model=UserResponse)
async def suspend_user(
    user_id: str,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Suspend user"""
    try:
        user = await service.update_user_status(user_id, UserStatus.SUSPENDED)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suspend user: {str(e)}",
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Delete user (soft delete)"""
    try:
        await service.delete_user(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        )
