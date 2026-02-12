from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db import Base


class DataType(str, enum.Enum):
    BATCH = "batch"
    QC = "qc"
    COMPLAINT = "complaint"
    CAPA = "capa"
    EQUIPMENT = "equipment"
    ENVIRONMENTAL = "environmental"
    RAW_MATERIAL = "raw_material"
    STABILITY = "stability"
    BATCH_RELEASE = "batch_release"


class Batch(Base):
    """Extended manufacturing batch records with full CPPs"""

    __tablename__ = "batches"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), unique=True, index=True)
    product_name = Column(String(100))
    product_code = Column(String(50))
    batch_size_kg = Column(Float)
    manufacturing_date = Column(DateTime)
    shift = Column(String(20))
    operator_primary = Column(String(50))
    operator_secondary = Column(String(50))
    # Equipment
    tablet_press_id = Column(String(50))
    granulator_id = Column(String(50))
    dryer_id = Column(String(50))
    blender_id = Column(String(50))
    # Process parameters
    compression_force = Column(Float)
    pre_compression_force = Column(Float)
    turret_speed = Column(Float)
    hardness = Column(Float)
    weight = Column(Float)
    thickness = Column(Float)
    friability = Column(Float)
    # Granulation
    granulation_temp = Column(Float)
    drying_temp_inlet = Column(Float)
    drying_temp_outlet = Column(Float)
    moisture_content = Column(Float)
    # Yield
    yield_percent = Column(Float)
    tablets_theoretical = Column(Integer)
    tablets_actual = Column(Integer)
    # Status
    status = Column(String(20), default="released")
    deviation_id = Column(String(50))
    comments = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class QCResult(Base):
    """Extended QC lab results with full CQAs"""

    __tablename__ = "qc_results"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), index=True)
    sample_id = Column(String(50))
    test_date = Column(DateTime)
    # Identification
    id_result = Column(String(20))
    # Assay
    assay_percent = Column(Float)
    assay_result = Column(String(20))
    # Dissolution
    dissolution_mean = Column(Float)
    dissolution_min = Column(Float)
    dissolution_result = Column(String(20))
    # Content Uniformity
    cu_av = Column(Float)
    cu_result = Column(String(20))
    # Impurities
    impurity_a = Column(Float)
    impurity_total = Column(Float)
    impurity_result = Column(String(20))
    # Physical
    hardness = Column(Float)
    friability = Column(Float)
    disintegration = Column(Float)
    weight_mean = Column(Float)
    # Microbial
    tamc = Column(Integer)
    tymc = Column(Integer)
    microbial_result = Column(String(20))
    # Overall
    overall_result = Column(String(20))
    analyst = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class Complaint(Base):
    """Customer complaints with investigation tracking"""

    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String(50), unique=True, index=True)
    complaint_date = Column(DateTime)
    batch_id = Column(String(50))
    category = Column(String(50))
    description = Column(Text)
    severity = Column(String(20))
    market = Column(String(50))
    reporter_type = Column(String(50))
    investigation_required = Column(String(10))
    root_cause = Column(Text)
    investigation_outcome = Column(Text)
    regulatory_reportable = Column(String(10))
    capa_reference = Column(String(50))
    status = Column(String(20), default="open")
    created_at = Column(DateTime, default=datetime.utcnow)


