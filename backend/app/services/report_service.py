"""
NYOS Hierarchical Report Generation Service

This service implements a 3-tier report generation system:
- Level 1: FileReport - Generated per CSV/Excel file upload
- Level 2: MonthlyReport - Aggregates FileReports into monthly summaries
- Level 3: APRReport - Synthesizes MonthlyReports into Annual Product Review

The architecture allows incremental report building:
Upload File → FileReport → MonthlyReport → APRReport
"""

import google.generativeai as genai
from app.config import GOOGLE_API_KEY
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app import models
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import pandas as pd
import io
from enum import Enum

genai.configure(api_key=GOOGLE_API_KEY)


class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# LEVEL 1: FILE REPORT GENERATION
# ============================================================================

def extract_file_metrics(df: pd.DataFrame, data_type: str) -> Dict[str, Any]:
    """Extract key metrics from a dataframe based on data type"""
    metrics = {
        "record_count": len(df),
        "data_type": data_type,
    }
    
    if data_type == "batch":
        metrics.update({
            "total_batches": len(df),
            "avg_yield": float(df["yield_percent"].mean()) if "yield_percent" in df.columns else None,
            "min_yield": float(df["yield_percent"].min()) if "yield_percent" in df.columns else None,
            "max_yield": float(df["yield_percent"].max()) if "yield_percent" in df.columns else None,
            "avg_hardness": float(df.get("tablet_hardness_n", df.get("hardness", pd.Series())).mean()) if any(c in df.columns for c in ["tablet_hardness_n", "hardness"]) else None,
            "products": df["product_name"].unique().tolist() if "product_name" in df.columns else [],
            "machines_used": df["tablet_press_id"].unique().tolist() if "tablet_press_id" in df.columns else [],
            "deviations_count": len(df[df.get("deviation_id", pd.Series()).notna()]) if "deviation_id" in df.columns else 0,
        })
        
    elif data_type == "qc":
        metrics.update({
            "total_tests": len(df),
            "pass_count": len(df[df.get("overall_result", pd.Series()).str.lower() == "pass"]) if "overall_result" in df.columns else None,
            "fail_count": len(df[df.get("overall_result", pd.Series()).str.lower() == "fail"]) if "overall_result" in df.columns else None,
            "avg_assay": float(df["assay_percent"].mean()) if "assay_percent" in df.columns else None,
            "avg_dissolution": float(df.get("dissolution_30min_mean", df.get("dissolution_mean", pd.Series())).mean()) if any(c in df.columns for c in ["dissolution_30min_mean", "dissolution_mean"]) else None,
            "oos_count": len(df[df.get("overall_result", pd.Series()).str.lower() == "oos"]) if "overall_result" in df.columns else 0,
        })
        
    elif data_type == "complaint":
        metrics.update({
            "total_complaints": len(df),
            "by_severity": df["severity"].value_counts().to_dict() if "severity" in df.columns else {},
            "by_category": df["category"].value_counts().to_dict() if "category" in df.columns else {},
            "open_count": len(df[df.get("status", df.get("complaint_status", pd.Series())).str.lower() == "open"]) if any(c in df.columns for c in ["status", "complaint_status"]) else None,
            "regulatory_reportable": len(df[df.get("regulatory_reportable", pd.Series()).str.lower() == "yes"]) if "regulatory_reportable" in df.columns else 0,
        })
        
    elif data_type == "capa":
        metrics.update({
            "total_capas": len(df),
            "by_type": df["capa_type"].value_counts().to_dict() if "capa_type" in df.columns else {},
            "by_source": df["source"].value_counts().to_dict() if "source" in df.columns else {},
            "open_count": len(df[~df.get("status", pd.Series()).str.lower().str.contains("closed", na=False)]) if "status" in df.columns else None,
            "critical_count": len(df[df.get("risk_score", pd.Series()).str.lower() == "critical"]) if "risk_score" in df.columns else 0,
            "avg_days_to_close": float(df["days_to_close"].mean()) if "days_to_close" in df.columns else None,
        })
        
    elif data_type == "equipment":
        metrics.update({
            "total_calibrations": len(df),
            "pass_count": len(df[df.get("result", pd.Series()).str.lower() == "pass"]) if "result" in df.columns else None,
            "fail_count": len(df[df.get("result", pd.Series()).str.lower() == "fail"]) if "result" in df.columns else None,
            "by_equipment_type": df["equipment_type"].value_counts().to_dict() if "equipment_type" in df.columns else {},
            "out_of_tolerance_count": len(df[df.get("out_of_tolerance", pd.Series()).str.lower() == "yes"]) if "out_of_tolerance" in df.columns else 0,
        })
        
    elif data_type == "environmental":
        metrics.update({
            "total_records": len(df),
            "by_room": df["room_name"].value_counts().to_dict() if "room_name" in df.columns else {},
            "excursions_count": len(df[df.get("overall_result", pd.Series()).str.lower() != "pass"]) if "overall_result" in df.columns else 0,
            "avg_temperature": float(df.get("temperature_c", df.get("temperature", pd.Series())).mean()) if any(c in df.columns for c in ["temperature_c", "temperature"]) else None,
            "avg_humidity": float(df.get("humidity_percent_rh", df.get("humidity", pd.Series())).mean()) if any(c in df.columns for c in ["humidity_percent_rh", "humidity"]) else None,
        })
        
    elif data_type == "stability":
        metrics.update({
            "total_tests": len(df),
            "studies_count": df["study_id"].nunique() if "study_id" in df.columns else None,
            "by_condition": df["stability_condition"].value_counts().to_dict() if "stability_condition" in df.columns else {},
            "failures_count": len(df[df.get("overall_result", pd.Series()).str.lower() == "fail"]) if "overall_result" in df.columns else 0,
            "timepoints": sorted(df["timepoint_months"].unique().tolist()) if "timepoint_months" in df.columns else [],
        })
        
    elif data_type == "raw_material":
        metrics.update({
            "total_receipts": len(df),
            "suppliers_count": df["supplier_name"].nunique() if "supplier_name" in df.columns else None,
            "materials_received": df["material_name"].unique().tolist() if "material_name" in df.columns else [],
            "rejected_count": len(df[df.get("disposition", pd.Series()).str.lower() == "rejected"]) if "disposition" in df.columns else 0,
            "coa_missing": len(df[df.get("coa_received", pd.Series()).str.lower() == "no"]) if "coa_received" in df.columns else 0,
        })
        
    elif data_type == "batch_release":
        metrics.update({
            "total_releases": len(df),
            "released_count": len(df[df.get("disposition", pd.Series()).str.lower() == "released"]) if "disposition" in df.columns else None,
            "rejected_count": len(df[df.get("disposition", pd.Series()).str.lower() == "rejected"]) if "disposition" in df.columns else 0,
            "avg_days_to_release": float(df["days_to_release"].mean()) if "days_to_release" in df.columns else None,
            "with_deviation": len(df[df.get("has_deviation", pd.Series()).str.lower() == "yes"]) if "has_deviation" in df.columns else 0,
            "with_oos": len(df[df.get("has_oos", pd.Series()).str.lower() == "yes"]) if "has_oos" in df.columns else 0,
        })
    
    return metrics


