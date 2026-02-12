import google.generativeai as genai
from app.config import GOOGLE_API_KEY
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models
from datetime import datetime, timedelta
from typing import Optional
import json

genai.configure(api_key=GOOGLE_API_KEY)


def get_data_context(db: Session, start_date: datetime = None, end_date: datetime = None) -> str:
    """Build comprehensive context from all data sources with optional date filtering"""
    
    # Base queries
    batch_query = db.query(models.Batch)
    qc_query = db.query(models.QCResult)
    complaint_query = db.query(models.Complaint)
    capa_query = db.query(models.CAPA)
    equipment_query = db.query(models.Equipment)
    
    # Apply date filters if provided
    if start_date:
        batch_query = batch_query.filter(models.Batch.manufacturing_date >= start_date)
        qc_query = qc_query.filter(models.QCResult.test_date >= start_date)
        complaint_query = complaint_query.filter(models.Complaint.complaint_date >= start_date)
        capa_query = capa_query.filter(models.CAPA.open_date >= start_date)
        equipment_query = equipment_query.filter(models.Equipment.actual_date >= start_date)
    
    if end_date:
        batch_query = batch_query.filter(models.Batch.manufacturing_date <= end_date)
        qc_query = qc_query.filter(models.QCResult.test_date <= end_date)
        complaint_query = complaint_query.filter(models.Complaint.complaint_date <= end_date)
        capa_query = capa_query.filter(models.CAPA.open_date <= end_date)
        equipment_query = equipment_query.filter(models.Equipment.actual_date <= end_date)
    
    batches = batch_query.order_by(models.Batch.manufacturing_date.desc()).limit(50).all()
    qc_results = qc_query.order_by(models.QCResult.test_date.desc()).limit(50).all()
    complaints = complaint_query.all()
    capas = capa_query.all()
    equipment = equipment_query.limit(50).all()

    # Calculate statistics
    total_batches = batch_query.count()
    avg_yield_query = db.query(func.avg(models.Batch.yield_percent))
    avg_hardness_query = db.query(func.avg(models.Batch.hardness))
    
    if start_date:
        avg_yield_query = avg_yield_query.filter(models.Batch.manufacturing_date >= start_date)
        avg_hardness_query = avg_hardness_query.filter(models.Batch.manufacturing_date >= start_date)
    if end_date:
        avg_yield_query = avg_yield_query.filter(models.Batch.manufacturing_date <= end_date)
        avg_hardness_query = avg_hardness_query.filter(models.Batch.manufacturing_date <= end_date)
    
    avg_yield = avg_yield_query.scalar() or 0
    avg_hardness = avg_hardness_query.scalar() or 0

    # Build period string
    period_str = "2020-2025 (6 years of APR data)"
    if start_date and end_date:
        period_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    elif start_date:
        period_str = f"From {start_date.strftime('%Y-%m-%d')}"
    elif end_date:
        period_str = f"Until {end_date.strftime('%Y-%m-%d')}"

    context = f"""
=== PHARMACEUTICAL PLANT DATA - PARACETAMOL 500mg ===
Analysis Period: {period_str}

GLOBAL STATISTICS:
- Total batches produced: {total_batches:,}
- Average yield: {avg_yield:.1f}%
- Average hardness: {avg_hardness:.1f} kp
- Customer complaints: {len(complaints)} ({len([c for c in complaints if c.status == 'open'])} open)
- CAPAs: {len(capas)} ({len([c for c in capas if c.status == 'open'])} open)

RECENT BATCHES (last {len(batches)}):
"""
    for b in batches[:15]:
        date_str = (
            b.manufacturing_date.strftime("%Y-%m-%d") if b.manufacturing_date else "N/A"
        )
        context += f"- {b.batch_id}: {date_str}, Press: {b.tablet_press_id or 'N/A'}, Hardness: {b.hardness or 0:.1f}kp, Yield: {b.yield_percent or 0:.1f}%\n"

    if qc_results:
        context += f"\nRECENT QC RESULTS ({len(qc_results)} tests):\n"
        for qc in qc_results[:15]:
            context += f"- {qc.batch_id}: Assay={qc.assay_percent or 0:.1f}%, Dissolution={qc.dissolution_mean or 0:.1f}%, Result: {qc.overall_result}\n"

    if complaints:
        context += f"\nCUSTOMER COMPLAINTS ({len(complaints)} total):\n"
        open_complaints = [
            c for c in complaints if c.status and c.status.lower() == "open"
        ]
        context += f"   Open: {len(open_complaints)}\n"
        by_category = {}
        for c in complaints:
            cat = c.category or "Other"
            by_category[cat] = by_category.get(cat, 0) + 1
        for cat, count in sorted(by_category.items(), key=lambda x: -x[1])[:5]:
            context += f"   - {cat}: {count}\n"
        by_severity = {}
        for c in complaints:
            sev = c.severity or "Unknown"
            by_severity[sev] = by_severity.get(sev, 0) + 1
        context += f"   By severity: {by_severity}\n"

    if capas:
        context += f"\nCAPAS ({len(capas)} total):\n"
        open_capas = [c for c in capas if c.status and "closed" not in c.status.lower()]
        context += f"   Open: {len(open_capas)}\n"
        by_source = {}
        for c in capas:
            src = c.source or "Other"
            by_source[src] = by_source.get(src, 0) + 1
        for src, count in sorted(by_source.items(), key=lambda x: -x[1])[:5]:
            context += f"   - Source {src}: {count}\n"
        critical = [c for c in capas if c.risk_score == "Critical"]
        context += f"   Critical CAPAs: {len(critical)}\n"

    if equipment:
        context += f"\nEQUIPMENT (recent calibrations):\n"
        failures = [e for e in equipment if e.result == "Fail"]
        context += f"   Calibration failures: {len(failures)}\n"
        by_type = {}
        for e in equipment:
            t = e.equipment_type or "Other"
            by_type[t] = by_type.get(t, 0) + 1
        context += f"   By type: {by_type}\n"

    return context


