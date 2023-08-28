from abc import ABC, abstractmethod

# AnalyzableEntity is an abstract class that defines the interface for any entity that can be analyzed.

class AnalyzableEntity(ABC):
    """
    An abstract class representing any entity that can be analyzed.
    This can be a Specimen or a SampleGroup.
    """

    @property
    @abstractmethod
    def analysis_type(self) -> str:
        pass

    @property
    @abstractmethod
    def strength(self) -> float:
        pass

    @property
    @abstractmethod
    def stress(self):
        pass

    @property
    @abstractmethod
    def strain(self):
        pass

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

class Specimen(AnalyzableEntity):
    def __init__(self, ...):
        # ...

    @property
    def analysis_type(self) -> str:
        return self._analysis_type

    @property
    def strength(self) -> float:
        return self._strength

    @property
    def stress(self):
        return self._stress

    @property
    def strain(self):
        return self._strain

    def calculate_characteristics(self):
        # ... calculation logic for a single specimen ...

    def plot(self):
        # ... plotting logic for a single specimen ...


class SampleGroup(AnalyzableEntity):
    def __init__(self, ...):
        # ...

    @property
    def analysis_type(self) -> str:
        # Maybe the analysis type is consistent across all specimens in the group, so we just retrieve the first one
        return self.specimens[0].analysis_type

    @property
    def strength(self) -> float:
        # This might be an average strength for the group or some other metric
        strengths = [specimen.strength for specimen in self.specimens]
        return sum(strengths) / len(strengths)

    @property
    def stress(self):
        # ... calculate group stress ...

    @property
    def strain(self):
        # ... calculate group strain ...

    def calculate_characteristics(self):
        # ... calculation logic for the entire group ...

    def plot(self):
        # ... plotting logic for the group ...