def detect_anomalies(df: pd.DataFrame, data_type: str) -> List[Dict[str, Any]]:
    """Detect anomalies and issues in the data"""
    anomalies = []
    
    if data_type == "batch":
        # Low yield anomalies
        if "yield_percent" in df.columns:
            low_yield = df[df["yield_percent"] < 95]
            if len(low_yield) > 0:
                anomalies.append({
                    "type": "low_yield",
                    "severity": "warning" if len(low_yield) < 5 else "critical",
                    "count": len(low_yield),
                    "description": f"{len(low_yield)} batches with yield below 95%",
                    "affected_batches": low_yield["batch_id"].tolist()[:10] if "batch_id" in low_yield.columns else []
                })
        
        # Deviations
        if "deviation_id" in df.columns:
            deviations = df[df["deviation_id"].notna() & (df["deviation_id"] != "")]
            if len(deviations) > 0:
                anomalies.append({
                    "type": "deviations",
                    "severity": "info",
                    "count": len(deviations),
                    "description": f"{len(deviations)} batches with deviations recorded"
                })
                
    elif data_type == "qc":
        # OOS results
        if "overall_result" in df.columns:
            oos = df[df["overall_result"].str.lower().isin(["fail", "oos"])]
            if len(oos) > 0:
                anomalies.append({
                    "type": "oos_results",
                    "severity": "critical",
                    "count": len(oos),
                    "description": f"{len(oos)} OOS/Fail results detected",
                    "affected_batches": oos["batch_id"].tolist()[:10] if "batch_id" in oos.columns else []
                })
        
        # Assay out of spec (95-105%)
        if "assay_percent" in df.columns:
            oos_assay = df[(df["assay_percent"] < 95) | (df["assay_percent"] > 105)]
            if len(oos_assay) > 0:
                anomalies.append({
                    "type": "oos_assay",
                    "severity": "critical",
                    "count": len(oos_assay),
                    "description": f"{len(oos_assay)} results with assay outside 95-105% specification"
                })
                
    elif data_type == "complaint":
        # High severity complaints
        if "severity" in df.columns:
            critical = df[df["severity"].str.lower().isin(["critical", "high"])]
            if len(critical) > 0:
                anomalies.append({
                    "type": "critical_complaints",
                    "severity": "critical",
                    "count": len(critical),
                    "description": f"{len(critical)} critical/high severity complaints"
                })
        
        # Regulatory reportable
        if "regulatory_reportable" in df.columns:
            reportable = df[df["regulatory_reportable"].str.lower() == "yes"]
            if len(reportable) > 0:
                anomalies.append({
                    "type": "regulatory_reportable",
                    "severity": "critical",
                    "count": len(reportable),
                    "description": f"{len(reportable)} regulatory reportable complaints"
                })
                
    elif data_type == "capa":
        # Overdue CAPAs
        if "target_date" in df.columns and "status" in df.columns:
            today = datetime.now()
            df["target_date"] = pd.to_datetime(df["target_date"], errors="coerce")
            overdue = df[(df["target_date"] < today) & (~df["status"].str.lower().str.contains("closed", na=False))]
            if len(overdue) > 0:
                anomalies.append({
                    "type": "overdue_capas",
                    "severity": "warning",
                    "count": len(overdue),
                    "description": f"{len(overdue)} overdue CAPAs not closed"
                })
        
        # Critical risk CAPAs
        if "risk_score" in df.columns:
            critical = df[df["risk_score"].str.lower() == "critical"]
            if len(critical) > 0:
                anomalies.append({
                    "type": "critical_capas",
                    "severity": "critical",
                    "count": len(critical),
                    "description": f"{len(critical)} critical risk CAPAs"
                })
                
    elif data_type == "equipment":
        # Failed calibrations
        if "result" in df.columns:
            failures = df[df["result"].str.lower() == "fail"]
            if len(failures) > 0:
                anomalies.append({
                    "type": "calibration_failures",
                    "severity": "warning",
                    "count": len(failures),
                    "description": f"{len(failures)} calibration failures",
                    "equipment": failures["equipment_id"].unique().tolist()[:10] if "equipment_id" in failures.columns else []
                })
    
    return anomalies


