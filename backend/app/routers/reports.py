"""
NYOS Reports Router

API endpoints for the hierarchical report generation system:
- Level 1: FileReports (per CSV/Excel upload)
- Level 2: MonthlyReports (aggregated monthly summaries)
- Level 3: APRReports (Annual Product Review)
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db import get_db
from app import models
from app.services.report_service import (
    generate_file_report,
    generate_monthly_report,
    generate_apr_report,
    get_report_hierarchy_status,
    regenerate_all_reports,
    ReportStatus
)
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
import json

router = APIRouter(prefix="/reports", tags=["reports"])


# ============================================================================
# SCHEMAS
# ============================================================================

class FileReportResponse(BaseModel):
    id: int
    filename: str
    data_type: str
    period_year: Optional[int]
    period_month: Optional[int]
    summary: Optional[str]
    recommendations: Optional[str]
    records_analyzed: int
    status: str
    generated_at: datetime

    class Config:
        from_attributes = True


class MonthlyReportResponse(BaseModel):
    id: int
    year: int
    month: int
    executive_summary: Optional[str]
    production_analysis: Optional[str]
    quality_analysis: Optional[str]
    compliance_analysis: Optional[str]
    recommendations: Optional[str]
    status: str
    generated_at: datetime

    class Config:
        from_attributes = True


class APRReportResponse(BaseModel):
    id: int
    year: int
    title: str
    executive_summary: Optional[str]
    production_review: Optional[str]
    quality_review: Optional[str]
    complaints_review: Optional[str]
    capa_review: Optional[str]
    equipment_review: Optional[str]
    stability_review: Optional[str]
    trend_analysis: Optional[str]
    conclusions: Optional[str]
    recommendations: Optional[str]
    total_batches: Optional[int]
    total_complaints: Optional[int]
    total_capas: Optional[int]
    overall_yield: Optional[float]
    overall_qc_pass_rate: Optional[float]
    status: str
    generated_at: datetime

    class Config:
        from_attributes = True


class ReportHierarchyStatus(BaseModel):
    year: int
    file_reports: dict
    monthly_reports: dict
    apr: dict


class GenerateMonthlyRequest(BaseModel):
    year: int
    month: int
    force_regenerate: bool = False


class GenerateAPRRequest(BaseModel):
    year: int
    force_regenerate: bool = False


# ============================================================================
# FILE REPORTS ENDPOINTS (Level 1)
# ============================================================================

@router.get("/files", response_model=List[FileReportResponse])
async def list_file_reports(
    db: Session = Depends(get_db),
    year: Optional[int] = None,
    data_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """List all file reports with optional filtering"""
    query = db.query(models.FileReport)
    
    if year:
        query = query.filter(models.FileReport.period_year == year)
    if data_type:
        query = query.filter(models.FileReport.data_type == data_type)
    if status:
        query = query.filter(models.FileReport.status == status)
    
    return query.order_by(models.FileReport.generated_at.desc()).limit(limit).all()


@router.get("/files/{report_id}", response_model=FileReportResponse)
async def get_file_report(report_id: int, db: Session = Depends(get_db)):
    """Get a specific file report by ID"""
    report = db.query(models.FileReport).filter(models.FileReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="File report not found")
    return report


@router.get("/files/{report_id}/full")
async def get_file_report_full(report_id: int, db: Session = Depends(get_db)):
    """Get a file report with all details including metrics and anomalies"""
    report = db.query(models.FileReport).filter(models.FileReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="File report not found")
    
    return {
        "id": report.id,
        "filename": report.filename,
        "data_type": report.data_type,
        "period_year": report.period_year,
        "period_month": report.period_month,
        "summary": report.summary,
        "recommendations": report.recommendations,
        "key_metrics": json.loads(report.key_metrics) if report.key_metrics else None,
        "anomalies": json.loads(report.anomalies) if report.anomalies else [],
        "records_analyzed": report.records_analyzed,
        "status": report.status,
        "error_message": report.error_message,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None
    }


# ============================================================================
# MONTHLY REPORTS ENDPOINTS (Level 2)
# ============================================================================

@router.get("/monthly", response_model=List[MonthlyReportResponse])
async def list_monthly_reports(
    db: Session = Depends(get_db),
    year: Optional[int] = None,
    status: Optional[str] = None
):
    """List all monthly reports with optional filtering"""
    query = db.query(models.MonthlyReport)
    
    if year:
        query = query.filter(models.MonthlyReport.year == year)
    if status:
        query = query.filter(models.MonthlyReport.status == status)
    
    return query.order_by(models.MonthlyReport.year.desc(), models.MonthlyReport.month.desc()).all()


@router.get("/monthly/{year}/{month}", response_model=MonthlyReportResponse)
async def get_monthly_report(year: int, month: int, db: Session = Depends(get_db)):
    """Get a specific monthly report"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    report = db.query(models.MonthlyReport).filter(
        and_(models.MonthlyReport.year == year, models.MonthlyReport.month == month)
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail=f"Monthly report for {year}-{month:02d} not found")
    return report


