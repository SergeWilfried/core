"""
Compliance API endpoints for KYC/AML and transaction monitoring
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ...exceptions import ComplianceError, KYCRequiredError, TransactionBlockedError
from ...models.compliance import (
    ComplianceCheck,
    ComplianceStatus,
    RiskLevel,
)
from ...models.payment import PaymentMethod
from ...models.rules import (
    ComplianceRule,
    RuleAction,
    RuleCondition,
    RuleSeverity,
    RuleType,
)
from ...repositories.formance import FormanceRepository
from ...services.compliance import ComplianceService
from ..dependencies import get_formance_client

router = APIRouter(prefix="/compliance", tags=["compliance"])


# Request/Response Models
class ComplianceCheckRequest(BaseModel):
    """Request to run compliance check"""

    organization_id: str = Field(..., description="Organization ID")
    customer_id: str = Field(..., description="Customer ID")
    account_id: str = Field(..., description="Account ID")
    amount: Decimal = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(..., min_length=3, max_length=3, description="Currency code")
    transaction_type: str = Field(..., description="Transaction type")
    payment_method: PaymentMethod | None = Field(None, description="Payment method")
    destination_country: str | None = Field(None, description="Destination country code")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class ComplianceCheckResponse(BaseModel):
    """Compliance check response"""

    compliance_check: ComplianceCheck
    approved: bool = Field(..., description="Whether transaction is approved")
    requires_review: bool = Field(..., description="Whether manual review is required")
    blocked: bool = Field(..., description="Whether transaction is blocked")
    message: str = Field(..., description="Result message")


class ManualReviewRequest(BaseModel):
    """Manual review action request"""

    reviewed_by: str = Field(..., description="User ID performing review")
    notes: str | None = Field(None, description="Review notes")


class RejectRequest(BaseModel):
    """Rejection request"""

    reviewed_by: str = Field(..., description="User ID performing rejection")
    reason: str = Field(..., description="Rejection reason")


class CreateRuleRequest(BaseModel):
    """Create compliance rule request"""

    organization_id: str | None = Field(None, description="Organization ID (None for global)")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    rule_type: RuleType = Field(..., description="Rule type")
    conditions: list[RuleCondition] = Field(default_factory=list, description="Rule conditions")
    conditions_logic: str = Field(default="AND", description="AND or OR")
    action: RuleAction = Field(..., description="Action when triggered")
    severity: RuleSeverity = Field(..., description="Severity level")
    risk_score_impact: int = Field(default=0, ge=0, le=100, description="Risk score impact")
    message: str | None = Field(None, description="Message when triggered")
    enabled: bool = Field(default=True, description="Whether rule is active")
    priority: int = Field(default=100, ge=1, le=1000, description="Evaluation priority")


# Dependency to get compliance service
async def get_compliance_service(
    client=Depends(get_formance_client),
) -> ComplianceService:
    """Get compliance service instance"""
    repository = FormanceRepository(client)
    return ComplianceService(repository)


@router.post("/check", response_model=ComplianceCheckResponse)
async def run_compliance_check(
    request: ComplianceCheckRequest,
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """
    Run compliance check for transaction

    Performs comprehensive compliance checks including:
    - KYC/KYB verification
    - Sanctions screening (OFAC, UN, EU)
    - Organization settings validation
    - Velocity/pattern monitoring
    - Geographic risk assessment
    - Custom rules evaluation
    - Risk score calculation

    Returns:
        ComplianceCheckResponse with approval status and details
    """
    try:
        compliance_check = await compliance_service.check_transaction(
            organization_id=request.organization_id,
            customer_id=request.customer_id,
            account_id=request.account_id,
            amount=request.amount,
            currency=request.currency,
            transaction_type=request.transaction_type,
            payment_method=request.payment_method,
            destination_country=request.destination_country,
            metadata=request.metadata,
        )

        return ComplianceCheckResponse(
            compliance_check=compliance_check,
            approved=compliance_check.is_approved(),
            requires_review=compliance_check.needs_review(),
            blocked=compliance_check.is_blocked(),
            message=compliance_check.reason or "Compliance check completed",
        )

    except TransactionBlockedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "transaction_blocked", "message": str(e)},
        )
    except KYCRequiredError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "kyc_required", "message": str(e)},
        )
    except ComplianceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "compliance_error", "message": str(e)},
        )


@router.get("/checks/{check_id}", response_model=ComplianceCheck)
async def get_compliance_check(
    check_id: str,
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """
    Get compliance check by ID

    Args:
        check_id: Compliance check identifier

    Returns:
        ComplianceCheck details
    """
    compliance_check = await compliance_service.get_compliance_check(check_id)
    if not compliance_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance check {check_id} not found",
        )
    return compliance_check


@router.get("/checks", response_model=list[ComplianceCheck])
async def list_compliance_checks(
    organization_id: str | None = Query(None, description="Filter by organization"),
    customer_id: str | None = Query(None, description="Filter by customer"),
    status_filter: ComplianceStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    risk_level: RiskLevel | None = Query(None, description="Filter by risk level"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """
    List compliance checks with filtering

    Args:
        organization_id: Filter by organization
        customer_id: Filter by customer
        status_filter: Filter by compliance status
        risk_level: Filter by risk level
        limit: Results limit
        offset: Pagination offset

    Returns:
        List of ComplianceCheck objects
    """
    # TODO: Implement in compliance service
    # For now, return empty list
    return []


@router.post("/checks/{check_id}/approve", response_model=ComplianceCheck)
async def approve_compliance_check(
    check_id: str,
    request: ManualReviewRequest,
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """
    Approve a compliance check requiring manual review

    Requires `COMPLIANCE_APPROVE` permission.

    Args:
        check_id: Compliance check identifier
        request: Manual review details

    Returns:
        Updated ComplianceCheck
    """
    try:
        return await compliance_service.approve_manual_review(
            check_id=check_id,
            reviewed_by=request.reviewed_by,
            notes=request.notes,
        )
    except ComplianceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/checks/{check_id}/reject", response_model=ComplianceCheck)
async def reject_compliance_check(
    check_id: str,
    request: RejectRequest,
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """
    Reject a compliance check

    Requires `COMPLIANCE_REJECT` permission.

    Args:
        check_id: Compliance check identifier
        request: Rejection details

    Returns:
        Updated ComplianceCheck
    """
    try:
        return await compliance_service.reject_manual_review(
            check_id=check_id,
            reviewed_by=request.reviewed_by,
            reason=request.reason,
        )
    except ComplianceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/rules", response_model=ComplianceRule, status_code=status.HTTP_201_CREATED)
async def create_compliance_rule(
    request: CreateRuleRequest,
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """
    Create new compliance rule

    Requires `COMPLIANCE_RULES_MANAGE` permission.

    Args:
        request: Rule creation request

    Returns:
        Created ComplianceRule
    """
    import secrets
    from datetime import datetime

    rule = ComplianceRule(
        id=f"rule_{secrets.token_hex(12)}",
        organization_id=request.organization_id,
        name=request.name,
        description=request.description,
        rule_type=request.rule_type,
        conditions=request.conditions,
        conditions_logic=request.conditions_logic,
        action=request.action,
        severity=request.severity,
        risk_score_impact=request.risk_score_impact,
        message=request.message,
        enabled=request.enabled,
        priority=request.priority,
        created_at=datetime.utcnow(),
    )

    await compliance_service.create_rule(
        organization_id=request.organization_id or "global",
        rule=rule,
    )

    return rule


@router.get("/rules", response_model=list[ComplianceRule])
async def list_compliance_rules(
    organization_id: str | None = Query(None, description="Filter by organization"),
    rule_type: RuleType | None = Query(None, description="Filter by rule type"),
    enabled: bool | None = Query(None, description="Filter by enabled status"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """
    List compliance rules

    Requires `COMPLIANCE_VIEW` permission.

    Args:
        organization_id: Filter by organization
        rule_type: Filter by rule type
        enabled: Filter by enabled status
        limit: Results limit
        offset: Pagination offset

    Returns:
        List of ComplianceRule objects
    """
    # TODO: Implement in compliance service
    return []


@router.get("/rules/{rule_id}", response_model=ComplianceRule)
async def get_compliance_rule(
    rule_id: str,
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """
    Get compliance rule by ID

    Args:
        rule_id: Rule identifier

    Returns:
        ComplianceRule details
    """
    # TODO: Implement in compliance service
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Rule {rule_id} not found",
    )


@router.patch("/rules/{rule_id}", response_model=ComplianceRule)
async def update_compliance_rule(
    rule_id: str,
    updates: dict,
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """
    Update compliance rule

    Requires `COMPLIANCE_RULES_MANAGE` permission.

    Args:
        rule_id: Rule identifier
        updates: Fields to update

    Returns:
        Updated ComplianceRule
    """
    # TODO: Implement in compliance service
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Rule {rule_id} not found",
    )


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_compliance_rule(
    rule_id: str,
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """
    Delete compliance rule

    Requires `COMPLIANCE_RULES_MANAGE` permission.

    Args:
        rule_id: Rule identifier
    """
    # TODO: Implement in compliance service
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Rule {rule_id} not found",
    )


@router.get("/reports/summary")
async def get_compliance_summary(
    organization_id: str = Query(..., description="Organization ID"),
    start_date: str | None = Query(None, description="Start date (ISO 8601)"),
    end_date: str | None = Query(None, description="End date (ISO 8601)"),
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """
    Get compliance summary report

    Requires `COMPLIANCE_REPORTS` permission.

    Args:
        organization_id: Organization ID
        start_date: Report period start
        end_date: Report period end

    Returns:
        Compliance summary with statistics
    """
    # TODO: Implement reporting functionality
    return {
        "organization_id": organization_id,
        "period": {"start": start_date, "end": end_date},
        "total_checks": 0,
        "approved": 0,
        "blocked": 0,
        "reviews": 0,
        "average_risk_score": 0,
        "sanctions_matches": 0,
        "high_risk_transactions": 0,
    }


@router.get("/sanctions/screen")
async def screen_sanctions(
    name: str = Query(..., min_length=2, description="Name to screen"),
    threshold: float = Query(0.8, ge=0, le=1, description="Match threshold"),
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """
    Screen name against sanctions lists

    Screens against OFAC, UN, and EU sanctions lists.

    Args:
        name: Name to screen
        threshold: Match confidence threshold (0-1)

    Returns:
        List of potential matches
    """
    matches = compliance_service.sanctions.screen(name, threshold=threshold)
    return {
        "query": name,
        "threshold": threshold,
        "matches_found": len(matches),
        "matches": matches,
    }


@router.get("/country-risk/{country_code}")
async def get_country_risk(
    country_code: str,
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """
    Get risk assessment for country

    Args:
        country_code: ISO 3166-1 alpha-2 country code

    Returns:
        Country risk information
    """
    risk_score = compliance_service.country_risk.get_country_risk_score(country_code)
    is_high_risk = compliance_service.country_risk.is_high_risk_country(country_code)
    is_sanctioned = compliance_service.sanctions.screen_country(country_code)

    return {
        "country_code": country_code,
        "risk_score": risk_score,
        "is_high_risk": is_high_risk,
        "is_sanctioned": is_sanctioned,
        "risk_level": (
            "critical"
            if risk_score >= 75
            else "high"
            if risk_score >= 50
            else "medium"
            if risk_score >= 25
            else "low"
        ),
    }
