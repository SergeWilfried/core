"""
User domain models
"""

from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserRole(str, Enum):
    """User roles"""

    SUPER_ADMIN = "super_admin"  # Platform super administrator
    ORG_OWNER = "org_owner"  # Organization owner
    ORG_ADMIN = "org_admin"  # Organization administrator
    FINANCE_MANAGER = "finance_manager"  # Finance/treasury manager
    ACCOUNTANT = "accountant"  # Accountant with read/limited write
    DEVELOPER = "developer"  # API developer access
    SUPPORT = "support"  # Support staff with read-only access
    VIEWER = "viewer"  # Read-only viewer


class UserStatus(str, Enum):
    """User status"""

    PENDING = "pending"  # Pending email verification
    ACTIVE = "active"  # Active user
    SUSPENDED = "suspended"  # Temporarily suspended
    INACTIVE = "inactive"  # Deactivated
    LOCKED = "locked"  # Locked due to security reasons


class Permission(str, Enum):
    """User permissions"""

    # Account permissions
    ACCOUNTS_READ = "accounts:read"
    ACCOUNTS_CREATE = "accounts:create"
    ACCOUNTS_UPDATE = "accounts:update"
    ACCOUNTS_DELETE = "accounts:delete"

    # Transaction permissions
    TRANSACTIONS_READ = "transactions:read"
    TRANSACTIONS_CREATE = "transactions:create"
    TRANSACTIONS_APPROVE = "transactions:approve"

    # Payment permissions
    PAYMENTS_READ = "payments:read"
    PAYMENTS_CREATE = "payments:create"
    PAYMENTS_APPROVE = "payments:approve"
    PAYMENTS_CANCEL = "payments:cancel"

    # Customer permissions
    CUSTOMERS_READ = "customers:read"
    CUSTOMERS_CREATE = "customers:create"
    CUSTOMERS_UPDATE = "customers:update"
    CUSTOMERS_DELETE = "customers:delete"

    # User management permissions
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"

    # Organization permissions
    ORG_READ = "org:read"
    ORG_UPDATE = "org:update"
    ORG_SETTINGS = "org:settings"

    # Card permissions
    CARDS_READ = "cards:read"
    CARDS_CREATE = "cards:create"
    CARDS_UPDATE = "cards:update"

    # Reporting permissions
    REPORTS_VIEW = "reports:view"
    REPORTS_EXPORT = "reports:export"

    # Audit permissions
    AUDIT_READ = "audit:read"

    # Compliance permissions
    COMPLIANCE_VIEW = "compliance:view"
    COMPLIANCE_APPROVE = "compliance:approve"
    COMPLIANCE_REJECT = "compliance:reject"
    COMPLIANCE_RULES_MANAGE = "compliance:rules:manage"
    COMPLIANCE_OVERRIDE = "compliance:override"
    COMPLIANCE_REPORTS = "compliance:reports"


# Role-based permission mapping
ROLE_PERMISSIONS: dict[UserRole, list[Permission]] = {
    UserRole.SUPER_ADMIN: list(Permission),  # All permissions
    UserRole.ORG_OWNER: [
        # Full access to organization resources
        Permission.ACCOUNTS_READ,
        Permission.ACCOUNTS_CREATE,
        Permission.ACCOUNTS_UPDATE,
        Permission.ACCOUNTS_DELETE,
        Permission.TRANSACTIONS_READ,
        Permission.TRANSACTIONS_CREATE,
        Permission.TRANSACTIONS_APPROVE,
        Permission.PAYMENTS_READ,
        Permission.PAYMENTS_CREATE,
        Permission.PAYMENTS_APPROVE,
        Permission.PAYMENTS_CANCEL,
        Permission.CUSTOMERS_READ,
        Permission.CUSTOMERS_CREATE,
        Permission.CUSTOMERS_UPDATE,
        Permission.CUSTOMERS_DELETE,
        Permission.USERS_READ,
        Permission.USERS_CREATE,
        Permission.USERS_UPDATE,
        Permission.USERS_DELETE,
        Permission.ORG_READ,
        Permission.ORG_UPDATE,
        Permission.ORG_SETTINGS,
        Permission.CARDS_READ,
        Permission.CARDS_CREATE,
        Permission.CARDS_UPDATE,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_EXPORT,
        Permission.AUDIT_READ,
        Permission.COMPLIANCE_VIEW,
        Permission.COMPLIANCE_APPROVE,
        Permission.COMPLIANCE_REJECT,
        Permission.COMPLIANCE_RULES_MANAGE,
        Permission.COMPLIANCE_OVERRIDE,
        Permission.COMPLIANCE_REPORTS,
    ],
    UserRole.ORG_ADMIN: [
        # Most permissions except org settings and user deletion
        Permission.ACCOUNTS_READ,
        Permission.ACCOUNTS_CREATE,
        Permission.ACCOUNTS_UPDATE,
        Permission.TRANSACTIONS_READ,
        Permission.TRANSACTIONS_CREATE,
        Permission.TRANSACTIONS_APPROVE,
        Permission.PAYMENTS_READ,
        Permission.PAYMENTS_CREATE,
        Permission.PAYMENTS_APPROVE,
        Permission.CUSTOMERS_READ,
        Permission.CUSTOMERS_CREATE,
        Permission.CUSTOMERS_UPDATE,
        Permission.USERS_READ,
        Permission.USERS_CREATE,
        Permission.USERS_UPDATE,
        Permission.ORG_READ,
        Permission.CARDS_READ,
        Permission.CARDS_CREATE,
        Permission.CARDS_UPDATE,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_EXPORT,
        Permission.AUDIT_READ,
        Permission.COMPLIANCE_VIEW,
        Permission.COMPLIANCE_APPROVE,
        Permission.COMPLIANCE_REJECT,
        Permission.COMPLIANCE_REPORTS,
    ],
    UserRole.FINANCE_MANAGER: [
        # Financial operations
        Permission.ACCOUNTS_READ,
        Permission.ACCOUNTS_CREATE,
        Permission.TRANSACTIONS_READ,
        Permission.TRANSACTIONS_CREATE,
        Permission.TRANSACTIONS_APPROVE,
        Permission.PAYMENTS_READ,
        Permission.PAYMENTS_CREATE,
        Permission.PAYMENTS_APPROVE,
        Permission.PAYMENTS_CANCEL,
        Permission.CUSTOMERS_READ,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_EXPORT,
        Permission.COMPLIANCE_VIEW,
        Permission.COMPLIANCE_APPROVE,
        Permission.COMPLIANCE_REPORTS,
    ],
    UserRole.ACCOUNTANT: [
        # Read and limited write
        Permission.ACCOUNTS_READ,
        Permission.TRANSACTIONS_READ,
        Permission.PAYMENTS_READ,
        Permission.CUSTOMERS_READ,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_EXPORT,
        Permission.AUDIT_READ,
    ],
    UserRole.DEVELOPER: [
        # API access
        Permission.ACCOUNTS_READ,
        Permission.ACCOUNTS_CREATE,
        Permission.TRANSACTIONS_READ,
        Permission.TRANSACTIONS_CREATE,
        Permission.PAYMENTS_READ,
        Permission.PAYMENTS_CREATE,
        Permission.CUSTOMERS_READ,
        Permission.CUSTOMERS_CREATE,
    ],
    UserRole.SUPPORT: [
        # Read-only for support
        Permission.ACCOUNTS_READ,
        Permission.TRANSACTIONS_READ,
        Permission.PAYMENTS_READ,
        Permission.CUSTOMERS_READ,
        Permission.CUSTOMERS_UPDATE,
    ],
    UserRole.VIEWER: [
        # Read-only
        Permission.ACCOUNTS_READ,
        Permission.TRANSACTIONS_READ,
        Permission.PAYMENTS_READ,
        Permission.CUSTOMERS_READ,
        Permission.REPORTS_VIEW,
    ],
}