@router.get("/monthly/{year}/{month}/full")
async def get_monthly_report_full(year: int, month: int, db: Session = Depends(get_db)):
    """Get a monthly report with all details including metrics and trends"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    report = db.query(models.MonthlyReport).filter(
        and_(models.MonthlyReport.year == year, models.MonthlyReport.month == month)
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail=f"Monthly report for {year}-{month:02d} not found")
    
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    
    return {
        "id": report.id,
        "year": report.year,
        "month": report.month,
        "month_name": month_names[report.month - 1],
        "executive_summary": report.executive_summary,
        "production_analysis": report.production_analysis,
        "quality_analysis": report.quality_analysis,
        "compliance_analysis": report.compliance_analysis,
        "recommendations": report.recommendations,
        "key_metrics": json.loads(report.key_metrics) if report.key_metrics else None,
        "trends_detected": json.loads(report.trends_detected) if report.trends_detected else [],
        "issues_summary": json.loads(report.issues_summary) if report.issues_summary else [],
        "file_report_ids": json.loads(report.file_report_ids) if report.file_report_ids else [],
        "status": report.status,
        "error_message": report.error_message,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None
    }


@router.post("/monthly/generate")
async def generate_monthly(
    request: GenerateMonthlyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate a monthly report by aggregating file reports"""
    if request.month < 1 or request.month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    try:
        report = await generate_monthly_report(
            db, request.year, request.month, request.force_regenerate
        )
        return {
            "success": True,
            "message": f"Monthly report for {request.year}-{request.month:02d} generated successfully",
            "report_id": report.id,
            "status": report.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


# ============================================================================
# APR REPORTS ENDPOINTS (Level 3)
# ============================================================================

@router.get("/apr", response_model=List[APRReportResponse])
async def list_apr_reports(db: Session = Depends(get_db)):
    """List all APR reports"""
    return db.query(models.APRReport).order_by(models.APRReport.year.desc()).all()


@router.get("/apr/{year}", response_model=APRReportResponse)
async def get_apr_report(year: int, db: Session = Depends(get_db)):
    """Get a specific APR report by year"""
    report = db.query(models.APRReport).filter(models.APRReport.year == year).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"APR for year {year} not found")
    return report


@router.get("/apr/{year}/full")
async def get_apr_report_full(year: int, db: Session = Depends(get_db)):
    """Get complete APR with all sections and metadata"""
    report = db.query(models.APRReport).filter(models.APRReport.year == year).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"APR for year {year} not found")
    
    return {
        "id": report.id,
        "year": report.year,
        "title": report.title,
        "sections": {
            "executive_summary": report.executive_summary,
            "production_review": report.production_review,
            "quality_review": report.quality_review,
            "complaints_review": report.complaints_review,
            "capa_review": report.capa_review,
            "equipment_review": report.equipment_review,
            "stability_review": report.stability_review,
            "trend_analysis": report.trend_analysis,
            "conclusions": report.conclusions,
            "recommendations": report.recommendations,
        },
        "statistics": {
            "total_batches": report.total_batches,
            "total_complaints": report.total_complaints,
            "total_capas": report.total_capas,
            "overall_yield": report.overall_yield,
            "overall_qc_pass_rate": report.overall_qc_pass_rate,
        },
        "monthly_report_ids": json.loads(report.monthly_report_ids) if report.monthly_report_ids else [],
        "status": report.status,
        "error_message": report.error_message,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
        "approved_by": report.approved_by,
        "approved_at": report.approved_at.isoformat() if report.approved_at else None
    }


