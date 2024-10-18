from dataclasses import dataclass
from typing import Any, Optional, Union

import numpy as np
import pandas as pd

from standard_base.entities.analyzable_entity import AnalyzableEntity
from standard_base.properties_calculators.base_standard_operator import BaseStandardOperator


@dataclass(frozen=True)
class Tolerance:
    """
    Represents the tolerance for a specific property. Tolerance can be defined
    as a true value with a tolerance value, or as upper and lower bounds.

    Responsibilities:
    - Validate that a given value falls within the tolerance bounds.
    - Provide a consistent interface for defining tolerances.
    - Calculate missing values based on the provided values.
    """

    # Either (true_value and tolerance) OR (upper and lower bounds) are provided
    true_values: Optional[Union[float, list, np.ndarray, pd.Series]] = None
    tolerances: Optional[Union[float, list, np.ndarray, pd.Series]] = None
    upper_bounds: Optional[Union[float, list, np.ndarray, pd.Series]] = None
    lower_bounds: Optional[Union[float, list, np.ndarray, pd.Series]] = None

    def __post_init__(self):
        # Convert input to np.ndarray if it's not already np.ndarray or pd.Series
        # for consistency and comparison operations
        true_values_array = self._convert_to_array(self.true_values)
        tolerances_array = self._convert_to_array(self.tolerances)
        upper_bounds_array = self._convert_to_array(self.upper_bounds)
        lower_bounds_array = self._convert_to_array(self.lower_bounds)

        # Calculate the missing values based on the provided values
        if true_values_array is not None and tolerances_array is not None:
            # Calculate upper and lower bounds from true_values and tolerances
            object.__setattr__(self, "upper_bounds", true_values_array + tolerances_array)
            object.__setattr__(self, "lower_bounds", true_values_array - tolerances_array)
            object.__setattr__(self, "true_values", true_values_array)
            object.__setattr__(self, "tolerances", tolerances_array)

        elif upper_bounds_array is not None and lower_bounds_array is not None:
            # Calculate true_values and tolerances from upper and lower bounds
            object.__setattr__(self, "true_values", (upper_bounds_array + lower_bounds_array) / 2)
            object.__setattr__(self, "tolerances", (upper_bounds_array - lower_bounds_array) / 2)
            object.__setattr__(self, "upper_bounds", upper_bounds_array)
            object.__setattr__(self, "lower_bounds", lower_bounds_array)
        else:
            raise ValueError("Either (true_values and tolerances) or (upper and lower bounds) must be provided.")

        # Additional validation for bounds
        # Convert both to NumPy arrays to ensure consistent types
        if not np.all(np.array(self.upper_bounds) > np.array(self.lower_bounds)):
            raise ValueError("Upper bounds must be greater than lower bounds.")

    @staticmethod
    def _convert_to_array(data: Optional[Union[float, list, np.ndarray, pd.Series]]) -> Optional[np.ndarray]:
        """Helper function to convert scalar, list, or pd.Series to np.ndarray."""
        if data is None:
            return None
        elif isinstance(data, (np.ndarray, pd.Series)):
            return data  # Returns wrong type when data is a pd.Series
        else:
            return np.array(data)

    def validate(self, data: Union[float, list, np.ndarray, pd.Series]) -> bool:
        """
        Validate that the given data falls within the tolerance bounds.
        Returns a boolean for scalar input, or a boolean array for array input.
        """
        data = np.array(data) if not isinstance(data, (np.ndarray, pd.Series)) else data
        if isinstance(data, pd.Series):
            data = data.to_numpy()

        return bool(np.all((data >= self.lower_bounds) & (data <= self.upper_bounds)))


@dataclass(frozen=True)
class CurveTolerances:
    """
    Represents tolerance for curves, encapsulating both x and y tolerances.
    """

    x: Tolerance
    y: Tolerance
    x_property: str  # Name of the x property (e.g., 'strain')
    y_property: str  # Name of the y property (e.g., 'stress')


