from abc import ABC, abstractmethod


class AnalyzableEntity(ABC):
    """
    Base class for Mechanical Testing sample objects that require data processing and plotting.
    Examples: A single Sample or a Collection of Samples.

    Responsibilities:
    1. **Hold Generic Operations**:
        - Provide methods such as unit conversion, calculating stress, strain, energy absorptivity, etc.
    2. **Define a Common Interface**:
        - Each subclass should define how key properties and methods are accessed and used.
        - For example, `SampleGeneric` must implement `_Strength` as part of the `AnalyzableEntity` interface.

    Abstract Methods:
    - Define methods that subclasses must implement, such as plotting or data extraction.
    """

    def __init__(self):
        raise NotImplementedError("This is an abstract base class and cannot be instantiated directly.")

    # Common Operations

    def plot_stress_strain(self) -> None:
        """
        Plot the stress-strain curve for a sample.
        Can be used to provide an automated view of the data, potentially overlayed with other samples.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def plot_force_displacement(self) -> None:
        """
        Plot the force-displacement curve for a sample.
        Can be used to provide an automated view of the data, potentially overlayed with other samples.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    # Interface - Abstract Methods

    @abstractmethod
    def plot(self) -> None:
        """
        Plot key performance indicators (KPI) relevant to the standard being used.
        This method must be implemented by subclasses to provide standard-specific views.
        """
        pass
