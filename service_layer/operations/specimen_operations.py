# app/service_layer/operations/specimen_operations.py

import inspect
import logging
from typing import TYPE_CHECKING, Callable, Optional, Tuple, List

import numpy as np
import pandas as pd
import scipy.optimize
import scipy.integrate
import scipy.interpolate 
from scipy.optimize import OptimizeWarning

from .data_processing_service import DataProcessingService

# Configure logging
logging.basicConfig(level=logging.ERROR)

if TYPE_CHECKING:
    from data_layer.metrics.specimen_metrics import SpecimenMetricsDTO
    from data_layer.models.specimen import Specimen
    from data_layer.models.specimen_properties import SpecimenPropertiesDTO
    from data_layer.IO.specimen_data_manager import SpecimenDataManager

class SpecimenOperations(DataProcessingService):
    """ Perform general operations on specimen data"""
    @staticmethod
    def calculate_stress_strain(specimen_properties: 'SpecimenPropertiesDTO', specimen_data : pd.DataFrame) -> Optional[pd.DataFrame]:
        """Calculate stress and strain from the specimen data."""
        
         # Function name retrieval for logging
        frame = inspect.currentframe()
        current_function_name = frame.f_code.co_name if frame is not None else "Unknown Function"
        
        # Fail early if the DataFrame does not have the required columns
        required_columns = {'Force', 'Displacement'}
        if not required_columns.issubset(specimen_data.columns):
            missing_columns = required_columns - set(specimen_data.columns)
            logging.error(f"Server_layer: {current_function_name} | Missing required columns in DataFrame: {', '.join(missing_columns)}. ")
            return None
        try:
            # Calculate Stress and Strain
            data = specimen_data.copy()
            Area = specimen_properties.cross_sectional_area # mm^2
            data['Stress'] = specimen_data['Force'] / Area # MPa (N/mm^2)
            data['Strain'] = specimen_data['Displacement'] / specimen_properties.original_length # mm/mm (unitless)
            return data
        except Exception as e:
            logging.error(f"Server_layer: {current_function_name} | Failed to calculate stress and strain: {e}.")
            return None
        
    @staticmethod
    def default_young_modulus_calculator(data_manager , pts) -> Optional[float]:
        
        # Function name retrieval for logging
        frame = inspect.currentframe()
        current_function_name = frame.f_code.co_name if frame is not None else "Unknown Function"
        
        start, end = data_manager.first_increase_index, data_manager.next_decrease_index
        
        # Fail early: Check indices
        if start is None or end is None:
            logging.warning(f"{current_function_name}: Start or end indices are None. Unable to calculate Young's modulus. Suggested Action: Check if data points are valid. {start}, {end}")
            return None

        stress, strain = data_manager.data['Stress'], data_manager.data['Strain']

        def linear_func(x, a, b):
            return a * x + b
   
        try:
            # Short try block only around curve fitting
            popt, _ = scipy.optimize.curve_fit(linear_func, strain[start:end], stress[start:end])
            return popt[0]
        
        except OptimizeWarning as ow:
            # Specific exception for optimization warnings
            logging.error(f"{current_function_name}: Optimize Warning in curve_fit: {ow}. Suggested Action: Check the validity of your data.")
            return None
        except RuntimeError as re:
            # Specific exception for curve_fit failure
            logging.error(f"{current_function_name}: Runtime Error in curve_fit: {re}. Suggested Action: Verify your data range.")
            raise  # Re-raise since we can't handle the error, but want to log it
        except Exception as e:
            logging.error(f"{current_function_name}:An unexpected error occurred: {e}.Suggested Action: Contact support.")
            raise  # Re-raise since we can't handle the error, but want to log it
    
    
    @staticmethod
    def calculate_young_modulus(data_manager: 'SpecimenDataManager',
                                pts: Optional[dict] = None, 
                                slope_algorithm: Optional[Callable] = None) -> Optional[float]:
        """Calculate Young's modulus of the specimen."""
        
        # Function name retrieval for logging
        frame = inspect.currentframe()
        current_function_name = frame.f_code.co_name if frame is not None else "Unknown Function"
        
        # Fail early: Check input types
        if not isinstance(data_manager, SpecimenDataManager):
            logging.error(f"{current_function_name}:Invalid type for data_manager")
            raise ValueError("Invalid type for data_manager")
        
        if data_manager.data is None:
            logging.error(f"{current_function_name}:Data must be loaded before Young's modulus can be calculated")
            raise ValueError("Data must be loaded before Young's modulus can be calculated")
        
        if slope_algorithm is None:
            slope_algorithm = SpecimenOperations.default_young_modulus_calculator
        
        if pts is None:
            pts = data_manager.points

        return slope_algorithm(data_manager, pts)
    
    @staticmethod
    def default_strength_calculator(data_manager :'SpecimenDataManager', youngs_modulus, offset=0.002, ) -> Optional[Tuple[float, float]]:
    
        # Function name retrieval for logging
        frame = inspect.currentframe()
        current_function_name = frame.f_code.co_name if frame is not None else "Unknown Function"
        
        start, end = data_manager.first_increase_index, data_manager.next_decrease_index
           
        if start is None or end is None or youngs_modulus is None:
            logging.warning(f"{current_function_name}: Start, end indices or Young Modulus are None. Unable to calculate Strength. Suggested Action: Check if data points are valid.")
            return None
        
        if data_manager.data is None:
            logging.error(f"{current_function_name}:Data must be loaded before Young's modulus can be calculated")
            raise ValueError("Data must be loaded before Young's modulus can be calculated")

        stress, strain = data_manager.data['Stress'], data_manager.data['Strain']
        offset_intercept = - (offset * youngs_modulus) - (youngs_modulus * strain[start])
        offset_line = (youngs_modulus * strain) + offset_intercept
        
        try:
            ys_strain, ys_stress = data_manager.points_of_interest.find_interaction_point((strain, stress), (strain, offset_line))
            return (ys_strain, ys_stress)
        
        except  Exception as e:
            logging.error(f"{current_function_name}:An unexpected error occurred: {e}.Suggested Action: Contact support.")
            raise

    @staticmethod
    def calculate_strength(data_manager: 'SpecimenDataManager', 
                           youngs_modulus: float,
                           intercept_algorithm: Optional[Callable] = None, 
                           offset: float = 0.002) -> Optional[Tuple[float, float]]:
        """Calculate the strength of the specimen."""
        if intercept_algorithm is None:
            intercept_algorithm = SpecimenOperations.default_strength_calculator
        
        return intercept_algorithm(data_manager, youngs_modulus, offset)
    
    @staticmethod
    def calculate_IY_strength(data_manager: 'SpecimenDataManager', index: Optional[int] = None) -> Optional[Tuple[float, float]]:
        
        # Function name retrieval for logging
        frame = inspect.currentframe()
        current_function_name = frame.f_code.co_name if frame is not None else "Unknown Function"
        
        if data_manager.data is None:
            logging.error(f"{current_function_name}:Data must be loaded before Young's modulus can be calculated")
            raise ValueError("Data must be loaded before Young's modulus can be calculated")
    
        stress, strain = data_manager.data['Stress'], data_manager.data['Strain']
        end = index or data_manager.next_decrease_index
        return (strain[end], stress[end])
        
    @staticmethod
    def calculate_energy_absorption(data: pd.DataFrame, strain_precentage: float) -> None:
        """Calculate the energy absorbed by the specimen up to a given strain percentage (in MPa and %)."""
        required_columns = {'Stress', 'Strain'}
        if not required_columns.issubset(data.columns):
            missing_columns = required_columns - set(data.columns)
            logging.error(f"calculate_energy_absorption: Missing required columns in DataFrame: {', '.join(missing_columns)}. Sugested Action: Ensure data has the required columns.")
            return None
        
        # check if the strain percentage is valid
        # if between 0 and 1 then okay
        # else if between 0 and 100 then convert to 0 and 1 and warn user
        # else raise error
        
        if 0 < strain_precentage <= 1:
            pass
        elif 0 < strain_precentage <= 100:
            strain_precentage = strain_precentage / 100
            logging.warning(f"Strain precentage is not between 0 and 1. Converted to {strain_precentage}")
        else:
            raise ValueError(f"Strain precentage must be between 0 and 1 or between 0 and 100. Provided value: {strain_precentage}")
        
        strain = data['Strain'] 
        stress = data['Stress'] # MPa
        
        index = (np.abs(strain - strain_precentage)).argmin()
        return scipy.integrate.trapz(stress[:index], strain[:index]) * 1000  # convert to kJ from J
    
    @staticmethod
    def calculate_specific_energy_absorption(energy_volumetic_kJ_m3: List[float], density: float) -> Optional[List[float]]:
        """Calculate the specific energy absorption of the specimen.""" 
        
        # convert Density to kg/m^3 from g/cm^3
        density_kg_meters = density * 1000  # kg/m^3
        
        return [energy_volumetic_kJ_m3 / density_kg_meters for energy_volumetic_kJ_m3 in energy_volumetic_kJ_m3]
    
    @staticmethod
    def calculate_stress_at_strain(data: pd.DataFrame, strain_target: float) -> Optional[float]:
        """Calculate the stress at a given strain."""
        required_columns = {'Stress', 'Strain'}
        if not required_columns.issubset(data.columns):
            missing_columns = required_columns - set(data.columns)
            logging.error(f"calculate_stress_at_strain: Missing required columns in DataFrame: {', '.join(missing_columns)}. Sugested Action: Ensure data has the required columns.")
            return None
        
        stress = data['Stress']
        strain = data['Strain']
        
        #  interpolate the stress at the given strain
        return scipy.interpolate.interp1d(strain, stress)(strain_target)

    @staticmethod
    def shift_data(shift , data : pd.DataFrame ) -> pd.DataFrame:
        """Shift the data by a specified value."""
        return data