class BenchmarkSample(AnalyzableEntity):
    """
    Represents a sample used for benchmarking mechanical testing data. This class
    extends AnalyzableEntity, adding specific properties and methods needed for
    benchmarking.

    Responsibilities:
    - Hold data that will be visualized or used as a reference for benchmarking.
    - Simplifies managing tolerances for different properties and provides helper methods for dynamically generating tolerances.
    """

    def __init__(
        self,
        name: str,
        length: Optional[float] = None,
        width: Optional[float] = None,
        thickness: Optional[float] = None,
        mass: Optional[float] = None,
        area: Optional[float] = None,
        volume: Optional[float] = None,
        density: Optional[float] = None,
        force: Optional[pd.Series] = pd.Series(dtype="float64", name="force"),
        displacement: Optional[pd.Series] = pd.Series(dtype="float64", name="displacement"),
        time: Optional[pd.Series] = pd.Series(dtype="float64", name="time"),
        stress: Optional[pd.Series] = pd.Series(dtype="float64", name="stress"),
        strain: Optional[pd.Series] = pd.Series(dtype="float64", name="strain"),
        specialized_data: Optional[dict] = None,
    ) -> None:
        # For each property we want (true value and tolrance | upper and lower bounds)
        # All the properties that we want to compare against the benchmark
        super().__init__(
            name=name,
            length=length,
            width=width,
            thickness=thickness,
            mass=mass,
            area=area,
            volume=volume,
            density=density,
            force=force,
            displacement=displacement,
            time=time,
            stress=stress,
            strain=strain,
            specialized_data=specialized_data,
        )
        # This class is Fancy warp around around a dictionary
        self.properties_tolerances: dict[str, Union[Tolerance, CurveTolerances]] = {}
        """
        Dictionary to store property tolerances. Each property can have a single Tolerance object or Tuple.
        single tolrance : {property_name: Tolerance} | multiple tolrances : {curve_name: x_tolerance, y_tolerance}
        """

    # Core Methods
    def add_property_tolerance(self, property_name: str, tolerance: Union[Tolerance, CurveTolerances]) -> bool:
        """Add a tolerance for a specific property."""
        if property_name in self.properties_tolerances:
            raise ValueError(f"Tolerance for property '{property_name}' already exists.")
        self.properties_tolerances[property_name] = tolerance
        return True

    def get_property_tolerance(self, property_name: str) -> Optional[Union[Tolerance, CurveTolerances]]:
        """Retrieve the tolerance for a specific property."""
        return self.properties_tolerances.get(property_name)

    def update_property_tolerance(self, property_name: str, tolerance: Tolerance) -> bool:
        """Update the tolerance for a specific property."""
        if property_name not in self.properties_tolerances:
            raise ValueError(f"No tolerance set for property '{property_name}'.")
        self.properties_tolerances[property_name] = tolerance
        return True

    def add_tolerance_from_percentage(self, property_name: str, true_value: float, percentage: float) -> bool:
        """
        Dynamically generate a tolerance for a property based on a percentage of the true value.
        E.g., if you give a 5% tolerance for stress, this will calculate the upper and lower bounds.
        """
        tolerance_value = true_value * (percentage / 100.0)
        tolerance = Tolerance(true_values=true_value, tolerances=tolerance_value)
        return self.add_property_tolerance(property_name, tolerance)

    @staticmethod
    def generate_tolerance_from_percentage(values: Union[np.ndarray, pd.Series], tolerance_str: str) -> Tolerance:
        """
        Helper method to generate Tolerance object from percentage string.

        Parameters:
        - values: The base values (e.g., y-values) for which the tolerance will be calculated.
        - tolerance_str: The percentage tolerance as a string (e.g., "5%").

        Returns:
        - Tolerance: A Tolerance object with calculated upper and lower bounds.
        """
        if not tolerance_str.endswith("%"):
            raise ValueError("Tolerance string must end with '%'.")

        try:
            tolerance_percentage = float(tolerance_str.strip("%")) / 100.0
            upper_bounds = values * (1 + tolerance_percentage)
            lower_bounds = values * (1 - tolerance_percentage)
            return Tolerance(upper_bounds=upper_bounds, lower_bounds=lower_bounds)
        except ValueError:
            raise ValueError("Invalid percentage value for tolerance.")

    def generate_curve_tolerance(
        self,
        x_property: str,
        y_property: str,
        x_tolerance: Union[str, Tolerance, None] = None,
        y_tolerance: Union[str, Tolerance, None] = None,
        curve_type: str = "",
        inplace: bool = True,
    ):
        """
        Generate upper and lower bounds for curves (e.g., stress-strain) by defining an acceptable percentage deviation.
        This will create an envelope around the curve with upper and lower bounds.
        """
        # Get x and y values from the sample using the property names
        x_values = getattr(self, x_property, None)
        y_values = getattr(self, y_property, None)
        curve_type = curve_type if curve_type else f"{y_property}_{x_property}"

        if x_values is None or y_values is None:
            raise ValueError(f"Missing x or y property values: {x_property}, {y_property}")

        # Validate that y_tolerance is provided
        if y_tolerance is None:
            raise ValueError("Y-tolerance must be provided for generating curve bounds.")

        # If no x_tolerance is provided, assume no tolerance for x-values (0%)
        if x_tolerance is None:
            x_tolerance = Tolerance(true_values=x_values, tolerances=0)

        # Handle tolerance if it's a percentage string
        if isinstance(x_tolerance, str):
            x_tolerance = self.generate_tolerance_from_percentage(x_values, x_tolerance)
        if isinstance(y_tolerance, str):
            y_tolerance = self.generate_tolerance_from_percentage(y_values, y_tolerance)

        curve_tolerance = CurveTolerances(x=x_tolerance, y=y_tolerance, x_property=x_property, y_property=y_property)

        if inplace:
            self.add_property_tolerance(curve_type, curve_tolerance)

        return curve_tolerance