class User(BaseModel):
    """User model"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: str = Field(..., description="User identifier")
    organization_id: str = Field(..., description="Organization ID")
    email: EmailStr = Field(..., description="User email")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    phone: Optional[str] = Field(default=None, description="Phone number")

    # Authentication
    password_hash: Optional[str] = Field(
        default=None, description="Hashed password", exclude=True
    )
    email_verified: bool = Field(default=False, description="Email verification status")
    email_verified_at: Optional[datetime] = Field(
        default=None, description="Email verification timestamp"
    )

    # Authorization
    role: UserRole = Field(..., description="User role")
    permissions: list[Permission] = Field(
        default_factory=list, description="Additional custom permissions"
    )

    # Branch access (NEW for multi-branch support)
    primary_branch_id: Optional[str] = Field(
        None, description="User's primary branch (None for org-wide users)"
    )
    accessible_branches: list[str] = Field(
        default_factory=list,
        description="Branches user can access (empty list = all branches)"
    )

    # Status
    status: UserStatus = Field(default=UserStatus.PENDING, description="User status")
    last_login_at: Optional[datetime] = Field(
        default=None, description="Last login timestamp"
    )
    failed_login_attempts: int = Field(
        default=0, description="Failed login attempts counter"
    )

    # 2FA
    two_factor_enabled: bool = Field(default=False, description="2FA enabled status")
    two_factor_secret: Optional[str] = Field(
        default=None, description="2FA secret", exclude=True
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )
    created_by: Optional[str] = Field(default=None, description="Created by user ID")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    @property
    def full_name(self) -> str:
        """Get full name"""
        return f"{self.first_name} {self.last_name}"

    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE

    def is_email_verified(self) -> bool:
        """Check if email is verified"""
        return self.email_verified

    def can_login(self) -> bool:
        """Check if user can login"""
        return (
            self.is_active()
            and self.is_email_verified()
            and self.status != UserStatus.LOCKED
        )

    def get_all_permissions(self) -> list[Permission]:
        """Get all permissions (role-based + custom)"""
        role_perms = ROLE_PERMISSIONS.get(self.role, [])
        return list(set(role_perms + self.permissions))

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission"""
        return permission in self.get_all_permissions()

    def has_branch_access(self, branch_id: str) -> bool:
        """
        Check if user can access a specific branch

        Args:
            branch_id: Branch identifier to check

        Returns:
            True if user can access the branch
        """
        # Organization-wide users (empty accessible_branches) can access all
        if not self.accessible_branches:
            return True

        # Check if branch in user's accessible list
        return branch_id in self.accessible_branches

    def can_access_all_branches(self) -> bool:
        """Check if user has organization-wide access"""
        return not self.accessible_branches

    def has_any_permission(self, permissions: list[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        user_perms = self.get_all_permissions()
        return any(perm in user_perms for perm in permissions)

    def has_all_permissions(self, permissions: list[Permission]) -> bool:
        """Check if user has all of the specified permissions"""
        user_perms = self.get_all_permissions()
        return all(perm in user_perms for perm in permissions)


class UserSession(BaseModel):
    """User session model"""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User ID")
    organization_id: str = Field(..., description="Organization ID")
    token: str = Field(..., description="Session token")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token")
    ip_address: Optional[str] = Field(default=None, description="IP address")
    user_agent: Optional[str] = Field(default=None, description="User agent")
    expires_at: datetime = Field(..., description="Session expiration")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    last_accessed_at: Optional[datetime] = Field(
        default=None, description="Last access timestamp"
    )

    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
