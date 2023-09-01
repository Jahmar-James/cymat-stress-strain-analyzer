# app/data_layer/models/analyzable_entity.py

from abc import ABC, abstractmethod

from pint import UnitRegistry

unit_registry = UnitRegistry()

class AnalyzableEntity(ABC):
    """
    An abstract class representing any entity that can be analyzed.
    This can be a Specimen or a SampleGroup.
    """
    def __init__(self, default_unit_map=None):
        self._set_unit_mapping(default_unit_map)

    def _set_unit_mapping(self, unit_map):
        if unit_map:
            self.default_unit_map = unit_map
        else:
            self.default_unit_map = {
                'strength': unit_registry.megapascal,
                'stress': unit_registry.megapascal,
                'strain': unit_registry.dimensionless, 
        }
   
    def strength(self, unit=None):
            return self._get_value_in_unit(self._strength, 'strength', unit)

    def stress(self, unit=None):
        return self._get_value_in_unit(self._stress, 'stress', unit)

    def strain(self, unit=None):
        return self._get_value_in_unit(self._strain, 'strain', unit)

    def _get_value_in_unit(self, value, unit_type, unit=None):
        default_unit = self.default_unit_map[unit_type]
        value_with_default_unit = value * default_unit

        if unit:
            return value_with_default_unit.to(unit)
        else:
            return value_with_default_unit
    
    @abstractmethod
    def calculate_characteristics(self):
        """
        Calculate the characteristics of the entity. This method should be implemented 
        to define how characteristics are computed for the specific entity.
        """
        pass

    @abstractmethod
    def plot(self):
        """
        Generate a plot for the entity's data. This could be a stress-strain curve or any other relevant visualization.
        """
        pass
    
    def reset_cached_properties(self, *properties):
        """Reset given cached properties, or all if none specified."""
        if properties:
            for prop in properties:
                if hasattr(self, prop):
                    delattr(self, prop)
        else:
            for attr in list(vars(self)):
                if hasattr(self, attr):
                    if attr.startswith("_"):
                        delattr(self, attr)
