"""
Unit tests for regulatory reporting functionality
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.exceptions import ValidationError
from core.models.compliance import (
    ComplianceCheck,
    ComplianceCheckType,
    ComplianceStatus,
    RiskLevel,
)
from core.models.regulatory import (
    CurrencyTransactionReport,
    RegulatoryReportingConfig,
    ReportPriority,
    ReportStatus,
    ReportType,
    SuspiciousActivityReport,
    SuspiciousActivityType,
)
from core.services.regulatory import RegulatoryReportingService


@pytest.fixture
def mock_repository():
    """Mock Formance repository"""
    repo = MagicMock()
    repo.get_organization = AsyncMock(
        return_value={
            "id": "org_test",
            "name": "Test Bank",
            "organization_type": "bank",
            "email": "test@bank.com",
            "phone": "+1234567890",
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "US",
            },
        }
    )
    repo.get_customer = AsyncMock(
        return_value={
            "id": "cust_test",
            "organization_id": "org_test",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "status": "active",
            "kyc_status": "verified",
        }
    )
    return repo


@pytest.fixture
def regulatory_service(mock_repository):
    """Create regulatory service with mock repository"""
    return RegulatoryReportingService(mock_repository)


@pytest.mark.asyncio
async def test_check_ctr_required_above_threshold(regulatory_service):
    """Test CTR requirement check for transaction above threshold"""
    result = await regulatory_service.check_ctr_required(
        organization_id="org_test",
        customer_id="cust_test",
        transaction_date=datetime.utcnow(),
        amount=Decimal("15000.00"),
        currency="USD",
    )

    assert result is True


@pytest.mark.asyncio
async def test_check_ctr_not_required_below_threshold(regulatory_service):
    """Test CTR requirement check for transaction below threshold"""
    result = await regulatory_service.check_ctr_required(
        organization_id="org_test",
        customer_id="cust_test",
        transaction_date=datetime.utcnow(),
        amount=Decimal("5000.00"),
        currency="USD",
    )

    assert result is False


@pytest.mark.asyncio
async def test_check_sar_required_high_risk(regulatory_service):
    """Test SAR requirement check for high-risk transaction"""
    compliance_check = ComplianceCheck(
        id="chk_test",
        organization_id="org_test",
        check_type=ComplianceCheckType.RISK_ASSESSMENT,
        status=ComplianceStatus.REVIEW,
        customer_id="cust_test",
        risk_score=85,
        risk_level=RiskLevel.HIGH,
    )

    result = await regulatory_service.check_sar_required(
        organization_id="org_test",
        compliance_check=compliance_check,
    )

    assert result is True


@pytest.mark.asyncio
async def test_check_sar_not_required_low_risk(regulatory_service):
    """Test SAR requirement check for low-risk transaction"""
    compliance_check = ComplianceCheck(
        id="chk_test",
        organization_id="org_test",
        check_type=ComplianceCheckType.RISK_ASSESSMENT,
        status=ComplianceStatus.APPROVED,
        customer_id="cust_test",
        risk_score=20,
        risk_level=RiskLevel.LOW,
    )

    result = await regulatory_service.check_sar_required(
        organization_id="org_test",
        compliance_check=compliance_check,
    )

    assert result is False


@pytest.mark.asyncio
async def test_generate_ctr_success(regulatory_service):
    """Test successful CTR generation"""
    ctr = await regulatory_service.generate_ctr(
        organization_id="org_test",
        customer_id="cust_test",
        transaction_ids=["txn_1", "txn_2"],
        prepared_by="user_compliance",
        branch_id="branch_main",
    )

    assert isinstance(ctr, CurrencyTransactionReport)
    assert ctr.report_type == ReportType.CTR
    assert ctr.status == ReportStatus.DRAFT
    assert ctr.organization_id == "org_test"
    assert ctr.prepared_by == "user_compliance"
    assert len(ctr.transactions) > 0


@pytest.mark.asyncio
async def test_generate_sar_success(regulatory_service):
    """Test successful SAR generation"""
    sar = await regulatory_service.generate_sar(
        organization_id="org_test",
        customer_id="cust_test",
        suspicious_activity_types=[SuspiciousActivityType.STRUCTURING],
        narrative_summary="Customer appears to be structuring transactions to avoid CTR reporting. "
        "Multiple deposits just under $10,000 over the past week.",
        transaction_ids=["txn_1", "txn_2", "txn_3"],
        prepared_by="user_compliance",
        activity_start_date=datetime.utcnow() - timedelta(days=7),
        priority=ReportPriority.HIGH,
    )

    assert isinstance(sar, SuspiciousActivityReport)
    assert sar.report_type == ReportType.SAR
    assert sar.status == ReportStatus.DRAFT
    assert sar.priority == ReportPriority.HIGH
    assert sar.organization_id == "org_test"
    assert len(sar.suspicious_activity_types) == 1
    assert len(sar.narrative_summary) >= 50


@pytest.mark.asyncio
async def test_generate_sar_narrative_too_short(regulatory_service):
    """Test SAR generation fails with short narrative"""
    with pytest.raises(ValidationError, match="at least 50 characters"):
        await regulatory_service.generate_sar(
            organization_id="org_test",
            customer_id="cust_test",
            suspicious_activity_types=[SuspiciousActivityType.FRAUD],
            narrative_summary="Too short",
            transaction_ids=["txn_1"],
            prepared_by="user_compliance",
            activity_start_date=datetime.utcnow(),
        )


@pytest.mark.asyncio
async def test_review_report_approve(regulatory_service):
    """Test report review and approval"""
    result = await regulatory_service.review_report(
        report_id="ctr_test123",
        report_type=ReportType.CTR,
        reviewed_by="user_manager",
        approved=True,
        notes="Looks good",
    )

    assert result is True


@pytest.mark.asyncio
async def test_review_report_reject(regulatory_service):
    """Test report review and rejection"""
    result = await regulatory_service.review_report(
        report_id="sar_test456",
        report_type=ReportType.SAR,
        reviewed_by="user_manager",
        approved=False,
        notes="Need more details in narrative",
    )

    assert result is True


@pytest.mark.asyncio
async def test_file_report(regulatory_service):
    """Test report filing"""
    bsa_id = await regulatory_service.file_report(
        report_id="ctr_test123",
        report_type=ReportType.CTR,
        filed_by="user_compliance",
    )

    assert bsa_id is not None
    assert bsa_id.startswith("BSA")


@pytest.mark.asyncio
async def test_list_reports(regulatory_service):
    """Test listing reports"""
    reports = await regulatory_service.list_reports(
        organization_id="org_test",
        limit=50,
        offset=0,
    )

    assert isinstance(reports, list)


@pytest.mark.asyncio
async def test_update_reporting_config(regulatory_service):
    """Test updating reporting configuration"""
    config = RegulatoryReportingConfig(
        organization_id="org_test",
        ctr_enabled=True,
        ctr_threshold=Decimal("15000.00"),
        sar_enabled=True,
        sar_risk_score_threshold=80,
    )

    updated = await regulatory_service.update_reporting_config(
        organization_id="org_test",
        config=config,
    )

    assert updated.organization_id == "org_test"
    assert updated.ctr_threshold == Decimal("15000.00")
    assert updated.sar_risk_score_threshold == 80


def test_reporting_config_defaults():
    """Test default reporting configuration"""
    config = RegulatoryReportingConfig(organization_id="org_test")

    assert config.ctr_enabled is True
    assert config.ctr_threshold == Decimal("10000.00")
    assert config.sar_enabled is True
    assert config.require_dual_approval is True
    assert config.report_retention_days == 1825  # 5 years


def test_ctr_model_validation():
    """Test CTR model validation"""
    from core.models.regulatory import FinancialInstitution, SubjectInformation, TransactionDetails

    filing_institution = FinancialInstitution(
        name="Test Bank",
        address_street="123 Main St",
        address_city="New York",
        address_postal_code="10001",
        address_country="US",
        phone="+1234567890",
    )

    person = SubjectInformation(
        entity_type="individual",
        first_name="John",
        last_name="Doe",
        relationship="customer",
    )

    txn = TransactionDetails(
        transaction_id="txn_test",
        transaction_date=datetime.utcnow(),
        transaction_type="deposit",
        amount=Decimal("15000.00"),
        currency="USD",
    )

    ctr = CurrencyTransactionReport(
        id="ctr_test",
        organization_id="org_test",
        filing_institution=filing_institution,
        transaction_date=datetime.utcnow(),
        person_on_behalf=person,
        transactions=[txn],
        total_amount=Decimal("15000.00"),
        total_cash_in=Decimal("15000.00"),
        currency="USD",
        transaction_type="deposit",
        branch_id="branch_main",
        branch_name="Main Branch",
        prepared_by="user_test",
    )

    assert ctr.id == "ctr_test"
    assert ctr.status == ReportStatus.DRAFT
    assert ctr.total_amount == Decimal("15000.00")


def test_sar_model_validation():
    """Test SAR model validation"""
    from core.models.regulatory import FinancialInstitution, SubjectInformation, TransactionDetails

    filing_institution = FinancialInstitution(
        name="Test Bank",
        address_street="123 Main St",
        address_city="New York",
        address_postal_code="10001",
        address_country="US",
        phone="+1234567890",
    )

    subject = SubjectInformation(
        entity_type="individual",
        first_name="Jane",
        last_name="Smith",
        relationship="customer",
    )

    txn = TransactionDetails(
        transaction_id="txn_test",
        transaction_date=datetime.utcnow(),
        transaction_type="transfer",
        amount=Decimal("9000.00"),
        currency="USD",
    )

    sar = SuspiciousActivityReport(
        id="sar_test",
        organization_id="org_test",
        filing_institution=filing_institution,
        activity_start_date=datetime.utcnow() - timedelta(days=7),
        activity_detected_date=datetime.utcnow(),
        subjects=[subject],
        suspicious_activity_types=[SuspiciousActivityType.STRUCTURING],
        transactions=[txn],
        total_amount=Decimal("9000.00"),
        narrative_summary="Suspicious pattern of transactions just below reporting threshold " * 3,
        prepared_by="user_test",
    )

    assert sar.id == "sar_test"
    assert sar.status == ReportStatus.DRAFT
    assert sar.priority == ReportPriority.NORMAL
    assert len(sar.subjects) == 1
    assert len(sar.suspicious_activity_types) == 1