@router.get("/apr/{year}/export")
async def export_apr_markdown(year: int, db: Session = Depends(get_db)):
    """Export APR as a formatted Markdown document"""
    report = db.query(models.APRReport).filter(models.APRReport.year == year).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"APR for year {year} not found")
    
    markdown = f"""# {report.title}

**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M') if report.generated_at else 'N/A'}
**Status:** {report.status}

---

## Executive Summary

{report.executive_summary or 'Not generated'}

---

## 1. Production Review

{report.production_review or 'Not generated'}

---

## 2. Quality Review

{report.quality_review or 'Not generated'}

---

## 3. Customer Complaints Review

{report.complaints_review or 'Not generated'}

---

## 4. CAPA Review

{report.capa_review or 'Not generated'}

---

## 5. Equipment Review

{report.equipment_review or 'Not generated'}

---

## 6. Stability Review

{report.stability_review or 'Not generated'}

---

## 7. Trend Analysis

{report.trend_analysis or 'Not generated'}

---

## 8. Conclusions

{report.conclusions or 'Not generated'}

---

## 9. Recommendations

{report.recommendations or 'Not generated'}

---

## Appendix: Annual Statistics

| Metric | Value |
|--------|-------|
| Total Batches | {report.total_batches or 'N/A'} |
| Total Complaints | {report.total_complaints or 'N/A'} |
| Total CAPAs | {report.total_capas or 'N/A'} |
| Overall Yield | {f"{report.overall_yield:.2f}%" if report.overall_yield else 'N/A'} |
| QC Pass Rate | {f"{report.overall_qc_pass_rate:.1f}%" if report.overall_qc_pass_rate else 'N/A'} |

---

*This report was automatically generated by NYOS APR System*
"""
    
    return StreamingResponse(
        iter([markdown]),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=APR_{year}.md"}
    )


@router.get("/apr/{year}/pdf")
async def export_apr_pdf(year: int, db: Session = Depends(get_db)):
    """Export APR as a professionally formatted PDF document with logo"""
    from app.services.pdf_service import generate_apr_pdf
    
    report = db.query(models.APRReport).filter(models.APRReport.year == year).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"APR for year {year} not found")
    
    if report.status != ReportStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot export incomplete report. Current status: {report.status}"
        )
    
    # Prepare APR data for PDF generation
    apr_data = {
        "year": report.year,
        "title": report.title,
        "executive_summary": report.executive_summary,
        "production_review": report.production_review,
        "quality_review": report.quality_review,
        "complaints_review": report.complaints_review,
        "capa_review": report.capa_review,
        "equipment_review": report.equipment_review,
        "stability_review": report.stability_review,
        "trend_analysis": report.trend_analysis,
        "conclusions": report.conclusions,
        "recommendations": report.recommendations,
        "total_batches": report.total_batches,
        "total_complaints": report.total_complaints,
        "total_capas": report.total_capas,
        "overall_yield": report.overall_yield,
        "overall_qc_pass_rate": report.overall_qc_pass_rate,
        "status": report.status,
        "approved_by": report.approved_by,
        "approved_at": report.approved_at.strftime('%Y-%m-%d') if report.approved_at else None,
        "generated_at": report.generated_at.strftime('%Y-%m-%d %H:%M') if report.generated_at else None
    }
    
    # Generate PDF
    pdf_buffer = generate_apr_pdf(apr_data)
    
    filename = f"APR_{year}_Paracetamol_500mg.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/pdf"
        }
    )


@router.post("/apr/generate")
async def generate_apr(
    request: GenerateAPRRequest,
    db: Session = Depends(get_db)
):
    """Generate an Annual Product Review from monthly reports"""
    try:
        report = await generate_apr_report(db, request.year, request.force_regenerate)
        return {
            "success": True,
            "message": f"APR for year {request.year} generated successfully",
            "report_id": report.id,
            "status": report.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating APR: {str(e)}")


@router.post("/apr/{year}/approve")
async def approve_apr(year: int, approved_by: str, db: Session = Depends(get_db)):
    """Mark an APR as approved"""
    report = db.query(models.APRReport).filter(models.APRReport.year == year).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"APR for year {year} not found")
    
    if report.status != ReportStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Cannot approve incomplete report")
    
    report.approved_by = approved_by
    report.approved_at = datetime.now()
    db.commit()
    
    return {"success": True, "message": f"APR {year} approved by {approved_by}"}


# ============================================================================
# HIERARCHY STATUS & BATCH OPERATIONS
# ============================================================================

@router.get("/status/{year}", response_model=ReportHierarchyStatus)
async def get_hierarchy_status(year: int, db: Session = Depends(get_db)):
    """Get the status of all reports in the hierarchy for a year"""
    return get_report_hierarchy_status(db, year)


