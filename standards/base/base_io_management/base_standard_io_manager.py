"""
Application Requirements Recap
Data Integrity: Ensure that stored data is accurate and consistent, as it is used for engineering applications.
Multiple Storage Formats: Support both file-based (CSV/JSON in zip) and database storage.
Moderate Data Scale: Maximum of 50 samples in memory at a time, and up to 500 samples stored per year.
Simple Data Recreation: Since recreating data is not costly, sophisticated backup solutions are not needed.
Backend Focus: No UI considerations within these classes, focusing on data storage, retrieval, and transformation.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Union

from utlils.pattern_based_mapper import PatternBasedMapper

from .sample_dto_ import (
    SampleDTO,
    SampleGroupDTO,
    SampleProcessedData,
    SampleRawData,
    SampleStandardKPIS,
    SampleTestConditions,
    VisualizationSampleDTO,
)

if TYPE_CHECKING:
    from ..analyzable_entity import AnalyzableEntity


class BaseStandardIOManager:
    """
    Manages the conversion of sample objects to and from persistent storage (e.g., files or databases).

    Responsibilities:
    - Maps sample objects to a suitable format for storage.
    - Handles saving data to Zip file and databases (SQL_:ite, Postgress).
    - Provides helper functions to serialize and deserialize sample objects, possibly using Pydantic for validation.

    Assumptions:
    - Data will primarily be saved in Human readable formats (e.g., JSON, CSV) as data will be shared with other team members.
    - Sample objects can be serialized into flat or minimally nested structures for persistence.
    - Complex relationships (e.g., deeply nested samples or real-time synchronization) are out of scope for this design.

    Methods:
    - save_sample: Save a sample object to persistent storage give sample object and destination. Return True if successful.
    - load_sample: Load a sample object from persistent storage given a source. Return the deserialized sample object.
    - remap_sample: Provide a mapping between the sample object and the storage format. Return the remapped sample object.
    """

    def __init__(
        self,
    ) -> None:
        self._file_manager = None
        self._db_manager = None
        self._mapper = PatternBasedMapper()

        raise NotImplementedError("This class is not implemented yet.")

    def convert_entity_to_dto(self, entity: "AnalyzableEntity"):
        """
        Converts an AnalyzableEntity to its corresponding DTO based on its type.
        """
        if entity.is_visualization_only:
            return self._convert_to_visualization_dto(entity)
        elif entity.is_sample_group:
            return self._convert_to_sample_group_dto(entity)
        else:
            try:
                return self._convert_to_sample_dto(entity)
            except Exception as e:
                raise ValueError(f"Failed to convert entity to DTO: {e}")

    @staticmethod
    def _convert_to_sample_dto(entity: "AnalyzableEntity") -> "SampleDTO":
        """
        Converts an AnalyzableEntity into a SampleDTO.
        Uses a naming convention to automatically map attributes.
        """
        # Map common fields
        dto_data = {
            "name": entity.name,
            "length": entity.length,
            "width": entity.width,
            "thickness": entity.thickness,
            "mass": entity.mass,
            "analysis_standard": entity.analysis_standard,
            "internal_units": entity.internal_units,
            "target_units": entity.target_units,
        }

        # Use getattr for dynamic mapping of complex attributes like raw and processed data
        dto_data["raw_data"] = BaseStandardIOManager._map_raw_data(entity)
        dto_data["processed_data"] = BaseStandardIOManager._map_processed_data(entity)
        dto_data["test_conditions"] = BaseStandardIOManager._map_test_conditions(entity)
        dto_data["standard_kpis"] = entity._kpis.copy()

        return SampleDTO(**dto_data)

    @staticmethod
    def _convert_to_visualization_dto(entity: "AnalyzableEntity") -> "VisualizationSampleDTO":
        """
        Converts an AnalyzableEntity into a VisualizationSampleDTO.
        """
        return VisualizationSampleDTO(
            name=entity.name,
            sample_id=entity.database_id,
            plotted_force=entity._force.tolist(),  # Assuming _force is a pd.Series
            plotted_displacement=entity._displacement.tolist(),  # Assuming _displacement is a pd.Series
            processed_data=BaseStandardIOManager._map_processed_data(entity),
        )

    @staticmethod
    def _convert_to_sample_group_dto(group: list["AnalyzableEntity"], group_name: str) -> "SampleGroupDTO":
        """
        Converts a list of AnalyzableEntity objects into a SampleGroupDTO.
        """
        sample_dtos = [BaseStandardIOManager._convert_to_sample_dto(sample) for sample in group]
        return SampleGroupDTO(group_name=group_name, samples=sample_dtos)

    # Helper methods to map complex attributes from AnalyzableEntity to DTO

    @staticmethod
    def _map_raw_data(entity: "AnalyzableEntity") -> "SampleRawData":
        raw_data = entity.get_raw_data()
        
        return SampleRawData(
            force_measurements=raw_data["force"].tolist() if "force" in raw_data else [],
            displacement_measurements=raw_data["displacement"].tolist() if "displacement" in raw_data else [],
            stress_measurements=raw_data["stress"].tolist() if "stress" in raw_data else [],
            strain_measurements=raw_data["strain"].tolist() if "strain" in raw_data else [],
        )

    @staticmethod
    def _map_processed_data(entity: "AnalyzableEntity") -> "SampleProcessedData":
        if entity.has_hysteresis:
            return SampleProcessedData(
                calculated_stress=entity._stress.tolist() if entity._stress is not None else [],
                calculated_strain=entity._strain.tolist() if entity._strain is not None else [],
                calculated_hysteresis_stress=entity._hysteresis_stress.tolist() if entity._hysteresis_stress is not None else [],
                calculated_hysteresis_strain=entity._hysteresis_strain.tolist() if entity._hysteresis_strain is not None else [],
            )
            
        return SampleProcessedData(
            calculated_stress=entity._stress.tolist() if entity._stress is not None else [],
            calculated_strain=entity._strain.tolist() if entity._strain is not None else [],
           
        )

    @staticmethod
    def _map_test_conditions(entity: "AnalyzableEntity") -> "SampleTestConditions":
        # Might make this an attribute of AnalyzableEntity instead
        return SampleTestConditions(
            material_type="Unknown",  # Assuming you have material information stored elsewhere
            equipment_details="Standard Equipment",
            operator_name="Unknown Operator",  # Assuming a default if not available
            test_date=datetime.utcnow(),  # You can update to use actual date if present
        )


from pathlib import Path


class FileOIManager:
    """
    Handles saving and loading of sample data to and from the file system (e.g., JSON, CSV, ZIP).

    Responsibilities:
    - Saves serialized sample objects to human-readable file formats (e.g., JSON, CSV).
    - Loads and deserializes sample data from files.
    - Ensures file integrity during read and write operations.

    Assumptions:
    - The file path provided will be valid and accessible for read/write operations.
    - Data will primarily be saved in formats that are easy to share and view (e.g., JSON, CSV, ZIP).
    """

    def __init__(self, file_path: Path) -> bool:
        raise NotImplementedError("This class is not implemented yet.")

    def get_sample(self, file_path: Union[list[Path], Path]) -> list[AnalyzableEntity]:
        if isinstance(Path):
            file_path = list(file_path)

        samples = []
        for file in file_path:
            if not isinstance(file, Path) or not file.exists():
                print(
                    f"File '{file.name} of type {type(file)} does not exist or was not a Path object. It will be skipped."
                )
                continue
            # Extract data from file
            sample_data = self.extract_sample_data(file_path)
            # Recreate AnalyzableEntity from the data
            sample = self.recreate_sample_dto(sample_data)
            if sample:
                samples.append(sample)

        return samples

    @staticmethod
    def extract_sample_data(file_path: Path) -> dict:
        raise NotImplementedError()

    @staticmethod
    def recreate_sample_dto(sample_data: dict) -> AnalyzableEntity:
        raise NotImplementedError()


class DatabaseIOManager:
    """
    Manages the saving and loading of sample data to and from a database (e.g., SQLite, PostgreSQL).

    Responsibilities:
    - Saves serialized sample objects to database tables.
    - Loads and deserializes sample data from database records.
    - Provides basic database management operations, such as creating tables and handling connections.

    Assumptions:
    - The database URI provided will be valid and the database schema will align with the sample object structure.
    - The primary focus is on SQL-based databases (SQLite, PostgreSQL).
    """

    def __init__(self, db_uri: str) -> bool:
        raise NotImplementedError("This class is not implemented yet.")
