# Organizations and Users Management Guide

## Overview

The BaaS Core Banking System now includes comprehensive multi-tenancy support through Organizations and Users management. This enables:

- **Multi-tenant architecture**: Multiple organizations on a single platform
- **Role-based access control (RBAC)**: Fine-grained permissions system
- **User authentication**: Secure login and session management
- **Team collaboration**: Multiple users per organization with different roles

## Architecture

### Organization Hierarchy

```
Platform
├── Organization 1
│   ├── User 1 (Owner)
│   ├── User 2 (Admin)
│   ├── User 3 (Finance Manager)
│   └── Accounts, Customers, Payments, etc.
├── Organization 2
│   ├── User 4 (Owner)
│   └── Accounts, Customers, Payments, etc.
└── Organization 3
    └── ...
```

### Data Model

```
Organization
    ├── Users (many)
    ├── Accounts (many)
    ├── Customers (many)
    ├── Payments (many)
    └── Settings
```

## Organizations

### Organization Types

| Type | Description | Use Case |
|------|-------------|----------|
| `individual` | Single person business | Freelancers, sole proprietors |
| `business` | Small business | SMBs, startups |
| `enterprise` | Large enterprise | Large corporations |
| `fintech` | Financial technology company | Fintech platforms |
| `marketplace` | Marketplace platform | E-commerce platforms |
| `non_profit` | Non-profit organization | NGOs, foundations |

### Organization Status

- **pending**: Registration pending verification
- **active**: Active and operational
- **suspended**: Temporarily suspended
- **inactive**: Deactivated
- **closed**: Permanently closed

### Organization Settings

```python
class OrganizationSettings:
    allow_mobile_money: bool = True
    allow_international: bool = False
    require_2fa: bool = False
    max_daily_transaction_limit: Optional[float] = None
    allowed_currencies: list[str] = ["USD"]
    webhook_url: Optional[str] = None
    api_callback_url: Optional[str] = None
```

### API Endpoints

#### Create Organization

```bash
POST /api/v1/organizations
```

**Request**:
```json
{
  "name": "Acme Corporation",
  "legal_name": "Acme Corp Inc.",
  "organization_type": "business",
  "email": "contact@acme.com",
  "phone": "+1234567890",
  "website": "https://acme.com",
  "address_street": "123 Main St",
  "address_city": "San Francisco",
  "address_state": "CA",
  "address_postal_code": "94102",
  "address_country": "US",
  "tax_id": "12-3456789",
  "settings": {
    "allow_mobile_money": true,
    "allowed_currencies": ["USD", "KES"]
  }
}
```

#### Get Organization

```bash
GET /api/v1/organizations/{organization_id}
```

#### List Organizations

```bash
GET /api/v1/organizations?limit=50&offset=0&status=active
```

#### Update Organization

```bash
PATCH /api/v1/organizations/{organization_id}
```

#### Update Organization Settings

```bash
PATCH /api/v1/organizations/{organization_id}/settings
```

#### Verify Organization (KYB)

```bash
POST /api/v1/organizations/{organization_id}/verify
```

#### Activate/Suspend Organization

```bash
POST /api/v1/organizations/{organization_id}/activate
POST /api/v1/organizations/{organization_id}/suspend
```

## Users

### User Roles

| Role | Description | Typical Use Case |
|------|-------------|------------------|
| `super_admin` | Platform super administrator | Platform operators |
| `org_owner` | Organization owner | Business owners |
| `org_admin` | Organization administrator | IT managers |
| `finance_manager` | Finance/treasury manager | CFOs, finance team |
| `accountant` | Accountant with limited access | Accounting team |
| `developer` | API developer access | Engineering team |
| `support` | Support staff (read-only) | Customer support |
| `viewer` | Read-only viewer | Stakeholders, auditors |

### Permissions System

The system uses a comprehensive role-based permissions model:

#### Permission Categories

**Account Permissions**:
- `accounts:read`
- `accounts:create`
- `accounts:update`
- `accounts:delete`

