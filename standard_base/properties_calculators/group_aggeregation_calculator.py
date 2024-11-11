import numpy as np
import pandas as pd
from scipy import stats

from .calculation_validation_helper import ValidationHelper


# Define the GroupAggregationOperator class as previously described
class GroupAggregationOperator:
    """
    A class to handle aggregation and calculations for a group of samples.
    All methods are static, follow a design-by-contract approach, and handle errors robustly.
    """

    @staticmethod
    def aggregate_scalar_properties(values: list[float], method: str = "mean") -> float:
        """
        Aggregate scalar properties (e.g., length, area) using a specified method.

        Preconditions:
        - `values` must be a non-empty list of floats or integers.
        - `method` must be a string representing a supported aggregation method ("mean", "median", "stddev")
          or a callable function.

        Postconditions:
        - Returns the aggregated value according to the specified method.

        Raises:
        - ValueError if the `values` list is empty or if `method` is unsupported.
        - TypeError if `values` is not a list of numbers or if `method` is not a string/callable.
        """
        # Validate inputs
        ValidationHelper.validate_non_empty_list(values, "aggregate_scalar_properties")
        ValidationHelper.validate_types_in_list(values, (float, int), "aggregate_scalar_properties")
        ValidationHelper.validate_type(method, (str, callable), "aggregate_scalar_properties")

        values_np = np.array(values)

        # Apply aggregation method
        if method == "mean":
            return np.mean(values_np)
        elif method == "median":
            return np.median(values_np)
        elif method == "stddev":
            return np.std(values_np, ddof=1)  # Using sample standard deviation (ddof=1)
        elif method == "mode":
            mode_result = stats.mode(values_np)
            return mode_result.mode[0]
        elif callable(method):
            return method(values)
        else:
            raise ValueError(f"Unsupported aggregation method: {method}")

    @staticmethod
    def aggregate_series(
        dfs: list[pd.Series],
        data_column,
        interp_column,
        method: str = "mean",
    ) -> pd.Series:
        """
        Aggregate multiple pandas Series using a specified method.

        Preconditions:
        - `series_list` must be a non-empty list of pandas Series objects.
        - All Series in the list must have the same index.
        - `method` must be a string representing a supported aggregation method ("mean", "median")
          or a callable function.

        Postconditions:
        - Returns a single pandas Series representing the aggregated result.

        Raises:
        - ValueError if the `series_list` is empty, if Series have mismatched indices, or if `method` is unsupported.
        - TypeError if `series_list` is not a list of Series or if `method` is not a string/callable.
        """
        # Validate inputs
        ValidationHelper.validate_type(dfs, list, "aggregate_series")
        ValidationHelper.validate_type(method, (str, callable), "aggregate_series")

        from .base_standard_operator import BaseStandardOperator

        # Apply aggregation method
        if method == "mean":
            if isinstance(dfs[0], pd.Series):
                # if all the same length okay otherwise raise error
                # Datafamre are preferred but series are okay is the same length
                if not all(len(df) == len(dfs[0]) for df in dfs):
                    raise ValueError("All series must have the same length to be averaged.")
                return np.mean(dfs, axis=0)

            return BaseStandardOperator.average_dataframes(
                df_list=dfs,
                avg_columns=data_column,
                interp_column=interp_column,
                step_size=GroupAggregationOperator.get_step_size_for_avg_agg(dfs, data_column),
            )
        else:
            raise ValueError(f"Unsupported aggregation method: {method}")

    @staticmethod
    def get_step_size_for_avg_agg(dfs: list[pd.DataFrame], prop: str) -> float:
        # Make helper function to calculate the step size
        max_observre_values = max([df[prop].max() for df in dfs])
        min_observre_values = min([df[prop].min() for df in dfs])
        max_len = max([len(df) for df in dfs])
        step_size = (max_observre_values - min_observre_values) / max_len
        return step_size


if __name__ == "__main__":
    # Test Cases

    # Test 1: Scalar properties aggregation - mean
    scalar_values = [1.0, 2.0, 3.0, 4.0]
    scalar_mean_result = GroupAggregationOperator.aggregate_scalar_properties(scalar_values, method="mean")

    # Test 2: Scalar properties aggregation - median
    scalar_median_result = GroupAggregationOperator.aggregate_scalar_properties(scalar_values, method="median")

    # Test 3: Scalar properties aggregation - standard deviation
    scalar_stddev_result = GroupAggregationOperator.aggregate_scalar_properties(scalar_values, method="stddev")

    # Test 4: Series aggregation - mean
    series1 = pd.Series([1, 2, 3])
    series2 = pd.Series([4, 5, 6])
    series3 = pd.Series([7, 8, 9])
    series_list = [series1, series2, series3]
    series_mean_result = GroupAggregationOperator.aggregate_series(series_list, method="mean")

    # Test 5: Series aggregation - median
    series_median_result = GroupAggregationOperator.aggregate_series(series_list, method="median")

    # Capture test results
    {
        "scalar_mean_result": scalar_mean_result,
        "scalar_median_result": scalar_median_result,
        "scalar_stddev_result": scalar_stddev_result,
        "series_mean_result": series_mean_result.tolist(),
        "series_median_result": series_median_result.tolist(),
    }
