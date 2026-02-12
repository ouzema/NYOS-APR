from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app import models
from app.schemas import DashboardStats, UploadResponse
from app.services.gemini_service import analyze_trends
from app.services.report_service import generate_file_report
from datetime import datetime, timedelta
import pandas as pd
import io

router = APIRouter(prefix="/data", tags=["data"])


def safe_float(val, default=0.0):
    """Safely convert to float"""
    try:
        if pd.isna(val):
            return default
        return float(val)
    except:
        return default


def safe_int(val, default=0):
    """Safely convert to int"""
    try:
        if pd.isna(val):
            return default
        return int(float(val))
    except:
        return default


def safe_str(val, default=""):
    """Safely convert to string"""
    if pd.isna(val):
        return default
    return str(val)


def safe_date(val):
    """Safely convert to datetime"""
    try:
        if pd.isna(val):
            return datetime.utcnow()
        return pd.to_datetime(val)
    except:
        return datetime.utcnow()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(db: Session = Depends(get_db)):
    total_batches = db.query(models.Batch).count()

    # Get date range from actual data
    max_date = db.query(func.max(models.Batch.manufacturing_date)).scalar()
    if max_date:
        month_ago = max_date - timedelta(days=30)
        batches_month = (
            db.query(models.Batch)
            .filter(models.Batch.manufacturing_date >= month_ago)
            .count()
        )
    else:
        batches_month = 0

    avg_yield = db.query(func.avg(models.Batch.yield_percent)).scalar() or 0

    # Case-insensitive status queries for complaints (Open, open, OPEN)
    complaints_open = (
        db.query(models.Complaint)
        .filter(func.lower(models.Complaint.status) == "open")
        .count()
    )

    # CAPAs: count all non-closed statuses as "open"
    capas_open = (
        db.query(models.CAPA)
        .filter(~func.lower(models.CAPA.status).like("%closed%"))
        .count()
    )

    # Equipment due for calibration
    equipment_due = (
        db.query(models.Equipment).filter(models.Equipment.result == "Fail").count()
    )

    return DashboardStats(
        total_batches=total_batches,
        batches_this_month=batches_month,
        avg_yield=round(avg_yield, 2),
        complaints_open=complaints_open,
        capas_open=capas_open,
        equipment_due=equipment_due,
    )


