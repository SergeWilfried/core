# Multi-Branch Architecture Guide

## Overview

This guide explains how to implement multi-branch support for organizations that operate multiple physical or virtual locations (e.g., retail banks, microfinance institutions, franchise networks).

## Architecture

### Hierarchy Levels

```
Platform
│
├── Organization (Acme Bank)
│   ├── Organization Settings (global policies)
│   │   └── Compliance: standard, sanctions: enabled, etc.
│   │
│   ├── Branches (multiple locations)
│   │   ├── Headquarters (BR-HQ)
│   │   │   ├── Branch Settings (can be stricter than org)
│   │   │   ├── Users (branch staff)
│   │   │   ├── Accounts (serviced here)
│   │   │   ├── Customers (registered here)
│   │   │   └── Transactions (processed here)
│   │   │
│   │   ├── Regional Branch (BR-001) - Nairobi
│   │   │   ├── Sub-branches (optional hierarchy)
│   │   │   │   ├── Agency (BR-001-A) - Westlands
│   │   │   │   └── Agency (BR-001-B) - CBD
│   │   │   └── ... resources
│   │   │
│   │   └── Regional Branch (BR-002) - Mombasa
│   │       └── ... resources
│   │
│   └── Organization-level Users (access all branches)
│       └── CEO, CFO, Compliance Officer
```

## Data Model Changes

### 1. Add Branch Foreign Keys

Update existing models to include `branch_id`:

```python
# core/models/account.py
class Account(BaseModel):
    id: str
    customer_id: str
    organization_id: str
    branch_id: Optional[str] = None  # NEW: Branch where account opened
    # ... rest of fields

# core/models/customer.py
class Customer(BaseModel):
    id: str
    organization_id: str
    branch_id: Optional[str] = None  # NEW: Branch where customer registered
    # ... rest of fields

# core/models/transaction.py
class Transaction(BaseModel):
    id: str
    organization_id: str
    branch_id: Optional[str] = None  # NEW: Branch that processed transaction
    processed_by_user_id: Optional[str] = None  # NEW: Staff who processed
    # ... rest of fields

# core/models/user.py
class User(BaseModel):
    id: str
    organization_id: str
    primary_branch_id: Optional[str] = None  # NEW: User's primary branch
    accessible_branches: list[str] = []  # NEW: Branches user can access
    # ... rest of fields
```

### 2. Branch Model

See [core/models/branch.py](core/models/branch.py) for complete implementation:

```python
class Branch(BaseModel):
    id: str
    organization_id: str
    parent_branch_id: Optional[str] = None  # For hierarchy
    name: str
    code: str  # e.g., "BR001"
    branch_type: BranchType  # headquarters, regional, branch, sub_branch, agency
    status: BranchStatus
    settings: BranchSettings  # Can override org settings
    manager_user_id: Optional[str] = None
    # ... address, contact, etc.
```

## Compliance Integration with Branches

### Branch-Level Compliance Settings

Branches can have **stricter** compliance rules than the organization, but never more lenient:

```python
# Organization settings (base level)
org_settings = OrganizationSettings(
    compliance_level="standard",
    max_transaction_amount=50000.00,
    enable_sanctions_screening=True,
)

# Branch settings (can be stricter)
branch_settings = BranchSettings(
    compliance_level_override="strict",  # Stricter than org
    max_transaction_amount=25000.00,  # Lower limit than org
    require_manager_approval_above=10000.00,  # Additional requirement
)

# Effective limits for this branch
effective_limit = branch.get_effective_transaction_limit(
    org_limit=org_settings.max_transaction_amount
)
# Returns: 25000.00 (more restrictive)

effective_compliance = branch.get_effective_compliance_level(
    org_compliance_level=org_settings.compliance_level
)
# Returns: "strict" (stricter)
```

### Updated Compliance Check

The `ComplianceService.check_transaction()` should be updated to consider branch:

