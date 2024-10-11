"""
Sample Data Transfer Objects (DTOs)

Overview:
This module defines the data transfer objects (DTOs) used to represent mechanical testing sample data
in a structured and validated format. These DTOs are designed to encapsulate both raw and processed
data for each sample, along with metadata and test conditions. They provide a consistent interface
for data validation, serialization, and transformation, supporting efficient data exchange between
the business logic, persistence layers, and external systems.

Key Responsibilities:
- Define structured representations of sample data using Pydantic models.
- Ensure data integrity through built-in validation rules and type annotations.
- Facilitate conversion between application-level objects and formats suitable for storage or API communication.
- Support the dynamic and flexible structure of mechanical test data, including both standardized KPIs and custom attributes.

Key Use Cases:
- Serialization: Convert sample data to JSON or other formats for storage or API responses.
- Deserialization: Validate and convert incoming data into structured sample objects.
- Transformation: Provide a unified interface for manipulating and accessing sample data.

Assumptions:
- The data structures are designed to accommodate common mechanical testing standards but remain flexible enough to handle custom extensions.

"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SampleDTO(BaseModel):
    """
    Data Transfer Object (DTO) for a single mechanical testing sample.

    Responsibilities:
    - Represents the primary data structure for a single sample, including raw and processed data.
    - Provides methods for serialization, deserialization, and validation of sample data.
    - Encapsulates all necessary information for a sample, including test conditions, raw measurements, and calculated results.

    Assumptions:
    - The DTO structure is compatible with various storage formats.
    - Complex data transformations or calculations are performed outside the DTO and stored in `processed_data`.
    """

    name: str
    length: float
    width: float
    thickness: float
    mass: float
    analysis_standard: str
    analysis_date: Optional[datetime] = None
    sample_id: Optional[str] = None  # Unique identifier for database storage
    raw_data: "SampleRawData"
    processed_data: "SampleProcessedData"
    test_conditions: "SampleTestConditions"
    standard_kpis: dict
    recalculation_properties: bool = False
    internal_units: dict
    target_units: Optional[dict] = None


class SampleRawData(BaseModel):
    """
    Represents raw data collected during mechanical testing of a sample.

    Assumptions:
    - Raw data is typically captured as lists of numerical values, with each list representing a series of measurements.
    - Calculated values such as stress and strain can be stored here if they are derived directly from the Mechanical Testing System.
    """

    time_measurements: Optional[list[float]] = None
    force_measurements: list[float]
    displacement_measurements: list[float]
    stress_measurements: Optional[list[float]] = None
    strain_measurements: Optional[list[float]] = None


class SampleProcessedData(BaseModel):
    """
    Represents processed data derived from the raw measurements of a sample.

    Assumptions:
    - Shifted data represents adjustments made to align or correct raw measurements before final analysis. ( e.g., zero-offset correction)
    - Calculated values are derived using standard formulas or custom calculations defined elsewhere.
    """

    shifted_applied_to_force: Optional[tuple[float, float]] = None  # Tuple of (x, y) values
    shifted_applied_to_displacement: Optional[tuple[float, float]] = None
    shifted_calculated_stress: Optional[tuple[float, float]] = None
    shifted_calculated_strain: Optional[tuple[float, float]] = None
    calculated_stress: Optional[list[float]] = None
    calculated_strain: Optional[list[float]] = None


class SampleTestConditions(BaseModel):
    """
    Represents the conditions under which a mechanical test was conducted.

    Assumptions:
    - Test conditions may include various environmental and procedural factors that affect the results.
    """

    material_type: str
    test_conditions: Optional[dict] = None
    equipment_details: str
    operator_name: str
    test_date: datetime

# Visualization DTOs varys to much.
class VisualizationSampleDTO(BaseModel):
    name: str
    sample_id: Optional[str] = None
    plotted_force: list[float]
    plotted_displacement: list[float]
    processed_data: "SampleProcessedData"


class SampleGroupDTO(BaseModel):
    """
    DTO representing a group of related mechanical testing samples.

    Assumptions:
    - Samples within the group may share common attributes or analysis standards.
    """

    group_name: str
    samples: list[SampleDTO]