@router.get("/status")
async def get_all_years_status(db: Session = Depends(get_db)):
    """Get status for all years with data"""
    # Find all years with file reports
    years = db.query(models.FileReport.period_year).distinct().all()
    years = sorted([y[0] for y in years if y[0] is not None], reverse=True)
    
    return {
        "years": years,
        "statuses": {year: get_report_hierarchy_status(db, year) for year in years}
    }


@router.post("/generate-all/{year}")
async def generate_all_reports(year: int, db: Session = Depends(get_db)):
    """Generate all monthly reports and APR for a year"""
    results = await regenerate_all_reports(db, year)
    return {
        "success": True,
        "year": year,
        "results": results
    }


@router.post("/generate-missing/{year}")
async def generate_missing_reports(year: int, db: Session = Depends(get_db)):
    """Generate only missing monthly reports and APR for a year"""
    results = {"monthly_reports": [], "apr": None}
    
    for month in range(1, 13):
        existing = db.query(models.MonthlyReport).filter(
            and_(models.MonthlyReport.year == year, models.MonthlyReport.month == month)
        ).first()
        
        if existing and existing.status == ReportStatus.COMPLETED.value:
            results["monthly_reports"].append({
                "month": month,
                "status": "exists",
                "id": existing.id
            })
        else:
            try:
                mr = await generate_monthly_report(db, year, month, force_regenerate=bool(existing))
                results["monthly_reports"].append({
                    "month": month,
                    "status": "generated",
                    "id": mr.id
                })
            except ValueError as e:
                results["monthly_reports"].append({
                    "month": month,
                    "status": "skipped",
                    "reason": str(e)
                })
            except Exception as e:
                results["monthly_reports"].append({
                    "month": month,
                    "status": "failed",
                    "error": str(e)
                })
    
    # Check APR
    existing_apr = db.query(models.APRReport).filter(models.APRReport.year == year).first()
    if existing_apr and existing_apr.status == ReportStatus.COMPLETED.value:
        results["apr"] = {"status": "exists", "id": existing_apr.id}
    else:
        try:
            apr = await generate_apr_report(db, year, force_regenerate=bool(existing_apr))
            results["apr"] = {"status": "generated", "id": apr.id}
        except Exception as e:
            results["apr"] = {"status": "failed", "error": str(e)}
    
    return results


# ============================================================================
# PIPELINE: FROM FILES TO APR
# ============================================================================

@router.post("/pipeline/{year}")
async def run_full_pipeline(year: int, db: Session = Depends(get_db)):
    """
    Run the complete report generation pipeline for a year:
    1. Check available file reports
    2. Generate missing monthly reports
    3. Generate APR from monthly reports
    
    This orchestrates the entire hierarchical report generation.
    """
    pipeline_result = {
        "year": year,
        "steps": [],
        "success": True
    }
    
    # Step 1: Check file reports
    file_reports = db.query(models.FileReport).filter(
        models.FileReport.period_year == year,
        models.FileReport.status == ReportStatus.COMPLETED.value
    ).all()
    
    pipeline_result["steps"].append({
        "step": 1,
        "name": "File Reports Check",
        "status": "completed",
        "details": f"Found {len(file_reports)} completed file reports for {year}"
    })
    
    if len(file_reports) == 0:
        pipeline_result["success"] = False
        pipeline_result["steps"].append({
            "step": 2,
            "name": "Pipeline Aborted",
            "status": "failed",
            "details": "No file reports available. Please upload CSV files first."
        })
        return pipeline_result
    
    # Step 2: Generate monthly reports
    months_generated = []
    months_failed = []
    
    for month in range(1, 13):
        try:
            mr = await generate_monthly_report(db, year, month, force_regenerate=False)
            months_generated.append(month)
        except ValueError:
            pass  # No data for this month
        except Exception as e:
            months_failed.append({"month": month, "error": str(e)})
    
    pipeline_result["steps"].append({
        "step": 2,
        "name": "Monthly Reports Generation",
        "status": "completed" if not months_failed else "partial",
        "details": f"Generated {len(months_generated)} monthly reports",
        "months_generated": months_generated,
        "months_failed": months_failed
    })
    
    # Step 3: Generate APR
    try:
        apr = await generate_apr_report(db, year, force_regenerate=False)
        pipeline_result["steps"].append({
            "step": 3,
            "name": "APR Generation",
            "status": "completed",
            "details": f"APR for {year} generated successfully",
            "apr_id": apr.id
        })
    except Exception as e:
        pipeline_result["success"] = False
        pipeline_result["steps"].append({
            "step": 3,
            "name": "APR Generation",
            "status": "failed",
            "details": str(e)
        })
    
    return pipeline_result