```python
async def check_transaction(
    self,
    organization_id: str,
    branch_id: Optional[str],  # NEW parameter
    customer_id: str,
    account_id: str,
    amount: Decimal,
    currency: str,
    # ... other params
) -> ComplianceCheck:
    """Run compliance check considering branch-level settings"""

    # Get organization settings
    org = await self.repository.get_organization(organization_id)

    # Get branch settings if branch specified
    branch = None
    if branch_id:
        branch_data = await self.repository.get_branch(branch_id)
        branch = Branch(**branch_data)

    # Determine effective compliance settings
    if branch:
        effective_compliance_level = branch.get_effective_compliance_level(
            org.settings.compliance_level
        )
        effective_max_amount = branch.get_effective_transaction_limit(
            org.settings.max_transaction_amount
        )

        # Check branch-specific rules
        if branch.settings.require_manager_approval_above:
            if amount > branch.settings.require_manager_approval_above:
                compliance_check.requires_manual_review = True
                compliance_check.reason = (
                    f"Amount exceeds branch approval threshold "
                    f"({branch.settings.require_manager_approval_above})"
                )
    else:
        effective_compliance_level = org.settings.compliance_level
        effective_max_amount = org.settings.max_transaction_amount

    # Continue with compliance checks using effective settings...
```

## User Access Control

### Branch Access Patterns

**Pattern 1: Single Branch Users** (Branch Teller)
```python
user = User(
    id="usr_teller_001",
    organization_id="org_acme_bank",
    primary_branch_id="branch_nairobi_001",
    accessible_branches=["branch_nairobi_001"],
    role=UserRole.ACCOUNTANT,
)
# Can only access: Branch Nairobi 001
```

**Pattern 2: Regional Users** (Regional Manager)
```python
user = User(
    id="usr_regional_mgr",
    organization_id="org_acme_bank",
    primary_branch_id="branch_nairobi_regional",
    accessible_branches=[
        "branch_nairobi_regional",
        "branch_nairobi_001",
        "branch_nairobi_002",
        "branch_nairobi_003",
    ],
    role=UserRole.FINANCE_MANAGER,
)
# Can access: All Nairobi region branches
```

**Pattern 3: Organization-Wide Users** (CEO, Compliance Officer)
```python
user = User(
    id="usr_compliance_officer",
    organization_id="org_acme_bank",
    primary_branch_id=None,  # No primary branch
    accessible_branches=[],  # Empty means ALL branches
    role=UserRole.ORG_ADMIN,
    permissions=[
        Permission.COMPLIANCE_VIEW,
        Permission.COMPLIANCE_APPROVE,
        Permission.COMPLIANCE_REPORTS,
    ],
)
# Can access: All branches in organization
```

### API Authorization Middleware

Add branch access validation:

```python
async def check_branch_access(user: User, branch_id: str) -> bool:
    """Check if user can access branch"""

    # Organization-wide users (empty accessible_branches)
    if not user.accessible_branches:
        return True

    # Check if branch in user's accessible list
    return branch_id in user.accessible_branches


# Usage in API endpoint
@router.get("/branches/{branch_id}/transactions")
async def get_branch_transactions(
    branch_id: str,
    current_user: User = Depends(get_current_user),
):
    # Check access
    if not await check_branch_access(current_user, branch_id):
        raise HTTPException(
            status_code=403,
            detail=f"User does not have access to branch {branch_id}"
        )

    # Fetch transactions...
```

## Formance Ledger Integration

### Account Naming Convention

Use branch codes in Formance account addresses:

```
# Without branches (current)
org:{org_id}:accounts:{account_id}

# With branches (recommended)
org:{org_id}:branch:{branch_code}:accounts:{account_id}

# Examples:
org:acme_bank:branch:BR-HQ:accounts:acc_12345
org:acme_bank:branch:BR-001:accounts:acc_67890
org:acme_bank:branch:BR-002-A:accounts:acc_11111
```

### Branch-Level Ledger Queries

Query transactions by branch:

```python
# Get all transactions for a branch
await formance_repo.get_transactions_by_pattern(
    ledger_id="org_acme_bank",
    address_pattern="org:acme_bank:branch:BR-001:*"
)

# Aggregate balances by branch
await formance_repo.get_aggregated_balances(
    ledger_id="org_acme_bank",
    address_pattern="org:acme_bank:branch:BR-001:accounts:*"
)
```