class CAPA(Base):
    """CAPA records with full tracking"""

    __tablename__ = "capas"
    id = Column(Integer, primary_key=True, index=True)
    capa_id = Column(String(50), unique=True, index=True)
    capa_type = Column(String(30))
    source = Column(String(50))
    source_reference = Column(String(50))
    open_date = Column(DateTime)
    problem_statement = Column(Text)
    problem_category = Column(String(50))
    risk_score = Column(String(20))
    rca_method = Column(String(50))
    root_cause_category = Column(String(100))
    root_cause_description = Column(Text)
    responsible_department = Column(String(50))
    capa_owner = Column(String(50))
    target_date = Column(DateTime)
    actual_completion_date = Column(DateTime)
    days_to_close = Column(Integer)
    status = Column(String(20), default="open")
    effectiveness_verified = Column(String(10))
    num_actions = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class Equipment(Base):
    """Equipment calibration records"""

    __tablename__ = "equipment"
    id = Column(Integer, primary_key=True, index=True)
    calibration_id = Column(String(50), index=True)
    equipment_id = Column(String(50), index=True)
    equipment_name = Column(String(100))
    equipment_type = Column(String(50))
    location = Column(String(50))
    criticality = Column(String(20))
    parameter = Column(String(50))
    scheduled_date = Column(DateTime)
    actual_date = Column(DateTime)
    next_due_date = Column(DateTime)
    as_found_value = Column(Float)
    as_left_value = Column(Float)
    deviation = Column(Float)
    result = Column(String(20))
    out_of_tolerance = Column(String(10))
    calibrated_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class Environmental(Base):
    """Environmental monitoring records"""

    __tablename__ = "environmental"
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(String(50), index=True)
    monitoring_date = Column(DateTime)
    room_code = Column(String(20))
    room_name = Column(String(100))
    room_classification = Column(String(20))
    sampling_point = Column(String(20))
    particles_05um = Column(Integer)
    particles_50um = Column(Integer)
    viable_active_air = Column(Integer)
    temperature = Column(Float)
    humidity = Column(Float)
    diff_pressure = Column(Float)
    overall_result = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class RawMaterial(Base):
    """Raw material receipts"""

    __tablename__ = "raw_materials"
    id = Column(Integer, primary_key=True, index=True)
    grn_number = Column(String(50), index=True)
    material_code = Column(String(50))
    material_name = Column(String(100))
    supplier_id = Column(String(50))
    supplier_name = Column(String(100))
    receipt_date = Column(DateTime)
    quantity = Column(Float)
    unit = Column(String(20))
    coa_received = Column(String(10))
    test_status = Column(String(20))
    disposition = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class Stability(Base):
    """Stability testing data"""

    __tablename__ = "stability"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String(50), index=True)
    batch_id = Column(String(50))
    stability_condition = Column(String(30))
    storage_temp = Column(Integer)
    storage_rh = Column(Integer)
    timepoint_months = Column(Integer)
    test_date = Column(DateTime)
    assay_percent = Column(Float)
    dissolution_percent = Column(Float)
    impurity_total = Column(Float)
    water_content = Column(Float)
    overall_result = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class BatchRelease(Base):
    """Batch release decisions"""

    __tablename__ = "batch_releases"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), index=True)
    qp_id = Column(String(20))
    qp_name = Column(String(100))
    review_start_date = Column(DateTime)
    qc_complete_date = Column(DateTime)
    release_date = Column(DateTime)
    disposition = Column(String(20))
    days_to_release = Column(Integer)
    has_deviation = Column(String(10))
    has_oos = Column(String(10))
    market_destination = Column(String(50))
    yield_percent = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), default="Nouvelle conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = relationship(
        "ChatMessage", back_populates="conversation", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    role = Column(String(20))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    conversation = relationship("Conversation", back_populates="messages")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255))
    data_type = Column(String(50))
    records_count = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    """Saved APR reports history"""

    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    report_type = Column(String(50))  # full_apr, summary, custom
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    content = Column(Text)
    metadata_json = Column(Text)  # JSON string with stats at generation time
    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(String(100), default="system")


class FileReport(Base):
    """Individual reports generated per uploaded CSV file (Level 1)"""

    __tablename__ = "file_reports"
    id = Column(Integer, primary_key=True, index=True)
    uploaded_file_id = Column(Integer, ForeignKey("uploaded_files.id"), index=True)
    filename = Column(String(255))
    data_type = Column(String(50))
    # Period extracted from the data
    period_year = Column(Integer)
    period_month = Column(Integer, nullable=True)  # None for yearly files
    # Report content
    summary = Column(Text)  # AI-generated summary of this file
    key_metrics = Column(Text)  # JSON: extracted KPIs from this file
    anomalies = Column(Text)  # JSON: detected issues/anomalies
    recommendations = Column(Text)  # AI recommendations
    records_analyzed = Column(Integer)
    # Status
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    uploaded_file = relationship("UploadedFile", backref="file_reports")


class MonthlyReport(Base):
    """Monthly aggregated reports (Level 2) - combines multiple FileReports"""

    __tablename__ = "monthly_reports"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, index=True)
    month = Column(Integer, index=True)  # 1-12
    # Content
    executive_summary = Column(Text)
    production_analysis = Column(Text)
    quality_analysis = Column(Text)
    compliance_analysis = Column(Text)
    key_metrics = Column(Text)  # JSON: aggregated metrics
    trends_detected = Column(Text)  # JSON: trends for this month
    issues_summary = Column(Text)  # JSON: issues found
    recommendations = Column(Text)
    # Linked file reports
    file_report_ids = Column(Text)  # JSON array of FileReport IDs used
    # Status
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)


class APRReport(Base):
    """Annual Product Review - synthesized from Monthly Reports (Level 3)"""

    __tablename__ = "apr_reports"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, index=True)
    title = Column(String(255))
    # Full APR sections
    executive_summary = Column(Text)
    production_review = Column(Text)
    quality_review = Column(Text)
    complaints_review = Column(Text)
    capa_review = Column(Text)
    equipment_review = Column(Text)
    stability_review = Column(Text)
    trend_analysis = Column(Text)
    conclusions = Column(Text)
    recommendations = Column(Text)
    # Metadata
    monthly_report_ids = Column(Text)  # JSON array of MonthlyReport IDs
    total_batches = Column(Integer)
    total_complaints = Column(Integer)
    total_capas = Column(Integer)
    overall_yield = Column(Float)
    overall_qc_pass_rate = Column(Float)
    # Status
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
