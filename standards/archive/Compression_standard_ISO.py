from abc import ABC, abstractmethod
import numpy as np
import scipy
from scipy.integrate import trapz

class StandardProtocol(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def get_properties(self):
        # Returns a list of property names that this standard can calculate
        pass

    @abstractmethod
    def get_units(self):
        # Returns a dictionary of property names with their units
        pass

    def calculate_property(self, property_name, specimen):
            try:
                # Switch based on property_name and call the appropriate method
                method_name = f'calculate_{property_name}'
                method = getattr(self, method_name)
                return method(specimen)
            except AttributeError as error:
                print(f"Standard {self.name} does not calculate property '{property_name}: {error}")
                return None
    
    def _calculate_stress_at_strain(self, specimen, strain_value):
        # Calculation for stress at a specific strain value.
        strain = specimen.strain
        stress = specimen.stress
        idx = (np.abs(strain - strain_value)).argmin()
        return round(stress[idx], 2)
    
    def _calculate_energy_absorption(self, specimen, strain_value):
        # Calculation for energy absorption at a specific strain value.
        strain = specimen.strain
        stress = specimen.stress
        idx = (np.abs(strain - strain_value)).argmin()
        energy_absorption_kJ_m3 = scipy.integrate.trapz(stress[:idx], strain[:idx])*1000 # 1 MJ/m^3 -> 1000 kJ/m^3
        density_kg_meters =  specimen.density * 1000  # 1 g/cc -> 1000 kg/m^3
        energy_absorption_kJ_kg = energy_absorption_kJ_m3 / density_kg_meters
        return round(energy_absorption_kJ_m3, 2), round(energy_absorption_kJ_kg, 2)

# Standard implementation
class Standard_2023(StandardProtocol):
    def __init__(self):
        super().__init__("Base")

    def get_properties(self):
        return [
            'initial_yield_strength', 'yield_strength', 'modulus', 
            'toughness', 'resilience', 'ductility',
            'stress_at_20_percent_strain', 'stress_at_50_percent_strain', 
            'energy_absorption_e20', 'energy_absorption_e50', 
            'specific_energy_absorption_e20', 'specific_energy_absorption_e50'
        ]
        
    def calculate_initial_yield_strength(self, specimen):
        # Use the already calculated value from SpecimenGraphManager
        if specimen.graph_manager.IYS is None:
            specimen.graph_manager.calculate_strength(specimen.stress, specimen.strain)
        return specimen.graph_manager.IYS

    def calculate_yield_strength(self, specimen):
        # Use the already calculated value from SpecimenGraphManager
        if specimen.graph_manager.YS is None:
            specimen.graph_manager.calculate_strength(specimen.stress, specimen.strain)
        return specimen.graph_manager.YS

    def calculate_modulus(self, specimen):
        # Use the already calculated value from SpecimenGraphManager
        if specimen.graph_manager.youngs_modulus is None:
            specimen.graph_manager.calculate_youngs_modulus(specimen.stress, specimen.strain)
        return specimen.graph_manager.youngs_modulus

    def calculate_toughness(self, specimen):
        # Use the already calculated value from SpecimenDataManager
        return specimen.data_manager.toughness

    def calculate_resilience(self, specimen):
        # Use the already calculated value from SpecimenDataManager
        return specimen.data_manager.resilience

    def calculate_ductility(self, specimen):
        # Use the already calculated value from SpecimenDataManager
        return specimen.data_manager.ductility

    def calculate_stress_at_20_percent_strain(self, specimen):
        return self._calculate_stress_at_strain(specimen, 0.2)

    def calculate_stress_at_50_percent_strain(self, specimen):
        return self._calculate_stress_at_strain(specimen, 0.5)

    def calculate_energy_absorption_e20(self, specimen):
        # Use the already calculated value from Specimen
        return specimen.E20_kJ_m3

    def calculate_energy_absorption_e50(self, specimen):
        # Use the already calculated value from Specimen
        return specimen.E50_kJ_m3

    def calculate_specific_energy_absorption_e20(self, specimen):
        # Use the already calculated value from Specimen
        return specimen.E20_kJ_kg

    def calculate_specific_energy_absorption_e50(self, specimen):
        # Use the already calculated value from Specimen
        return specimen.E50_kJ_kg

class ISO_13314_Standard(StandardProtocol):
    def __init__(self):
        super().__init__("ISO_13314:2011(E)")
        # Initialization specific to ISO_13314

    def get_properties(self):
        return [
            'compressive_proof_strength', 
            'first_maximum_compressive_strength',
            'plateau_stress',
            'plateau_end',
            'stress_at_20_percent_strain',
            'stress_at_50_percent_strain',
            'quasi_elastic_modulus',
            'energy_absorption',
            'energy_absorption_kj_m3',
            'specific_energy_absorption',
            'energy_absorption_efficiency',
            'densification'
            
        ]
    
    def get_units(self):
        return {
            'compressive_proof_strength': '[MPa,(mm/mm)]',
            'first_maximum_compressive_strength': '[MPa,(mm/mm)]',
            'plateau_stress': 'MPa',
            'plateau_end': 'mm/mm',
            'stress_at_20_percent_strain': 'MPa',
            'stress_at_50_percent_strain': 'MPa',
            'quasi_elastic_modulus': 'MPa',
            'energy_absorption': 'MJ/m^3',
            'energy_absorption_kj_m3': 'kJ/m^3',
            'specific_energy_absorption': 'kJ/kg',
            'energy_absorption_efficiency': '%',
            'densification': '[MPa,(mm/mm)]'
        }
    
    def get_LSLs(self, data, tolerance_percentage=10):
        default_LSLs = {prop: data[prop].mean() * (1 - tolerance_percentage / 100) for prop in self.get_properties()}
        specified_LSLs = {
            'compressive_proof_strength': (LSL_value_1, LSL_value_2),  # Example values
            'first_maximum_compressive_strength': LSL_value,
            # ... other properties with their specified LSLs ...
        }
        return {prop: specified_LSLs.get(prop, default_LSLs[prop]) for prop in self.get_properties()}

    def get_USLs(self, data, tolerance_percentage=10):
        default_USLs = {prop: data[prop].mean() * (1 + tolerance_percentage / 100) for prop in self.get_properties()}
        specified_USLs = {
            'plateau_stress': (),  # Example values
            'plateau_end': (),
            # ... other properties with their specified USLs ...
        }
        return {prop: specified_USLs.get(prop, default_USLs[prop]) for prop in self.get_properties()}

    def calculate_compressive_proof_strength(self, specimen):
        # Use the already calculated value from SpecimenGraphManager
        return specimen.graph_manager.compressive_proof_strength
    
    def calculate_first_maximum_compressive_strength(self, specimen):
        return self._calculate_first_maximum_compressive_strength(specimen.strain, specimen.stress)
        
    # Define the function to calculate the first maximum compressive strength
    def _calculate_first_maximum_compressive_strength(self,strain, stress, window_length=51, polyorder=3, prominence_factor=0.01):
        """
        Calculate the first maximum compressive strength from stress-strain data.

        Parameters:
        - strain (array-like): The strain data.
        - stress (array-like): The stress data.
        - window_length (int): The length of the filter window (number of coefficients). Window length must be a positive odd integer.
        - polyorder (int): The order of the polynomial used to fit the samples. polyorder must be less than window_length.
        - prominence_factor (float): The factor to calculate prominence of peaks as a percentage of the peak to peak variation.

        Returns:
        - first_peak_strain (float): The strain at the first local maximum.
        - first_peak_stress (float): The stress at the first local maximum.
        """
        from scipy.signal import savgol_filter, find_peaks
        # Apply Savitzky-Golay filter to smooth the stress data
        smoothed_stress = savgol_filter(stress, window_length=window_length, polyorder=polyorder)

        # Find peaks with a prominence
        peaks, properties = find_peaks(smoothed_stress, prominence=np.ptp(smoothed_stress) * prominence_factor)
        
        # Filter out the peaks that are too close to the beginning (assuming no valid peak in the first 0.5% of strain)
        valid_peaks = [peak for peak in peaks if strain[peak] > strain[0] + 0.005]

        # If there are no valid peaks, return None
        if not valid_peaks:
            return None, None

        # The first valid peak is considered the first local maximum
        first_peak_index = valid_peaks[0]
        first_peak_strain = strain[first_peak_index]
        first_peak_stress = stress[first_peak_index]

        return first_peak_strain, first_peak_stress

    def calculate_quasi_elastic_modulus(self, specimen):
        return specimen.data_manager.modulus
    
    def calculate_plateau_stress(self, specimen, lower_strain=0.2, upper_strain=0.4): # Later get for UI
        # Find the average stress between 20% and 40% compressive strain
        strains = specimen.strain
        stresses = specimen.stress
        # Get indices within the strain range
        lower_idx = (np.abs(strains - lower_strain)).argmin()
        upper_idx = (np.abs(strains - upper_strain)).argmin()
        plateau_stresses = stresses[lower_idx:upper_idx]
        plateau_stress = np.mean(plateau_stresses)
        self.plateau_stress = plateau_stress
        return plateau_stress

    def calculate_plateau_end(self, specimen):
        # Find the point where stress is 1.3 times the plateau stress
        plateau_stress =  self.plateau_stress if hasattr(self, 'plateau_stress') else self.calculate_plateau_stress(specimen)
        stresses = specimen.stress
        plateau_end_index = np.where(stresses > 1.3 * plateau_stress)[0][0]
        plateau_end_strain = specimen.strain[plateau_end_index]
        self.plateau_end_index = plateau_end_index
        return plateau_end_strain # (mm/mm)
    
    def calculate_densification(self, specimen):
        # Find the point where stress is 1.3 times the plateau stress
        if hasattr(self, 'self.plateau_end_index'):
            index = self.plateau_end_index
            densification =  specimen.stress[index],specimen.strain[index]  
        else:
            densification_strain = self.calculate_plateau_end(specimen)
            densification = specimen.stress[self.plateau_end_index], densification_strain
        return densification # [MPa,(mm/mm)]
    
    def calculate_stress_at_20_percent_strain(self, specimen):
        return self._calculate_stress_at_strain(specimen, 0.2)

    def calculate_stress_at_50_percent_strain(self, specimen):
        return self._calculate_stress_at_strain(specimen, 0.5)
    
    def calculate_energy_absorption(self, specimen):
        # Use the calculate_energy_absorption method from StandardProtocol to compute W
        strain_limit = specimen.strain[self.plateau_end_index] if hasattr(self, 'plateau_end_index') else self.calculate_plateau_end(specimen)
        self.W_kJ_m3, self.W_kJ_kg = self._calculate_energy_absorption(specimen, strain_limit)
        # Convert to MJ/m^3 as specified by the ISO standard
        W_MJ_m3 = self.W_kJ_m3 / 1000
        self.W_MJ_m3 = W_MJ_m3
        return W_MJ_m3
    
    def calculate_energy_absorption_kj_m3(self, specimen):
        return self.W_kJ_m3
    
    def calculate_specific_energy_absorption(self, specimen):
        return self.W_kJ_kg
    
    def calculate_energy_absorption_efficiency(self, specimen):

        if hasattr(self, 'plateau_end_index'):
            stress_at_strain = specimen.stress[self.plateau_end_index] #N/mm^2
            strain_limit = specimen.strain[self.plateau_end_index] * 100 # convert to percent
        else:
            strain_limit =  self.calculate_plateau_end(specimen) * 100
            stress_at_strain = self._calculate_stress_at_strain(specimen, strain_limit)

        if not hasattr(self, 'W_kJ_m3'):
            W_kJ_m3, _ = self._calculate_energy_absorption(specimen, strain_limit/100)
            W_MJ_m3 = W_kJ_m3 / 1000
            self.W_MJ_m3 = W_MJ_m3

        We = (self.W_MJ_m3 / (stress_at_strain * (strain_limit)) ) * 10**4
        return We # percent

class StandardFactory:
    _registry = {
        "base": Standard_2023,
        "ISO_13314:2011(E)":ISO_13314_Standard,
        # ... other standards ...
    }

    @staticmethod
    def get_standard(name: str ) -> StandardProtocol:
        if name in StandardFactory._registry:
            return StandardFactory._registry[name]()
        else:
            raise ValueError(f"Standard '{name}' is not registered in the factory.")

# QC Manager
class SpecimenQCManager:
    def __init__(self, specimen):
        self.specimen = specimen
        self.standard = None
        self.property_dict = {}

    def update_standards(self, name: str = 'base' ):
        self.standard = StandardFactory.get_standard(name)
        self.property_dict = {prop: None for prop in self.standard.get_properties()}

    def calculate_KPIs(self):
        units_dict = self.standard.get_units()

        for prop in self.property_dict.keys():
            # self.property_dict[prop] = self.standard.calculate_property(prop, self.specimen)
            value = self.standard.calculate_property(prop, self.specimen)
            # Store the value and unit in a tuple or a dict
            self.property_dict[prop] = {"value": value, "unit": units_dict.get(prop, "unit")}
      