SYSTEM_PROMPT = """You are NYOS, an AI assistant expert in pharmaceutical quality and APR (Annual Product Review) analysis.
You analyze production data for Paracetamol 500mg tablets over a 6-year period (2020-2025).

Your role:
1. Detect trends and drifts in production data
2. Identify anomalies, weak signals, and potential issues
3. Analyze correlations between equipment, batches, and quality results
4. Clearly summarize the plant's quality situation
5. Recommend corrective and preventive actions

Hidden scenarios to detect:
- 2020: COVID-19 impact on production
- 2021: Press-A degradation (Sept-Nov)
- 2022: Excipient supplier issue MCC (June)
- 2023: Analytical method transition (Q2)
- 2024: Seasonal temperature effect (Jul-Aug)
- 2025: Press-B drift + New API supplier (Nov)

Rules:
- Be precise with numerical data
- Flag any potential issues
- Respond in English
- Use bullet points and markdown formatting
- Cite specific batches, dates, and values when relevant
"""


async def chat_with_gemini(message: str, db: Session) -> str:
    try:
        context = get_data_context(db)
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        full_prompt = f"""{SYSTEM_PROMPT}

DATA CONTEXT:
{context}

USER QUESTION:
{message}

RESPONSE:"""

        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Gemini connection error: {str(e)}. Check your API key."


async def analyze_trends(db: Session, parameter: str = "hardness", days: int = 30):
    batches = db.query(models.Batch).order_by(models.Batch.manufacturing_date).all()

    if not batches:
        return {"error": "Not enough data", "dates": [], "values": []}

    max_date = max(b.manufacturing_date for b in batches if b.manufacturing_date)
    cutoff = max_date - timedelta(days=days)

    filtered = [
        b for b in batches if b.manufacturing_date and b.manufacturing_date >= cutoff
    ]

    if len(filtered) < 2:
        return {
            "error": "Not enough data for this period",
            "dates": [],
            "values": [],
        }

    values = [
        getattr(b, parameter, 0)
        for b in filtered
        if getattr(b, parameter, None) is not None
    ]
    dates = [
        b.manufacturing_date.strftime("%Y-%m-%d")
        for b in filtered
        if getattr(b, parameter, None) is not None
    ]

    if len(values) < 2:
        return {"error": "Not enough data", "dates": [], "values": []}

    trend = "stable"
    alert = False
    if len(values) >= 5:
        mid = len(values) // 2
        first_avg = sum(values[:mid]) / mid
        last_avg = sum(values[mid:]) / (len(values) - mid)
        change = ((last_avg - first_avg) / first_avg) * 100 if first_avg else 0

        if change > 5:
            trend = "up"
            alert = True
        elif change < -5:
            trend = "down"
            alert = True

    return {
        "dates": dates,
        "values": values,
        "parameter": parameter,
        "trend_direction": trend,
        "alert": alert,
        "average": round(sum(values) / len(values), 2) if values else 0,
        "min": round(min(values), 2) if values else 0,
        "max": round(max(values), 2) if values else 0,
        "count": len(values),
    }