@router.get("/batches")
async def get_batches(db: Session = Depends(get_db), limit: int = 100, offset: int = 0):
    batches = (
        db.query(models.Batch)
        .order_by(models.Batch.manufacturing_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return batches


@router.get("/trends/{parameter}")
async def get_trends(parameter: str, days: int = 30, db: Session = Depends(get_db)):
    valid_params = [
        "hardness",
        "yield_percent",
        "compression_force",
        "weight",
        "thickness",
        "assay_percent",
        "dissolution_mean",
    ]
    if parameter not in valid_params:
        raise HTTPException(
            status_code=400, detail=f"Paramètre invalide. Valides: {valid_params}"
        )
    return await analyze_trends(db, parameter, days)


@router.get("/complaints")
async def get_complaints(db: Session = Depends(get_db), status: str = None):
    query = db.query(models.Complaint)
    if status:
        query = query.filter(models.Complaint.status == status)
    return query.order_by(models.Complaint.complaint_date.desc()).all()


@router.get("/capas")
async def get_capas(db: Session = Depends(get_db), status: str = None):
    query = db.query(models.CAPA)
    if status:
        query = query.filter(models.CAPA.status == status)
    return query.order_by(models.CAPA.open_date.desc()).all()


@router.get("/equipment")
async def get_equipment(db: Session = Depends(get_db)):
    return db.query(models.Equipment).order_by(models.Equipment.next_due_date).all()


@router.get("/environmental")
async def get_environmental(db: Session = Depends(get_db), limit: int = 100):
    return (
        db.query(models.Environmental)
        .order_by(models.Environmental.monitoring_date.desc())
        .limit(limit)
        .all()
    )


@router.get("/stability")
async def get_stability(db: Session = Depends(get_db)):
    return (
        db.query(models.Stability)
        .order_by(models.Stability.test_date.desc())
        .limit(500)
        .all()
    )


@router.get("/raw-materials")
async def get_raw_materials(db: Session = Depends(get_db), limit: int = 100):
    return (
        db.query(models.RawMaterial)
        .order_by(models.RawMaterial.receipt_date.desc())
        .limit(limit)
        .all()
    )


@router.get("/batch-releases")
async def get_batch_releases(db: Session = Depends(get_db), limit: int = 100):
    return (
        db.query(models.BatchRelease)
        .order_by(models.BatchRelease.release_date.desc())
        .limit(limit)
        .all()
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_data(
    file: UploadFile = File(...),
    data_type: str = "batch",
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    generate_report: bool = True,  # Auto-generate file report after upload
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400, detail="Seuls les fichiers CSV sont acceptés"
        )

    contents = await file.read()
    # Store contents for report generation later
    file_contents = contents
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    records_count = 0

    if data_type == "batch":
        for _, row in df.iterrows():
            batch_id = safe_str(row.get("batch_id"), f"BATCH-{records_count}")
            existing = (
                db.query(models.Batch).filter(models.Batch.batch_id == batch_id).first()
            )

            # Handle hardness conversion: tablet_hardness_n is in Newtons, convert to kp (1 kp = 9.81 N)
            hardness_val = row.get("tablet_hardness_n")
            if pd.notna(hardness_val):
                hardness = safe_float(hardness_val) / 9.81  # Convert N to kp
            else:
                hardness = safe_float(
                    row.get("ipc_hardness_mean", row.get("hardness", 0))
                )

            data = {
                "batch_id": batch_id,
                "product_name": safe_str(row.get("product_name"), "Paracetamol 500mg"),
                "product_code": safe_str(row.get("product_code")),
                "batch_size_kg": safe_float(row.get("batch_size_kg")),
                "manufacturing_date": safe_date(row.get("manufacturing_date")),
                "shift": safe_str(row.get("shift")),
                "operator_primary": safe_str(row.get("operator_primary")),
                "operator_secondary": safe_str(row.get("operator_secondary")),
                "tablet_press_id": safe_str(row.get("tablet_press_id")),
                "granulator_id": safe_str(row.get("granulator_id")),
                "dryer_id": safe_str(row.get("dryer_id")),
                "blender_id": safe_str(row.get("blender_id")),
                # Compression forces
                "compression_force": safe_float(
                    row.get(
                        "compression_force_main_kn",
                        row.get(
                            "main_compression_force_kn", row.get("compression_force", 0)
                        ),
                    )
                ),
                "pre_compression_force": safe_float(
                    row.get(
                        "compression_force_pre_kn",
                        row.get("pre_compression_force_kn", 0),
                    )
                ),
                "turret_speed": safe_float(row.get("turret_speed_rpm")),
                # Hardness (converted from N to kp)
                "hardness": hardness,
                # Weight in mg
                "weight": safe_float(
                    row.get(
                        "tablet_weight_mg",
                        row.get("ipc_weight_mean", row.get("weight", 0)),
                    )
                ),
                # Thickness in mm
                "thickness": safe_float(
                    row.get(
                        "tablet_thickness_mm",
                        row.get("ipc_thickness_mean", row.get("thickness", 0)),
                    )
                ),
                # Friability
                "friability": safe_float(
                    row.get("friability_percent", row.get("ipc_friability_percent", 0))
                ),
                "granulation_temp": safe_float(row.get("granulation_temperature_c")),
                "drying_temp_inlet": safe_float(row.get("inlet_air_temp_c")),
                "drying_temp_outlet": safe_float(row.get("outlet_air_temp_c")),
                "moisture_content": safe_float(
                    row.get("final_moisture_content_percent")
                ),
                "yield_percent": safe_float(
                    row.get(
                        "yield_percent",
                        row.get("actual_yield_pct", row.get("yield_percentage", 98)),
                    )
                ),
                "tablets_theoretical": safe_int(
                    row.get("theoretical_yield_tablets", row.get("tablets_theoretical"))
                ),
                "tablets_actual": safe_int(
                    row.get("actual_yield_tablets", row.get("tablets_actual"))
                ),
                "status": safe_str(row.get("status"), "released"),
                "deviation_id": safe_str(row.get("deviation_id")),
                "comments": safe_str(row.get("comments")),
            }

            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                db.add(models.Batch(**data))
            records_count += 1

    elif data_type == "qc":
        for _, row in df.iterrows():
            batch_id = safe_str(row.get("batch_id"))
            sample_id = safe_str(row.get("sample_id"), f"QC-{records_count}")

            # Convert hardness from Newton to kp if needed
            hardness_val = safe_float(
                row.get(
                    "hardness_mean_n", row.get("hardness_kp", row.get("hardness_mean"))
                )
            )
            if hardness_val > 50:  # Likely in Newton, convert to kp
                hardness_val = hardness_val / 9.81

            # Calculate dissolution mean from vessel values if not provided directly
            dissolution_mean_val = safe_float(
                row.get("dissolution_30min_mean", row.get("dissolution_mean"))
            )
            if dissolution_mean_val == 0:
                # Try to calculate from vessel values
                vessel_vals = []
                for i in range(1, 7):
                    v = safe_float(row.get(f"dissolution_vessel_{i}"))
                    if v > 0:
                        vessel_vals.append(v)
                if vessel_vals:
                    dissolution_mean_val = sum(vessel_vals) / len(vessel_vals)

            qc = models.QCResult(
                batch_id=batch_id,
                sample_id=sample_id,
                test_date=safe_date(row.get("test_date", row.get("testing_date"))),
                id_result=safe_str(row.get("id_ir_result", row.get("id_hplc_result"))),
                assay_percent=safe_float(
                    row.get("assay_percent", row.get("assay_mean"))
                ),
                assay_result=safe_str(row.get("assay_result")),
                dissolution_mean=dissolution_mean_val,
                dissolution_min=safe_float(
                    row.get("dissolution_30min_min", row.get("dissolution_min"))
                ),
                dissolution_result=safe_str(row.get("dissolution_result")),
                cu_av=safe_float(row.get("cu_acceptance_value", row.get("cu_av"))),
                cu_result=safe_str(row.get("cu_result")),
                impurity_a=safe_float(row.get("impurity_a_percent")),
                impurity_total=safe_float(row.get("total_impurities_percent")),
                impurity_result=safe_str(
                    row.get("impurities_result", row.get("impurity_result"))
                ),
                hardness=hardness_val,
                friability=safe_float(row.get("friability_percent")),
                disintegration=safe_float(
                    row.get("disintegration_max_min", row.get("disintegration_min"))
                ),
                weight_mean=safe_float(row.get("weight_mean_mg")),
                tamc=safe_int(row.get("tamc_cfu_g")),
                tymc=safe_int(row.get("tymc_cfu_g")),
                microbial_result=safe_str(
                    row.get("micro_result", row.get("microbial_result"))
                ),
                overall_result=safe_str(row.get("overall_result"), "Pass"),
                analyst=safe_str(row.get("analyst_chemical")),
            )
            db.add(qc)
            records_count += 1

    elif data_type == "complaint":
        for _, row in df.iterrows():
            complaint_id = safe_str(row.get("complaint_id"), f"CMP-{records_count}")
            existing = (
                db.query(models.Complaint)
                .filter(models.Complaint.complaint_id == complaint_id)
                .first()
            )

            data = {
                "complaint_id": complaint_id,
                "complaint_date": safe_date(row.get("complaint_date", row.get("date"))),
                "batch_id": safe_str(row.get("batch_id")),
                "category": safe_str(row.get("category")),
                "description": safe_str(row.get("description")),
                "severity": safe_str(row.get("severity"), "low"),
                "market": safe_str(row.get("market")),
                "reporter_type": safe_str(row.get("reporter_type")),
                "investigation_required": safe_str(row.get("investigation_required")),
                "root_cause": safe_str(row.get("root_cause")),
                "investigation_outcome": safe_str(row.get("investigation_outcome")),
                "regulatory_reportable": safe_str(row.get("regulatory_reportable")),
                "capa_reference": safe_str(row.get("capa_reference")),
                "status": safe_str(
                    row.get("complaint_status", row.get("status")), "open"
                ),
            }

            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                db.add(models.Complaint(**data))
            records_count += 1

    elif data_type == "capa":
        for _, row in df.iterrows():
            capa_id = safe_str(row.get("capa_id"), f"CAPA-{records_count}")
            existing = (
                db.query(models.CAPA).filter(models.CAPA.capa_id == capa_id).first()
            )

            data = {
                "capa_id": capa_id,
                "capa_type": safe_str(row.get("capa_type", row.get("type"))),
                "source": safe_str(row.get("source")),
                "source_reference": safe_str(row.get("source_reference")),
                "open_date": safe_date(
                    row.get("open_date", row.get("date", row.get("initiation_date")))
                ),
                "problem_statement": safe_str(row.get("problem_statement")),
                "problem_category": safe_str(row.get("problem_category")),
                "risk_score": safe_str(row.get("risk_score")),
                "rca_method": safe_str(row.get("rca_method")),
                "root_cause_category": safe_str(row.get("root_cause_category")),
                "root_cause_description": safe_str(
                    row.get("root_cause_description", row.get("root_cause"))
                ),
                "responsible_department": safe_str(row.get("responsible_department")),
                "capa_owner": safe_str(row.get("capa_owner")),
                "target_date": (
                    safe_date(row.get("target_date"))
                    if pd.notna(row.get("target_date"))
                    else None
                ),
                "actual_completion_date": (
                    safe_date(row.get("actual_completion_date"))
                    if pd.notna(row.get("actual_completion_date"))
                    else None
                ),
                "days_to_close": safe_int(row.get("days_to_close")),
                "status": safe_str(row.get("status"), "open"),
                "effectiveness_verified": safe_str(row.get("effectiveness_verified")),
                "num_actions": safe_int(row.get("num_actions")),
            }

            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                db.add(models.CAPA(**data))
            records_count += 1

    elif data_type == "equipment":
        for _, row in df.iterrows():
            cal_id = safe_str(row.get("calibration_id"), f"CAL-{records_count}")

            equipment = models.Equipment(
                calibration_id=cal_id,
                equipment_id=safe_str(row.get("equipment_id")),
                equipment_name=safe_str(row.get("equipment_name", row.get("name"))),
                equipment_type=safe_str(row.get("equipment_type")),
                location=safe_str(row.get("location")),
                criticality=safe_str(row.get("criticality")),
                parameter=safe_str(row.get("parameter")),
                scheduled_date=safe_date(row.get("scheduled_date")),
                actual_date=safe_date(
                    row.get("actual_date", row.get("calibration_date"))
                ),
                next_due_date=safe_date(
                    row.get("next_due_date", row.get("next_calibration"))
                ),
                as_found_value=safe_float(row.get("as_found_value")),
                as_left_value=safe_float(row.get("as_left_value")),
                deviation=safe_float(row.get("deviation")),
                result=safe_str(row.get("result", row.get("status")), "Pass"),
                out_of_tolerance=safe_str(row.get("out_of_tolerance")),
                calibrated_by=safe_str(row.get("calibrated_by")),
            )
            db.add(equipment)
            records_count += 1

    elif data_type == "environmental":
        for _, row in df.iterrows():
            env = models.Environmental(
                record_id=safe_str(row.get("record_id"), f"EM-{records_count}"),
                monitoring_date=safe_date(row.get("monitoring_date")),
                room_code=safe_str(row.get("room_code")),
                room_name=safe_str(row.get("room_name")),
                room_classification=safe_str(row.get("room_classification")),
                sampling_point=safe_str(row.get("sampling_point")),
                particles_05um=safe_int(row.get("particles_05um_per_m3")),
                particles_50um=safe_int(row.get("particles_50um_per_m3")),
                viable_active_air=safe_int(row.get("viable_active_air_cfu_m3")),
                temperature=safe_float(row.get("temperature_c")),
                humidity=safe_float(row.get("humidity_percent_rh")),
                diff_pressure=safe_float(row.get("diff_pressure_pa")),
                overall_result=safe_str(row.get("overall_result")),
            )
            db.add(env)
            records_count += 1

    elif data_type == "stability":
        for _, row in df.iterrows():
            stab = models.Stability(
                study_id=safe_str(row.get("study_id"), f"STAB-{records_count}"),
                batch_id=safe_str(row.get("batch_id")),
                stability_condition=safe_str(row.get("stability_condition")),
                storage_temp=safe_int(row.get("storage_temp_c")),
                storage_rh=safe_int(row.get("storage_rh_percent")),
                timepoint_months=safe_int(row.get("timepoint_months")),
                test_date=safe_date(row.get("test_date")),
                assay_percent=safe_float(row.get("assay_percent")),
                dissolution_percent=safe_float(row.get("dissolution_30min_percent")),
                impurity_total=safe_float(row.get("total_impurities_percent")),
                water_content=safe_float(row.get("water_content_percent")),
                overall_result=safe_str(row.get("overall_result")),
            )
            db.add(stab)
            records_count += 1

    elif data_type == "raw_material":
        for _, row in df.iterrows():
            rm = models.RawMaterial(
                grn_number=safe_str(row.get("grn_number"), f"GRN-{records_count}"),
                material_code=safe_str(row.get("material_code")),
                material_name=safe_str(row.get("material_name")),
                supplier_id=safe_str(row.get("supplier_id")),
                supplier_name=safe_str(row.get("supplier_name")),
                receipt_date=safe_date(row.get("receipt_date")),
                quantity=safe_float(row.get("quantity_received")),
                unit=safe_str(row.get("unit")),
                coa_received=safe_str(row.get("coa_received")),
                test_status=safe_str(row.get("test_status")),
                disposition=safe_str(row.get("disposition")),
            )
            db.add(rm)
            records_count += 1

    elif data_type == "batch_release":
        for _, row in df.iterrows():
            br = models.BatchRelease(
                batch_id=safe_str(row.get("batch_id")),
                qp_id=safe_str(row.get("qp_id")),
                qp_name=safe_str(row.get("qp_name")),
                review_start_date=safe_date(row.get("review_start_date")),
                qc_complete_date=safe_date(row.get("qc_complete_date")),
                release_date=(
                    safe_date(row.get("release_date"))
                    if pd.notna(row.get("release_date"))
                    else None
                ),
                disposition=safe_str(row.get("disposition")),
                days_to_release=safe_int(row.get("days_to_release")),
                has_deviation=safe_str(row.get("has_deviation")),
                has_oos=safe_str(row.get("has_oos")),
                market_destination=safe_str(row.get("market_destination")),
                yield_percent=safe_float(row.get("actual_yield_pct")),
            )
            db.add(br)
            records_count += 1

    else:
        raise HTTPException(
            status_code=400, detail=f"Type de données inconnu: {data_type}"
        )

    upload_record = models.UploadedFile(
        filename=file.filename,
        data_type=data_type,
        records_count=records_count,
    )
    db.add(upload_record)
    db.commit()
    db.refresh(upload_record)  # Get the ID
    
    # Trigger file report generation in background
    if generate_report and background_tasks:
        background_tasks.add_task(
            trigger_file_report_generation,
            file_contents,
            file.filename,
            data_type,
            upload_record.id
        )

    return UploadResponse(
        filename=file.filename,
        records_imported=records_count,
        data_type=data_type,
    )


async def trigger_file_report_generation(
    file_contents: bytes,
    filename: str,
    data_type: str,
    uploaded_file_id: int
):
    """Background task to generate file report after upload"""
    from app.db import SessionLocal
    db = SessionLocal()
    try:
        await generate_file_report(
            db, 
            file_contents, 
            filename, 
            data_type, 
            uploaded_file_id
        )
    except Exception as e:
        print(f"Error generating file report for {filename}: {e}")
    finally:
        db.close()


@router.get("/uploads")
async def get_uploads(db: Session = Depends(get_db)):
    return (
        db.query(models.UploadedFile)
        .order_by(models.UploadedFile.uploaded_at.desc())
        .all()
    )


@router.get("/stats/summary")
async def get_summary_stats(db: Session = Depends(get_db)):
    """Get comprehensive statistics for AI analysis"""
    return {
        "batches": {
            "total": db.query(models.Batch).count(),
            "avg_yield": db.query(func.avg(models.Batch.yield_percent)).scalar() or 0,
            "avg_hardness": db.query(func.avg(models.Batch.hardness)).scalar() or 0,
        },
        "qc": {
            "total_tests": db.query(models.QCResult).count(),
            "pass_rate": db.query(models.QCResult)
            .filter(models.QCResult.overall_result == "Pass")
            .count()
            / max(db.query(models.QCResult).count(), 1)
            * 100,
        },
        "complaints": {
            "total": db.query(models.Complaint).count(),
            "open": db.query(models.Complaint)
            .filter(models.Complaint.status == "open")
            .count(),
        },
        "capas": {
            "total": db.query(models.CAPA).count(),
            "open": db.query(models.CAPA).filter(models.CAPA.status == "open").count(),
        },
        "equipment": {
            "calibrations": db.query(models.Equipment).count(),
            "failures": db.query(models.Equipment)
            .filter(models.Equipment.result == "Fail")
            .count(),
        },
        "stability": {
            "studies": db.query(
                func.count(func.distinct(models.Stability.study_id))
            ).scalar()
            or 0,
        },
    }
