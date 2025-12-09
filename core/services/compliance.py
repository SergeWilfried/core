"""
Compliance Service for KYC/AML and transaction monitoring

Integrates with:
- Rule engine for configurable compliance checks
- Sanctions screening (OFAC, UN, EU)
- Velocity monitoring
- Risk scoring
- Formance ledger for audit trails
"""

import logging
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from ..models.compliance import (
    ComplianceCheck,
    ComplianceCheckType,
    ComplianceStatus,
    RiskLevel,
    RiskScore,
    SanctionMatch,
    SanctionListType,
    VelocityCheck,
    ComplianceAlert,
)
from ..models.rules import (
    ComplianceRule,
    RuleAction,
    RuleEvaluationResult,
    RuleSeverity,
    RuleType,
)
from ..models.customer import Customer, KYCStatus
from ..models.organization import Organization, OrganizationSettings
from ..models.payment import PaymentMethod, MobileMoneyProvider
from ..utils.sanctions import sanctions_screening, country_risk_assessment
from ..repositories.formance import FormanceRepository
from ..exceptions import (
    ComplianceError,
    KYCRequiredError,
    TransactionBlockedError,
)

logger = logging.getLogger(__name__)


class ComplianceService:
    """
    Compliance orchestration service

    Responsibilities:
    - Pre-transaction compliance checks
    - Rule engine evaluation
    - Sanctions screening
    - Velocity monitoring
    - Risk scoring
    - Audit trail management
    """

    def __init__(self, repository: FormanceRepository):
        """
        Initialize compliance service

        Args:
            repository: Formance repository for data access
        """
        self.repository = repository
        self.sanctions = sanctions_screening
        self.country_risk = country_risk_assessment

        # In-memory rule cache (in production, use Redis)
        self._rules_cache: dict[str, list[ComplianceRule]] = {}
        self._rules_cache_ttl = timedelta(minutes=15)
        self._rules_cache_timestamp: Optional[datetime] = None

    async def check_transaction(
        self,
        organization_id: str,
        customer_id: str,
        account_id: str,
        amount: Decimal,
        currency: str,
        transaction_type: str,
        payment_method: Optional[PaymentMethod] = None,
        destination_country: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> ComplianceCheck:
        """
        Comprehensive compliance check for transaction

        Args:
            organization_id: Organization ID
            customer_id: Customer ID
            account_id: Account ID
            amount: Transaction amount
            currency: Currency code
            transaction_type: Type of transaction
            payment_method: Payment method
            destination_country: Destination country code
            metadata: Additional metadata

        Returns:
            ComplianceCheck result

        Raises:
            TransactionBlockedError: If transaction is blocked
            KYCRequiredError: If KYC verification required
        """
        check_id = f"chk_{secrets.token_hex(12)}"
        logger.info(f"Starting compliance check {check_id} for customer {customer_id}")

        # Initialize check
        compliance_check = ComplianceCheck(
            id=check_id,
            organization_id=organization_id,
            check_type=ComplianceCheckType.RISK_ASSESSMENT,
            status=ComplianceStatus.PENDING,
            customer_id=customer_id,
            account_id=account_id,
            metadata=metadata or {},
        )

        try:
            # Get organization settings
            org_data = await self.repository.get_organization(organization_id)
            if not org_data:
                raise ComplianceError(f"Organization {organization_id} not found")

            org = Organization(**org_data)

            # Check if organization can operate
            if not org.can_operate():
                compliance_check.status = ComplianceStatus.BLOCKED
                compliance_check.reason = f"Organization not operational: {org.status.value}"
                logger.warning(f"Organization {organization_id} cannot operate")
                raise TransactionBlockedError(compliance_check.reason)

            # Get customer data
            customer_data = await self.repository.get_customer(customer_id)
            if not customer_data:
                raise ComplianceError(f"Customer {customer_id} not found")

            customer = Customer(**customer_data)

            # Build evaluation context
            context = {
                "organization_id": organization_id,
                "customer_id": customer_id,
                "account_id": account_id,
                "amount": float(amount),
                "currency": currency,
                "transaction_type": transaction_type,
                "payment_method": payment_method.value if payment_method else None,
                "destination_country": destination_country,
                "customer_status": customer.status.value,
                "kyc_status": customer.kyc_status.value,
                "organization_type": org.organization_type.value,
            }

            # 1. KYC/KYB Verification Check
            kyc_result = await self._check_kyc_verification(customer, org)
            compliance_check.rules_evaluated.append("kyc_verification")
            if kyc_result["blocked"]:
                compliance_check.status = ComplianceStatus.BLOCKED
                compliance_check.reason = kyc_result["reason"]
                compliance_check.risk_score = 80
                logger.warning(f"KYC check failed for customer {customer_id}")
                raise KYCRequiredError(kyc_result["reason"])

            # 2. Sanctions Screening
            sanctions_result = await self._check_sanctions(customer, org.settings)
            compliance_check.rules_evaluated.append("sanctions_screening")
            compliance_check.sanctions_matches = sanctions_result["matches"]
            if sanctions_result["blocked"]:
                compliance_check.status = ComplianceStatus.BLOCKED
                compliance_check.reason = "Sanctions screening failed"
                compliance_check.risk_score = 100
                logger.error(f"Sanctions match for customer {customer_id}")
                raise TransactionBlockedError("Transaction blocked due to sanctions screening")

            # 3. Organization Settings Check
            org_check = await self._check_organization_settings(
                org.settings, amount, currency, payment_method, destination_country
            )
            compliance_check.rules_evaluated.append("organization_settings")
            if org_check["blocked"]:
                compliance_check.status = ComplianceStatus.BLOCKED
                compliance_check.reason = org_check["reason"]
                compliance_check.risk_score = 60
                raise TransactionBlockedError(org_check["reason"])

            # 4. Velocity Check
            velocity_result = await self._check_velocity(
                organization_id, customer_id, account_id, amount, org.settings
            )
            compliance_check.rules_evaluated.append("velocity_check")
            if velocity_result["blocked"]:
                compliance_check.status = ComplianceStatus.BLOCKED
                compliance_check.reason = velocity_result["reason"]
                compliance_check.risk_score = 70
                raise TransactionBlockedError(velocity_result["reason"])

            # 5. Geographic Risk Check
            if destination_country:
                geo_result = await self._check_geographic_risk(
                    destination_country, org.settings
                )
                compliance_check.rules_evaluated.append("geographic_risk")
                if geo_result["blocked"]:
                    compliance_check.status = ComplianceStatus.BLOCKED
                    compliance_check.reason = geo_result["reason"]
                    compliance_check.risk_score = 85
                    raise TransactionBlockedError(geo_result["reason"])

            # 6. Evaluate Custom Rules
            rules_result = await self._evaluate_rules(organization_id, context)
            compliance_check.rules_evaluated.extend(
                [r.rule_id for r in rules_result]
            )
            compliance_check.rules_triggered = [
                r.rule_id for r in rules_result if r.triggered
            ]

            # Check for blocking rules
            for result in rules_result:
                if result.triggered and result.action == RuleAction.BLOCK:
                    compliance_check.status = ComplianceStatus.BLOCKED
                    compliance_check.reason = result.message or f"Rule {result.rule_name} triggered"
                    compliance_check.risk_score = min(compliance_check.risk_score + result.risk_score_impact, 100)
                    raise TransactionBlockedError(compliance_check.reason)

            # Check for review requirements
            for result in rules_result:
                if result.triggered and result.action == RuleAction.REVIEW:
                    compliance_check.requires_manual_review = True
                    compliance_check.status = ComplianceStatus.REVIEW
                    compliance_check.reason = result.message or f"Manual review required: {result.rule_name}"

            # 7. Calculate Risk Score
            risk_score_data = await self._calculate_risk_score(
                organization_id,
                customer_id,
                context,
                sanctions_result,
                velocity_result,
                destination_country,
            )
            compliance_check.risk_score = risk_score_data["overall_score"]
            compliance_check.risk_level = risk_score_data["risk_level"]
            compliance_check.details = risk_score_data

            # Final status determination
            if compliance_check.status == ComplianceStatus.PENDING:
                if compliance_check.risk_score >= 75:
                    compliance_check.status = ComplianceStatus.REVIEW
                    compliance_check.requires_manual_review = True
                    compliance_check.reason = "High risk score requires manual review"
                elif compliance_check.requires_manual_review:
                    compliance_check.status = ComplianceStatus.REVIEW
                else:
                    compliance_check.status = ComplianceStatus.APPROVED
                    compliance_check.reason = "All compliance checks passed"

            logger.info(
                f"Compliance check {check_id} completed: {compliance_check.status.value} "
                f"(risk score: {compliance_check.risk_score})"
            )

            # Store compliance check (in production, save to database)
            # await self.repository.create_compliance_check(compliance_check)

            return compliance_check

        except (TransactionBlockedError, KYCRequiredError) as e:
            # Store failed check
            # await self.repository.create_compliance_check(compliance_check)
            raise
        except Exception as e:
            logger.error(f"Compliance check {check_id} error: {e}")
            compliance_check.status = ComplianceStatus.BLOCKED
            compliance_check.reason = f"Compliance check error: {str(e)}"
            raise ComplianceError(f"Compliance check failed: {e}")

    async def _check_kyc_verification(
        self, customer: Customer, org: Organization
    ) -> dict:
        """Check KYC/KYB verification status"""
        # Check customer KYC
        if not customer.is_active():
            return {
                "blocked": True,
                "reason": f"Customer status: {customer.status.value}",
            }

        if not customer.is_kyc_verified():
            return {
                "blocked": True,
                "reason": f"KYC verification required (status: {customer.kyc_status.value})",
            }

        # Check organization KYB
        if not org.is_verified():
            return {
                "blocked": True,
                "reason": f"Organization verification required (KYB status: {org.kyb_status})",
            }

        return {"blocked": False, "reason": None}

    async def _check_sanctions(
        self, customer: Customer, org_settings: OrganizationSettings
    ) -> dict:
        """Screen customer against sanction lists"""
        # Skip if disabled in org settings
        if not org_settings.enable_sanctions_screening:
            return {"blocked": False, "matches": []}

        # Screen customer name
        full_name = f"{customer.first_name} {customer.last_name}"
        matches = self.sanctions.screen(
            full_name,
            list_types=[
                SanctionListType.OFAC,
                SanctionListType.UN,
                SanctionListType.EU,
            ],
            threshold=0.85,
        )

        # Block if high confidence match
        blocked = any(match["match_score"] >= 0.95 for match in matches)

        return {"blocked": blocked, "matches": matches}

    async def _check_organization_settings(
        self,
        settings: OrganizationSettings,
        amount: Decimal,
        currency: str,
        payment_method: Optional[PaymentMethod],
        destination_country: Optional[str],
    ) -> dict:
        """Check transaction against organization settings"""
        # Check currency allowed
        if currency not in settings.allowed_currencies:
            return {
                "blocked": True,
                "reason": f"Currency {currency} not allowed for organization",
            }

        # Check transaction amount limit
        if (
            settings.max_transaction_amount
            and amount > settings.max_transaction_amount
        ):
            return {
                "blocked": True,
                "reason": f"Amount exceeds organization limit of {settings.max_transaction_amount}",
            }

        # Check mobile money allowed
        if (
            payment_method == PaymentMethod.MOBILE_MONEY
            and not settings.allow_mobile_money
        ):
            return {
                "blocked": True,
                "reason": "Mobile money payments not enabled for organization",
            }

        # Check international payments
        if destination_country and not settings.allow_international:
            return {
                "blocked": True,
                "reason": "International payments not enabled for organization",
            }

        # Check restricted countries
        if (
            destination_country
            and destination_country in settings.restricted_countries
        ):
            return {
                "blocked": True,
                "reason": f"Transactions to {destination_country} are blocked",
            }

        return {"blocked": False, "reason": None}

    async def _check_velocity(
        self,
        organization_id: str,
        customer_id: str,
        account_id: str,
        amount: Decimal,
        org_settings: OrganizationSettings,
    ) -> dict:
        """Check transaction velocity limits"""
        if not org_settings.enable_velocity_monitoring:
            return {"blocked": False, "reason": None}

        # TODO: In production, query actual transaction history from database
        # For now, simulate velocity check

        # Check daily limit
        if (
            org_settings.max_daily_transaction_limit
            and amount > org_settings.max_daily_transaction_limit
        ):
            return {
                "blocked": True,
                "reason": f"Exceeds daily transaction limit of {org_settings.max_daily_transaction_limit}",
            }

        # In production:
        # - Query transactions for customer in last 24 hours
        # - Sum amounts and count transactions
        # - Check against velocity rules

        return {"blocked": False, "reason": None}

    async def _check_geographic_risk(
        self, country_code: str, org_settings: OrganizationSettings
    ) -> dict:
        """Check geographic risk"""
        # Check if country is sanctioned
        if self.sanctions.screen_country(country_code):
            return {
                "blocked": True,
                "reason": f"Country {country_code} is under sanctions",
            }

        # Check country risk score
        risk_score = self.country_risk.get_country_risk_score(country_code)
        if risk_score >= 75 and org_settings.compliance_level == "strict":
            return {
                "blocked": True,
                "reason": f"Country {country_code} has high risk score ({risk_score})",
            }

        return {"blocked": False, "reason": None, "risk_score": risk_score}

    async def _evaluate_rules(
        self, organization_id: str, context: dict
    ) -> list[RuleEvaluationResult]:
        """Evaluate compliance rules against context"""
        # Get rules for organization (with caching)
        rules = await self._get_rules(organization_id)

        results = []
        for rule in rules:
            if not rule.should_apply_to(context.get("customer_id")):
                continue

            triggered = rule.evaluate(context)
            result = RuleEvaluationResult(
                rule_id=rule.id,
                rule_name=rule.name,
                triggered=triggered,
                action=rule.action if triggered else None,
                severity=rule.severity if triggered else None,
                message=rule.message if triggered else None,
                risk_score_impact=rule.risk_score_impact if triggered else 0,
                context=context,
            )
            results.append(result)

            if triggered:
                logger.info(
                    f"Rule {rule.name} triggered for customer {context.get('customer_id')}"
                )

        return results

    async def _get_rules(self, organization_id: str) -> list[ComplianceRule]:
        """Get rules for organization with caching"""
        # Check cache
        if self._rules_cache_timestamp:
            age = datetime.utcnow() - self._rules_cache_timestamp
            if age < self._rules_cache_ttl and organization_id in self._rules_cache:
                return self._rules_cache[organization_id]

        # TODO: Load from database in production
        # For now, return empty list
        rules = []

        # Cache rules
        self._rules_cache[organization_id] = rules
        self._rules_cache_timestamp = datetime.utcnow()

        return rules

    async def _calculate_risk_score(
        self,
        organization_id: str,
        customer_id: str,
        context: dict,
        sanctions_result: dict,
        velocity_result: dict,
        destination_country: Optional[str],
    ) -> dict:
        """Calculate comprehensive risk score"""
        # Component scores (0-100)
        kyc_score = 0 if context.get("kyc_status") == "verified" else 30

        sanctions_score = 0
        if sanctions_result["matches"]:
            max_match_score = max(m["match_score"] for m in sanctions_result["matches"])
            sanctions_score = int(max_match_score * 100)

        transaction_score = 0
        amount = context.get("amount", 0)
        if amount > 10000:
            transaction_score = min(int((amount / 10000) * 20), 40)

        geographic_score = 0
        if destination_country:
            geographic_score = self.country_risk.get_country_risk_score(
                destination_country
            )

        velocity_score = 20 if velocity_result.get("blocked") else 0

        # Calculate overall score (weighted average)
        overall_score = int(
            (kyc_score * 0.25)
            + (sanctions_score * 0.30)
            + (transaction_score * 0.20)
            + (geographic_score * 0.15)
            + (velocity_score * 0.10)
        )

        risk_level = RiskScore.calculate_risk_level(overall_score)

        return {
            "overall_score": overall_score,
            "risk_level": risk_level,
            "kyc_score": kyc_score,
            "sanctions_score": sanctions_score,
            "transaction_score": transaction_score,
            "geographic_score": geographic_score,
            "velocity_score": velocity_score,
            "risk_factors": self._identify_risk_factors(context, overall_score),
        }

    def _identify_risk_factors(self, context: dict, overall_score: int) -> list[str]:
        """Identify risk factors"""
        factors = []

        if context.get("kyc_status") != "verified":
            factors.append("unverified_kyc")

        if context.get("amount", 0) > 10000:
            factors.append("high_value_transaction")

        if overall_score >= 50:
            factors.append("elevated_risk_score")

        return factors

    async def create_rule(
        self, organization_id: str, rule: ComplianceRule
    ) -> ComplianceRule:
        """
        Create new compliance rule

        Args:
            organization_id: Organization ID
            rule: Rule to create

        Returns:
            Created rule
        """
        # TODO: Store in database
        logger.info(f"Created compliance rule {rule.id} for org {organization_id}")

        # Invalidate cache
        self._rules_cache_timestamp = None

        return rule

    async def get_compliance_check(self, check_id: str) -> Optional[ComplianceCheck]:
        """Get compliance check by ID"""
        # TODO: Retrieve from database
        return None

    async def approve_manual_review(
        self, check_id: str, reviewed_by: str, notes: Optional[str] = None
    ) -> ComplianceCheck:
        """Approve a compliance check requiring manual review"""
        # TODO: Update in database
        logger.info(f"Compliance check {check_id} approved by {reviewed_by}")
        raise NotImplementedError("Manual review approval not yet implemented")

    async def reject_manual_review(
        self, check_id: str, reviewed_by: str, reason: str
    ) -> ComplianceCheck:
        """Reject a compliance check"""
        # TODO: Update in database
        logger.info(f"Compliance check {check_id} rejected by {reviewed_by}")
        raise NotImplementedError("Manual review rejection not yet implemented")