def get_full_stats(db: Session, start_date: datetime = None, end_date: datetime = None) -> dict:
    from sqlalchemy import func

    # Base queries with optional date filters
    batch_query = db.query(models.Batch)
    qc_query = db.query(models.QCResult)
    complaint_query = db.query(models.Complaint)
    capa_query = db.query(models.CAPA)
    equipment_query = db.query(models.Equipment)
    
    if start_date:
        batch_query = batch_query.filter(models.Batch.manufacturing_date >= start_date)
        qc_query = qc_query.filter(models.QCResult.test_date >= start_date)
        complaint_query = complaint_query.filter(models.Complaint.complaint_date >= start_date)
        capa_query = capa_query.filter(models.CAPA.open_date >= start_date)
        equipment_query = equipment_query.filter(models.Equipment.actual_date >= start_date)
    
    if end_date:
        batch_query = batch_query.filter(models.Batch.manufacturing_date <= end_date)
        qc_query = qc_query.filter(models.QCResult.test_date <= end_date)
        complaint_query = complaint_query.filter(models.Complaint.complaint_date <= end_date)
        capa_query = capa_query.filter(models.CAPA.open_date <= end_date)
        equipment_query = equipment_query.filter(models.Equipment.actual_date <= end_date)

    batches = batch_query.all()
    qc_results = qc_query.all()
    complaints = complaint_query.all()
    capas = capa_query.all()
    equipment = equipment_query.all()

    # Calculate QC pass rate based on actual pharmaceutical specifications
    # Specs: Assay 95-105%, Dissolution >80%
    qc_pass_count = len(
        [
            q
            for q in qc_results
            if q.assay_percent
            and q.dissolution_mean
            and 95 <= q.assay_percent <= 105
            and q.dissolution_mean >= 80
        ]
    )

    stats = {
        "total_batches": len(batches),
        "avg_hardness": (
            round(
                sum(b.hardness for b in batches if b.hardness)
                / max(len([b for b in batches if b.hardness]), 1),
                2,
            )
            if batches
            else 0
        ),
        "avg_yield": (
            round(
                sum(b.yield_percent for b in batches if b.yield_percent)
                / max(len([b for b in batches if b.yield_percent]), 1),
                2,
            )
            if batches
            else 0
        ),
        "machines": {},
        "qc_pass_rate": (
            round(qc_pass_count / max(len(qc_results), 1) * 100, 1) if qc_results else 0
        ),
        "qc_total": len(qc_results),
        "qc_failed": len(qc_results) - qc_pass_count,
        "complaints_by_category": {},
        "complaints_total": len(complaints),
        "complaints_open": len(
            [c for c in complaints if c.status and c.status.lower() == "open"]
        ),
        "complaints_closed": len(
            [c for c in complaints if c.status and c.status.lower() == "closed"]
        ),
        "capas_total": len(capas),
        "capas_open": len(
            [c for c in capas if c.status and "closed" not in c.status.lower()]
        ),
        "capas_closed": len(
            [c for c in capas if c.status and "closed" in c.status.lower()]
        ),
        "equipment_due": len([e for e in equipment if e.result == "Fail"]),
        "equipment_total": len(equipment),
    }

    for b in batches:
        machine = b.tablet_press_id or "Unknown"
        if machine not in stats["machines"]:
            stats["machines"][machine] = {
                "count": 0,
                "hardness_sum": 0,
                "yield_sum": 0,
            }
        stats["machines"][machine]["count"] += 1
        stats["machines"][machine]["hardness_sum"] += b.hardness or 0
        stats["machines"][machine]["yield_sum"] += b.yield_percent or 0

    for m, data in stats["machines"].items():
        if data["count"] > 0:
            data["avg_hardness"] = round(data["hardness_sum"] / data["count"], 2)
            data["avg_yield"] = round(data["yield_sum"] / data["count"], 2)

    for c in complaints:
        cat = c.category or "Unknown"
        stats["complaints_by_category"][cat] = (
            stats["complaints_by_category"].get(cat, 0) + 1
        )

    return stats