### Posting with Branch Metadata

```python
# Transaction metadata should include branch info
await formance_repo.post_transaction(
    ledger_id="org_acme_bank",
    postings=[
        {
            "source": "org:acme_bank:branch:BR-001:accounts:acc_12345",
            "destination": "org:acme_bank:branch:BR-002:accounts:acc_67890",
            "amount": 100000,
            "asset": "KES/2"
        }
    ],
    metadata={
        "organization_id": "org_acme_bank",
        "from_branch_id": "branch_nairobi_001",
        "from_branch_code": "BR-001",
        "to_branch_id": "branch_mombasa_001",
        "to_branch_code": "BR-002",
        "processed_by_user_id": "usr_teller_001",
        "compliance_check_id": "chk_xyz123",
        "transaction_type": "inter_branch_transfer",
    }
)
```

## Reporting & Analytics

### Branch Performance Dashboard

```python
from core.models.branch import BranchPerformanceMetrics

# Generate metrics for branch
metrics = BranchPerformanceMetrics(
    branch_id="branch_nairobi_001",
    organization_id="org_acme_bank",
    period_start=datetime(2025, 12, 1),
    period_end=datetime(2025, 12, 31),
    total_transactions=1543,
    total_transaction_volume=15_430_000.00,
    average_transaction_amount=10_000.00,
    new_accounts_opened=45,
    new_customers=38,
    compliance_checks_performed=1543,
    transactions_blocked=12,
    manual_reviews_required=23,
    average_risk_score=28.5,
)
```

### Organization-Wide Rollup

```python
# Get all branch metrics
all_branches = await branch_service.list_branches(org_id)

total_volume = sum(
    branch.metrics.total_transaction_volume
    for branch in all_branches
)

# Compare branch performance
top_performing_branch = max(
    all_branches,
    key=lambda b: b.metrics.total_transaction_volume
)
```

## Database Schema

### Branches Table

```sql
CREATE TABLE branches (
    id VARCHAR(255) PRIMARY KEY,
    organization_id VARCHAR(255) NOT NULL REFERENCES organizations(id),
    parent_branch_id VARCHAR(255) REFERENCES branches(id),

    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    branch_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',

    email VARCHAR(255),
    phone VARCHAR(50),

    address_street VARCHAR(255),
    address_city VARCHAR(100),
    address_state VARCHAR(100),
    address_postal_code VARCHAR(20),
    address_country VARCHAR(2) NOT NULL,

    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),

    manager_user_id VARCHAR(255) REFERENCES users(id),

    settings JSONB,
    metadata JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    opened_at TIMESTAMP,
    closed_at TIMESTAMP,

    UNIQUE(organization_id, code)
);

CREATE INDEX idx_branches_org ON branches(organization_id);
CREATE INDEX idx_branches_parent ON branches(parent_branch_id);
CREATE INDEX idx_branches_status ON branches(status);
```

### User Branch Assignments

```sql
CREATE TABLE user_branch_assignments (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id),
    branch_id VARCHAR(255) NOT NULL REFERENCES branches(id),
    organization_id VARCHAR(255) NOT NULL REFERENCES organizations(id),

    role_at_branch VARCHAR(50),
    is_primary BOOLEAN DEFAULT TRUE,

    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(255) REFERENCES users(id),

    metadata JSONB,

    UNIQUE(user_id, branch_id)
);

CREATE INDEX idx_user_branches_user ON user_branch_assignments(user_id);
CREATE INDEX idx_user_branches_branch ON user_branch_assignments(branch_id);
```

### Update Existing Tables

