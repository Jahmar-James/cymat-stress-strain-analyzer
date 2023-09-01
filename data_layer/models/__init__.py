# app/data_layer/models/__init__.py

from collections import namedtuple

from data_layer.models.analyzable_entity import AnalyzableEntity
from data_layer.models.specimen import Specimen
from data_layer.models.specimen_properties import SpecimenPropertiesDTO
from data_layer.models.specimen_DB import SpecimenDB
from data_layer.models.sample_group import SampleGroup

Property = namedtuple('Property', ['value', 'default_unit'])