async def generate_summary_stream(db: Session):
    try:
        context = get_data_context(db)
        stats = get_full_stats(db)
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        prompt = f"""{SYSTEM_PROMPT}

DATA CONTEXT:
{context}

STATISTICS:
- Total batches: {stats['total_batches']}
- Average hardness: {stats['avg_hardness']}N
- Average yield: {stats['avg_yield']}%
- QC compliance rate: {stats['qc_pass_rate']}%
- Open complaints: {stats['complaints_open']}
- Open CAPAs: {stats['capas_open']}
- Equipment requiring calibration: {stats['equipment_due']}
- Complaints by category: {stats['complaints_by_category']}
- Performance by machine: {stats['machines']}

Generate a detailed executive summary of the plant status.
Structure your response with:
1. **Overall Status** - (Good / Warning / Critical)
2. **Production Performance** - yield, volumes
3. **Quality** - QC results, trends
4. **Issues Detected** - complaints, CAPAs, anomalies
5. **Recommendations** - priority actions

Use bullet points and **bold** text for important points.

SUMMARY:"""

        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield f"data: {json.dumps({'text': chunk.text})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


async def generate_report(db: Session, start_date: datetime = None, end_date: datetime = None, title: str = None) -> dict:
    """Generate APR report with optional date filtering and return both report and metadata"""
    try:
        context = get_data_context(db, start_date, end_date)
        stats = get_full_stats(db, start_date, end_date)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Build period string for the report
        if start_date and end_date:
            period_str = f"{start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
            year_str = f"{start_date.year}" if start_date.year == end_date.year else f"{start_date.year}-{end_date.year}"
            doc_id = f"APR-PARA-500mg-{start_date.year}-{end_date.year}-V1.0"
        else:
            period_str = "January 1, 2025 to January 31, 2026"
            year_str = "2025"
            doc_id = "APR-PARA-500mg-2025-2026-V1.0"

        current_date = datetime.now().strftime("%B %d, %Y")
        
        prompt = f"""You are a senior pharmaceutical quality expert at NYOS PharmaCo Global. Generate a COMPLETE and PROFESSIONAL Annual Product Review (APR) report.

IMPORTANT INSTRUCTIONS:
1. DO NOT use placeholder text like "[Plant Name]" - use ACTUAL data provided
2. Use specific numbers and statistics from the data provided
3. Format as a professional regulatory document
4. Include actual analysis and insights, not generic statements

ACTUAL PLANT DATA:
Manufacturing Site: NYOS PharmaCo Global, Dublin Facility
Product: Paracetamol 500mg Tablets (PARA-500-TAB)
Document ID: {doc_id}
Analysis Period: {period_str}
Date Prepared: {current_date}
Prepared By: Quality Assurance Department

ACTUAL STATISTICS FROM DATABASE:
- Total batches manufactured: {stats['total_batches']}
- Average batch hardness: {stats['avg_hardness']}N
- Average batch yield: {stats['avg_yield']}%
- QC pass rate (annual): {stats['qc_pass_rate']}%
- Total complaints received: {stats['complaints_open'] + stats.get('complaints_closed', 0)} ({stats['complaints_open']} still open)
- Total CAPAs: {stats['capas_open'] + stats.get('capas_closed', 0)} ({stats['capas_open']} still open)
- Equipment requiring calibration: {stats['equipment_due']}
- Complaints breakdown: {stats['complaints_by_category']}
- Machine performance data: {stats['machines']}

RAW DATA CONTEXT:
{context}

Generate the report with this EXACT structure. Fill all sections with REAL data and analysis:

---

# ANNUAL PRODUCT REVIEW REPORT (APR)

**Paracetamol 500mg Tablets**

**Period:** {period_str}

---

**Document ID:** {doc_id}
**Product:** Paracetamol 500mg Tablets (PARA-500-TAB)
**Manufacturing Site:** NYOS PharmaCo Global, Dublin Facility
**Analysis Period:** {period_str}
**Date Prepared:** {current_date}
**Prepared By:** Quality Assurance Department

---

## 1. EXECUTIVE SUMMARY

Write a comprehensive executive summary including:
- Total batches produced ({stats['total_batches']}) and production volume assessment
- Overall yield performance ({stats['avg_yield']}%)
- Quality metrics summary (QC pass rate: {stats['qc_pass_rate']}%)
- Average hardness ({stats['avg_hardness']}N)
- Highlight any critical trends or issues found in the data
- Key conclusions about product quality and process control

If QC pass rate is below 99%, flag this as a concern.
If there are open complaints or CAPAs, mention the backlog.

## 2. PRODUCTION PERFORMANCE

### 2.1 Volume Summary
- Provide actual batch counts from data
- Calculate approximate tablet output (batches × ~100,000 tablets)
- Assess production consistency

### 2.2 Yield Analysis
- Average yield: {stats['avg_yield']}%
- Analyze yield trends by machine if available
- Identify any batches with yield below 95%

### 2.3 Equipment Utilization
Analyze the machine performance data: {stats['machines']}
- Compare performance across tablet presses
- Identify best and worst performing equipment

## 3. QUALITY CONTROL RESULTS

### 3.1 In-Process Controls
- Tablet hardness: {stats['avg_hardness']}N (target: 10-15 kp)
- Friability results
- Weight variation

### 3.2 Finished Product Testing
- Assay results (target: 95-105%)
- Dissolution performance
- Content uniformity
- QC pass rate: {stats['qc_pass_rate']}%

Calculate how many batches failed QC based on the pass rate.

### 3.3 Out-of-Specification (OOS) Investigations
List any OOS events and their root causes.

## 4. CUSTOMER COMPLAINTS

### 4.1 Complaint Summary
- Total complaints: {stats['complaints_open'] + stats.get('complaints_closed', 0)}
- Open complaints: {stats['complaints_open']}
- By category: {stats['complaints_by_category']}

### 4.2 Complaint Analysis
Analyze the complaint categories and identify the most frequent issue.
Calculate complaint rate per batch if possible.

### 4.3 Trending
Compare to industry standards (~0.5-1% complaint rate).

## 5. CAPA MANAGEMENT

### 5.1 CAPA Summary
- Total CAPAs: {stats['capas_open'] + stats.get('capas_closed', 0)}
- Open CAPAs: {stats['capas_open']}

### 5.2 CAPA Sources
Analyze CAPA origins (deviations, complaints, audits).

### 5.3 CAPA Effectiveness
Comment on closure rate and effectiveness verification.

## 6. EQUIPMENT STATUS

### 6.1 Calibration Status
- Equipment requiring calibration: {stats['equipment_due']}
- Flag overdue calibrations as quality risks

### 6.2 Preventive Maintenance
Comment on PM compliance.

## 7. TREND ANALYSIS

### 7.1 Process Capability Trends
Analyze trends in yield, hardness, dissolution over time.

### 7.2 Identified Concerns
List any drifts or weak signals found in the data.

### 7.3 Comparison to Previous Period
If relevant data available, compare year-over-year.

## 8. CONCLUSIONS

Summarize overall product quality status.
State whether the process remains in a validated state.

## 9. RECOMMENDATIONS

List specific, actionable recommendations:
1. If complaints are high - recommend investigation
2. If CAPAs are open - recommend closure targets  
3. If equipment overdue - recommend immediate scheduling
4. Process improvements based on data analysis

---

**Report Approval:**

Prepared by: Quality Assurance Department
Date: {current_date}

Reviewed by: _____________________
Date: _________

Approved by: _____________________
Date: _________

---

Remember: Use ACTUAL numbers from the statistics. Do not use placeholder text. Be specific and data-driven."""

        response = model.generate_content(prompt)
        report_content = response.text
        
        # Return both report and metadata
        return {
            "report": report_content,
            "metadata": {
                "title": title or f"APR Report - Paracetamol 500mg - {year_str}",
                "period_start": start_date.isoformat() if start_date else None,
                "period_end": end_date.isoformat() if end_date else None,
                "stats": stats,
                "generated_at": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {"report": f"Error generating report: {str(e)}", "metadata": None}
