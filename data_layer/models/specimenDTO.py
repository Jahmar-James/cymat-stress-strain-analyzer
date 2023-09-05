# app/data_layer/models/specimenDTO.py

from typing import TYPE_CHECKING, Optional, Union

import pandas as pd
from pydantic import BaseModel, ConfigDict

from ..IO.repositories.specimen_orm import Specimen_Table
from ..metrics.specimen_metrics import SpecimenMetricsDTO
from ..models.specimen_properties import SpecimenPropertiesDTO

if TYPE_CHECKING:
    from .specimen import Specimen
    from .specimen_DB import SpecimenDB

# DTO Class to store specimen data
class SpecimenDTO(BaseModel):
    """ 
    Data Transfer Object for Specimen class. 
    """
    model_config = ConfigDict(from_attributes=True)

    # Specimen attributes
    name: str
    properties: SpecimenPropertiesDTO # Pydantic model containing specimen properties in namedtuple format
    metrics: SpecimenMetricsDTO # Pydantic model containing specimen metrics in namedtuple format

    # SpecimenDB attributes
    id: Optional[int]
    status: Optional[str]
    type: Optional[str]
    analysis_type: Optional[str]
    analysis_date: Optional[str]
    production_date: Optional[str]
    cross_sectional_image: Optional[str]
    notes: Optional[str]
    
    # SpecimenDataManager attributes 
    data_manager: dict # attributes of SpecimenDataManager class except data attribute

     # if saving to a zip data is a file path, if saving to a database data is a byte stream
    data_file_path: Optional[str]  # path to HDF5 or CSV file from data_manager
    data_content: Optional[pd.DataFrame]


    @classmethod
    def from_specimen(cls, specimen: Union['Specimen', 'SpecimenDB']):
        # Initial attributes

        properties = (specimen.properties.model_copy() 
                  if isinstance(specimen.properties, SpecimenPropertiesDTO) 
                  else SpecimenPropertiesDTO(**specimen.properties.dict())) or None
    
        metrics = (specimen.metrics.model_copy() 
                if isinstance(specimen.metrics, SpecimenMetricsDTO) 
               else SpecimenMetricsDTO(**specimen.metrics.dict())) or None
        
        attributes = {
            "name": specimen.name,
            "properties": properties,
            "metrics": metrics,
            "data_content": specimen.data if hasattr(specimen.data_manager, 'data') else None,
            "data_manager": specimen.data_manager.__dict__
        }

        # If specimen is of type SpecimenDB, extract its specific attributes
        if isinstance(specimen, SpecimenDB):
            db_attributes = {
                attr: getattr(specimen, attr, None) 
                for attr in ['id', 'status', 'type', 'analysis_type', 'analysis_date', 
                            'production_date', 'cross_sectional_image', 'notes']
            }
            attributes.update(db_attributes)  # merge the dictionaries

        return cls(**attributes)
  
    @classmethod
    def from_orm_model(cls, orm_instance : 'Specimen_Table') -> 'SpecimenDTO':
        return cls.model_validate(orm_instance)
    
    def to_orm_model(self) -> 'Specimen_Table':
        return Specimen_Table(
            status=self.status,
            name=self.name,
            type=self.type,
            properties=self.properties.dict(),
            data=self.data_content.to_csv().encode() if self.data_content is not None else None,
            analysis_type=self.analysis_type,
            metrics=self.metrics.dict(),
            analysis_date=self.analysis_date,
            production_date=self.production_date,
            cross_sectional_image=self.cross_sectional_image.encode() if self.cross_sectional_image else None,
            notes=self.notes
        )