def extract_period_from_data(df: pd.DataFrame, data_type: str) -> tuple:
    """Extract year and month from the data based on date columns"""
    date_columns = {
        "batch": "manufacturing_date",
        "qc": "test_date",
        "complaint": "complaint_date",
        "capa": "open_date",
        "equipment": "actual_date",
        "environmental": "monitoring_date",
        "stability": "test_date",
        "raw_material": "receipt_date",
        "batch_release": "release_date",
    }
    
    date_col = date_columns.get(data_type)
    if date_col and date_col in df.columns:
        dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
        if len(dates) > 0:
            # Get the most common year
            years = dates.dt.year.value_counts()
            year = int(years.index[0]) if len(years) > 0 else None
            
            # Check if data spans multiple months or is single month
            months = dates.dt.month.unique()
            if len(months) == 1:
                month = int(months[0])
            else:
                month = None  # yearly data
            
            return year, month
    
    return None, None


async def generate_file_report(
    db: Session,
    file_content: bytes,
    filename: str,
    data_type: str,
    uploaded_file_id: int
) -> models.FileReport:
    """
    Generate a Level 1 report for an uploaded file.
    This is called after each CSV/Excel upload.
    """
    try:
        # Parse the file
        df = pd.read_csv(io.StringIO(file_content.decode("utf-8")))
        
        # Extract metrics
        metrics = extract_file_metrics(df, data_type)
        
        # Detect anomalies
        anomalies = detect_anomalies(df, data_type)
        
        # Extract period
        year, month = extract_period_from_data(df, data_type)
        
        # Create initial report record
        file_report = models.FileReport(
            uploaded_file_id=uploaded_file_id,
            filename=filename,
            data_type=data_type,
            period_year=year,
            period_month=month,
            records_analyzed=len(df),
            key_metrics=json.dumps(metrics),
            anomalies=json.dumps(anomalies),
            status=ReportStatus.PROCESSING.value
        )
        db.add(file_report)
        db.commit()
        db.refresh(file_report)
        
        # Generate AI summary
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        
        prompt = f"""You are a pharmaceutical quality expert analyzing data from a {data_type} file.

FILE: {filename}
PERIOD: {f"Year {year}" if year else "Unknown"}{f", Month {month}" if month else ""}
DATA TYPE: {data_type}
RECORDS: {len(df)}

KEY METRICS:
{json.dumps(metrics, indent=2)}

ANOMALIES DETECTED:
{json.dumps(anomalies, indent=2) if anomalies else "None detected"}

Generate a concise analytical summary (max 500 words) covering:
1. **Overview**: What this data represents
2. **Key Findings**: Important observations from the metrics
3. **Issues**: Any problems or anomalies detected
4. **Quality Assessment**: Overall quality status (Good/Warning/Critical)

Be specific with numbers. Use bullet points for clarity."""

        response = model.generate_content(prompt)
        summary = response.text
        
        # Generate recommendations
        rec_prompt = f"""Based on this pharmaceutical {data_type} data analysis:

METRICS: {json.dumps(metrics, indent=2)}
ANOMALIES: {json.dumps(anomalies, indent=2) if anomalies else "None"}

Provide 3-5 specific, actionable recommendations. Be concise and practical."""

        rec_response = model.generate_content(rec_prompt)
        recommendations = rec_response.text
        
        # Update the report
        file_report.summary = summary
        file_report.recommendations = recommendations
        file_report.status = ReportStatus.COMPLETED.value
        db.commit()
        db.refresh(file_report)
        
        return file_report
        
    except Exception as e:
        # Update status to failed
        if file_report:
            file_report.status = ReportStatus.FAILED.value
            file_report.error_message = str(e)
            db.commit()
        raise e


