"""
User management and authentication service
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from ..exceptions import ValidationError
from ..models.user import Permission, User, UserRole, UserSession, UserStatus
from ..repositories.formance import FormanceRepository

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users and authentication"""

    def __init__(self, formance_repo: FormanceRepository):
        self.formance_repo = formance_repo

    def _hash_password(self, password: str) -> str:
        """
        Hash password using SHA-256

        TODO: Replace with proper password hashing (bcrypt, argon2)
        This is a placeholder implementation
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password) == password_hash

    def _generate_token(self) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)

    async def create_user(
        self,
        organization_id: str,
        email: str,
        first_name: str,
        last_name: str,
        role: UserRole,
        password: str | None = None,
        phone: str | None = None,
        permissions: list[Permission] | None = None,
        created_by: str | None = None,
        metadata: dict | None = None,
    ) -> User:
        """
        Create a new user

        Args:
            organization_id: Organization ID
            email: User email
            first_name: First name
            last_name: Last name
            role: User role
            password: User password (will be hashed)
            phone: Phone number
            permissions: Additional custom permissions
            created_by: User ID who created this user
            metadata: Additional metadata

        Returns:
            Created User object
        """
        logger.info(f"Creating user: {email} for organization {organization_id}")

        # Hash password if provided
        password_hash = self._hash_password(password) if password else None

        user_data = await self.formance_repo.create_user(
            organization_id=organization_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            password_hash=password_hash,
            phone=phone,
            permissions=permissions or [],
            created_by=created_by,
            metadata=metadata or {},
        )

        user = User(**user_data)
        logger.info(f"User created: {user.id}")
        return user

    async def get_user(self, user_id: str) -> User:
        """
        Get user by ID

        Args:
            user_id: User identifier

        Returns:
            User object
        """
        user_data = await self.formance_repo.get_user(user_id)
        return User(**user_data)

    async def get_user_by_email(self, email: str, organization_id: str | None = None) -> User:
        """
        Get user by email

        Args:
            email: User email
            organization_id: Optional organization ID filter

        Returns:
            User object
        """
        user_data = await self.formance_repo.get_user_by_email(email, organization_id)
        return User(**user_data)

    async def update_user(
        self,
        user_id: str,
        update_data: dict,
    ) -> User:
        """
        Update user

        Args:
            user_id: User identifier
            update_data: Dictionary of fields to update

        Returns:
            Updated User object
        """
        logger.info(f"Updating user: {user_id}")

        user_data = await self.formance_repo.update_user(user_id, update_data)
        return User(**user_data)

    async def update_user_status(
        self,
        user_id: str,
        status: UserStatus,
    ) -> User:
        """
        Update user status

        Args:
            user_id: User identifier
            status: New user status

        Returns:
            Updated User object
        """
        logger.info(f"Updating user {user_id} status to {status}")

        return await self.update_user(user_id, {"status": status.value})

    async def update_user_role(
        self,
        user_id: str,
        role: UserRole,
    ) -> User:
        """
        Update user role

        Args:
            user_id: User identifier
            role: New user role

        Returns:
            Updated User object
        """
        logger.info(f"Updating user {user_id} role to {role}")

        return await self.update_user(user_id, {"role": role.value})

    async def list_organization_users(
        self,
        organization_id: str,
        limit: int = 50,
        offset: int = 0,
        status: UserStatus | None = None,
        role: UserRole | None = None,
    ) -> list[User]:
        """
        List users in an organization

        Args:
            organization_id: Organization ID
            limit: Maximum number of users to return
            offset: Number of users to skip
            status: Filter by status
            role: Filter by role

        Returns:
            List of User objects
        """
        users_data = await self.formance_repo.list_organization_users(
            organization_id=organization_id,
            limit=limit,
            offset=offset,
            status=status.value if status else None,
            role=role.value if role else None,
        )
        return [User(**data) for data in users_data]

    async def verify_email(self, user_id: str) -> User:
        """
        Mark user email as verified

        Args:
            user_id: User identifier

        Returns:
            Updated User object
        """
        logger.info(f"Verifying email for user: {user_id}")

        return await self.update_user(
            user_id,
            {
                "email_verified": True,
                "email_verified_at": datetime.utcnow(),
                "status": UserStatus.ACTIVE.value,
            },
        )

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
    ) -> User:
        """
        Change user password

        Args:
            user_id: User identifier
            old_password: Current password
            new_password: New password

        Returns:
            Updated User object

        Raises:
            ValidationError: If old password is incorrect
        """
        user = await self.get_user(user_id)

        if not user.password_hash:
            raise ValidationError("User has no password set")

        if not self._verify_password(old_password, user.password_hash):
            raise ValidationError("Incorrect password")

        new_hash = self._hash_password(new_password)

        return await self.update_user(user_id, {"password_hash": new_hash})

    async def reset_password(
        self,
        user_id: str,
        new_password: str,
    ) -> User:
        """
        Reset user password (admin action)

        Args:
            user_id: User identifier
            new_password: New password

        Returns:
            Updated User object
        """
        logger.info(f"Resetting password for user: {user_id}")

        new_hash = self._hash_password(new_password)
        return await self.update_user(user_id, {"password_hash": new_hash})

    async def authenticate(
        self,
        email: str,
        password: str,
        organization_id: str | None = None,
    ) -> tuple[User, UserSession]:
        """
        Authenticate user with email and password

        Args:
            email: User email
            password: User password
            organization_id: Optional organization ID

        Returns:
            Tuple of (User, UserSession)

        Raises:
            ValidationError: If authentication fails
        """
        logger.info(f"Authenticating user: {email}")

        try:
            user = await self.get_user_by_email(email, organization_id)
        except Exception:
            raise ValidationError("Invalid email or password")

        # Check if user can login
        if not user.can_login():
            raise ValidationError(f"User account is {user.status}")

        # Verify password
        if not user.password_hash or not self._verify_password(password, user.password_hash):
            # Increment failed login attempts
            await self.update_user(
                user.id,
                {"failed_login_attempts": user.failed_login_attempts + 1},
            )
            raise ValidationError("Invalid email or password")

        # Reset failed login attempts on successful login
        if user.failed_login_attempts > 0:
            await self.update_user(
                user.id,
                {"failed_login_attempts": 0, "last_login_at": datetime.utcnow()},
            )

        # Create session
        session = await self._create_session(user)

        logger.info(f"User authenticated: {user.id}")
        return user, session

    async def _create_session(
        self,
        user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserSession:
        """
        Create a new user session

        Args:
            user: User object
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            UserSession object
        """
        token = self._generate_token()
        refresh_token = self._generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=24)

        session_data = await self.formance_repo.create_user_session(
            user_id=user.id,
            organization_id=user.organization_id,
            token=token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )

        return UserSession(**session_data)

    async def validate_session(self, token: str) -> tuple[User, UserSession]:
        """
        Validate session token and return user

        Args:
            token: Session token

        Returns:
            Tuple of (User, UserSession)

        Raises:
            ValidationError: If session is invalid or expired
        """
        session_data = await self.formance_repo.get_session_by_token(token)

        if not session_data:
            raise ValidationError("Invalid session token")

        session = UserSession(**session_data)

        if session.is_expired():
            raise ValidationError("Session expired")

        user = await self.get_user(session.user_id)

        if not user.can_login():
            raise ValidationError(f"User account is {user.status}")

        return user, session

    async def logout(self, token: str) -> None:
        """
        Logout user by invalidating session

        Args:
            token: Session token
        """
        logger.info("Logging out session")
        await self.formance_repo.delete_user_session(token)

    async def delete_user(self, user_id: str) -> None:
        """
        Delete (soft delete) a user

        Args:
            user_id: User identifier
        """
        logger.info(f"Deleting user: {user_id}")

        await self.update_user_status(user_id, UserStatus.INACTIVE)