**Transaction Permissions**:
- `transactions:read`
- `transactions:create`
- `transactions:approve`

**Payment Permissions**:
- `payments:read`
- `payments:create`
- `payments:approve`
- `payments:cancel`

**Customer Permissions**:
- `customers:read`
- `customers:create`
- `customers:update`
- `customers:delete`

**User Management Permissions**:
- `users:read`
- `users:create`
- `users:update`
- `users:delete`

**Organization Permissions**:
- `org:read`
- `org:update`
- `org:settings`

**Card Permissions**:
- `cards:read`
- `cards:create`
- `cards:update`

**Reporting Permissions**:
- `reports:view`
- `reports:export`

**Audit Permissions**:
- `audit:read`

### Role-Permission Mapping

Each role has a predefined set of permissions:

```python
# Example: Finance Manager permissions
ROLE_PERMISSIONS[UserRole.FINANCE_MANAGER] = [
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
]
```

### User Status

- **pending**: Pending email verification
- **active**: Active user
- **suspended**: Temporarily suspended
- **inactive**: Deactivated
- **locked**: Locked due to security reasons

### API Endpoints

#### Create User

```bash
POST /api/v1/users
```

**Request**:
```json
{
  "organization_id": "org_acme",
  "email": "john@acme.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "finance_manager",
  "password": "SecurePassword123!",
  "phone": "+1234567890"
}
```

#### User Login

```bash
POST /api/v1/users/login
```

**Request**:
```json
{
  "email": "john@acme.com",
  "password": "SecurePassword123!",
  "organization_id": "org_acme"
}
```

**Response**:
```json
{
  "user": {
    "id": "usr_john",
    "organization_id": "org_acme",
    "email": "john@acme.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "finance_manager",
    "status": "active"
  },
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZn...",
  "expires_at": "2025-12-10T10:00:00Z"
}
```

#### User Logout

```bash
POST /api/v1/users/logout
```

#### Get User

```bash
GET /api/v1/users/{user_id}
```

#### List Organization Users

```bash
GET /api/v1/users/organization/{organization_id}?limit=50&offset=0&status=active&role=finance_manager
```

#### Update User

```bash
PATCH /api/v1/users/{user_id}
```

#### Change Password

```bash
POST /api/v1/users/{user_id}/change-password
```

**Request**:
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword123!"
}
```

#### Reset Password (Admin)

```bash
POST /api/v1/users/{user_id}/reset-password
```

#### Verify Email

```bash
POST /api/v1/users/{user_id}/verify-email
```

#### Activate/Suspend User

```bash
POST /api/v1/users/{user_id}/activate
POST /api/v1/users/{user_id}/suspend
```

## Authentication & Authorization

### Authentication Flow

1. **User Login**: POST `/api/v1/users/login`
   - Email + Password validation
   - Check user status (active, email verified)
   - Generate session token
   - Return user info + token

2. **Token Usage**: Include in `Authorization` header
   ```
   Authorization: Bearer <token>
   ```

3. **Session Validation**: Automatic on each request
   - Validate token
   - Check expiration
   - Load user + permissions

4. **Logout**: POST `/api/v1/users/logout`
   - Invalidate session token

### Authorization Flow

```python
# Check if user has specific permission
if user.has_permission(Permission.PAYMENTS_CREATE):
    # Allow payment creation
    pass

# Check if user has any of multiple permissions
if user.has_any_permission([Permission.PAYMENTS_READ, Permission.TRANSACTIONS_READ]):
    # Allow viewing financial data
    pass

# Check if user has all permissions
if user.has_all_permissions([Permission.ACCOUNTS_CREATE, Permission.CUSTOMERS_CREATE]):
    # Allow account+customer creation
    pass
```

## Usage Examples

### Python SDK Example

```python
from core.services.organizations import OrganizationService
from core.services.users import UserService
from core.models.organization import OrganizationType
from core.models.user import UserRole

# Create organization
org = await org_service.create_organization(
    name="Acme Corporation",
    organization_type=OrganizationType.BUSINESS,
    email="contact@acme.com",
    address_country="US",
)

