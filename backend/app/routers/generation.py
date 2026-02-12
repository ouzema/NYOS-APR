"""
NYOS APR - Data Generation API Router
======================================
API endpoints for generating and downloading synthetic pharmaceutical data.

Endpoints:
- POST /generate/month - Generate data for a specific month
- POST /generate/year - Generate data for a specific year  
- POST /generate/custom - Generate data for a custom date range
- GET /generate/download/{filename} - Download generated files
- GET /generate/data-types - List available data types

Author: NYOS APR Team
Date: February 2026
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta, time
from io import BytesIO
import asyncio

from app.services.data_generation_service import (
    PharmaceuticalDataGenerator,
    generate_csv_for_period,
    create_zip_archive
)

router = APIRouter(prefix="/generate", tags=["Data Generation"])


# ============== Request/Response Models ==============

class MonthGenerationRequest(BaseModel):
    """Request model for generating monthly data."""
    year: int = Field(..., ge=2020, le=2030, description="Year (2020-2030)")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    batches_per_day: int = Field(default=20, ge=1, le=100, description="Number of batches per day")
    data_types: Optional[List[str]] = Field(
        default=None,
        description="List of data types to generate. None = all types."
    )


class YearGenerationRequest(BaseModel):
    """Request model for generating yearly data."""
    year: int = Field(..., ge=2020, le=2030, description="Year (2020-2030)")
    batches_per_day: int = Field(default=20, ge=1, le=100, description="Number of batches per day")
    data_types: Optional[List[str]] = Field(
        default=None,
        description="List of data types to generate. None = all types."
    )


class CustomGenerationRequest(BaseModel):
    """Request model for generating data over a custom date range."""
    start_date: date = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="End date (YYYY-MM-DD)")
    batches_per_day: int = Field(default=20, ge=1, le=100, description="Number of batches per day")
    data_types: Optional[List[str]] = Field(
        default=None,
        description="List of data types to generate. None = all types."
    )


class DataTypeInfo(BaseModel):
    """Information about a data type."""
    name: str
    display_name: str
    description: str
    approximate_columns: int


class GenerationResponse(BaseModel):
    """Response from data generation."""
    success: bool
    message: str
    files_generated: List[str]
    total_records: Dict[str, int]
    period_start: str
    period_end: str


# ============== Helper Functions ==============

DATA_TYPE_INFO = {
    "manufacturing": DataTypeInfo(
        name="manufacturing",
        display_name="Manufacturing Batch Records",
        description="Comprehensive manufacturing data with CPPs, IPCs, yields, and equipment tracking",
        approximate_columns=45
    ),
    "qc": DataTypeInfo(
        name="qc",
        display_name="QC Lab Results",
        description="Quality control testing data: assay, dissolution, impurities, microbial",
        approximate_columns=35
    ),
    "complaints": DataTypeInfo(
        name="complaints",
        display_name="Customer Complaints",
        description="Customer complaint records with categories, severity, and investigations",
        approximate_columns=17
    ),
    "capa": DataTypeInfo(
        name="capa",
        display_name="CAPA Records",
        description="Corrective and Preventive Action records with root cause analysis",
        approximate_columns=18
    ),
    "environmental": DataTypeInfo(
        name="environmental",
        display_name="Environmental Monitoring",
        description="Cleanroom environmental data: particles, viable counts, temperature/humidity",
        approximate_columns=18
    ),
    "equipment": DataTypeInfo(
        name="equipment",
        display_name="Equipment Calibration",
        description="Calibration and maintenance records for manufacturing and lab equipment",
        approximate_columns=17
    ),
    "stability": DataTypeInfo(
        name="stability",
        display_name="Stability Studies",
        description="ICH stability testing data: long-term, accelerated, intermediate conditions",
        approximate_columns=14
    ),
    "raw_materials": DataTypeInfo(
        name="raw_materials",
        display_name="Raw Materials",
        description="Material receipt and testing data with supplier information",
        approximate_columns=15
    ),
    "batch_release": DataTypeInfo(
        name="batch_release",
        display_name="Batch Release",
        description="Batch disposition and QP release decisions",
        approximate_columns=16
    )
}


async def generate_data_async(
    start_date: datetime,
    end_date: datetime,
    batches_per_day: int,
    data_types: Optional[List[str]]
) -> Dict[str, BytesIO]:
    """Generate data asynchronously."""
    # Run generation in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: generate_csv_for_period(
            start_date=start_date,
            end_date=end_date,
            data_types=data_types,
            batches_per_day=batches_per_day
        )
    )


# ============== API Endpoints ==============

@router.get("/data-types", response_model=List[DataTypeInfo])
async def list_data_types():
    """
    List all available data types that can be generated.
    
    Returns information about each data type including:
    - Name (used in API calls)
    - Display name (human readable)
    - Description
    - Approximate number of columns
    """
    return list(DATA_TYPE_INFO.values())


@router.post("/month/download")
async def generate_and_download_month(request: MonthGenerationRequest):
    """
    Generate data for a specific month and return as a ZIP file.
    
    This endpoint generates all requested data types for the specified
    month and returns them as a downloadable ZIP archive.
    
    The ZIP contains CSV files named: `{year}_{month:02d}_{data_type}.csv`
    """
    # Validate data types
    if request.data_types:
        invalid_types = [t for t in request.data_types if t not in DATA_TYPE_INFO]
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data types: {invalid_types}. Valid types: {list(DATA_TYPE_INFO.keys())}"
            )
    
    # Calculate date range
    start_date = datetime(request.year, request.month, 1)
    if request.month == 12:
        end_date = datetime(request.year + 1, 1, 1)
    else:
        end_date = datetime(request.year, request.month + 1, 1)
    end_date = end_date.replace(day=1) - __import__('datetime').timedelta(days=1)
    
    try:
        # Generate data
        csv_buffers = await generate_data_async(
            start_date=start_date,
            end_date=end_date,
            batches_per_day=request.batches_per_day,
            data_types=request.data_types
        )
        
        # Create ZIP archive
        prefix = f"{request.year}_{request.month:02d}"
        zip_buffer = create_zip_archive(csv_buffers, prefix)
        
        # Return as downloadable file
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=apr_data_{prefix}.zip"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/year/download")
async def generate_and_download_year(request: YearGenerationRequest):
    """
    Generate data for an entire year and return as a ZIP file.
    
    This endpoint generates all requested data types for the specified
    year and returns them as a downloadable ZIP archive.
    
    Note: This may take a while for a full year of data.
    """
    # Validate data types
    if request.data_types:
        invalid_types = [t for t in request.data_types if t not in DATA_TYPE_INFO]
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data types: {invalid_types}. Valid types: {list(DATA_TYPE_INFO.keys())}"
            )
    
    # Calculate date range
    start_date = datetime(request.year, 1, 1)
    end_date = datetime(request.year, 12, 31)
    
    try:
        # Generate data
        csv_buffers = await generate_data_async(
            start_date=start_date,
            end_date=end_date,
            batches_per_day=request.batches_per_day,
            data_types=request.data_types
        )
        
        # Create ZIP archive
        prefix = f"{request.year}_full_year"
        zip_buffer = create_zip_archive(csv_buffers, prefix)
        
        # Return as downloadable file
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=apr_data_{prefix}.zip"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/custom/download")
async def generate_and_download_custom(request: CustomGenerationRequest):
    """
    Generate data for a custom date range and return as a ZIP file.
    
    This endpoint generates all requested data types for the specified
    date range and returns them as a downloadable ZIP archive.
    """
    # Validate dates
    if request.end_date < request.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    # Validate data types
    if request.data_types:
        invalid_types = [t for t in request.data_types if t not in DATA_TYPE_INFO]
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data types: {invalid_types}. Valid types: {list(DATA_TYPE_INFO.keys())}"
            )
    
    # Convert to datetime
    start_date = datetime.combine(request.start_date, time(0, 0, 0))
    end_date = datetime.combine(request.end_date, time(23, 59, 59))
    
    try:
        # Generate data
        csv_buffers = await generate_data_async(
            start_date=start_date,
            end_date=end_date,
            batches_per_day=request.batches_per_day,
            data_types=request.data_types
        )
        
        # Create ZIP archive
        prefix = f"{request.start_date}_to_{request.end_date}"
        zip_buffer = create_zip_archive(csv_buffers, prefix)
        
        # Return as downloadable file
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=apr_data_{prefix}.zip"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/month/preview", response_model=GenerationResponse)
async def preview_month_generation(request: MonthGenerationRequest):
    """
    Preview monthly data generation without downloading.
    
    Returns statistics about what would be generated without
    actually creating the files. Useful for estimating file sizes.
    """
    # Validate data types
    if request.data_types:
        invalid_types = [t for t in request.data_types if t not in DATA_TYPE_INFO]
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data types: {invalid_types}. Valid types: {list(DATA_TYPE_INFO.keys())}"
            )
    
    # Calculate date range
    start_date = datetime(request.year, request.month, 1)
    if request.month == 12:
        end_date = datetime(request.year + 1, 1, 1)
    else:
        end_date = datetime(request.year, request.month + 1, 1)
    end_date = end_date.replace(day=1) - __import__('datetime').timedelta(days=1)
    
    # Calculate number of days
    num_days = (end_date - start_date).days + 1
    
    # Estimate record counts
    data_types = request.data_types or list(DATA_TYPE_INFO.keys())
    total_records = {}
    
    for dt in data_types:
        if dt == "manufacturing":
            total_records[dt] = num_days * request.batches_per_day
        elif dt == "qc":
            total_records[dt] = num_days * request.batches_per_day  # One per batch
        elif dt == "complaints":
            total_records[dt] = int(num_days * request.batches_per_day * 0.008)  # ~0.8% rate
        elif dt == "capa":
            total_records[dt] = int(num_days / 30 * 10)  # ~10 per month
        elif dt == "environmental":
            total_records[dt] = num_days * 6 * 3  # 6 rooms, 3 readings/day
        elif dt == "equipment":
            total_records[dt] = int(num_days / 30 * 13)  # Various frequencies
        elif dt == "stability":
            total_records[dt] = int(num_days * request.batches_per_day / 20 * 3 * 8)  # Subset of batches
        elif dt == "raw_materials":
            total_records[dt] = int(num_days / 7 * 5)  # ~5 per week
        elif dt == "batch_release":
            total_records[dt] = num_days * request.batches_per_day
    
    return GenerationResponse(
        success=True,
        message=f"Preview for {request.month}/{request.year}",
        files_generated=[f"{dt}.csv" for dt in data_types],
        total_records=total_records,
        period_start=start_date.strftime("%Y-%m-%d"),
        period_end=end_date.strftime("%Y-%m-%d")
    )


@router.get("/single/{data_type}")
async def generate_single_data_type(
    data_type: str,
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    batches_per_day: int = Query(default=20, ge=1, le=100)
):
    """
    Generate and download a single data type as CSV.
    
    This is a convenience endpoint for downloading a specific
    data type without having to unzip an archive.
    """
    if data_type not in DATA_TYPE_INFO:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data type: {data_type}. Valid types: {list(DATA_TYPE_INFO.keys())}"
        )
    
    # Calculate date range
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    end_date = end_date.replace(day=1) - __import__('datetime').timedelta(days=1)
    
    try:
        # Generate only the requested data type
        csv_buffers = await generate_data_async(
            start_date=start_date,
            end_date=end_date,
            batches_per_day=batches_per_day,
            data_types=[data_type]
        )
        
        buffer = csv_buffers.get(data_type)
        if not buffer:
            raise HTTPException(status_code=500, detail="Failed to generate data")
        
        filename = f"{year}_{month:02d}_{data_type}.csv"
        
        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.get("/scenarios")
async def list_hidden_scenarios():
    """
    List the hidden scenarios embedded in the generated data.
    
    These scenarios create realistic anomalies for APR analysis:
    - Trends, shifts, and out-of-spec situations
    - Equipment degradation patterns
    - Supplier quality issues
    - Seasonal effects
    
    Use these to validate your analysis capabilities.
    """
    scenarios = [
        {
            "period": "March-May 2020",
            "scenario": "COVID-19 Disruption",
            "effects": ["Reduced batch production (10-15/day)", "Lower yields (-2%)", "Staffing challenges"],
            "data_types_affected": ["manufacturing", "complaints"]
        },
        {
            "period": "September-November 2021",
            "scenario": "Press-A Degradation",
            "effects": ["Gradual hardness drift", "Compression force variation", "Increased friability"],
            "data_types_affected": ["manufacturing", "qc"]
        },
        {
            "period": "June 2022",
            "scenario": "MCC Excipient Issue",
            "effects": ["Dissolution drop (-5%)", "50% more complaints", "Supplier investigation"],
            "data_types_affected": ["qc", "complaints", "capa"]
        },
        {
            "period": "Q2 2023",
            "scenario": "Lab Method Transition",
            "effects": ["Assay bias (+1.5%)", "Method validation period", "Increased variability"],
            "data_types_affected": ["qc"]
        },
        {
            "period": "July-August 2024",
            "scenario": "Summer Heat Effect",
            "effects": ["Elevated inlet air temps", "Humidity excursions", "Environmental alerts"],
            "data_types_affected": ["manufacturing", "environmental"]
        },
        {
            "period": "August 2025 (days 1-15)",
            "scenario": "Press-B Drift",
            "effects": ["Hardness increase (+1.5N)", "Dissolution drop (-8%)", "OOS investigations"],
            "data_types_affected": ["manufacturing", "qc", "capa"]
        },
        {
            "period": "November-December 2025",
            "scenario": "New API Supplier",
            "effects": ["Yield adjustment (-1%)", "30% more CAPAs", "Process optimization needed"],
            "data_types_affected": ["manufacturing", "capa"]
        }
    ]
    
    return {
        "total_scenarios": len(scenarios),
        "scenarios": scenarios,
        "note": "These scenarios are embedded deterministically based on the seed. Same date range will always produce same anomalies."
    }