class Benchmark:
    """
    Manages the comparison of mechanical testing samples against benchmark standards.
    This class handles the collection of samples and their comparison to a set of
    defined standards.

    Responsibilities:
    - Store and manage a list of BenchmarkSample instances.
    - Compare samples against defined benchmarks.
    - Select and manage the current benchmark sample.
    - Utilize a factory pattern to generate benchmarks based on different criteria.
    """

    def __init__(
        self,
    ) -> None:
        self.samples = []  # List to store samples (AnalyzableEntity instances)
        self.benchmark_standards = {}  # Dictionary to store BenchmarkSample instances by key ( Factory pattern )
        self.current_benchmark_sample: Optional[BenchmarkSample] = None  # Currently selected benchmark

    def add_sample(self, sample: AnalyzableEntity) -> bool:
        """Add a sample to the list if it's a valid AnalyzableEntity instance."""
        if isinstance(sample, AnalyzableEntity):
            self.samples.append(sample)
            return True
        return False

    def remove_sample(self, sample: AnalyzableEntity) -> bool:
        """Remove a sample from the list if it exists."""
        if sample in self.samples:
            self.samples.remove(sample)
            return True
        return False

    def set_current_benchmark_sample(self, key: str) -> bool:
        if key in self.benchmark_standards:
            self.current_benchmark_sample = self.benchmark_standards[key]
            return True
        return False

    def compare_samples(
        self, benchmark_sample: Optional[BenchmarkSample], samples: Optional[list[AnalyzableEntity]]
    ) -> Optional[dict[str, Any]]:
        """
        Main comparison method that compares each sample's properties to the benchmark.
        """
        if benchmark_sample:
            self.current_benchmark_sample = benchmark_sample
        if samples:
            self.samples = samples

        if not self.current_benchmark_sample:
            raise ValueError("No current benchmark sample set for comparison.")

        failed_samples = {}

        for sample in self.samples:
            sample_results = self._compare_sample_to_benchmark(
                sample, self.current_benchmark_sample.properties_tolerances
            )
            # If any property failed the comparison, store the result in failed_samples
            if sample_results:
                failed_samples[sample.name] = sample_results

        return failed_samples if failed_samples else None

    @staticmethod
    def _compare_sample_to_benchmark(
        sample: AnalyzableEntity, properties_tolerances: dict[str, Union[Tolerance, CurveTolerances]]
    ) -> dict[str, Any]:
        """
        Compare an individual sample to the current benchmark sample.
        """
        sample_results = {}

        for property_name, benchmark_tolerance in properties_tolerances.items():
            if isinstance(benchmark_tolerance, Tolerance):
                comparison_result = Benchmark._compare_scalar_tolerance(sample, property_name, benchmark_tolerance)

            elif isinstance(benchmark_tolerance, CurveTolerances):
                comparison_result = Benchmark._compare_curve_tolerance(sample, benchmark_tolerance)
            else:
                raise ValueError(
                    f"Unsupported tolerance type for property '{property_name}' in sample '{sample.name}'."
                )

            # Collect results for properties that failed comparison
            if not comparison_result:
                sample_results[property_name] = comparison_result

        return sample_results

    @staticmethod
    def _compare_scalar_tolerance(sample: AnalyzableEntity, property_name: str, tolerance: Tolerance) -> bool:
        """
        Helper method to compare a scalar property (float or array) to a scalar Tolerance.
        """
        sample_value = getattr(sample, property_name, None)

        if sample_value is None:
            raise ValueError(f"Sample '{sample.name}' does not have the property '{property_name}'.")

        # Compare scalar values (float, int)
        if isinstance(sample_value, (float, int)):
            return tolerance.validate(sample_value)

        # Compare Series or NumPy arrays
        elif isinstance(sample_value, (np.ndarray, pd.Series)):
            return Benchmark._compare_array_property(sample_value, tolerance, sample.property_calculator)
        else:
            raise ValueError(f"Unsupported property type for '{property_name}' in sample '{sample.name}'.")

    @staticmethod
    def _compare_array_property(
        sample_value: Union[pd.Series, np.ndarray],
        tolerance: Tolerance,
        property_calculator: BaseStandardOperator,
        return_failed_values: bool = False,
    ) -> Union[bool, np.ndarray]:
        """
        Compare array-like properties (NumPy arrays or Pandas Series) with tolerance bounds.
        Interpolates sample values only if their lengths differ from the benchmark.

        Algorithm:
        1. Extract X-values for both the benchmark and the sample.
        2. If the lengths of the sample and benchmark x-values are different, interpolate the sample's y-values
           to match the benchmark's x-values.
        3. Compare the aligned y-values to the benchmark's tolerance bounds.
        """
        if isinstance(sample_value, pd.Series):
            sample_value = sample_value.copy().to_numpy()

        # Extract or generate x-values from the benchmark
        x_benchmark = (
            tolerance.true_values.index
            if isinstance(tolerance.true_values, pd.Series)
            else np.arange(len(tolerance.true_values))  # type: ignore
            # (private method) will unsure its a numpy array or pandas series
            # # Ensure 'tolerance.true_values' is a numpy array or pandas series
        )

        y_sample = property_calculator.interpolate_series_if_needed(x_benchmark, sample_value)

        within_bounds = (y_sample >= tolerance.lower_bounds) & (y_sample <= tolerance.upper_bounds)

        bool_all_values_within = np.all(within_bounds)

        if return_failed_values:
            sample_values_outside = sample_value[~within_bounds]
            return sample_values_outside

        return bool(bool_all_values_within)

    @staticmethod
    def _compare_curve_tolerance(sample: AnalyzableEntity, curve_tolerance: CurveTolerances) -> bool:
        """
        Helper method to compare curve-like properties (x and y values) to a CurveTolerances object.
        """
        # Fetch x and y values based on property names stored in CurveTolerances
        x_values = getattr(sample, curve_tolerance.x_property, None)
        y_values = getattr(sample, curve_tolerance.y_property, None)

        if x_values is None or y_values is None:
            raise ValueError(
                f"Sample '{sample.name}' does not have the required properties "
                f"'{curve_tolerance.x_property}' and '{curve_tolerance.y_property}'."
            )

        # Ensure x and y are valid NumPy arrays or Pandas Series
        if isinstance(x_values, (np.ndarray, pd.Series)) and isinstance(y_values, (np.ndarray, pd.Series)):
            return Benchmark._compare_curves_property(x_values, y_values, curve_tolerance, sample.property_calculator)
        else:
            raise ValueError(
                f"Invalid curve data format for sample '{sample.name}' with properties "
                f"'{curve_tolerance.x_property}' and '{curve_tolerance.y_property}'."
            )

    @staticmethod
    def _compare_curves_property(
        x_values: Union[np.ndarray, pd.Series],
        y_values: Union[np.ndarray, pd.Series],
        tolerance: CurveTolerances,
        property_calculator: BaseStandardOperator,
        return_failed_values: bool = False,
    ) -> Union[bool, tuple[np.ndarray, np.ndarray]]:
        """
        Compare curve-like properties by finding intersections or interpolating to match x-values
        and checking against tolerance bounds.
        """
        x_tolerance = tolerance.x
        y_tolerance = tolerance.y
        x_upper_bound = x_tolerance.upper_bounds
        y_upper_bound = y_tolerance.upper_bounds
        x_lower_bound = x_tolerance.lower_bounds
        y_lower_bound = y_tolerance.lower_bounds

        # if pandas series, convert to numpy array
        if isinstance(x_values, pd.Series):
            x_values = x_values.to_numpy()
        if isinstance(y_values, pd.Series):
            y_values = y_values.to_numpy()
        if isinstance(x_tolerance.upper_bounds, pd.Series):
            x_upper_bound = x_tolerance.upper_bounds.to_numpy()
        if isinstance(y_tolerance.upper_bounds, pd.Series):
            y_upper_bound = y_tolerance.upper_bounds.to_numpy()
        if isinstance(x_tolerance.lower_bounds, pd.Series):
            x_lower_bound = x_tolerance.lower_bounds.to_numpy()
        if isinstance(y_tolerance.lower_bounds, pd.Series):
            y_lower_bound = y_tolerance.lower_bounds.to_numpy()

        # Find intersections if exact comparison is needed, otherwise use interpolation
        upper_bound_intersections = property_calculator.find_intersections(
            series1=(x_upper_bound, y_upper_bound), series2=(x_values, y_values), method="exact"
        )
        lower_bound_intersections = property_calculator.find_intersections(
            series1=(x_lower_bound, y_lower_bound), series2=(x_values, y_values), method="exact"
        )

        if return_failed_values and (upper_bound_intersections or lower_bound_intersections):
            return upper_bound_intersections, lower_bound_intersections

        # if no intersections found, the the sample curve is within the tolerance bounds
        return bool(not upper_bound_intersections and not lower_bound_intersections)