# Create owner user
owner = await user_service.create_user(
    organization_id=org.id,
    email="owner@acme.com",
    first_name="Alice",
    last_name="Smith",
    role=UserRole.ORG_OWNER,
    password="SecurePassword123!",
)

# Verify email
await user_service.verify_email(owner.id)

# Login
user, session = await user_service.authenticate(
    email="owner@acme.com",
    password="SecurePassword123!",
)

# Check permissions
if user.has_permission(Permission.PAYMENTS_CREATE):
    # Create payment
    pass
```

### cURL Examples

**Create Organization**:
```bash
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "organization_type": "business",
    "email": "contact@acme.com",
    "address_country": "US"
  }'
```

**Create User**:
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_acme",
    "email": "john@acme.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "finance_manager",
    "password": "SecurePassword123!"
  }'
```

**Login**:
```bash
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@acme.com",
    "password": "SecurePassword123!"
  }'
```

## Security Considerations

### Password Security

**Current Implementation** (Placeholder):
- Uses SHA-256 hashing
- ⚠️ **TODO**: Replace with bcrypt or argon2

**Recommendations**:
```python
# Install: pip install bcrypt
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
```

### Session Security

- **Token Generation**: Cryptographically secure random tokens
- **Token Expiration**: 24 hours (configurable)
- **Refresh Tokens**: Supported for long-term sessions
- **Session Storage**: TODO - Implement Redis for session storage

### Best Practices

1. **2FA**: Implement two-factor authentication for sensitive roles
2. **Password Policy**: Enforce strong passwords (8+ chars, mixed case, numbers, symbols)
3. **Rate Limiting**: Implement rate limiting on login endpoints
4. **Audit Logging**: Log all authentication attempts and authorization failures
5. **Session Rotation**: Rotate session tokens periodically
6. **IP Whitelisting**: Allow IP whitelisting for organization access

## Multi-Tenancy Patterns

### Data Isolation

Organizations are fully isolated:
- Each organization has its own set of accounts, customers, payments
- Users can only access data within their organization
- API endpoints validate organization ownership

### Shared Resources

Some resources may be shared across organizations:
- Payment providers (M-Pesa, MTN, etc.)
- Currency exchange rates
- Compliance/KYC providers

## Database Schema (Recommended)

```sql
-- Organizations table
CREATE TABLE organizations (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    organization_type VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    kyb_status VARCHAR(50) NOT NULL DEFAULT 'not_started',
    settings JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Users table
CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,
    organization_id VARCHAR(255) NOT NULL REFERENCES organizations(id),
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    email_verified BOOLEAN DEFAULT FALSE,
    permissions JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(organization_id, email)
);

-- User sessions table
CREATE TABLE user_sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id),
    organization_id VARCHAR(255) NOT NULL REFERENCES organizations(id),
    token VARCHAR(512) NOT NULL UNIQUE,
    refresh_token VARCHAR(512),
    ip_address VARCHAR(45),
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP
);

CREATE INDEX idx_sessions_token ON user_sessions(token);
CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);
```

## Future Enhancements

1. **OAuth2 Integration**: Support for Google, Microsoft, GitHub login
2. **SSO/SAML**: Enterprise single sign-on
3. **API Keys**: Long-lived API keys for service accounts
4. **Webhooks**: Event-driven notifications for user/org changes
5. **Audit Logs**: Comprehensive audit trail for all operations
6. **Team Management**: Sub-teams within organizations
7. **Custom Roles**: Allow organizations to define custom roles
8. **Password Recovery**: Email-based password reset flow
9. **Email Verification**: Automated email verification flow
10. **2FA Implementation**: TOTP-based two-factor authentication

## Resources

- [RBAC Best Practices](https://auth0.com/docs/manage-users/access-control/rbac)
- [Multi-Tenancy Patterns](https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/overview)
- [OWASP Authentication](https://owasp.org/www-project-top-ten/2017/A2_2017-Broken_Authentication)

