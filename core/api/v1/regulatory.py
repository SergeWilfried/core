"""
Regulatory Reporting API endpoints

Provides endpoints for:
- SAR (Suspicious Activity Report) management
- CTR (Currency Transaction Report) management
- Report lifecycle (review, approve, file)
- Report listing and retrieval
"""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ...exceptions import RegulatoryReportError, ValidationError
from ...models.regulatory import (
    CurrencyTransactionReport,
    RegulatoryReportingConfig,
    RegulatoryReportSummary,
    ReportPriority,
    ReportStatus,
    ReportType,
    SuspiciousActivityReport,
    SuspiciousActivityType,
)
from ...repositories.formance import FormanceRepository
from ...services.regulatory import RegulatoryReportingService
from ..dependencies import get_formance_repository

router = APIRouter(prefix="/regulatory", tags=["regulatory"])


# Request/Response models
class GenerateCTRRequest(BaseModel):
    """Request to generate CTR"""

    customer_id: str = Field(..., description="Customer ID")
    transaction_ids: list[str] = Field(..., description="Transaction IDs")
    branch_id: str | None = Field(None, description="Branch ID")


class GenerateSARRequest(BaseModel):
    """Request to generate SAR"""

    customer_id: str = Field(..., description="Customer ID")
    suspicious_activity_types: list[SuspiciousActivityType] = Field(
        ..., description="Types of suspicious activity"
    )
    narrative_summary: str = Field(
        ..., min_length=50, description="Detailed narrative (minimum 50 characters)"
    )
    transaction_ids: list[str] = Field(..., description="Transaction IDs involved")
    activity_start_date: datetime = Field(..., description="Activity start date")
    activity_end_date: datetime | None = Field(None, description="Activity end date")
    compliance_check_ids: list[str] | None = Field(None, description="Related compliance check IDs")
    alert_ids: list[str] | None = Field(None, description="Related alert IDs")
    priority: ReportPriority = Field(default=ReportPriority.NORMAL, description="Report priority")


class ReviewReportRequest(BaseModel):
    """Request to review a report"""

    approved: bool = Field(..., description="Whether to approve the report")
    notes: str | None = Field(None, description="Review notes")


class CheckCTRRequiredRequest(BaseModel):
    """Request to check if CTR is required"""

    customer_id: str = Field(..., description="Customer ID")
    transaction_date: datetime = Field(..., description="Transaction date")
    amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field(default="USD", description="Currency code")


class CheckCTRRequiredResponse(BaseModel):
    """Response indicating if CTR is required"""

    required: bool = Field(..., description="Whether CTR is required")
    threshold: Decimal = Field(..., description="CTR threshold")
    amount: Decimal = Field(..., description="Transaction amount")
    reason: str | None = Field(None, description="Reason if required")


class FileReportResponse(BaseModel):
    """Response after filing a report"""

    report_id: str = Field(..., description="Report ID")
    report_type: ReportType = Field(..., description="Report type")
    status: ReportStatus = Field(..., description="New status")
    bsa_identifier: str | None = Field(None, description="BSA identifier")
    filed_at: datetime = Field(..., description="Filing timestamp")


# Dependency injection
def get_regulatory_service(
    repository: FormanceRepository = Depends(get_formance_repository),
) -> RegulatoryReportingService:
    """Get regulatory reporting service"""
    return RegulatoryReportingService(repository)


# Endpoints
@router.post(
    "/ctr/check",
    response_model=CheckCTRRequiredResponse,
    summary="Check if CTR is required",
    description="Check if a Currency Transaction Report is required for a transaction",
)
async def check_ctr_required(
    request: CheckCTRRequiredRequest,
    organization_id: str = Query(..., description="Organization ID"),
    service: RegulatoryReportingService = Depends(get_regulatory_service),
):
    """Check if CTR is required"""
    try:
        required = await service.check_ctr_required(
            organization_id=organization_id,
            customer_id=request.customer_id,
            transaction_date=request.transaction_date,
            amount=request.amount,
            currency=request.currency,
        )

        config = await service._get_reporting_config(organization_id)

        return CheckCTRRequiredResponse(
            required=required,
            threshold=config.ctr_threshold,
            amount=request.amount,
            reason=f"Transaction amount {request.amount} exceeds threshold {config.ctr_threshold}"
            if required
            else None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check CTR requirement: {str(e)}",
        )


@router.post(
    "/ctr",
    response_model=CurrencyTransactionReport,
    status_code=status.HTTP_201_CREATED,
    summary="Generate CTR",
    description="Generate a Currency Transaction Report",
)
async def generate_ctr(
    request: GenerateCTRRequest,
    organization_id: str = Query(..., description="Organization ID"),
    prepared_by: str = Query(..., description="User ID preparing report"),
    service: RegulatoryReportingService = Depends(get_regulatory_service),
):
    """Generate Currency Transaction Report"""
    try:
        ctr = await service.generate_ctr(
            organization_id=organization_id,
            customer_id=request.customer_id,
            transaction_ids=request.transaction_ids,
            prepared_by=prepared_by,
            branch_id=request.branch_id,
        )
        return ctr
    except RegulatoryReportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CTR: {str(e)}",
        )


