import pytest
import pandas as pd
from unittest.mock import MagicMock
from .mechanical_test_data_preprocessor import MechanicalTestDataPreprocessor, ureg  # Adjust the import according to your module structure

def test_MechanicalTestDataPreprocessor_init_default():
    # Test initialization with default parameters
    preprocessor = MechanicalTestDataPreprocessor()
    
    assert preprocessor.expected_units == MechanicalTestDataPreprocessor.EXPECTED_UNITS
    assert preprocessor.column_mapping == MechanicalTestDataPreprocessor.COLUMN_MAPPING
    assert set(unit for sublist in preprocessor.KNOWN_UNITS.values() for unit in sublist) == preprocessor.flat_known_units

def test_MechanicalTestDataPreprocessor_init_custom():
    # Custom mappings and units
    custom_mapping = {'stress': ['sigma'], 'strain': ['epsilon']}
    custom_units = {'stress': ureg.pascal, 'strain': ureg.dimensionless}
    custom_known_units = {'stress': ['Pa', 'kPa']}
    
    preprocessor = MechanicalTestDataPreprocessor(column_mapping=custom_mapping, expected_units=custom_units, known_units=custom_known_units)
    
    assert preprocessor.column_mapping == custom_mapping
    assert preprocessor.expected_units == custom_units
    assert set(unit for sublist in custom_known_units.values() for unit in sublist) == preprocessor.flat_known_units

@pytest.fixture
def preprocessor():
    return MechanicalTestDataPreprocessor()

def test_preprocess_data_with_dataframe(preprocessor: MechanicalTestDataPreprocessor):
    # Input is already a DataFrame
    input_df = pd.DataFrame({
        'force (kN)': [100, 200],
        'strain (%)': [0.1, 0.2],
        'time min': [10, 20],
        'displacement [cm]': [1, 2]
    })

    # Expected DataFrame after conversions
    expected_df = pd.DataFrame({
        'force': [100000.0, 200000.0],  # kN to N
        'strain': [0.001, 0.002],       # % to dimensionless
        'time': [600, 1200],            # min to s
        'displacement': [10, 20]        # cm to mm
    })

    # Mocking internal methods to isolate the test from other dependencies
    preprocessor.convert_lines_to_df = MagicMock(return_value=input_df)
    preprocessor.remap_df_columns = MagicMock(return_value=input_df)  # Assuming direct passthrough for simplicity
    preprocessor._convert_units = MagicMock(return_value=expected_df)

    # Execute the method under test
    result_df = preprocessor.preprocess_data(input_df)

    # Verifying the internal methods were called correctly
    preprocessor.remap_df_columns.assert_called_once_with(input_df, preprocessor.column_mapping)
    preprocessor._convert_units.assert_called_once()

    # Asserting the processed data matches expected results
    pd.testing.assert_frame_equal(result_df, expected_df)

