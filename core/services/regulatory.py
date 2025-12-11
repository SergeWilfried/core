"""
Regulatory Reporting Service for SAR, CTR, and other regulatory filings

This service handles:
- Automatic detection of reportable activities
- Report generation (SAR, CTR)
- Report lifecycle management (draft, review, approve, file)
- Integration with compliance system
- FinCEN BSA E-Filing integration (optional)
"""

import logging
import secrets
from datetime import datetime, timedelta
from decimal import Decimal

from ..exceptions import (
    RegulatoryReportError,
    ValidationError,
)
from ..models.compliance import (
    ComplianceAlert,
    ComplianceCheck,
    RiskLevel,
)
from ..models.customer import Customer
from ..models.organization import Organization
from ..models.regulatory import (
    CurrencyTransactionReport,
    FinancialInstitution,
    RegulatoryReportingConfig,
    RegulatoryReportSummary,
    ReportPriority,
    ReportStatus,
    ReportType,
    SubjectInformation,
    SuspiciousActivityReport,
    SuspiciousActivityType,
    TransactionDetails,
)
from ..repositories.formance import FormanceRepository

logger = logging.getLogger(__name__)


class RegulatoryReportingService:
    """
    Service for automated regulatory reporting (SAR, CTR)

    Responsibilities:
    - Detect reportable activities
    - Generate regulatory reports
    - Manage report lifecycle
    - Submit reports to regulators
    """

    def __init__(self, repository: FormanceRepository):
        """
        Initialize regulatory reporting service

        Args:
            repository: Formance repository for data access
        """
        self.repository = repository

    async def check_ctr_required(
        self,
        organization_id: str,
        customer_id: str,
        transaction_date: datetime,
        amount: Decimal,
        currency: str = "USD",
    ) -> bool:
        """
        Check if Currency Transaction Report (CTR) is required

        CTR required for currency transactions >= $10,000 in single day

        Args:
            organization_id: Organization ID
            customer_id: Customer ID
            transaction_date: Transaction date
            amount: Transaction amount
            currency: Currency code

        Returns:
            True if CTR required
        """
        # Get organization's reporting config
        config = await self._get_reporting_config(organization_id)

        if not config.ctr_enabled:
            return False

        # Check if transaction meets threshold
        if amount >= config.ctr_threshold:
            logger.info(
                f"CTR required: Single transaction {amount} {currency} "
                f"exceeds threshold {config.ctr_threshold}"
            )
            return True

        # Check aggregated transactions for the day
        day_start = transaction_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_start + timedelta(days=1)

        # TODO: Query actual transactions from database
        # For now, assume single transaction
        aggregated_amount = amount

        if aggregated_amount >= config.ctr_threshold:
            logger.info(
                f"CTR required: Aggregated transactions {aggregated_amount} {currency} "
                f"exceed threshold {config.ctr_threshold}"
            )
            return True

        return False

    async def check_sar_required(
        self,
        organization_id: str,
        compliance_check: ComplianceCheck,
        alert: ComplianceAlert | None = None,
    ) -> bool:
        """
        Check if Suspicious Activity Report (SAR) is required

        SAR may be required based on:
        - High risk score
        - Specific alert types
        - Manual compliance review flagging
        - Pattern detection

        Args:
            organization_id: Organization ID
            compliance_check: Compliance check result
            alert: Optional compliance alert

        Returns:
            True if SAR may be required
        """
        config = await self._get_reporting_config(organization_id)

        if not config.sar_enabled:
            return False

        # Check risk score threshold
        if compliance_check.risk_score >= config.sar_risk_score_threshold:
            logger.warning(
                f"SAR potentially required: Risk score {compliance_check.risk_score} "
                f"exceeds threshold {config.sar_risk_score_threshold}"
            )
            return True

        # Check if sanctioned
        if compliance_check.sanctions_matches:
            logger.warning("SAR potentially required: Sanctions match detected")
            return True

        # Check if alert indicates suspicious activity
        if alert and alert.severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            logger.warning(f"SAR potentially required: High severity alert {alert.alert_type}")
            return True

        # Check if manual review flagged for SAR
        if compliance_check.metadata.get("flag_for_sar"):
            logger.warning("SAR required: Flagged by manual review")
            return True

        return False

    async def generate_ctr(
        self,
        organization_id: str,
        customer_id: str,
        transaction_ids: list[str],
        prepared_by: str,
        branch_id: str | None = None,
    ) -> CurrencyTransactionReport:
        """
        Generate Currency Transaction Report (CTR)

        Args:
            organization_id: Organization ID
            customer_id: Customer ID
            transaction_ids: Transaction IDs to include
            prepared_by: User ID preparing the report
            branch_id: Optional branch ID

        Returns:
            CurrencyTransactionReport

        Raises:
            RegulatoryReportError: If report generation fails
        """
        report_id = f"ctr_{secrets.token_hex(12)}"
        logger.info(f"Generating CTR {report_id} for customer {customer_id}")

        try:
            # Get organization
            org_data = await self.repository.get_organization(organization_id)
            if not org_data:
                raise RegulatoryReportError(f"Organization {organization_id} not found")
            org = Organization(**org_data)

            # Get customer
            customer_data = await self.repository.get_customer(customer_id)
            if not customer_data:
                raise RegulatoryReportError(f"Customer {customer_id} not found")
            customer = Customer(**customer_data)

            # Get transactions
            # TODO: Fetch actual transactions from database
            transactions: list[TransactionDetails] = []
            total_cash_in = Decimal("0")
            total_cash_out = Decimal("0")
            transaction_date = datetime.utcnow()

            for txn_id in transaction_ids:
                # Mock transaction - replace with actual fetch
                txn_detail = TransactionDetails(
                    transaction_id=txn_id,
                    transaction_date=transaction_date,
                    transaction_type="cash_deposit",
                    amount=Decimal("15000.00"),
                    currency="USD",
                    payment_instrument="cash",
                    branch_id=branch_id,
                )
                transactions.append(txn_detail)

                if txn_detail.transaction_type in ["deposit", "cash_deposit"]:
                    total_cash_in += txn_detail.amount
                else:
                    total_cash_out += txn_detail.amount

            total_amount = total_cash_in + total_cash_out

            # Build filing institution info
            filing_institution = self._build_filing_institution(org)

            # Build subject information
            person_on_behalf = self._build_subject_info(customer)

            # Create CTR
            ctr = CurrencyTransactionReport(
                id=report_id,
                organization_id=organization_id,
                report_type=ReportType.CTR,
                status=ReportStatus.DRAFT,
                filing_institution=filing_institution,
                transaction_date=transaction_date,
                person_on_behalf=person_on_behalf,
                transactions=transactions,
                total_cash_in=total_cash_in,
                total_cash_out=total_cash_out,
                total_amount=total_amount,
                currency="USD",
                transaction_type="deposit",
                multiple_transactions=len(transaction_ids) > 1,
                branch_id=branch_id or "default",
                branch_name="Main Branch",
                identification_verified=customer.is_kyc_verified(),
                verification_method="kyc_process",
                prepared_by=prepared_by,
                created_at=datetime.utcnow(),
            )

            # Store CTR (TODO: Implement storage)
            logger.info(f"CTR {report_id} generated successfully")

            return ctr

        except Exception as e:
            logger.error(f"Failed to generate CTR {report_id}: {e}")
            raise RegulatoryReportError(f"CTR generation failed: {e}")

    async def generate_sar(
        self,
        organization_id: str,
        customer_id: str,
        suspicious_activity_types: list[SuspiciousActivityType],
        narrative_summary: str,
        transaction_ids: list[str],
        prepared_by: str,
        activity_start_date: datetime,
        activity_end_date: datetime | None = None,
        compliance_check_ids: list[str] | None = None,
        alert_ids: list[str] | None = None,
        priority: ReportPriority = ReportPriority.NORMAL,
    ) -> SuspiciousActivityReport:
        """
        Generate Suspicious Activity Report (SAR)

        Args:
            organization_id: Organization ID
            customer_id: Customer ID
            suspicious_activity_types: Types of suspicious activity
            narrative_summary: Detailed narrative (minimum 50 characters)
            transaction_ids: Transaction IDs involved
            prepared_by: User ID preparing the report
            activity_start_date: When suspicious activity started
            activity_end_date: When suspicious activity ended (optional)
            compliance_check_ids: Related compliance check IDs
            alert_ids: Related alert IDs
            priority: Report priority

        Returns:
            SuspiciousActivityReport

        Raises:
            RegulatoryReportError: If report generation fails
            ValidationError: If narrative too short
        """
        report_id = f"sar_{secrets.token_hex(12)}"
        logger.info(f"Generating SAR {report_id} for customer {customer_id}")

        # Validate narrative length
        if len(narrative_summary) < 50:
            raise ValidationError("SAR narrative must be at least 50 characters")

        try:
            # Get organization
            org_data = await self.repository.get_organization(organization_id)
            if not org_data:
                raise RegulatoryReportError(f"Organization {organization_id} not found")
            org = Organization(**org_data)

            # Get customer
            customer_data = await self.repository.get_customer(customer_id)
            if not customer_data:
                raise RegulatoryReportError(f"Customer {customer_id} not found")
            customer = Customer(**customer_data)

            # Get transactions
            # TODO: Fetch actual transactions from database
            transactions: list[TransactionDetails] = []
            total_amount = Decimal("0")

            for txn_id in transaction_ids:
                # Mock transaction - replace with actual fetch
                txn_detail = TransactionDetails(
                    transaction_id=txn_id,
                    transaction_date=activity_start_date,
                    transaction_type="suspicious_transfer",
                    amount=Decimal("5000.00"),
                    currency="USD",
                )
                transactions.append(txn_detail)
                total_amount += txn_detail.amount

            # Build filing institution info
            filing_institution = self._build_filing_institution(org)

            # Build subject information
            subjects = [self._build_subject_info(customer)]

            # Create SAR
            sar = SuspiciousActivityReport(
                id=report_id,
                organization_id=organization_id,
                report_type=ReportType.SAR,
                status=ReportStatus.DRAFT,
                priority=priority,
                filing_institution=filing_institution,
                activity_start_date=activity_start_date,
                activity_end_date=activity_end_date,
                activity_detected_date=datetime.utcnow(),
                subjects=subjects,
                suspicious_activity_types=suspicious_activity_types,
                transactions=transactions,
                total_amount=total_amount,
                total_currency="USD",
                narrative_summary=narrative_summary,
                compliance_check_ids=compliance_check_ids or [],
                alert_ids=alert_ids or [],
                prepared_by=prepared_by,
                created_at=datetime.utcnow(),
            )

            # Store SAR (TODO: Implement storage)
            logger.info(f"SAR {report_id} generated successfully")

            return sar

        except Exception as e:
            logger.error(f"Failed to generate SAR {report_id}: {e}")
            raise RegulatoryReportError(f"SAR generation failed: {e}")

    async def review_report(
        self,
        report_id: str,
        report_type: ReportType,
        reviewed_by: str,
        approved: bool,
        notes: str | None = None,
    ) -> bool:
        """
        Review a regulatory report

        Args:
            report_id: Report ID
            report_type: Type of report
            reviewed_by: User ID reviewing
            approved: Whether approved
            notes: Review notes

        Returns:
            True if status updated successfully

        Raises:
            RegulatoryReportError: If review fails
        """
        logger.info(f"Reviewing {report_type.value} {report_id} by {reviewed_by}")

        try:
            # TODO: Fetch report from database
            # Update status based on approval

            # TODO: Update report in database
            logger.info(
                f"{report_type.value} {report_id} "
                f"{'approved' if approved else 'rejected'} by {reviewed_by}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to review {report_type.value} {report_id}: {e}")
            raise RegulatoryReportError(f"Report review failed: {e}")

    async def file_report(
        self,
        report_id: str,
        report_type: ReportType,
        filed_by: str,
    ) -> str:
        """
        File a regulatory report with authorities

        Args:
            report_id: Report ID
            report_type: Type of report
            filed_by: User ID filing the report

        Returns:
            BSA identifier or filing confirmation

        Raises:
            RegulatoryReportError: If filing fails
        """
        logger.info(f"Filing {report_type.value} {report_id} by {filed_by}")

        try:
            # TODO: Fetch report from database

            # Check if report is approved
            # if report.status != ReportStatus.APPROVED:
            #     raise RegulatoryReportError("Only approved reports can be filed")

            # TODO: Integrate with FinCEN BSA E-Filing System
            # For now, generate mock BSA identifier
            bsa_identifier = f"BSA{secrets.token_hex(8).upper()}"

            # Update report status
            # report.status = ReportStatus.FILED
            # report.filed_by = filed_by
            # report.filed_at = datetime.utcnow()
            # report.bsa_identifier = bsa_identifier

            # TODO: Save updated report

            logger.info(
                f"{report_type.value} {report_id} filed successfully "
                f"with BSA identifier {bsa_identifier}"
            )

            return bsa_identifier

        except Exception as e:
            logger.error(f"Failed to file {report_type.value} {report_id}: {e}")
            raise RegulatoryReportError(f"Report filing failed: {e}")

    async def list_reports(
        self,
        organization_id: str,
        report_type: ReportType | None = None,
        status: ReportStatus | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RegulatoryReportSummary]:
        """
        List regulatory reports

        Args:
            organization_id: Organization ID
            report_type: Optional filter by report type
            status: Optional filter by status
            start_date: Optional filter by start date
            end_date: Optional filter by end date
            limit: Maximum results
            offset: Results offset

        Returns:
            List of report summaries
        """
        # TODO: Query reports from database with filters
        logger.info(
            f"Listing reports for org {organization_id} (type={report_type}, status={status})"
        )

        # Mock response
        return []

    async def get_report(
        self,
        report_id: str,
        report_type: ReportType,
    ) -> SuspiciousActivityReport | CurrencyTransactionReport | None:
        """
        Get regulatory report by ID

        Args:
            report_id: Report ID
            report_type: Report type

        Returns:
            Report or None if not found
        """
        # TODO: Fetch from database
        logger.info(f"Fetching {report_type.value} {report_id}")
        return None

    async def update_reporting_config(
        self,
        organization_id: str,
        config: RegulatoryReportingConfig,
    ) -> RegulatoryReportingConfig:
        """
        Update regulatory reporting configuration

        Args:
            organization_id: Organization ID
            config: New configuration

        Returns:
            Updated configuration
        """
        # TODO: Store in database
        logger.info(f"Updated reporting config for org {organization_id}")
        return config

    async def _get_reporting_config(self, organization_id: str) -> RegulatoryReportingConfig:
        """Get reporting configuration for organization"""
        # TODO: Fetch from database
        # For now, return default config
        return RegulatoryReportingConfig(
            organization_id=organization_id,
            ctr_enabled=True,
            ctr_threshold=Decimal("10000.00"),
            ctr_auto_generate=True,
            sar_enabled=True,
            sar_auto_generate=False,
            sar_risk_score_threshold=75,
        )

    def _build_filing_institution(self, org: Organization) -> FinancialInstitution:
        """Build filing institution information from organization"""
        return FinancialInstitution(
            name=org.name,
            ein=org.tax_id,
            address_street=org.address.street if org.address else "Unknown",
            address_city=org.address.city if org.address else "Unknown",
            address_state=org.address.state if org.address else None,
            address_postal_code=org.address.postal_code if org.address else "00000",
            address_country=org.address.country if org.address else "US",
            phone=org.phone or "+10000000000",
            email=org.email,
            type_of_filing_institution=org.organization_type.value,
        )

    def _build_subject_info(self, customer: Customer) -> SubjectInformation:
        """Build subject information from customer"""
        return SubjectInformation(
            entity_type="individual",
            first_name=customer.first_name,
            last_name=customer.last_name,
            email=customer.email,
            phone=customer.phone,
            address_street=customer.address.street if customer.address else None,
            address_city=customer.address.city if customer.address else None,
            address_state=customer.address.state if customer.address else None,
            address_postal_code=customer.address.postal_code if customer.address else None,
            address_country=customer.address.country if customer.address else None,
            relationship="customer",
            is_politically_exposed=customer.is_pep if hasattr(customer, "is_pep") else False,
        )