# ============================================================================
# LEVEL 2: MONTHLY REPORT GENERATION
# ============================================================================

async def generate_monthly_report(
    db: Session,
    year: int,
    month: int,
    force_regenerate: bool = False
) -> models.MonthlyReport:
    """
    Generate a Level 2 monthly report by aggregating all FileReports for that month.
    """
    # Check if report already exists
    existing = db.query(models.MonthlyReport).filter(
        and_(models.MonthlyReport.year == year, models.MonthlyReport.month == month)
    ).first()
    
    if existing and not force_regenerate:
        return existing
    
    # Get all file reports for this month
    file_reports = db.query(models.FileReport).filter(
        and_(
            models.FileReport.period_year == year,
            models.FileReport.status == ReportStatus.COMPLETED.value
        )
    ).filter(
        (models.FileReport.period_month == month) | (models.FileReport.period_month.is_(None))
    ).all()
    
    if not file_reports:
        raise ValueError(f"No file reports found for {year}-{month:02d}")
    
    # Aggregate metrics from all file reports
    aggregated_metrics = {}
    all_anomalies = []
    file_report_ids = []
    
    for fr in file_reports:
        file_report_ids.append(fr.id)
        
        # Parse metrics
        if fr.key_metrics:
            metrics = json.loads(fr.key_metrics)
            data_type = metrics.get("data_type", fr.data_type)
            if data_type not in aggregated_metrics:
                aggregated_metrics[data_type] = []
            aggregated_metrics[data_type].append(metrics)
        
        # Collect anomalies
        if fr.anomalies:
            anomalies = json.loads(fr.anomalies)
            for a in anomalies:
                a["source_file"] = fr.filename
                all_anomalies.append(a)
    
    # Create or update monthly report
    if existing:
        monthly_report = existing
        monthly_report.status = ReportStatus.PROCESSING.value
    else:
        monthly_report = models.MonthlyReport(
            year=year,
            month=month,
            file_report_ids=json.dumps(file_report_ids),
            status=ReportStatus.PROCESSING.value
        )
        db.add(monthly_report)
    
    db.commit()
    db.refresh(monthly_report)
    
    # Generate comprehensive monthly analysis using AI
    model = genai.GenerativeModel("gemini-2.5-flash")
    month_names = ["January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December"]
    month_name = month_names[month - 1]
    
    # Collect all file summaries
    file_summaries = []
    for fr in file_reports:
        file_summaries.append(f"**{fr.filename}** ({fr.data_type}):\n{fr.summary[:500] if fr.summary else 'No summary'}")
    
    # Generate Executive Summary
    exec_prompt = f"""You are a pharmaceutical quality expert creating a monthly report for {month_name} {year}.

FILE REPORTS ANALYZED ({len(file_reports)} files):
{chr(10).join(file_summaries)}

AGGREGATED METRICS BY TYPE:
{json.dumps(aggregated_metrics, indent=2)}

ANOMALIES DETECTED THIS MONTH:
{json.dumps(all_anomalies, indent=2) if all_anomalies else "None"}

Generate an EXECUTIVE SUMMARY (300-400 words) for this month covering:
1. Overall plant performance status
2. Key achievements and concerns
3. Most critical issues requiring attention
4. Month-over-month highlights

Use professional pharmaceutical language. Be specific with data."""

    exec_response = model.generate_content(exec_prompt)
    monthly_report.executive_summary = exec_response.text
    
    # Generate Production Analysis
    prod_prompt = f"""Analyze the PRODUCTION data for {month_name} {year}:

BATCH/MANUFACTURING METRICS:
{json.dumps(aggregated_metrics.get('batch', []), indent=2)}

BATCH RELEASE METRICS:
{json.dumps(aggregated_metrics.get('batch_release', []), indent=2)}

Create a PRODUCTION ANALYSIS section (200-300 words) covering:
- Batch volumes and yields
- Process performance
- Equipment utilization
- Deviations and issues"""

    prod_response = model.generate_content(prod_prompt)
    monthly_report.production_analysis = prod_response.text
    
    # Generate Quality Analysis
    quality_prompt = f"""Analyze the QUALITY data for {month_name} {year}:

QC/LAB METRICS:
{json.dumps(aggregated_metrics.get('qc', []), indent=2)}

STABILITY METRICS:
{json.dumps(aggregated_metrics.get('stability', []), indent=2)}

ENVIRONMENTAL METRICS:
{json.dumps(aggregated_metrics.get('environmental', []), indent=2)}

RAW MATERIALS METRICS:
{json.dumps(aggregated_metrics.get('raw_material', []), indent=2)}

Create a QUALITY ANALYSIS section (200-300 words) covering:
- QC test results and compliance rates
- Stability study status
- Environmental monitoring results
- Raw material quality"""

    quality_response = model.generate_content(quality_prompt)
    monthly_report.quality_analysis = quality_response.text
    
    # Generate Compliance Analysis
    comp_prompt = f"""Analyze the COMPLIANCE data for {month_name} {year}:

COMPLAINTS METRICS:
{json.dumps(aggregated_metrics.get('complaint', []), indent=2)}

CAPA METRICS:
{json.dumps(aggregated_metrics.get('capa', []), indent=2)}

EQUIPMENT CALIBRATION METRICS:
{json.dumps(aggregated_metrics.get('equipment', []), indent=2)}

Create a COMPLIANCE ANALYSIS section (200-300 words) covering:
- Customer complaints summary
- CAPA status and effectiveness
- Equipment compliance
- Regulatory concerns"""

    comp_response = model.generate_content(comp_prompt)
    monthly_report.compliance_analysis = comp_response.text
    
    # Store aggregated data
    monthly_report.key_metrics = json.dumps(aggregated_metrics)
    monthly_report.issues_summary = json.dumps(all_anomalies)
    
    # Detect trends
    trends = detect_monthly_trends(db, year, month)
    monthly_report.trends_detected = json.dumps(trends)
    
    # Generate recommendations
    rec_prompt = f"""Based on the {month_name} {year} monthly analysis:

KEY ISSUES:
{json.dumps(all_anomalies[:10], indent=2) if all_anomalies else "None significant"}

TRENDS:
{json.dumps(trends, indent=2)}

Provide 5-7 prioritized recommendations for immediate action and continuous improvement."""

    rec_response = model.generate_content(rec_prompt)
    monthly_report.recommendations = rec_response.text
    
    monthly_report.status = ReportStatus.COMPLETED.value
    db.commit()
    db.refresh(monthly_report)
    
    return monthly_report