@router.post(
    "/sar",
    response_model=SuspiciousActivityReport,
    status_code=status.HTTP_201_CREATED,
    summary="Generate SAR",
    description="Generate a Suspicious Activity Report",
)
async def generate_sar(
    request: GenerateSARRequest,
    organization_id: str = Query(..., description="Organization ID"),
    prepared_by: str = Query(..., description="User ID preparing report"),
    service: RegulatoryReportingService = Depends(get_regulatory_service),
):
    """Generate Suspicious Activity Report"""
    try:
        sar = await service.generate_sar(
            organization_id=organization_id,
            customer_id=request.customer_id,
            suspicious_activity_types=request.suspicious_activity_types,
            narrative_summary=request.narrative_summary,
            transaction_ids=request.transaction_ids,
            prepared_by=prepared_by,
            activity_start_date=request.activity_start_date,
            activity_end_date=request.activity_end_date,
            compliance_check_ids=request.compliance_check_ids,
            alert_ids=request.alert_ids,
            priority=request.priority,
        )
        return sar
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RegulatoryReportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SAR: {str(e)}",
        )


@router.get(
    "/reports",
    response_model=list[RegulatoryReportSummary],
    summary="List reports",
    description="List regulatory reports with optional filters",
)
async def list_reports(
    organization_id: str = Query(..., description="Organization ID"),
    report_type: ReportType | None = Query(None, description="Filter by report type"),
    status: ReportStatus | None = Query(None, description="Filter by status"),
    start_date: datetime | None = Query(None, description="Filter by start date"),
    end_date: datetime | None = Query(None, description="Filter by end date"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    service: RegulatoryReportingService = Depends(get_regulatory_service),
):
    """List regulatory reports"""
    try:
        reports = await service.list_reports(
            organization_id=organization_id,
            report_type=report_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        return reports
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reports: {str(e)}",
        )


@router.get(
    "/reports/{report_id}",
    response_model=SuspiciousActivityReport | CurrencyTransactionReport,
    summary="Get report",
    description="Get regulatory report by ID",
)
async def get_report(
    report_id: str,
    report_type: ReportType = Query(..., description="Report type"),
    service: RegulatoryReportingService = Depends(get_regulatory_service),
):
    """Get regulatory report by ID"""
    try:
        report = await service.get_report(report_id, report_type)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found",
            )
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report: {str(e)}",
        )


@router.post(
    "/reports/{report_id}/review",
    status_code=status.HTTP_200_OK,
    summary="Review report",
    description="Review and approve/reject a regulatory report",
)
async def review_report(
    report_id: str,
    request: ReviewReportRequest,
    report_type: ReportType = Query(..., description="Report type"),
    reviewed_by: str = Query(..., description="User ID reviewing"),
    service: RegulatoryReportingService = Depends(get_regulatory_service),
):
    """Review a regulatory report"""
    try:
        success = await service.review_report(
            report_id=report_id,
            report_type=report_type,
            reviewed_by=reviewed_by,
            approved=request.approved,
            notes=request.notes,
        )
        return {
            "report_id": report_id,
            "report_type": report_type,
            "status": ReportStatus.APPROVED if request.approved else ReportStatus.REJECTED,
            "reviewed_by": reviewed_by,
            "success": success,
        }
    except RegulatoryReportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review report: {str(e)}",
        )


@router.post(
    "/reports/{report_id}/file",
    response_model=FileReportResponse,
    summary="File report",
    description="File a regulatory report with authorities",
)
async def file_report(
    report_id: str,
    report_type: ReportType = Query(..., description="Report type"),
    filed_by: str = Query(..., description="User ID filing report"),
    service: RegulatoryReportingService = Depends(get_regulatory_service),
):
    """File a regulatory report with authorities"""
    try:
        bsa_identifier = await service.file_report(
            report_id=report_id,
            report_type=report_type,
            filed_by=filed_by,
        )
        return FileReportResponse(
            report_id=report_id,
            report_type=report_type,
            status=ReportStatus.FILED,
            bsa_identifier=bsa_identifier,
            filed_at=datetime.utcnow(),
        )
    except RegulatoryReportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to file report: {str(e)}",
        )


@router.get(
    "/config",
    response_model=RegulatoryReportingConfig,
    summary="Get reporting config",
    description="Get regulatory reporting configuration",
)
async def get_reporting_config(
    organization_id: str = Query(..., description="Organization ID"),
    service: RegulatoryReportingService = Depends(get_regulatory_service),
):
    """Get regulatory reporting configuration"""
    try:
        config = await service._get_reporting_config(organization_id)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config: {str(e)}",
        )


@router.put(
    "/config",
    response_model=RegulatoryReportingConfig,
    summary="Update reporting config",
    description="Update regulatory reporting configuration",
)
async def update_reporting_config(
    config: RegulatoryReportingConfig,
    service: RegulatoryReportingService = Depends(get_regulatory_service),
):
    """Update regulatory reporting configuration"""
    try:
        updated_config = await service.update_reporting_config(
            organization_id=config.organization_id,
            config=config,
        )
        return updated_config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update config: {str(e)}",
        )