```sql
-- Add branch_id to accounts
ALTER TABLE accounts ADD COLUMN branch_id VARCHAR(255) REFERENCES branches(id);
CREATE INDEX idx_accounts_branch ON accounts(branch_id);

-- Add branch_id to customers
ALTER TABLE customers ADD COLUMN branch_id VARCHAR(255) REFERENCES branches(id);
CREATE INDEX idx_customers_branch ON customers(branch_id);

-- Add branch_id to transactions
ALTER TABLE transactions ADD COLUMN branch_id VARCHAR(255) REFERENCES branches(id);
ALTER TABLE transactions ADD COLUMN processed_by_user_id VARCHAR(255) REFERENCES users(id);
CREATE INDEX idx_transactions_branch ON transactions(branch_id);

-- Add branch fields to users
ALTER TABLE users ADD COLUMN primary_branch_id VARCHAR(255) REFERENCES branches(id);
CREATE INDEX idx_users_primary_branch ON users(primary_branch_id);
```

## Migration Strategy

### Phase 1: Add Branch Support (Backward Compatible)

1. Create `branches` table
2. Add `branch_id` columns (nullable) to existing tables
3. Existing records have `branch_id = NULL` (treated as org-level)
4. New records can specify branch

### Phase 2: Branch Assignment

1. Create headquarters branch for each organization
2. Assign existing users/accounts/customers to HQ branch
3. Enable branch creation in UI

### Phase 3: Enforce Branch Assignment

1. Make `branch_id` required for new records
2. Update business logic to always specify branch
3. Migrate remaining NULL records

## API Endpoints

### Branch Management

```
POST   /api/v1/branches                    # Create branch
GET    /api/v1/branches                    # List organization branches
GET    /api/v1/branches/{branch_id}        # Get branch details
PATCH  /api/v1/branches/{branch_id}        # Update branch
DELETE /api/v1/branches/{branch_id}        # Delete/close branch

POST   /api/v1/branches/{branch_id}/activate      # Activate branch
POST   /api/v1/branches/{branch_id}/suspend       # Suspend branch

GET    /api/v1/branches/{branch_id}/users         # List branch users
POST   /api/v1/branches/{branch_id}/users         # Assign user to branch
DELETE /api/v1/branches/{branch_id}/users/{user_id}  # Remove user

GET    /api/v1/branches/{branch_id}/accounts      # List branch accounts
GET    /api/v1/branches/{branch_id}/customers     # List branch customers
GET    /api/v1/branches/{branch_id}/transactions  # List branch transactions

GET    /api/v1/branches/{branch_id}/metrics       # Branch performance metrics
GET    /api/v1/branches/{branch_id}/compliance    # Branch compliance summary
```

## Best Practices

### 1. Always Validate Branch Access

```python
# Bad: No branch check
async def get_account(account_id: str):
    return await repo.get_account(account_id)

# Good: Check user can access account's branch
async def get_account(
    account_id: str,
    current_user: User = Depends(get_current_user)
):
    account = await repo.get_account(account_id)
    if not await check_branch_access(current_user, account.branch_id):
        raise HTTPException(403, "Access denied")
    return account
```

### 2. Use Branch Codes in Human-Facing IDs

```python
# Account number format: {branch_code}-{sequence}
account_number = f"{branch.code}-{sequence:08d}"
# Example: BR-001-00012345

# Transaction reference: {branch_code}-{date}-{sequence}
ref = f"{branch.code}-{date.strftime('%Y%m%d')}-{seq:06d}"
# Example: BR-001-20251209-000123
```

### 3. Aggregate from Bottom-Up

```python
# Calculate metrics: Branch → Regional → Organization
branch_metrics = calculate_branch_metrics(branch_id)
regional_metrics = sum(branch_metrics for branches in region)
org_metrics = sum(regional_metrics for all regions)
```

### 4. Compliance Escalation Path

```
Branch Teller
    ↓ (if > $10K)
Branch Manager
    ↓ (if > $50K)
Regional Compliance Officer
    ↓ (if high risk)
Organization Compliance Officer
```

## Summary

Multi-branch support adds:
- ✅ Branch model with hierarchy
- ✅ Branch-specific compliance settings (stricter than org)
- ✅ User-branch assignments with access control
- ✅ Branch-level reporting and metrics
- ✅ Formance ledger integration with branch addressing
- ✅ Backward compatibility (branch_id nullable)

This architecture supports organizations from single-branch startups to multi-national banks with thousands of locations.