def detect_monthly_trends(db: Session, year: int, month: int) -> List[Dict[str, Any]]:
    """Detect trends by comparing with previous months"""
    trends = []
    
    # Get previous month's report for comparison
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    
    prev_report = db.query(models.MonthlyReport).filter(
        and_(models.MonthlyReport.year == prev_year, models.MonthlyReport.month == prev_month)
    ).first()
    
    if prev_report and prev_report.key_metrics:
        prev_metrics = json.loads(prev_report.key_metrics)
        # Compare batch yields
        if "batch" in prev_metrics:
            # Trend analysis would be done here comparing current vs previous
            trends.append({
                "type": "yield_comparison",
                "description": "Yield trend vs previous month",
                "status": "stable"  # Would be calculated
            })
    
    return trends


# ============================================================================
# LEVEL 3: APR (ANNUAL PRODUCT REVIEW) GENERATION
# ============================================================================

async def generate_apr_report(
    db: Session,
    year: int,
    force_regenerate: bool = False
) -> models.APRReport:
    """
    Generate a Level 3 Annual Product Review by synthesizing all MonthlyReports.
    If no monthly reports exist, generates directly from database data.
    This is the final, comprehensive report for regulatory purposes.
    """
    # Check if APR already exists
    existing = db.query(models.APRReport).filter(
        models.APRReport.year == year
    ).first()
    
    if existing and not force_regenerate:
        return existing
    
    # Get all monthly reports for this year (optional - may not exist)
    monthly_reports = db.query(models.MonthlyReport).filter(
        and_(
            models.MonthlyReport.year == year,
            models.MonthlyReport.status == ReportStatus.COMPLETED.value
        )
    ).order_by(models.MonthlyReport.month).all()
    
    # Flag to track if we're working directly from DB
    direct_from_db = len(monthly_reports) == 0
    
    # Aggregate annual statistics
    all_metrics = []
    all_issues = []
    monthly_report_ids = []
    
    if not direct_from_db:
        # Use monthly reports data
        for mr in monthly_reports:
            monthly_report_ids.append(mr.id)
            if mr.key_metrics:
                metrics = json.loads(mr.key_metrics)
                all_metrics.append({"month": mr.month, "metrics": metrics})
            if mr.issues_summary:
                issues = json.loads(mr.issues_summary)
                for issue in issues:
                    issue["month"] = mr.month
                    all_issues.append(issue)
    
    # Calculate annual totals from database (always from DB for accuracy)
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31, 23, 59, 59)
    
    # Additional data for direct-from-DB mode
    db_batches = []
    db_complaints = []
    db_capas = []
    db_qc_results = []
    db_equipment = []
    db_stability = []
    
    if direct_from_db:
        # Fetch detailed data directly from database
        batches = db.query(models.Batch).filter(
            and_(models.Batch.manufacturing_date >= start_date, models.Batch.manufacturing_date <= end_date)
        ).limit(100).all()
        for b in batches:
            db_batches.append({
                "batch_id": b.batch_id,
                "product": b.product_name,
                "status": b.status,
                "yield": b.yield_percent,
                "month": b.manufacturing_date.month if b.manufacturing_date else 0
            })
        
        complaints = db.query(models.Complaint).filter(
            and_(models.Complaint.complaint_date >= start_date, models.Complaint.complaint_date <= end_date)
        ).limit(100).all()
        for c in complaints:
            db_complaints.append({
                "complaint_id": c.complaint_id,
                "category": c.category,
                "severity": c.severity,
                "status": c.status,
                "month": c.complaint_date.month if c.complaint_date else 0
            })
            if c.severity in ["Critical", "Major"]:
                all_issues.append({
                    "type": "complaint",
                    "id": c.complaint_id,
                    "severity": c.severity,
                    "description": c.description[:100] if c.description else "No description",
                    "month": c.complaint_date.month if c.complaint_date else 0
                })
        
        capas = db.query(models.CAPA).filter(
            and_(models.CAPA.open_date >= start_date, models.CAPA.open_date <= end_date)
        ).limit(100).all()
        for cap in capas:
            db_capas.append({
                "capa_id": cap.capa_id,
                "type": cap.capa_type,
                "status": cap.status,
                "risk_score": cap.risk_score,
                "month": cap.open_date.month if cap.open_date else 0
            })
        
        qc_results = db.query(models.QCResult).filter(
            and_(models.QCResult.test_date >= start_date, models.QCResult.test_date <= end_date)
        ).limit(100).all()
        for qc in qc_results:
            db_qc_results.append({
                "batch_id": qc.batch_id,
                "sample_id": qc.sample_id,
                "result": qc.overall_result,
                "assay": qc.assay_percent,
                "month": qc.test_date.month if qc.test_date else 0
            })
            if qc.overall_result == "Fail":
                all_issues.append({
                    "type": "qc_failure",
                    "batch_id": qc.batch_id,
                    "sample_id": qc.sample_id,
                    "month": qc.test_date.month if qc.test_date else 0
                })
        
        # Check if Equipment table exists and has data
        try:
            equipment = db.query(models.Equipment).limit(50).all()
            for eq in equipment:
                db_equipment.append({
                    "equipment_id": eq.equipment_id,
                    "name": eq.equipment_name,
                    "status": eq.status if hasattr(eq, 'status') else "N/A"
                })
        except Exception:
            pass
        
        # Stability data from batches (no separate StabilityResult model)
        db_stability = []  # Stability data not available in current schema
    
    total_batches = db.query(models.Batch).filter(
        and_(models.Batch.manufacturing_date >= start_date, models.Batch.manufacturing_date <= end_date)
    ).count()
    
    total_complaints = db.query(models.Complaint).filter(
        and_(models.Complaint.complaint_date >= start_date, models.Complaint.complaint_date <= end_date)
    ).count()
    
    total_capas = db.query(models.CAPA).filter(
        and_(models.CAPA.open_date >= start_date, models.CAPA.open_date <= end_date)
    ).count()
    
    avg_yield = db.query(func.avg(models.Batch.yield_percent)).filter(
        and_(models.Batch.manufacturing_date >= start_date, models.Batch.manufacturing_date <= end_date)
    ).scalar() or 0
    
    qc_total = db.query(models.QCResult).filter(
        and_(models.QCResult.test_date >= start_date, models.QCResult.test_date <= end_date)
    ).count()
    
    qc_pass = db.query(models.QCResult).filter(
        and_(
            models.QCResult.test_date >= start_date,
            models.QCResult.test_date <= end_date,
            models.QCResult.overall_result == "Pass"
        )
    ).count()
    
    qc_pass_rate = (qc_pass / qc_total * 100) if qc_total > 0 else 0
    
    # Create or update APR
    if existing:
        apr = existing
        apr.status = ReportStatus.PROCESSING.value
    else:
        apr = models.APRReport(
            year=year,
            title=f"Annual Product Review {year} - Paracetamol 500mg",
            monthly_report_ids=json.dumps(monthly_report_ids),
            total_batches=total_batches,
            total_complaints=total_complaints,
            total_capas=total_capas,
            overall_yield=round(avg_yield, 2),
            overall_qc_pass_rate=round(qc_pass_rate, 2),
            status=ReportStatus.PROCESSING.value
        )
        db.add(apr)
    
    db.commit()
    db.refresh(apr)
    
    # Collect all monthly summaries
    monthly_summaries = []
    for mr in monthly_reports:
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_summaries.append(f"**{month_names[mr.month-1]}**: {mr.executive_summary[:300] if mr.executive_summary else 'No data'}")
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    # Build data context based on source
    if direct_from_db:
        data_source_note = "Data sourced directly from database records."
        batch_data = json.dumps(db_batches[:50], indent=2)
        complaint_data = json.dumps(db_complaints[:30], indent=2)
        capa_data = json.dumps(db_capas[:30], indent=2)
        qc_data = json.dumps(db_qc_results[:30], indent=2)
        equipment_data = json.dumps(db_equipment[:20], indent=2) if db_equipment else "No equipment data"
        stability_data = json.dumps(db_stability[:20], indent=2) if db_stability else "No stability data"
        monthly_context = "Monthly breakdown not available - generating from raw data."
    else:
        data_source_note = f"Data aggregated from {len(monthly_reports)} monthly reports."
        batch_data = json.dumps([{"month": m["month"], "batch_metrics": m["metrics"].get("batch", [])} for m in all_metrics], indent=2)
        complaint_data = json.dumps([{"month": m["month"], "complaints": m["metrics"].get("complaint", [])} for m in all_metrics], indent=2)
        capa_data = json.dumps([{"month": m["month"], "capas": m["metrics"].get("capa", [])} for m in all_metrics], indent=2)
        qc_data = json.dumps([{"month": m["month"], "qc_metrics": m["metrics"].get("qc", []), "stability": m["metrics"].get("stability", [])} for m in all_metrics], indent=2)
        equipment_data = json.dumps([{"month": m["month"], "equipment": m["metrics"].get("equipment", [])} for m in all_metrics], indent=2)
        stability_data = json.dumps([{"month": m["month"], "stability": m["metrics"].get("stability", [])} for m in all_metrics], indent=2)
        monthly_context = chr(10).join(monthly_summaries) if monthly_summaries else "No monthly summaries available."
    
    # Generate APR Executive Summary
    exec_prompt = f"""You are creating an ANNUAL PRODUCT REVIEW (APR) for Paracetamol 500mg - Year {year}.

{data_source_note}

ANNUAL STATISTICS:
- Total batches produced: {total_batches}
- Average yield: {avg_yield:.2f}%
- Total customer complaints: {total_complaints}
- Total CAPAs: {total_capas}
- QC Pass Rate: {qc_pass_rate:.1f}%
- QC Tests Performed: {qc_total}
- QC Tests Passed: {qc_pass}

CONTEXT:
{monthly_context}

ISSUES THROUGHOUT THE YEAR:
{json.dumps(all_issues[:20], indent=2) if all_issues else "None significant"}

Generate a comprehensive EXECUTIVE SUMMARY (500-600 words) for the APR covering:
1. Overall annual performance assessment
2. Key achievements and milestones
3. Major quality events and their resolution
4. Regulatory compliance status
5. Strategic recommendations for next year

This is for regulatory submission - be thorough and professional."""

    exec_response = model.generate_content(exec_prompt)
    apr.executive_summary = exec_response.text
    
    # Generate Production Review
    prod_prompt = f"""Create the PRODUCTION REVIEW section for APR {year}:

Total batches: {total_batches}
Average yield: {avg_yield:.2f}%

BATCH DATA:
{batch_data}

Generate a comprehensive production review (400-500 words) covering:
- Annual production volumes and trends
- Yield analysis by month/quarter
- Equipment performance
- Process improvements implemented
- Manufacturing deviations summary"""

    prod_response = model.generate_content(prod_prompt)
    apr.production_review = prod_response.text
    
    # Generate Quality Review
    quality_prompt = f"""Create the QUALITY REVIEW section for APR {year}:

QC Pass Rate: {qc_pass_rate:.1f}%
Total QC Tests: {qc_total}
Tests Passed: {qc_pass}

QC DATA:
{qc_data}

Generate a comprehensive quality review (400-500 words) covering:
- QC test results summary
- OOS investigations
- Stability program update
- Analytical method performance
- Specification compliance"""

    quality_response = model.generate_content(quality_prompt)
    apr.quality_review = quality_response.text
    
    # Generate Complaints Review
    comp_prompt = f"""Create the COMPLAINTS REVIEW section for APR {year}:

Total complaints: {total_complaints}

COMPLAINT DATA:
{complaint_data}

Generate a comprehensive complaints review (300-400 words) covering:
- Complaint trends by category
- Severity distribution
- Investigation outcomes
- Root causes identified
- Corrective actions taken"""

    comp_response = model.generate_content(comp_prompt)
    apr.complaints_review = comp_response.text
    
    # Generate CAPA Review
    capa_prompt = f"""Create the CAPA REVIEW section for APR {year}:

Total CAPAs: {total_capas}

CAPA DATA:
{capa_data}

Generate a comprehensive CAPA review (300-400 words) covering:
- CAPA initiation trends
- Closure metrics and effectiveness
- Root cause analysis summary
- Recurring issues
- System improvements"""

    capa_response = model.generate_content(capa_prompt)
    apr.capa_review = capa_response.text
    
    # Generate Equipment Review
    equip_prompt = f"""Create the EQUIPMENT REVIEW section for APR {year}:

EQUIPMENT DATA:
{equipment_data}

Generate a comprehensive equipment review (250-300 words) covering:
- Calibration compliance
- Preventive maintenance status
- Equipment failures/repairs
- Capacity utilization"""

    equip_response = model.generate_content(equip_prompt)
    apr.equipment_review = equip_response.text
    
    # Generate Stability Review
    stab_prompt = f"""Create the STABILITY REVIEW section for APR {year}:

STABILITY DATA:
{stability_data}

Generate a comprehensive stability review (250-300 words) covering:
- Ongoing stability studies
- Results summary by condition
- Any OOS trends
- Shelf-life confirmation"""

    stab_response = model.generate_content(stab_prompt)
    apr.stability_review = stab_response.text
    
    # Generate Trend Analysis
    if direct_from_db:
        metrics_data = f"""BATCH TRENDS: {batch_data[:2000]}
QC TRENDS: {qc_data[:2000]}
COMPLAINT PATTERNS: {complaint_data[:1000]}"""
    else:
        metrics_data = json.dumps(all_metrics, indent=2)
    
    trend_prompt = f"""Create the TREND ANALYSIS section for APR {year}:

ALL ISSUES DETECTED:
{json.dumps(all_issues, indent=2) if all_issues else "None"}

ANNUAL DATA:
{metrics_data}

Generate a comprehensive trend analysis (400-500 words) covering:
- Key trends identified throughout the year
- Seasonal patterns
- Process drifts detected
- Early warning indicators
- Year-over-year comparison insights"""

    trend_response = model.generate_content(trend_prompt)
    apr.trend_analysis = trend_response.text
    
    # Generate Conclusions
    conc_prompt = f"""Create the CONCLUSIONS section for APR {year}:

ANNUAL STATS:
- Total batches: {total_batches}
- Average yield: {avg_yield:.2f}%
- QC Pass Rate: {qc_pass_rate:.1f}%
- Total complaints: {total_complaints}
- Total CAPAs: {total_capas}

Summarize:
- Overall product quality status
- Process control effectiveness
- Regulatory compliance position
- Decision: recommend continued manufacturing (Yes/No with justification)

Keep it professional and suitable for regulatory submission (200-300 words)."""

    conc_response = model.generate_content(conc_prompt)
    apr.conclusions = conc_response.text
    
    # Generate Recommendations
    rec_prompt = f"""Create the RECOMMENDATIONS section for APR {year}:

Based on all the analysis, provide:
1. Priority actions for next year (5-7 items)
2. Process improvement opportunities
3. Monitoring enhancements
4. Resource requirements

Be specific and actionable (300-400 words)."""

    rec_response = model.generate_content(rec_prompt)
    apr.recommendations = rec_response.text
    
    apr.status = ReportStatus.COMPLETED.value
    db.commit()
    db.refresh(apr)
    
    return apr


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_report_hierarchy_status(db: Session, year: int = None) -> Dict[str, Any]:
    """Get the status of all reports in the hierarchy for a given year"""
    
    if year is None:
        year = datetime.now().year
    
    # File reports
    file_reports = db.query(models.FileReport).filter(
        models.FileReport.period_year == year
    ).all()
    
    # Monthly reports
    monthly_reports = db.query(models.MonthlyReport).filter(
        models.MonthlyReport.year == year
    ).all()
    
    # APR
    apr = db.query(models.APRReport).filter(
        models.APRReport.year == year
    ).first()
    
    monthly_status = {i: None for i in range(1, 13)}
    for mr in monthly_reports:
        monthly_status[mr.month] = {
            "id": mr.id,
            "status": mr.status,
            "generated_at": mr.generated_at.isoformat() if mr.generated_at else None
        }
    
    return {
        "year": year,
        "file_reports": {
            "total": len(file_reports),
            "completed": len([fr for fr in file_reports if fr.status == ReportStatus.COMPLETED.value]),
            "pending": len([fr for fr in file_reports if fr.status == ReportStatus.PENDING.value]),
            "failed": len([fr for fr in file_reports if fr.status == ReportStatus.FAILED.value]),
        },
        "monthly_reports": monthly_status,
        "apr": {
            "exists": apr is not None,
            "id": apr.id if apr else None,
            "status": apr.status if apr else None,
            "generated_at": apr.generated_at.isoformat() if apr and apr.generated_at else None
        }
    }


async def regenerate_all_reports(db: Session, year: int) -> Dict[str, Any]:
    """Regenerate all monthly reports and APR for a year"""
    results = {"monthly_reports": [], "apr": None}
    
    # Generate all monthly reports
    for month in range(1, 13):
        try:
            mr = await generate_monthly_report(db, year, month, force_regenerate=True)
            results["monthly_reports"].append({
                "month": month,
                "status": "success",
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
    
    # Generate APR
    try:
        apr = await generate_apr_report(db, year, force_regenerate=True)
        results["apr"] = {"status": "success", "id": apr.id}
    except Exception as e:
        results["apr"] = {"status": "failed", "error": str(e)}
    
    return results
