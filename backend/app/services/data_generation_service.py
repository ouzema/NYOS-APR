"""
NYOS APR - Enhanced Data Generation Service
============================================
Generates detailed pharmaceutical CSV data files with customizable date ranges.
Used by the backoffice interface for on-demand data generation.

Features:
- Generate data by specific month/year or date range
- All data types: Manufacturing, QC, Complaints, CAPA, Equipment, Environmental, Stability, Raw Materials, Batch Release
- Realistic pharmaceutical scenarios with hidden anomalies
- Downloadable CSV files

Author: NYOS APR Team
Date: February 2026
"""

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from io import BytesIO, StringIO
import random
import zipfile
import os

# Initialize Faker
fake = Faker()


class PharmaceuticalDataGenerator:
    """
    Centralized pharmaceutical data generator for NYOS APR.
    Generates realistic, interconnected pharmaceutical quality data.
    """
    
    # Configuration constants
    PRODUCTS = [
        {"name": "Paracetamol 500mg Tablets", "code": "PARA-500-TAB", "batch_prefix": "PARA"},
        {"name": "Ibuprofen 400mg Tablets", "code": "IBU-400-TAB", "batch_prefix": "IBU"},
        {"name": "Aspirin 100mg Tablets", "code": "ASP-100-TAB", "batch_prefix": "ASP"},
    ]
    
    TABLET_PRESSES = ["Press-A", "Press-B", "Press-C", "Press-D"]
    GRANULATORS = ["Gran-01", "Gran-02", "Gran-03"]
    DRYERS = ["FBD-01", "FBD-02", "FBD-03"]
    BLENDERS = ["Blend-01", "Blend-02", "Blend-03"]
    
    OPERATORS = [f"OP-{i:03d}" for i in range(1, 51)]  # 50 operators
    QC_ANALYSTS = [f"QC-{i:03d}" for i in range(1, 31)]  # 30 QC analysts
    QP_LIST = [f"QP-{i:02d}" for i in range(1, 10)]  # 9 Qualified Persons
    
    HPLC_SYSTEMS = ["HPLC-01", "HPLC-02", "HPLC-03", "HPLC-04"]
    DISSOLUTION_APPARATUS = ["Diss-01", "Diss-02", "Diss-03"]
    
    CLEANROOMS = [
        {"code": "CR-001", "name": "Dispensing Area", "class": "ISO 8"},
        {"code": "CR-002", "name": "Granulation Suite", "class": "ISO 8"},
        {"code": "CR-003", "name": "Compression Room A", "class": "ISO 7"},
        {"code": "CR-004", "name": "Compression Room B", "class": "ISO 7"},
        {"code": "CR-005", "name": "Packaging Hall", "class": "ISO 8"},
        {"code": "CR-006", "name": "QC Laboratory", "class": "ISO 7"},
    ]
    
    SUPPLIERS = [
        {"id": "SUP-001", "name": "ChemPharma Inc.", "materials": ["Paracetamol API", "Ibuprofen API"]},
        {"id": "SUP-002", "name": "ExcipientCorp", "materials": ["MCC", "Lactose", "Starch"]},
        {"id": "SUP-003", "name": "BinderSolutions", "materials": ["PVP K30", "HPMC"]},
        {"id": "SUP-004", "name": "CoatingMasters", "materials": ["Opadry", "Titanium Dioxide"]},
        {"id": "SUP-005", "name": "PackagingPro", "materials": ["HDPE Bottles", "Blister Foil"]},
        {"id": "SUP-006", "name": "GlobalAPI Ltd.", "materials": ["Aspirin API"]},
    ]
    
    COMPLAINT_CATEGORIES = {
        "Product Quality": [
            "Broken tablets", "Discolored tablets", "Chipped tablets", 
            "Foreign particle", "Odor complaint", "Wrong count", "Packaging damage"
        ],
        "Efficacy": ["Not effective", "Delayed onset", "Short duration"],
        "Adverse Event": ["Allergic reaction", "GI upset", "Headache", "Skin rash", "Nausea"],
        "Labeling": ["Missing expiry", "Illegible lot", "Wrong instructions"],
    }
    
    MARKETS = ["USA", "Canada", "UK", "Germany", "France", "Australia", "Japan", "Brazil", "India", "Mexico", "Spain", "Italy"]
    
    CAPA_SOURCES = ["Deviation", "Customer Complaint", "OOS Investigation", "Internal Audit", 
                   "External Audit", "Management Review", "Trend Analysis", "Self-Identified"]
    
    ROOT_CAUSE_CATEGORIES = [
        "Procedure not followed", "Procedure inadequate", "Training deficiency",
        "Equipment malfunction", "Environmental factor", "Raw material variation",
        "Human error", "Communication failure", "Design flaw", "Supplier issue"
    ]
    
    def __init__(self, seed: int = 42):
        """Initialize generator with seed for reproducibility."""
        self.seed = seed
        self._reset_seed()
        
    def _reset_seed(self):
        """Reset random seeds for consistent generation."""
        np.random.seed(self.seed)
        random.seed(self.seed)
        Faker.seed(self.seed)
    
    def _get_scenario_adjustments(self, date: datetime, equipment: str = None) -> Dict[str, Any]:
        """
        Return scenario-specific adjustments based on date and context.
        These create realistic hidden anomalies for analysis.
        """
        adjustments = {
            "yield_modifier": 0,
            "hardness_modifier": 0,
            "dissolution_modifier": 0,
            "complaint_rate_modifier": 1.0,
            "capa_rate_modifier": 1.0,
            "scenario_description": None
        }
        
        year = date.year
        month = date.month
        day = date.day
        
        # 2020: COVID-19 impact (March-May)
        if year == 2020 and month in [3, 4, 5]:
            adjustments["yield_modifier"] = -2.0
            adjustments["scenario_description"] = "COVID-19 disruption"
        
        # 2021: Press-A degradation (Sept-Nov)
        if year == 2021 and month in [9, 10, 11] and equipment == "Press-A":
            day_in_period = (date - datetime(2021, 9, 1)).days
            adjustments["hardness_modifier"] = min(day_in_period * 0.05, 2.0)
            adjustments["scenario_description"] = "Press-A wear"
        
        # 2022: MCC supplier issue (June)
        if year == 2022 and month == 6:
            adjustments["dissolution_modifier"] = -5.0
            adjustments["complaint_rate_modifier"] = 1.5
            adjustments["scenario_description"] = "MCC excipient issue"
        
        # 2023: Lab method transition (Q2)
        if year == 2023 and month in [4, 5, 6]:
            adjustments["scenario_description"] = "Method transition"
        
        # 2024: Summer temperature effect (Jul-Aug)
        if year == 2024 and month in [7, 8]:
            adjustments["scenario_description"] = "Summer heat effect"
        
        # 2025: Press-B drift + API supplier change (Aug)
        if year == 2025 and month == 8:
            if equipment == "Press-B" and day <= 15:
                adjustments["hardness_modifier"] = 1.5
                adjustments["dissolution_modifier"] = -8.0
            adjustments["scenario_description"] = "Press-B drift & new API supplier"
        
        # 2025: New API supplier adjustment period (Nov-Dec)
        if year == 2025 and month in [11, 12]:
            adjustments["yield_modifier"] = -1.0
            adjustments["capa_rate_modifier"] = 1.3
            adjustments["scenario_description"] = "New API supplier adjustment"
        
        return adjustments
    
    def generate_manufacturing_data(
        self,
        start_date: datetime,
        end_date: datetime,
        batches_per_day: int = 20,
        product_index: int = 0
    ) -> pd.DataFrame:
        """
        Generate comprehensive manufacturing batch records.
        
        Args:
            start_date: Start of the period
            end_date: End of the period
            batches_per_day: Number of batches to generate per day
            product_index: Index of product to generate (0=Paracetamol, etc.)
        
        Returns:
            DataFrame with manufacturing records
        """
        self._reset_seed()
        product = self.PRODUCTS[product_index]
        records = []
        batch_index = 1
        
        current_date = start_date
        while current_date <= end_date:
            daily_batches = batches_per_day
            
            # Reduced production during known disruptions
            adjustments = self._get_scenario_adjustments(current_date)
            if adjustments["scenario_description"] == "COVID-19 disruption":
                daily_batches = random.randint(10, 15)
            
            for _ in range(daily_batches):
                year_suffix = str(current_date.year)[-2:]
                batch_id = f"{product['batch_prefix']}-{year_suffix}-{batch_index:05d}"
                
                # Shift assignment
                shift = random.choices(["Day", "Evening", "Night"], weights=[0.5, 0.35, 0.15])[0]
                shift_hours = {"Day": (6, 13), "Evening": (14, 21), "Night": (22, 29)}
                start_hour = random.randint(*shift_hours[shift]) % 24
                
                mfg_start = current_date.replace(hour=start_hour, minute=random.randint(0, 59))
                
                # Equipment assignment
                tablet_press = random.choice(self.TABLET_PRESSES)
                granulator = random.choice(self.GRANULATORS)
                dryer = random.choice(self.DRYERS)
                blender = random.choice(self.BLENDERS)
                
                # Get scenario adjustments for this specific equipment
                equip_adjustments = self._get_scenario_adjustments(current_date, tablet_press)
                
                # Operators
                operator_primary = random.choice(self.OPERATORS)
                operator_secondary = random.choice([op for op in self.OPERATORS if op != operator_primary])
                
                # Process parameters
                api_weight_kg = round(np.random.normal(50.0, 0.5), 3)
                excipient_weight_kg = round(np.random.normal(45.0, 0.4), 3)
                batch_size_kg = round(api_weight_kg + excipient_weight_kg, 3)
                
                # Granulation parameters
                granulation_mixing_time = round(np.random.normal(15.0, 1.0), 2)
                binder_volume_ml = round(np.random.normal(2500, 100), 1)
                granulation_temp = round(np.random.normal(28, 2), 1)
                
                # Drying parameters
                inlet_air_temp = round(np.random.normal(60, 2), 1)
                outlet_air_temp = round(np.random.normal(40, 2), 1)
                drying_time_min = round(np.random.normal(45, 5), 1)
                moisture_content = round(np.random.normal(2.0, 0.3), 2)
                
                # Adjust for summer heat
                if equip_adjustments["scenario_description"] == "Summer heat effect":
                    inlet_air_temp = round(np.random.normal(63, 3), 1)
                    outlet_air_temp = round(np.random.normal(43, 2), 1)
                
                # Compression parameters
                compression_force_main = round(np.random.normal(18.0, 1.5) + equip_adjustments["hardness_modifier"], 2)
                compression_force_pre = round(np.random.normal(3.0, 0.3), 2)
                turret_speed = round(np.random.normal(45, 3), 1)
                
                tablet_weight = round(np.random.normal(500, 5), 1)
                tablet_thickness = round(np.random.normal(4.5, 0.1), 2)
                tablet_hardness = round(np.random.normal(120 + equip_adjustments["hardness_modifier"] * 5, 10), 1)
                friability = round(np.random.exponential(0.3), 3)
                disintegration_time = round(np.random.normal(8, 2), 1)
                
                # Yield calculations
                theoretical_yield = int((api_weight_kg * 1000) / 0.5 * 1000)
                base_yield_pct = 98.5 + equip_adjustments["yield_modifier"]
                actual_yield_pct = round(np.random.normal(base_yield_pct, 1.0), 2)
                actual_yield_pct = max(90.0, min(100.0, actual_yield_pct))
                actual_yield = int(theoretical_yield * actual_yield_pct / 100)
                
                # Rejects
                reject_count = int(np.random.exponential(50))
                reject_reasons = ["Weight", "Capping", "Sticking", "Chipping", "None"]
                reject_reason = random.choice(reject_reasons) if reject_count > 10 else "None"
                
                # Deviation tracking
                has_deviation = random.random() < 0.02
                deviation_id = f"DEV-{current_date.year}-{random.randint(1, 999):03d}" if has_deviation else ""
                deviation_type = random.choice(["Process", "Equipment", "Material", "Documentation"]) if has_deviation else ""
                
                # Environment
                room_temp = round(np.random.normal(22, 1), 1)
                room_humidity = round(np.random.normal(45, 5), 1)
                diff_pressure = round(np.random.normal(15, 2), 1)
                
                # Timing
                process_time_hours = round(np.random.normal(8, 1), 2)
                mfg_end = mfg_start + timedelta(hours=process_time_hours)
                
                records.append({
                    # Identifiers
                    "batch_id": batch_id,
                    "product_name": product["name"],
                    "product_code": product["code"],
                    "batch_size_kg": batch_size_kg,
                    
                    # Timing
                    "manufacturing_date": current_date.strftime("%Y-%m-%d"),
                    "manufacturing_start": mfg_start.strftime("%Y-%m-%d %H:%M"),
                    "manufacturing_end": mfg_end.strftime("%Y-%m-%d %H:%M"),
                    "shift": shift,
                    "process_time_hours": process_time_hours,
                    
                    # Personnel
                    "operator_primary": operator_primary,
                    "operator_secondary": operator_secondary,
                    
                    # Equipment
                    "tablet_press_id": tablet_press,
                    "granulator_id": granulator,
                    "dryer_id": dryer,
                    "blender_id": blender,
                    
                    # Materials
                    "api_weight_kg": api_weight_kg,
                    "excipient_weight_kg": excipient_weight_kg,
                    
                    # Granulation
                    "granulation_mixing_time_min": granulation_mixing_time,
                    "binder_volume_ml": binder_volume_ml,
                    "granulation_temp_c": granulation_temp,
                    
                    # Drying
                    "inlet_air_temp_c": inlet_air_temp,
                    "outlet_air_temp_c": outlet_air_temp,
                    "drying_time_min": drying_time_min,
                    "moisture_content_pct": moisture_content,
                    
                    # Compression
                    "compression_force_main_kn": compression_force_main,
                    "compression_force_pre_kn": compression_force_pre,
                    "turret_speed_rpm": turret_speed,
                    "tablet_weight_mg": tablet_weight,
                    "tablet_thickness_mm": tablet_thickness,
                    "tablet_hardness_n": tablet_hardness,
                    "friability_pct": friability,
                    "disintegration_time_min": disintegration_time,
                    
                    # Yield
                    "theoretical_yield_tablets": theoretical_yield,
                    "actual_yield_tablets": actual_yield,
                    "yield_percent": actual_yield_pct,
                    "reject_count": reject_count,
                    "reject_reason": reject_reason,
                    
                    # Deviation
                    "has_deviation": "Yes" if has_deviation else "No",
                    "deviation_id": deviation_id,
                    "deviation_type": deviation_type,
                    
                    # Environment
                    "room_temp_c": room_temp,
                    "room_humidity_pct": room_humidity,
                    "differential_pressure_pa": diff_pressure,
                    
                    # Status
                    "batch_status": "Complete",
                    "release_status": "Pending QC"
                })
                
                batch_index += 1
            
            current_date += timedelta(days=1)
        
        return pd.DataFrame(records)
    
    def generate_qc_data(
        self,
        manufacturing_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate QC lab testing data based on manufacturing records.
        
        Args:
            manufacturing_df: DataFrame from generate_manufacturing_data
            
        Returns:
            DataFrame with QC test results
        """
        self._reset_seed()
        records = []
        
        for _, mfg_row in manufacturing_df.iterrows():
            batch_id = mfg_row["batch_id"]
            mfg_date = datetime.strptime(mfg_row["manufacturing_date"], "%Y-%m-%d")
            tablet_press = mfg_row["tablet_press_id"]
            
            # Testing 1-3 days after manufacturing
            test_date = mfg_date + timedelta(days=random.randint(1, 3))
            
            # Get scenario adjustments
            adjustments = self._get_scenario_adjustments(test_date, tablet_press)
            
            # Analysts
            analyst_chemical = random.choice(self.QC_ANALYSTS)
            analyst_physical = random.choice([a for a in self.QC_ANALYSTS if a != analyst_chemical])
            
            # Equipment
            hplc_system = random.choice(self.HPLC_SYSTEMS)
            diss_apparatus = random.choice(self.DISSOLUTION_APPARATUS)
            
            # Sample ID
            sample_id = f"QC-{batch_id}"
            
            # Identification
            id_ir_result = "Conforms" if random.random() > 0.001 else "Does Not Conform"
            id_hplc_rt = round(np.random.normal(8.5, 0.1), 3)
            
            # Assay (95-105% spec)
            assay_base = 100.0
            if adjustments["scenario_description"] == "Method transition":
                assay_base = 101.5
            assay_percent = round(np.random.normal(assay_base, 1.5), 2)
            assay_result = "Pass" if 95.0 <= assay_percent <= 105.0 else "Fail"
            
            # Dissolution (Q=80%, individual ≥75%)
            diss_base = 92.0 + adjustments["dissolution_modifier"]
            diss_std = 3.0
            
            dissolution_vessels = [round(np.random.normal(diss_base, diss_std), 1) for _ in range(6)]
            dissolution_mean = round(np.mean(dissolution_vessels), 1)
            dissolution_min = min(dissolution_vessels)
            dissolution_result = "Pass" if dissolution_min >= 75.0 else "Fail"
            
            # Content Uniformity
            cu_values = [round(np.random.normal(100, 2), 1) for _ in range(10)]
            cu_av = round(abs(np.mean(cu_values) - 100) + 2.4 * np.std(cu_values), 1)
            cu_result = "Pass" if cu_av <= 15.0 else "Fail"
            
            # Impurities
            impurity_a = round(np.random.exponential(0.05), 3)
            impurity_b = round(np.random.exponential(0.03), 3)
            total_impurities = round(impurity_a + impurity_b + np.random.exponential(0.02), 3)
            impurities_result = "Pass" if total_impurities <= 1.0 else "Fail"
            
            # Physical tests
            hardness_mean = round(np.random.normal(12.0 + adjustments["hardness_modifier"] * 0.5, 1), 1)  # kp
            friability = round(np.random.exponential(0.3), 2)
            disintegration_max = round(np.random.normal(8, 2), 1)
            weight_mean = round(np.random.normal(500, 3), 1)
            weight_rsd = round(np.random.exponential(1.0), 2)
            
            # Microbial limits
            tamc = int(np.random.exponential(50))  # <1000 CFU/g
            tymc = int(np.random.exponential(20))  # <100 CFU/g
            micro_result = "Pass" if tamc < 1000 and tymc < 100 else "Fail"
            
            # Overall result
            all_pass = all([
                assay_result == "Pass",
                dissolution_result == "Pass",
                cu_result == "Pass",
                impurities_result == "Pass",
                micro_result == "Pass",
                friability < 1.0,
                disintegration_max < 15
            ])
            overall_result = "Pass" if all_pass else "Fail"
            
            records.append({
                "sample_id": sample_id,
                "batch_id": batch_id,
                "test_date": test_date.strftime("%Y-%m-%d"),
                "product_name": mfg_row["product_name"],
                "product_code": mfg_row["product_code"],
                
                # Analysts
                "analyst_chemical": analyst_chemical,
                "analyst_physical": analyst_physical,
                
                # Equipment
                "hplc_system": hplc_system,
                "dissolution_apparatus": diss_apparatus,
                
                # Identification
                "id_ir_result": id_ir_result,
                "id_hplc_rt_min": id_hplc_rt,
                
                # Assay
                "assay_percent": assay_percent,
                "assay_result": assay_result,
                
                # Dissolution
                "dissolution_vessel_1": dissolution_vessels[0],
                "dissolution_vessel_2": dissolution_vessels[1],
                "dissolution_vessel_3": dissolution_vessels[2],
                "dissolution_vessel_4": dissolution_vessels[3],
                "dissolution_vessel_5": dissolution_vessels[4],
                "dissolution_vessel_6": dissolution_vessels[5],
                "dissolution_mean": dissolution_mean,
                "dissolution_min": dissolution_min,
                "dissolution_result": dissolution_result,
                
                # Content Uniformity
                "cu_acceptance_value": cu_av,
                "cu_result": cu_result,
                
                # Impurities
                "impurity_a_pct": impurity_a,
                "impurity_b_pct": impurity_b,
                "total_impurities_pct": total_impurities,
                "impurities_result": impurities_result,
                
                # Physical
                "hardness_mean_kp": hardness_mean,
                "friability_pct": friability,
                "disintegration_max_min": disintegration_max,
                "weight_mean_mg": weight_mean,
                "weight_rsd_pct": weight_rsd,
                
                # Microbial
                "tamc_cfu_g": tamc,
                "tymc_cfu_g": tymc,
                "micro_result": micro_result,
                
                # Overall
                "overall_result": overall_result,
                "comments": "" if overall_result == "Pass" else "Investigation required"
            })
        
        return pd.DataFrame(records)
    
    def generate_complaints_data(
        self,
        manufacturing_df: pd.DataFrame,
        complaint_rate: float = 0.008
    ) -> pd.DataFrame:
        """
        Generate customer complaints linked to batches.
        
        Args:
            manufacturing_df: DataFrame from generate_manufacturing_data
            complaint_rate: Probability of complaint per batch (default 0.8%)
            
        Returns:
            DataFrame with complaint records
        """
        self._reset_seed()
        records = []
        complaint_index = 1
        
        batch_ids = manufacturing_df["batch_id"].tolist()
        
        for batch_id in batch_ids:
            mfg_row = manufacturing_df[manufacturing_df["batch_id"] == batch_id].iloc[0]
            mfg_date = datetime.strptime(mfg_row["manufacturing_date"], "%Y-%m-%d")
            
            adjustments = self._get_scenario_adjustments(mfg_date)
            effective_rate = complaint_rate * adjustments["complaint_rate_modifier"]
            
            if random.random() < effective_rate:
                # Complaint received 2-90 days after manufacturing
                complaint_date = mfg_date + timedelta(days=random.randint(2, 90))
                
                year = complaint_date.year
                complaint_id = f"CMP-{year}-{complaint_index:05d}"
                
                category = random.choice(list(self.COMPLAINT_CATEGORIES.keys()))
                description = random.choice(self.COMPLAINT_CATEGORIES[category])
                
                severity = random.choices(
                    ["Critical", "Major", "Minor"],
                    weights=[0.05, 0.25, 0.70]
                )[0]
                
                if category == "Adverse Event":
                    severity = random.choices(["Critical", "Major"], weights=[0.4, 0.6])[0]
                
                market = random.choice(self.MARKETS)
                reporter_type = random.choices(
                    ["Patient", "Healthcare Professional", "Pharmacist", "Distributor"],
                    weights=[0.4, 0.3, 0.2, 0.1]
                )[0]
                
                investigation_required = "Yes" if severity in ["Critical", "Major"] else random.choice(["Yes", "No"])
                
                # Investigation outcome
                if investigation_required == "Yes":
                    root_causes = [
                        "Manufacturing process variation",
                        "Storage condition issue",
                        "Packaging defect",
                        "User handling error",
                        "No issue confirmed",
                        "Transportation damage"
                    ]
                    root_cause = random.choice(root_causes)
                    investigation_outcome = random.choice([
                        "Confirmed - CAPA initiated",
                        "Not confirmed - No action required",
                        "Confirmed - Process adjustment made",
                        "Under investigation"
                    ])
                else:
                    root_cause = ""
                    investigation_outcome = "Not investigated"
                
                # Regulatory reportable
                regulatory_reportable = "Yes" if (category == "Adverse Event" and severity == "Critical") else "No"
                
                # CAPA reference
                capa_ref = f"CAPA-{year}-{random.randint(1, 200):03d}" if "CAPA" in investigation_outcome else ""
                
                # Status
                days_since = (datetime.now() - complaint_date).days
                if days_since > 60:
                    status = "Closed"
                elif days_since > 30:
                    status = random.choice(["Closed", "Under Investigation"])
                else:
                    status = random.choice(["Open", "Under Investigation"])
                
                records.append({
                    "complaint_id": complaint_id,
                    "complaint_date": complaint_date.strftime("%Y-%m-%d"),
                    "batch_id": batch_id,
                    "product_name": mfg_row["product_name"],
                    "product_code": mfg_row["product_code"],
                    "category": category,
                    "description": description,
                    "severity": severity,
                    "market": market,
                    "reporter_type": reporter_type,
                    "investigation_required": investigation_required,
                    "root_cause": root_cause,
                    "investigation_outcome": investigation_outcome,
                    "regulatory_reportable": regulatory_reportable,
                    "capa_reference": capa_ref,
                    "status": status,
                    "days_to_close": random.randint(5, 45) if status == "Closed" else None
                })
                
                complaint_index += 1
        
        return pd.DataFrame(records)
    
    def generate_capa_data(
        self,
        start_date: datetime,
        end_date: datetime,
        base_count: int = 10
    ) -> pd.DataFrame:
        """
        Generate CAPA records for a period.
        
        Args:
            start_date: Start of the period
            end_date: End of the period  
            base_count: Base number of CAPAs per month
            
        Returns:
            DataFrame with CAPA records
        """
        self._reset_seed()
        records = []
        capa_index = 1
        
        # Calculate months in range
        current = start_date.replace(day=1)
        while current <= end_date:
            year = current.year
            month = current.month
            
            adjustments = self._get_scenario_adjustments(current)
            month_capas = int(base_count * adjustments["capa_rate_modifier"])
            
            for _ in range(month_capas):
                open_date = datetime(year, month, random.randint(1, 28))
                capa_id = f"CAPA-{year}-{capa_index:04d}"
                
                source = random.choices(
                    self.CAPA_SOURCES,
                    weights=[0.35, 0.20, 0.15, 0.10, 0.05, 0.05, 0.05, 0.05]
                )[0]
                
                if source == "Deviation":
                    source_ref = f"DEV-{year}-{random.randint(1, 500):04d}"
                elif source == "Customer Complaint":
                    source_ref = f"CMP-{year}-{random.randint(1, 200):05d}"
                elif source == "OOS Investigation":
                    source_ref = f"OOS-{year}-{random.randint(1, 100):03d}"
                else:
                    source_ref = f"REF-{year}-{random.randint(1, 50):03d}"
                
                capa_type = random.choice(["Corrective", "Preventive", "Corrective & Preventive"])
                
                problem_categories = [
                    "Process deviation", "Equipment failure", "Documentation error",
                    "Training gap", "Supplier issue", "Environmental excursion"
                ]
                problem_category = random.choice(problem_categories)
                problem_statement = fake.sentence(nb_words=12)
                
                root_cause_category = random.choice(self.ROOT_CAUSE_CATEGORIES)
                root_cause_desc = fake.sentence(nb_words=15)
                
                rca_methods = ["5 Whys", "Fishbone Diagram", "Fault Tree Analysis", "FMEA"]
                rca_method = random.choice(rca_methods)
                
                risk_scores = ["Critical", "High", "Medium", "Low"]
                risk_score = random.choices(risk_scores, weights=[0.05, 0.15, 0.50, 0.30])[0]
                
                departments = ["Manufacturing", "Quality Control", "Quality Assurance", 
                             "Warehouse", "Engineering", "Packaging"]
                responsible_dept = random.choice(departments)
                capa_owner = random.choice(self.OPERATORS[:20])
                
                # Target date 30-90 days from open
                target_date = open_date + timedelta(days=random.randint(30, 90))
                
                # Status and completion
                days_since = (datetime.now() - open_date).days
                if days_since > 120:
                    status = random.choices(["Closed - Effective", "Closed - Not Effective"], weights=[0.9, 0.1])[0]
                    actual_completion = target_date + timedelta(days=random.randint(-10, 30))
                    days_to_close = (actual_completion - open_date).days
                    effectiveness_verified = "Yes"
                elif days_since > 60:
                    status = random.choices(["Closed - Effective", "Implementation", "Verification"], weights=[0.6, 0.2, 0.2])[0]
                    actual_completion = target_date + timedelta(days=random.randint(-10, 20)) if "Closed" in status else None
                    days_to_close = (actual_completion - open_date).days if actual_completion else None
                    effectiveness_verified = "Yes" if "Closed" in status else "Pending"
                else:
                    status = random.choice(["Open", "Implementation", "Root Cause Analysis"])
                    actual_completion = None
                    days_to_close = None
                    effectiveness_verified = "Pending"
                
                num_actions = random.randint(1, 5)
                
                records.append({
                    "capa_id": capa_id,
                    "capa_type": capa_type,
                    "source": source,
                    "source_reference": source_ref,
                    "open_date": open_date.strftime("%Y-%m-%d"),
                    "problem_statement": problem_statement,
                    "problem_category": problem_category,
                    "risk_score": risk_score,
                    "rca_method": rca_method,
                    "root_cause_category": root_cause_category,
                    "root_cause_description": root_cause_desc,
                    "responsible_department": responsible_dept,
                    "capa_owner": capa_owner,
                    "target_date": target_date.strftime("%Y-%m-%d"),
                    "actual_completion_date": actual_completion.strftime("%Y-%m-%d") if actual_completion else "",
                    "days_to_close": days_to_close,
                    "status": status,
                    "effectiveness_verified": effectiveness_verified,
                    "num_actions": num_actions
                })
                
                capa_index += 1
            
            # Move to next month
            if month == 12:
                current = datetime(year + 1, 1, 1)
            else:
                current = datetime(year, month + 1, 1)
        
        return pd.DataFrame(records)
    
    def generate_environmental_data(
        self,
        start_date: datetime,
        end_date: datetime,
        readings_per_day: int = 3
    ) -> pd.DataFrame:
        """
        Generate environmental monitoring data.
        
        Args:
            start_date: Start of the period
            end_date: End of the period
            readings_per_day: Number of readings per room per day
            
        Returns:
            DataFrame with environmental records
        """
        self._reset_seed()
        records = []
        record_index = 1
        
        current_date = start_date
        while current_date <= end_date:
            for room in self.CLEANROOMS:
                for reading in range(readings_per_day):
                    record_id = f"EM-{current_date.year}-{record_index:06d}"
                    
                    # Sampling time
                    hour = [8, 14, 20][reading]
                    monitoring_time = current_date.replace(hour=hour, minute=random.randint(0, 30))
                    
                    # Particle counts based on room class
                    if room["class"] == "ISO 7":
                        particles_05um = int(np.random.normal(150000, 30000))
                        particles_50um = int(np.random.exponential(200))
                    else:  # ISO 8
                        particles_05um = int(np.random.normal(2500000, 500000))
                        particles_50um = int(np.random.exponential(10000))
                    
                    # Viable counts
                    viable_air = int(np.random.exponential(5))
                    viable_surface = int(np.random.exponential(3))
                    
                    # Environmental parameters
                    temperature = round(np.random.normal(21, 1), 1)
                    humidity = round(np.random.normal(45, 5), 1)
                    diff_pressure = round(np.random.normal(15, 2), 1)
                    
                    # Summer heat effect
                    if current_date.month in [7, 8]:
                        temperature = round(np.random.normal(23, 1.5), 1)
                        humidity = round(np.random.normal(50, 7), 1)
                    
                    # Check limits
                    temp_in_spec = 18 <= temperature <= 25
                    humidity_in_spec = 30 <= humidity <= 60
                    pressure_in_spec = diff_pressure >= 10
                    
                    overall_result = "Pass" if all([temp_in_spec, humidity_in_spec, pressure_in_spec]) else "Fail"
                    
                    records.append({
                        "record_id": record_id,
                        "monitoring_date": current_date.strftime("%Y-%m-%d"),
                        "monitoring_time": monitoring_time.strftime("%H:%M"),
                        "room_code": room["code"],
                        "room_name": room["name"],
                        "room_classification": room["class"],
                        "particles_05um_per_m3": particles_05um,
                        "particles_50um_per_m3": particles_50um,
                        "viable_air_cfu_m3": viable_air,
                        "viable_surface_cfu_plate": viable_surface,
                        "temperature_c": temperature,
                        "humidity_pct": humidity,
                        "differential_pressure_pa": diff_pressure,
                        "temperature_in_spec": "Yes" if temp_in_spec else "No",
                        "humidity_in_spec": "Yes" if humidity_in_spec else "No",
                        "pressure_in_spec": "Yes" if pressure_in_spec else "No",
                        "overall_result": overall_result,
                        "monitored_by": random.choice(self.OPERATORS[:10])
                    })
                    
                    record_index += 1
            
            current_date += timedelta(days=1)
        
        return pd.DataFrame(records)
    
    def generate_equipment_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Generate equipment calibration/maintenance data.
        
        Args:
            start_date: Start of the period
            end_date: End of the period
            
        Returns:
            DataFrame with equipment calibration records
        """
        self._reset_seed()
        records = []
        cal_index = 1
        
        equipment_list = [
            {"id": "BAL-001", "name": "Analytical Balance 1", "type": "Balance", "freq_days": 30, "criticality": "High"},
            {"id": "BAL-002", "name": "Analytical Balance 2", "type": "Balance", "freq_days": 30, "criticality": "High"},
            {"id": "BAL-003", "name": "Floor Scale", "type": "Balance", "freq_days": 90, "criticality": "Medium"},
            {"id": "HPLC-01", "name": "HPLC System 1", "type": "Chromatography", "freq_days": 180, "criticality": "High"},
            {"id": "HPLC-02", "name": "HPLC System 2", "type": "Chromatography", "freq_days": 180, "criticality": "High"},
            {"id": "DISS-01", "name": "Dissolution Apparatus 1", "type": "Dissolution", "freq_days": 90, "criticality": "High"},
            {"id": "DISS-02", "name": "Dissolution Apparatus 2", "type": "Dissolution", "freq_days": 90, "criticality": "High"},
            {"id": "HARD-01", "name": "Hardness Tester 1", "type": "Physical Testing", "freq_days": 30, "criticality": "Medium"},
            {"id": "HARD-02", "name": "Hardness Tester 2", "type": "Physical Testing", "freq_days": 30, "criticality": "Medium"},
            {"id": "PH-001", "name": "pH Meter 1", "type": "Electrochemistry", "freq_days": 30, "criticality": "Medium"},
            {"id": "TEMP-01", "name": "Temperature Probe 1", "type": "Temperature", "freq_days": 365, "criticality": "High"},
            {"id": "PRESS-A", "name": "Tablet Press A", "type": "Manufacturing", "freq_days": 90, "criticality": "Critical"},
            {"id": "PRESS-B", "name": "Tablet Press B", "type": "Manufacturing", "freq_days": 90, "criticality": "Critical"},
        ]
        
        for equip in equipment_list:
            current = start_date
            while current <= end_date:
                cal_id = f"CAL-{current.year}-{cal_index:05d}"
                
                # Scheduled vs actual date (usually on time, sometimes delayed)
                scheduled_date = current
                delay_days = random.choices([0, 1, 2, 3, 5, 10], weights=[0.7, 0.1, 0.1, 0.05, 0.03, 0.02])[0]
                actual_date = scheduled_date + timedelta(days=delay_days)
                
                # Next due date
                next_due = actual_date + timedelta(days=equip["freq_days"])
                
                # Calibration results
                if equip["type"] == "Balance":
                    parameter = "Mass accuracy"
                    as_found = round(np.random.normal(100.000, 0.005), 4)
                    as_left = round(np.random.normal(100.000, 0.002), 4)
                    tolerance = 0.01
                elif equip["type"] == "Temperature":
                    parameter = "Temperature"
                    as_found = round(np.random.normal(25.0, 0.3), 2)
                    as_left = round(np.random.normal(25.0, 0.1), 2)
                    tolerance = 0.5
                else:
                    parameter = "Performance check"
                    as_found = round(np.random.normal(100, 2), 2)
                    as_left = round(np.random.normal(100, 1), 2)
                    tolerance = 5.0
                
                deviation = abs(as_found - as_left)
                out_of_tolerance = deviation > tolerance
                result = "Fail" if out_of_tolerance and random.random() < 0.05 else "Pass"
                
                records.append({
                    "calibration_id": cal_id,
                    "equipment_id": equip["id"],
                    "equipment_name": equip["name"],
                    "equipment_type": equip["type"],
                    "criticality": equip["criticality"],
                    "parameter": parameter,
                    "scheduled_date": scheduled_date.strftime("%Y-%m-%d"),
                    "actual_date": actual_date.strftime("%Y-%m-%d"),
                    "next_due_date": next_due.strftime("%Y-%m-%d"),
                    "as_found_value": as_found,
                    "as_left_value": as_left,
                    "deviation": round(deviation, 4),
                    "tolerance": tolerance,
                    "out_of_tolerance": "Yes" if out_of_tolerance else "No",
                    "result": result,
                    "calibrated_by": random.choice(self.QC_ANALYSTS[:10]),
                    "reviewed_by": random.choice(self.QC_ANALYSTS[10:20])
                })
                
                cal_index += 1
                current += timedelta(days=equip["freq_days"])
        
        return pd.DataFrame(records)
    
    def generate_stability_data(
        self,
        manufacturing_df: pd.DataFrame,
        batches_per_study: int = 3
    ) -> pd.DataFrame:
        """
        Generate stability testing data based on manufacturing batches.
        
        Args:
            manufacturing_df: DataFrame from generate_manufacturing_data
            batches_per_study: Number of batches to include in stability
            
        Returns:
            DataFrame with stability test results
        """
        self._reset_seed()
        records = []
        study_index = 1
        
        # Select batches for stability (typically 3 batches per quarter)
        batch_ids = manufacturing_df["batch_id"].unique()
        selected_batches = [batch_ids[i] for i in range(0, len(batch_ids), max(1, len(batch_ids) // (batches_per_study * 4)))][:batches_per_study * 4]
        
        conditions = [
            {"name": "Long-term", "temp": 25, "rh": 60, "timepoints": [0, 3, 6, 9, 12, 18, 24, 36]},
            {"name": "Accelerated", "temp": 40, "rh": 75, "timepoints": [0, 1, 2, 3, 6]},
            {"name": "Intermediate", "temp": 30, "rh": 65, "timepoints": [0, 3, 6, 9, 12]},
        ]
        
        for batch_id in selected_batches:
            mfg_row = manufacturing_df[manufacturing_df["batch_id"] == batch_id].iloc[0]
            mfg_date = datetime.strptime(mfg_row["manufacturing_date"], "%Y-%m-%d")
            
            for condition in conditions:
                study_id = f"STAB-{mfg_date.year}-{study_index:04d}"
                
                for timepoint in condition["timepoints"]:
                    test_date = mfg_date + timedelta(days=timepoint * 30)
                    
                    # Initial values
                    base_assay = 100.0
                    base_dissolution = 92.0
                    base_impurities = 0.1
                    base_water = 2.0
                    
                    # Degradation over time (accelerated degrades faster)
                    if condition["name"] == "Accelerated":
                        deg_rate = 0.08
                    elif condition["name"] == "Intermediate":
                        deg_rate = 0.04
                    else:
                        deg_rate = 0.015
                    
                    assay = round(base_assay - (deg_rate * timepoint) + np.random.normal(0, 0.5), 2)
                    dissolution = round(base_dissolution - (deg_rate * timepoint * 0.5) + np.random.normal(0, 1), 1)
                    total_impurities = round(base_impurities + (deg_rate * timepoint * 0.3) + np.random.exponential(0.02), 3)
                    water_content = round(base_water + (deg_rate * timepoint * 0.1) + np.random.normal(0, 0.1), 2)
                    
                    # Determine result
                    in_spec = 95.0 <= assay <= 105.0 and dissolution >= 80.0 and total_impurities <= 1.0
                    
                    records.append({
                        "study_id": study_id,
                        "batch_id": batch_id,
                        "stability_condition": condition["name"],
                        "storage_temp_c": condition["temp"],
                        "storage_rh_pct": condition["rh"],
                        "timepoint_months": timepoint,
                        "test_date": test_date.strftime("%Y-%m-%d"),
                        "assay_percent": assay,
                        "dissolution_pct": dissolution,
                        "total_impurities_pct": total_impurities,
                        "water_content_pct": water_content,
                        "appearance": "White, round tablets" if assay > 95 else "Slight yellowing observed",
                        "overall_result": "Pass" if in_spec else "Fail",
                        "analyst": random.choice(self.QC_ANALYSTS)
                    })
                
                study_index += 1
        
        return pd.DataFrame(records)
    
    def generate_raw_materials_data(
        self,
        start_date: datetime,
        end_date: datetime,
        receipts_per_week: int = 5
    ) -> pd.DataFrame:
        """
        Generate raw material receipt/testing data.
        
        Args:
            start_date: Start of the period
            end_date: End of the period
            receipts_per_week: Average number of material receipts per week
            
        Returns:
            DataFrame with raw material records
        """
        self._reset_seed()
        records = []
        grn_index = 1
        
        materials = [
            "Paracetamol API", "Ibuprofen API", "Aspirin API",
            "MCC (Microcrystalline Cellulose)", "Lactose Monohydrate", "Pregelatinized Starch",
            "PVP K30 (Povidone)", "HPMC (Hypromellose)", "Magnesium Stearate",
            "Colloidal Silicon Dioxide", "Croscarmellose Sodium", "Opadry Coating"
        ]
        
        current_date = start_date
        while current_date <= end_date:
            weekly_receipts = random.randint(receipts_per_week - 2, receipts_per_week + 2)
            
            for _ in range(weekly_receipts):
                grn_number = f"GRN-{current_date.year}-{grn_index:06d}"
                receipt_date = current_date + timedelta(days=random.randint(0, 6))
                
                material = random.choice(materials)
                
                # Find supplier
                supplier = random.choice(self.SUPPLIERS)
                
                # Material code
                material_code = f"MAT-{material[:3].upper()}-{random.randint(100, 999)}"
                
                # Quantity
                if "API" in material:
                    quantity = round(np.random.normal(100, 20), 1)
                    unit = "kg"
                else:
                    quantity = round(np.random.normal(500, 100), 1)
                    unit = "kg"
                
                # COA received
                coa_received = random.choices(["Yes", "No"], weights=[0.98, 0.02])[0]
                
                # Testing status
                test_statuses = ["Pass", "Pass", "Pass", "Pass", "Fail", "Pending"]
                test_status = random.choice(test_statuses)
                
                # Disposition
                if test_status == "Pass":
                    disposition = "Released"
                elif test_status == "Fail":
                    disposition = "Rejected"
                else:
                    disposition = "Quarantine"
                
                records.append({
                    "grn_number": grn_number,
                    "receipt_date": receipt_date.strftime("%Y-%m-%d"),
                    "material_code": material_code,
                    "material_name": material,
                    "supplier_id": supplier["id"],
                    "supplier_name": supplier["name"],
                    "quantity": quantity,
                    "unit": unit,
                    "batch_lot_number": f"{supplier['id'][-3:]}-{receipt_date.strftime('%y%m')}-{random.randint(1, 99):02d}",
                    "expiry_date": (receipt_date + timedelta(days=random.randint(365, 730))).strftime("%Y-%m-%d"),
                    "coa_received": coa_received,
                    "test_status": test_status,
                    "disposition": disposition,
                    "received_by": random.choice(self.OPERATORS[:10]),
                    "storage_location": f"WH-{random.choice(['A', 'B', 'C'])}-{random.randint(1, 50):02d}"
                })
                
                grn_index += 1
            
            current_date += timedelta(days=7)
        
        return pd.DataFrame(records)
    
    def generate_batch_release_data(
        self,
        manufacturing_df: pd.DataFrame,
        qc_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate batch release decision data.
        
        Args:
            manufacturing_df: DataFrame from generate_manufacturing_data
            qc_df: DataFrame from generate_qc_data
            
        Returns:
            DataFrame with batch release records
        """
        self._reset_seed()
        records = []
        
        for _, mfg_row in manufacturing_df.iterrows():
            batch_id = mfg_row["batch_id"]
            mfg_date = datetime.strptime(mfg_row["manufacturing_date"], "%Y-%m-%d")
            
            # Find corresponding QC result
            qc_row = qc_df[qc_df["batch_id"] == batch_id]
            if len(qc_row) == 0:
                continue
            qc_row = qc_row.iloc[0]
            
            qc_date = datetime.strptime(qc_row["test_date"], "%Y-%m-%d")
            qc_result = qc_row["overall_result"]
            
            # Review dates
            review_start = qc_date + timedelta(days=random.randint(1, 3))
            qc_complete = review_start + timedelta(days=random.randint(1, 2))
            
            # Release decision
            has_deviation = mfg_row["has_deviation"] == "Yes"
            has_oos = qc_result == "Fail"
            
            if has_oos:
                disposition = random.choices(["Rejected", "Released with deviation"], weights=[0.7, 0.3])[0]
            elif has_deviation:
                disposition = random.choices(["Released", "Released with deviation"], weights=[0.8, 0.2])[0]
            else:
                disposition = "Released"
            
            if disposition != "Rejected":
                release_date = qc_complete + timedelta(days=random.randint(1, 5))
                days_to_release = (release_date - mfg_date).days
            else:
                release_date = None
                days_to_release = None
            
            # QP assignment
            qp = random.choice(self.QP_LIST)
            qp_name = fake.name()
            
            # Market destination
            market = random.choice(self.MARKETS)
            
            records.append({
                "batch_id": batch_id,
                "product_name": mfg_row["product_name"],
                "product_code": mfg_row["product_code"],
                "manufacturing_date": mfg_row["manufacturing_date"],
                "qp_id": qp,
                "qp_name": qp_name,
                "review_start_date": review_start.strftime("%Y-%m-%d"),
                "qc_complete_date": qc_complete.strftime("%Y-%m-%d"),
                "release_date": release_date.strftime("%Y-%m-%d") if release_date else "",
                "disposition": disposition,
                "days_to_release": days_to_release,
                "has_deviation": mfg_row["has_deviation"],
                "has_oos": "Yes" if has_oos else "No",
                "yield_percent": mfg_row["yield_percent"],
                "market_destination": market,
                "batch_size_kg": mfg_row["batch_size_kg"]
            })
        
        return pd.DataFrame(records)
    
    def generate_all_data(
        self,
        start_date: datetime,
        end_date: datetime,
        batches_per_day: int = 20
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate all data types for a given period.
        
        Args:
            start_date: Start of the period
            end_date: End of the period
            batches_per_day: Number of manufacturing batches per day
            
        Returns:
            Dictionary of DataFrames keyed by data type
        """
        print(f"Generating data from {start_date.date()} to {end_date.date()}...")
        
        # Generate in dependency order
        print("  → Manufacturing data...")
        manufacturing_df = self.generate_manufacturing_data(start_date, end_date, batches_per_day)
        
        print("  → QC data...")
        qc_df = self.generate_qc_data(manufacturing_df)
        
        print("  → Complaints data...")
        complaints_df = self.generate_complaints_data(manufacturing_df)
        
        print("  → CAPA data...")
        capa_df = self.generate_capa_data(start_date, end_date)
        
        print("  → Environmental data...")
        environmental_df = self.generate_environmental_data(start_date, end_date)
        
        print("  → Equipment data...")
        equipment_df = self.generate_equipment_data(start_date, end_date)
        
        print("  → Stability data...")
        stability_df = self.generate_stability_data(manufacturing_df)
        
        print("  → Raw materials data...")
        raw_materials_df = self.generate_raw_materials_data(start_date, end_date)
        
        print("  → Batch release data...")
        batch_release_df = self.generate_batch_release_data(manufacturing_df, qc_df)
        
        print("✓ All data generated!")
        
        return {
            "manufacturing": manufacturing_df,
            "qc": qc_df,
            "complaints": complaints_df,
            "capa": capa_df,
            "environmental": environmental_df,
            "equipment": equipment_df,
            "stability": stability_df,
            "raw_materials": raw_materials_df,
            "batch_release": batch_release_df
        }


def generate_csv_for_period(
    year: int = None,
    month: int = None,
    start_date: datetime = None,
    end_date: datetime = None,
    data_types: List[str] = None,
    batches_per_day: int = 20
) -> Dict[str, BytesIO]:
    """
    Convenient function to generate CSV files for a period.
    
    Args:
        year: Year to generate (if month not specified, generates full year)
        month: Month to generate (1-12)
        start_date: Custom start date (overrides year/month)
        end_date: Custom end date (overrides year/month)
        data_types: List of data types to generate (None = all)
        batches_per_day: Number of batches per day
        
    Returns:
        Dictionary of BytesIO buffers containing CSV data
    """
    # Determine date range
    if start_date is None:
        if year is None:
            year = datetime.now().year
        
        if month is not None:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        else:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
    
    if end_date is None:
        end_date = start_date + timedelta(days=30)
    
    # Generate data
    generator = PharmaceuticalDataGenerator()
    all_data = generator.generate_all_data(start_date, end_date, batches_per_day)
    
    # Filter data types if specified
    if data_types:
        all_data = {k: v for k, v in all_data.items() if k in data_types}
    
    # Convert to CSV buffers
    csv_buffers = {}
    for name, df in all_data.items():
        csv_string = df.to_csv(index=False)
        buffer = BytesIO(csv_string.encode('utf-8'))
        buffer.seek(0)
        csv_buffers[name] = buffer

    return csv_buffers


def create_zip_archive(csv_buffers: Dict[str, BytesIO], prefix: str = "apr_data") -> BytesIO:
    """
    Create a ZIP archive containing all CSV files.
    
    Args:
        csv_buffers: Dictionary of data type -> BytesIO with CSV content
        prefix: Prefix for the filenames
        
    Returns:
        BytesIO buffer containing the ZIP archive
    """
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, buffer in csv_buffers.items():
            filename = f"{prefix}_{name}.csv"
            zf.writestr(filename, buffer.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer
