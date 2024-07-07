#add pint 

import os
from datetime import datetime
from scipy.optimize import curve_fit
from scipy.integrate import trapz
from scipy.signal import argrelextrema
from scipy.signal import medfilt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiPoint, Point

from standards.specimen_DIN import SpecimenDINAnalysis
from standards.Compression_standard_ISO import SpecimenQCManager

def median_filter(data, denoise_strength = 21):
    return data.apply(lambda x: medfilt(x, denoise_strength))

class Specimen:
    def __init__(self, name, data, length, width, thickness, weight):
        self.name = name
        self.length = float(length)
        self.width = float(width)
        self.thickness = float(thickness)
        self.weight = float(weight)
        self.calculate_properties()
        self.data_manager = SpecimenDataManager(self, data, self.cross_sectional_area, self.original_length)
        self.graph_manager = SpecimenGraphManager(self)
        self.din_analyzer = None
        self.manual_strain_shift = 0
        self.qc_manager = SpecimenQCManager(self)

    def calculate_quality_control_KPIs(self, standard_name: str):
        self.qc_manager.update_standards(standard_name)
        self.qc_manager.calculate_KPIs()
        return self.qc_manager.property_dict

    def set_analyzer(self):
        self.din_analyzer = SpecimenDINAnalysis(self.stress, self.shifted_strain)

    def calculate_properties(self):
        self.cross_sectional_area = self.length * self.width  # mm^2
        self.original_length = self.thickness  # mm
        volume = self.length * self.width * self.thickness  # mm^3
        self.density = self.weight / (volume * 10**(-3))

    def display_properties_in_label(self, label):
        properties_text = f"Specimen Properties\n\n"
        properties_text += f"Name: {self.name}\n"
        properties_text += f"Dim (L W t): \n{self.length:.2f} x {self.width:.2f} x {self.thickness:.2f}(mm)\n"
        properties_text += f"Weight: {self.weight:.3f} g\n"
        properties_text += f"Density: {self.density:.4f} (g/cc)\n"
        properties_text += f"Cross-sectional: {self.cross_sectional_area:.1f} (mm^2)\n"
        properties_text += f"Original Length: {self.original_length:.2f} (mm)"
        label.config(text=properties_text)

    def process_data(self, condition=None):
        self.data_manager.clean_data(condition)
        self.data_manager.add_stress_and_strain(condition, recalculate=True)  # TODO  Marker to test if there a need to recalculate
        if  self.processed_hysteresis_data is not None:
            self.calculate_shift_from_hysteresis()
        

    def calculate_general_KPI(self):
        self.calculate_energy()
    
    def calculate_energy(self):
        def calculate_Ev(stress, strain, compression):
            idx = (np.abs(strain - compression)).argmin()
            return trapz(stress[:idx], strain[:idx])
        
        
        self.E20_kJ_m3 = calculate_Ev(self.stress, self.shifted_strain, 0.2)*1000 # kJ/m^3
        self.E50_kJ_m3 = calculate_Ev(self.stress, self.shifted_strain,0.5)*1000 # kJ/m^3
        self.E80_kJ_m3 = calculate_Ev(self.stress, self.shifted_strain, 0.8)*1000 # kJ/m^3

        density_kg_meters = self.density * 1000  # kg/m^3
        self.E20_kJ_kg = self.E20_kJ_m3 / density_kg_meters
        self.E50_kJ_kg = self.E50_kJ_m3 / density_kg_meters
        self.E80_kJ_kg = self.E80_kJ_m3 / density_kg_meters
         

    def find_IYS_align(self):
        self.graph_manager.Calculate_Strength_Alignment()
    
    def calculate_shift_from_hysteresis(self):
        if self.processed_hysteresis_data.empty:
            return None
        if self.data_manager.modulus is None:
            self.data_manager.get_modulus_from_hysteresis()

    def plot_stress_strain(self, ax):
        ax.plot(self.shifted_strain, self.stress, alpha = 0.6, label=self.name)

    def plot_curves(self, ax, OFFSET=0.002, debugging=True):
        self.graph_manager.plot_curves(ax, OFFSET, debugging)
        self.calculate_general_KPI()

    def save_data(self, temp_dir):
        # Save the raw data and the formatted data
        self.data_manager.save(temp_dir)

    @property
    def strain(self):
        return self.data_manager.formatted_data['strain']

    @property
    def stress(self):
        return self.data_manager.formatted_data['stress']

    @property
    def force(self):
        return self.data_manager.formatted_data['force'] * -1

    @property
    def displacement(self):
        return self.data_manager.formatted_data['displacement'] * -1

    @property
    def shifted_strain(self):
        return self.graph_manager.strain_shifted + self.manual_strain_shift

    @property
    def shifted_displacement(self):
        force = self.force
        displacement = self.displacement
        first_increase_index = self.graph_manager.find_first_significant_increase(force, displacement)
        return displacement - displacement[first_increase_index] +(self.manual_strain_shift * self.original_length)

    @property
    def IYS(self):
        return self.graph_manager.IYS
    
    @property
    def YS(self):
        return self.graph_manager.YS

    @property
    def youngs_modulus(self):
        return self.graph_manager.youngs_modulus

    @property
    def data(self):
        return self.data_manager.split_raw_data_df

    @property
    def processed_data(self):
        return self.data_manager.formatted_data
    
    @property
    def processed_hysteresis_data(self):
        return self.data_manager.formatted_hysteresis_data

    @property
    def shifted_data(self):
        data = self.processed_data.copy()
        data['stress'] = self.stress
        data["Shifted Strain"] = self.shifted_strain
        data["Shifted Displacement (mm)"] = self.shifted_displacement
        data["Force"] = self.force
        return data

    @classmethod
    def from_dict(cls, data, temp_dir=None):
        # Initialize specimen with base properties
        specimen = cls(data['name'], None, data['length'],
                       data['width'], data['thickness'], data['weight'])
        specimen.manual_strain_shift = data.get('manual_strain_shift', 0)

        # Initialize Data and Graph managers
        specimen.data_manager = SpecimenDataManager.from_dict(data['data_manager'], specimen, temp_dir=temp_dir)
        specimen.graph_manager = SpecimenGraphManager.from_dict(data['graph_manager'], specimen, temp_dir=temp_dir)

        return specimen

class SpecimenGraphManager:
    def __init__(self, specimen):
        self.specimen = specimen
        self.first_increase_index = None
        self.next_decrease_index = None
        self.IYS = None
        self.YS = None
        self.youngs_modulus = None
        self.strain_offset = None
        self.offset_line = None
        self.compressive_proof_strength = None, None

    # Determine the plastic region 
    def find_first_significant_increase(self, stress, strain, threshold=0.015, testing=False,  min_force=80, max_force=1000):
        """Find the index of the first significant increase in stress.

        Args:
            stress (np.ndarray): Array of stress values.
            strain (np.ndarray): Array of strain values.
            threshold (float): Threshold for rate of change of stress/strain.
            testing (bool): Whether or not to show the plot.
            min_force (float): Minimum force value.
            max_force (float): Maximum force value.

        Returns:
            int or None: Index of the first significant increase in stress, or None if not found.
        """

        stress = np.array(self.specimen.stress)  # MPa
        strain = np.array(self.specimen.strain)  # %

        if np.isnan(stress).any() or np.isnan(strain).any():
            print("Warning: NaN values detected in stress or strain data. Please handle them.")

        stress_diff = np.diff(stress)
        strain_diff = np.diff(strain)
        print(f"\n\nSpecimen{self.specimen.name}:\n")

        strain_diff_masked = np.ma.masked_where(strain_diff == 0, strain_diff)
        rate_of_change = np.ma.divide(stress_diff, strain_diff_masked)
        rate_of_change = rate_of_change.filled(np.nan)

        max_abs_rate_of_change = np.nanmax(np.abs(rate_of_change))
        roc_normalized = np.divide(rate_of_change, max_abs_rate_of_change, out=np.zeros_like(
            rate_of_change), where=max_abs_rate_of_change != 0)


        # print( f"\n Rate of chanage{rate_of_change} and\n roc norm : {roc_normalized}")

        # Find the index of the first significant increase in the rate of change within tolerance

        i = np.argmax((roc_normalized >= threshold) & (
            self.specimen.force[:-1] >= min_force) & (self.specimen.force[:-1] <= max_force))

        print(f"Index of {i}  verser argmax i {i} with threshold of the first significant increase in stress: {threshold}")
        # If the index is zero, find the first index greater than zero.
        if i == 0:
            i = np.argmax(self.specimen.force > 500)
            print(f"No first significant increase Found, using force lead to a index of {i}")

        if ((strain[0]-strain[i]) < (-0.04)):
            print("moved too much")
            i = np.argmax((strain > 0) & (self.specimen.force >= min_force) & (
                self.specimen.force <= max_force))

        if testing:
            x = np.arange(len(roc_normalized))
            plt.plot(x, roc_normalized, linestyle=":")
            plt.title("find_first_significant_increase")
            plt.show()

        print(f"First significant increase index: {i} has a stress of {stress[i]:.2f} MPa and strain of {strain[i]:.6f} and force of {self.specimen.force[i]} N")
        return i

    def find_next_significant_decrease(self, stress, strain, start_index=0, threshold=0.0005, testing=False):
        """Find the index of the next significant decrease in stress after the given start index.

        Args:
            stress (np.ndarray): Array of stress values.
            strain (np.ndarray): Array of strain values.
            start_index (int): Index to start searching for the next significant decrease in stress.
            threshold (float): Threshold for rate of change of stress/strain.
            testing (bool): Whether or not to show the plot.

        Returns:
            int or None: Index of the next significant decrease in stress after the start index, or None if not found.
        """
        if start_index == 0:
            first_index_above_zero = np.argmax(self.specimen.force > 0)
            start_index = first_index_above_zero
        stress = np.array(self.specimen.stress)  # MPa
        strain = np.array(self.specimen.strain)  # %

        if np.isnan(stress).any() or np.isnan(strain).any():
            print("Warning: NaN values detected in stress or strain data. Please handle them.")

        stress_diff = np.diff(stress)
        strain_diff = np.diff(strain)

        # Test
        strain_diff_masked = np.ma.masked_where(strain_diff == 0, strain_diff)
        rate_of_change = np.ma.divide(stress_diff, strain_diff_masked)
        rate_of_change = rate_of_change.filled(np.nan)

        max_abs_rate_of_change = np.nanmax(np.abs(rate_of_change))

        if max_abs_rate_of_change == 0:
            print("Warning: Maximum absolute rate of change is zero. Cannot normalize.")
        else:
            roc_normalized = np.divide(rate_of_change, max_abs_rate_of_change, out=np.zeros_like(
                rate_of_change), where=max_abs_rate_of_change != 0)

        # print(f"inside of next")
        # print(f"roc is {rate_of_change} and roc norm = {roc_normalized}")
        # print(f"\n roc max is {np.nanmax(rate_of_change)} and roc norm  max = {np.nanmax(roc_normalized)}")

        # print(  f"threshold of the next significant decrease in stress after the given start index: {threshold}")

        # i = np.argmax(roc_normalized[start_index:] <= -threshold)

        indices = np.argwhere(roc_normalized[start_index:] <= -threshold)
        if len(indices) > 0:
            i = indices[0][0]
        else:
            i = None

        if i is not None:
            if testing:
                x = np.arange(len(roc_normalized))
                plt.plot(x, roc_normalized, linestyle=":")
                plt.axvline(x=start_index+i, color="r")
                plt.title("find_next_significant_decrease")
                plt.show()

            print(f"i plus start {i+start_index}")
            if roc_normalized[start_index + i] <= -threshold:
                print(
                    f"Next significant decrease index: {start_index + i} has a stress of {stress[start_index + i]:.2f} MPa and strain of {strain[start_index + i]:.6f}")
                return start_index + i
        else:
            print("No significant decrease found")
        return None
    
    #find intercept for YS
    @staticmethod
    def find_interaction_point( plot1, plot2, min_dist_from_origin=0.001, max_attempts=3):
        # Get the x and y data from each tuple
        x1, y1 = plot1
        x2, y2 = plot2

        # Create LineString objects
        line1 = LineString(zip(x1, y1))
        line2 = LineString(zip(x2, y2))

        # Shift line2 to find a valid intersection
        shift_step = 0.001
        attempts = 0

        while attempts < max_attempts:
            intersection = line1.intersection(line2)
            if intersection.is_empty:
                # Shift line2 and try again
                line2 = LineString([(x, y + shift_step) for x, y in line2.coords])
                attempts += 1
            else:
                # Check if the intersection point is not too close to the origin
                origin = Point(0, 0)
                valid_intersection = None

                if isinstance(intersection, MultiPoint):
                    points = intersection.geoms
                else:
                    points = [intersection]

                for point in points:
                    if point.distance(origin) >= min_dist_from_origin:
                        valid_intersection = point
                        break

                if valid_intersection is not None:
                    #print(valid_intersection.geom_type)
                    # shapely migration from 1.8 to 2.0
                    try:
                        if valid_intersection.geom_type == 'MultiPoint':
                            x_int = [point.x for point in valid_intersection]
                            y_int = [point.y for point in valid_intersection]
                        elif valid_intersection.geom_type == 'MultiLineString':  # new clause
                            x_int, y_int = [], []
                            for line in valid_intersection.geoms:
                                x_line, y_line = line.xy
                                x_int.extend(x_line)
                                y_int.extend(y_line)
                        elif valid_intersection.geom_type == 'GeometryCollection':  # new clause
                            x_int, y_int = [], []
                            for geom in valid_intersection.geoms:
                                if geom.geom_type == 'Point':
                                    x_int.append(geom.x)
                                    y_int.append(geom.y)
                                elif geom.geom_type == 'LineString':
                                    x_line, y_line = geom.xy
                                    x_int.extend(x_line)
                                    y_int.extend(y_line)
                        else:
                            x_int, y_int = valid_intersection.xy
                    except NotImplementedError:
                        x_int, y_int = valid_intersection.coords[0]
                    return (x_int[0], y_int[0])
                else:
                    # Shift line2 and try again
                    line2 = LineString([(x, y + shift_step)
                                       for x, y in line2.coords])
                    attempts += 1

        return None, None

    # plotting calculations
    def calculate_shifted_strain(self, stress, strain):
        if self.first_increase_index is None:
            self.first_increase_index = self.find_first_significant_increase(stress, strain)
        self.strain_shifted = strain - strain[self.first_increase_index]

    def calculate_next_decrease_index(self, stress):
        if self.next_decrease_index is None:
            self.next_decrease_index = self.find_next_significant_decrease(
                stress, self.strain_shifted, self.first_increase_index + 1)

    def calculate_youngs_modulus(self, stress, strain):
        start, end = self.first_increase_index, self.next_decrease_index
        if start is not None and end is not None:
            if end - start < 5:
                print("Not enough data points to calculate Young's Modulus accurately.")
                print(f"It was calculated between the strain values {strain[start]} and {strain[end]}")
                print("It is advised to mannually select the region by selecting 'Enable Selection Mode' in the menu bar. ")
                slope = (stress[end] - stress[start]) / (strain[end] - strain[start])
                self.youngs_modulus = slope
                return
            else:
                def linear_func(x, a, b):
                    return a * x + b
                popt, _ = curve_fit(linear_func, strain[start:end], stress[start:end])
                self.youngs_modulus = popt[0]  # slope of the line

    def calculate_strength(self, stress, strain, offset=0.002):
        start, end = self.first_increase_index, self.next_decrease_index
        if start is not None and end is not None and self.youngs_modulus is not None:

            offset_intercept = - (offset * self.youngs_modulus) - (self.youngs_modulus *  strain[start]) # y-intercept for the offset line

            self.offset_line = (self.youngs_modulus * strain) + offset_intercept  # equation for the offset line
            ss_plot = (strain, stress)
            linear_plot = (strain, self.offset_line)

            ys_strain, ys_stress = self.find_interaction_point(ss_plot, linear_plot)
            self.YS = (ys_strain, ys_stress)
            self.IYS = (strain[end], stress[end])

    
    def Calculate_Strength_Alignment(self, OFFSET=0.002):
        # Check if youngs_modulus and IYS are already calculated
        if self.youngs_modulus is not None and self.IYS is not None:
            return
        
        if self.specimen.processed_hysteresis_data  is None or  self.specimen.processed_hysteresis_data.empty:
            self.stress = np.array(self.specimen.stress.values)  # MPa
            self.strain = np.array(self.specimen.strain.values)  # %

            if not self.specimen.data_manager.has_preload_stess_and_strain:
                self.calculate_shifted_strain(self.stress, self.strain)
                self.calculate_next_decrease_index(self.stress)
            self.calculate_youngs_modulus(self.stress, self.strain)

            self.strain_shifted = self.strain_shifted if not self.specimen.data_manager.has_preload_stess_and_strain else self.specimen.data_manager.formatted_data['strain']
            self.calculate_strength(self.stress, self.strain_shifted, OFFSET)
        else:
            self.youngs_modulus = self.specimen.data_manager.modulus 
            self.strain_shifted = self.specimen.processed_data['shiftd strain']
            self.strain_hyst_shifted = self.specimen.processed_hysteresis_data['shiftd strain']

    def plot_curves(self, ax=None, OFFSET=0.002, debugging=False):   
            
        print( f"\n{self.specimen.name}: IYS is {self.specimen.IYS}, ax is {ax}, offset is {OFFSET} , debug mode is {debugging}")

        ESTIMATED_PLASTIC_INDEX_START = 'Start of Plastic Region'
        ESTIMATED_PLASTIC_INDEX_END = 'End of Plastic Region'

        self.prepare_data()
        ax = self.check_ax(ax)

        self.plot_shifted_curve(ax)
        if not self.specimen.data_manager.has_preload_stess_and_strain:
            if self.specimen.processed_hysteresis_data is None:    
                self.plot_offset_curve(ax, OFFSET)
                self.plot_scatter_points(ax)   
                if debugging:
                    self.plot_debugging_curves(ax, ESTIMATED_PLASTIC_INDEX_START, ESTIMATED_PLASTIC_INDEX_END)
            else:
                if not self.specimen.processed_hysteresis_data.empty:
                    self.youngs_modulus = self.specimen.data_manager.modulus 
                    self.strain_hyst_shifted = self.specimen.processed_hysteresis_data['shiftd strain']
                    self.plot_hysteresis_data(ax)
        return ax
    

    def prepare_data(self):
        if self.youngs_modulus is None:
            self.Calculate_Strength_Alignment()

        self.stress = np.array(self.specimen.stress.values)  # MPa
        self.strain = np.array(self.specimen.strain.values)  # %

    def check_ax(self, ax):
        if ax is None:
            ax = plt.gca()
        return ax
    
    def plot_shifted_curve(self, ax):
        ax.plot(self.strain_shifted, self.stress, label="Shifted Stress-Strain Curve")

    def plot_offset_curve(self, ax, OFFSET):
        # filter using boolean indexing, such that offset line is only plotted to the max stress
        if self.youngs_modulus is None or self.offset_line is None:
            return None    
        mask = self.offset_line < max(self.stress)
        offset_line_masked = self.offset_line[mask]
        strain_shifted_masked = self.strain_shifted[mask]
        ax.plot(strain_shifted_masked,offset_line_masked, alpha=0.7,  label=f"{OFFSET*100}% Offset Stress-Strain Curve")
    
    
    def plot_debugging_curves(self, ax, ESTIMATED_PLASTIC_INDEX_START, ESTIMATED_PLASTIC_INDEX_END):
        ax.plot(self.strain, self.stress, linestyle=':', alpha=0.5, label="Original Stress-Strain Curve")
        ax.axvline(self.strain_shifted[self.first_increase_index], linestyle='--', label=ESTIMATED_PLASTIC_INDEX_START)
        if self.next_decrease_index is not None:
            ax.axvline(self.strain_shifted[self.next_decrease_index], linestyle='--', label=ESTIMATED_PLASTIC_INDEX_END)

    def plot_hysteresis_data(self, ax):
        ax.plot(self.specimen.processed_hysteresis_data['shiftd strain'], self.specimen.processed_hysteresis_data['stress'], alpha=0.5, color='navy', linestyle='--', label="Hysteresis Stress-Strain Curve")  
        if self.specimen.data_manager.modulus is None:
            self.specimen.data_manager.get_modulus_from_hysteresis()

        slope = self.specimen.data_manager.modulus
        self.plot_zero_slope_line(ax,slope)
        self.plot_one_pnt_line(ax,slope)
        self.plot_strength_points(ax)

    def plot_zero_slope_line(self, ax,slope):
          
        y = slope * self.strain_hyst_shifted  
        x = self.strain_hyst_shifted 

        # Filter using boolean indexing
        mask = y > 0
        y_filtered = y[mask]
        x_filtered = x[mask]

        ax.plot(x_filtered , y_filtered,  alpha=0.4,color='greenyellow', label='Zere Slope Line')

    def plot_one_pnt_line(self, ax, slope, offset=0.01,  recalculating = False):

        max_strain = max(self.strain_shifted)
        num_points = len(self.strain_shifted)

        x = np.linspace(0, max_strain, num = num_points)
        y = slope *(x - offset)

        linear_plot = x,y
        ss_plot = self.strain_shifted, self.stress

        ps_strain, ps_stress = self.find_interaction_point(ss_plot, linear_plot)
        self.compressive_proof_strength = ps_strain, ps_stress 
        self.specimen.data_manager.compressive_proof_strength = ps_stress

        if recalculating:
            return ps_strain, ps_stress
        
        # Filter using boolean indexing
        max_stress = max(self.stress)
        mask_1 = y > 0
        mask_2 = y < max_stress
        mask  = mask_1 & mask_2
        y_filtered = y[mask]
        x_filtered = x[mask]

        ax.plot(x_filtered , y_filtered ,  alpha=0.6,color='red', label='1% Slope Line')

    def plot_strength_points(self, ax,):
        if self.compressive_proof_strength is not None:
            ps_strain, ps_stress = self.compressive_proof_strength
            if ps_strain is not None and ps_stress is not None:
                ax.scatter(ps_strain, ps_stress, c="green", label=f"Compressive Proof Strength: ({ps_strain:.3f}, {ps_stress:.3f})") 

    def plot_scatter_points(self, ax):
        def plot_iys(ax):
            if self.IYS is not None:
                iys_strain, iys_stress = self.IYS
                if iys_strain is not None and iys_stress is not None:
                    ax.scatter(iys_strain, iys_stress, c="red", label=f"IYS: ({iys_strain:.3f}, {iys_stress:.3f})")

        def plot_ys(ax):
            if self.YS is not None:
                ys_strain, ys_stress = self.YS
                if ys_strain is not None and ys_stress is not None:
                    ax.scatter(ys_strain, ys_stress, c="blue", label=f"YS: ({ys_strain:.3f}, {ys_stress:.3f})")
        
        plot_iys(ax)
        plot_ys(ax)


    @classmethod
    def from_dict(cls, data, specimen, temp_dir=None):
        # Initialize the GraphManager with the data loaded from the CSV files
        manager = cls(specimen)
        for attr,  value in data.items():
            if isinstance( value, str) and  value.endswith('_data.csv'):
                csv_file = value
                file_path = os.path.join(
                    temp_dir, csv_file) if temp_dir else csv_file
                array = np.loadtxt(file_path, delimiter=',')
                setattr(manager, attr, array)
            else:
                setattr(manager, attr, value)  # This line sets attributes that aren't csv files

        return manager


class SpecimenDataManager:
    def __init__(self, specimen, raw_data, area, original_length):
        self.specimen = specimen
        self.hysteresis_data = None
        self.raw_data = None
        self.formatted_raw_data = None
        self.formatted_hysteresis_data = None
        self.raw_data_df = None
        self.split_raw_data_df = None
        self.cross_sectional_area = area
        self.original_length = original_length
        self.headers = []
        self.units = []
        self.modulus = None
        self.pt_70_plt = None
        self._toughness = None
        self._resilience = None
        self._ductility  = None
        self.has_preload_stess_and_strain = False
        self.COLUMN_MAPPING = {
            'stress': ['stress', 'contrainte'],
            'strain': ['strain', 'deformation'],
            'force': ['force', 'load'],
            'displacement': ['displacement', 'elongation',]
        }
        self.import_condition = None

        # Determine the type of data and assign appropriately
        if raw_data:
            if len(raw_data) == 1:
                self.raw_data = raw_data[0]
            else:
                self.hysteresis_data = raw_data[0]
                self.raw_data = raw_data[1]

    def clean_data(self, condition=None):
        self.import_condition = condition
        if 'df' in str(condition):
            self.clean_data_df()
        else:     
            self.clean_raw_data()
        if self.hysteresis_data is not None:
            if 'df' in str(condition):
                self.clean_hysteresis_df( recalculate=True)
            else:
                self.clean_hysteresis_data()

    # add filtering and noise reduction

    def clean_raw_data(self):
        self.formatted_data = self.clean_specific_data(self.raw_data)

        self.raw_data_df = pd.DataFrame({'Raw Data': self.raw_data})
        delimiter = '\t|\\n'
        self.split_raw_data_df = self.raw_data_df['Raw Data'].str.split(delimiter, expand=True)
        self.split_raw_data_df.columns = ['Column 1', 'Column 2', 'Column 3', 'Column 4',
                                          'Column 5', 'Column 6', 'Column 7', 'Column 8', 'Column 9', 'Column 10']
        
    def clean_data_df(self):
        print(f"Cleaning data from dataframe with the following columns:{self.raw_data.columns}")
        self.split_raw_data_df = self.raw_data.copy()
        self.formatted_data = self.raw_data.copy()

    def clean_hysteresis_df(self, recalculate=False):
        if isinstance(self.hysteresis_data, pd.DataFrame):
            # Clean and typecast the hysteresis data
            self.formatted_hysteresis_data = self.hysteresis_data
            if recalculate:
                if 'stress' in self.formatted_hysteresis_data.columns:
                    self.formatted_hysteresis_data['stress'] = self.formatted_hysteresis_data['force'].astype(float) / self.cross_sectional_area
                    self.formatted_hysteresis_data['stress'] = self.formatted_hysteresis_data['stress'].astype(float)

                if 'strain' in self.formatted_hysteresis_data.columns:
                    self.formatted_hysteresis_data['strain'] = self.formatted_hysteresis_data['displacement'].astype(float) / self.original_length
                    self.formatted_hysteresis_data['strain'] = self.formatted_hysteresis_data['strain'].astype(float)
            
    def clean_hysteresis_data(self):
        self.formatted_hysteresis_data = self.clean_specific_data(self.hysteresis_data)

    def _remap_columns(self, df :pd.DataFrame, column_mapping : dict) -> pd.DataFrame:
            remapped_columns = {}
            for standard_name, variations in column_mapping.items():
                for variation in variations:
                    matching_columns = [col for col in df.columns if variation in col.lower()]
                    if matching_columns:
                        remapped_columns[matching_columns[0]] = standard_name
                        break
            return df.rename(columns=remapped_columns)  

    def clean_specific_data(self, data):
        time_row = self.find_time_row(data)
        headers, units = self.extract_headers_and_units(data, time_row)
        data_rows = self.extract_data_rows(data, time_row, headers)
        fomated_data = self.format_data(data_rows, headers)
        return self._remap_columns(fomated_data, self.COLUMN_MAPPING)

    @staticmethod
    def find_time_row(data):
        return next((index for index, line in enumerate(data) if line.startswith('Data Acquisition')), None)

    @staticmethod
    def extract_headers_and_units(data, time_row):
        headers_row = data[time_row + 1].split()
        units_row = data[time_row + 2].split()

        headers = [header for header in headers_row if header in ['Displacement', 'Force', 'Time']]
        units = [unit for unit, header in zip(units_row, headers_row) if header in headers]

        return headers, units

    @staticmethod
    def extract_data_rows(data, time_row, headers):
        data_rows = []
        for line in data[time_row + 3:]:
            if line.startswith('Data Acquisition'):
                continue
            if line.strip():  # Check if the line is not empty or contains only white spaces
                data_rows.append(line.split()[:3])
        return pd.DataFrame(data_rows, columns=headers)

    @staticmethod
    def format_data(data, headers):
        pattern = r'^\D*$'  # this pattern matches any string that does not contain digits
        mask = data['Displacement'].str.match(pattern)
        return data[~mask].astype({header: float for header in headers})

    def add_stress_and_strain(self, condition=None, recalculate=False):
        if 'stress' in str(condition):
            # add condition to control recalculating stress and strain

            if 'force' not in self.formatted_data.columns:
                self.has_preload_stess_and_strain = True
                print("No force data found. Please check the data.")

            if recalculate and not self.has_preload_stess_and_strain:
                self.formatted_data['stress'] = ( self.formatted_data['force'] / self.cross_sectional_area)
                self.formatted_data['strain'] = ( (self.formatted_data['displacement']) / self.original_length)  
            return None
            raise NotImplementedError("Remapping stress and strain data is not yet implemented.")
        
        self.formatted_data['stress'] = ( self.formatted_data['force'] / self.cross_sectional_area)*-1
        self.formatted_data['strain'] = ( (self.formatted_data['displacement']) / self.original_length)*-1
        
        if self.specimen.processed_hysteresis_data is not None:
            self.formatted_hysteresis_data['stress'] = ( self.formatted_hysteresis_data['force'] / self.cross_sectional_area)*-1
            self.formatted_hysteresis_data['strain'] = ( (self.formatted_hysteresis_data ['displacement']) / self.original_length)*-1


    def align_hysteresis_data(self, max_stress_index):
        
        max_stress_hysteresis = self.formatted_hysteresis_data["stress"].iloc[max_stress_index]

        first_stress_index_raw_at_max = np.argwhere(self.formatted_data["stress"] > max_stress_hysteresis)

        if first_stress_index_raw_at_max.size > 0:
            first_stress_index_raw_at_max = first_stress_index_raw_at_max[0][0]
            
            # Determine the local maximum stress after the point where the stress exceeds max_stress_hysteresis
            local_maxima_indices = argrelextrema(self.formatted_data.iloc[first_stress_index_raw_at_max:]["stress"].values, np.greater)
            if local_maxima_indices[0].size > 0:
                # Adjust the index to match the original dataframe
                local_max_index = local_maxima_indices[0][0] + first_stress_index_raw_at_max
            else:
                # If there's no local maximum, find the closest stress index as before
                local_max_index = (self.formatted_data["stress"] - max_stress_hysteresis).abs().idxmin()
            
            # Find the closest corresponding stress in the masked raw data
            closest_stress_index_raw = (self.formatted_data.iloc[:local_max_index]["stress"] - max_stress_hysteresis).abs().idxmin()
        else:
            # If there's no stress greater than max_stress_hysteresis, find the closest stress index as before
            closest_stress_index_raw = (self.formatted_data["stress"] - max_stress_hysteresis).abs().idxmin()

        # Get the corresponding strain for closest stress in raw data
        closest_strain_raw = self.formatted_data["strain"].iloc[closest_stress_index_raw]
        closest_stress_raw = self.formatted_data["stress"].iloc[closest_stress_index_raw]

        self.pt_70_plt = closest_strain_raw,closest_stress_raw
        self.pt_20_plt = self.formatted_data["strain"].iloc[-1], self.formatted_data["stress"].iloc[-1]

        # Calculate the offset between the strain of max stress point in hysteresis data and raw data
        strain_offset = self.formatted_hysteresis_data["strain"].iloc[max_stress_index] - closest_strain_raw

        # Adjust the strain data in hysteresis data by subtracting the offset
        self.formatted_hysteresis_data["strain"] = self.formatted_hysteresis_data["strain"] - strain_offset

    def get_modulus_from_hysteresis(self):
        # self.formatted_hysteresis_data = median_filter(self.formatted_hysteresis_data, denoise_strength = 21)
        force = self.formatted_hysteresis_data['force'].values
        max_force_index = np.argmax(force*-1) if 'df' not in str(self.import_condition) else np.argmax(force)
        # negative_force = force*-1
        # max_force_index = np.argmax(negative_force)
        max_stress_index = np.argmax(self.formatted_hysteresis_data['stress'].values)

        self.align_hysteresis_data(max_stress_index)

        assert max_force_index == max_stress_index, 'The max force and max stress do not occur at the same index'
        peak_pt_by_force = self.formatted_hysteresis_data["displacement"].iloc[max_force_index], self.formatted_hysteresis_data["force"].iloc[max_force_index]
        peak_pt_by_stress = self.formatted_hysteresis_data["strain"].iloc[max_stress_index], self.formatted_hysteresis_data["stress"].iloc[max_stress_index]

        end_pt_by_force = self.formatted_hysteresis_data["displacement"].iloc[-1], self.formatted_hysteresis_data["force"].iloc[-1]
        end_pt_by_stress = self.formatted_hysteresis_data["strain"].iloc[-1], self.formatted_hysteresis_data["stress"].iloc[-1]

        modulus_by_force = (peak_pt_by_force[1] - end_pt_by_force[1]) / (peak_pt_by_force[0] - end_pt_by_force[0])
        modulus_by_stress = (peak_pt_by_stress[1] - end_pt_by_stress[1]) / (peak_pt_by_stress[0] - end_pt_by_stress[0])

        self.modulus = modulus_by_stress
        self.shift_data()

    def get_b_intercept(self):
        # y = mx + b 
        slope = self.modulus

        pt = self.pt_70_plt
        x, y = pt
        b = y - (slope * x)
        return b
    
    def shift_data(self):
       
        b = self.get_b_intercept()
        slope = self.modulus
        target_strain = -b / slope

        print(f"Modulus: {slope} and the b intercept: {b} so x should be {b/slope}")

        strain_shift  = abs(target_strain)

        # Shift the strain data in both datasets
        self.formatted_data['shiftd strain'] = self.formatted_data['strain'] - strain_shift
        self.formatted_hysteresis_data['shiftd strain'] = self.formatted_hysteresis_data['strain'] - strain_shift
        self.shift_offset = strain_shift

    @property
    def toughness(self):
        if self._toughness is None:
            self._toughness = self.calculate_toughness()
        return self._toughness 
    
    @property
    def ductility(self):
        if self._ductility is None:
            self._ductility = self.calculate_ductility()
        return self._ductility 
    
    @property
    def resilience(self):
        if self._resilience is None:
            self._resilience = self.calculate_resilience()
        return self._resilience 
    
    

    def calculate_toughness(self):
        return np.trapz(self.specimen.stress, self.specimen.shifted_strain)

    def calculate_ductility(self):
        return max(self.specimen.shifted_strain)

    def calculate_resilience(self):
        if self.specimen.IYS is None:
            return None
        yield_stress, yield_strain = self.specimen.IYS
        return 0.5 * yield_stress * yield_strain

    @classmethod
    def from_dict(cls, data, specimen, temp_dir=None):
        # Initialize the DataManager with the data loaded from the CSV files
        manager = cls(specimen, None, data['cross_sectional_area'], data['original_length'])
        for attr, value in data.items():
            if isinstance( value, str) and value.endswith('_data.csv'):
                csv_file = value
                file_path = os.path.join(
                    temp_dir, csv_file) if temp_dir else csv_file
                df = pd.read_csv(file_path)
                setattr(manager, attr, df)

            if attr == 'has_preload_stess_and_strain':
                setattr(manager, attr, value)

        return manager
    
    def save(self, directory):
        # Check for formatted and hysteresis data - keyword and will be short circuited to false if any of the left side conditions are false
        is_formatted_data = self.formatted_data is not None and isinstance(self.formatted_data, pd.DataFrame) and not self.formatted_data.empty
        is_hysteresis_data = self.formatted_hysteresis_data is not None and isinstance(self.formatted_hysteresis_data, pd.DataFrame) and not self.formatted_hysteresis_data.empty

        # remove end line from name and spaces
        name = self.specimen.name.replace('\n', '').replace(' ', '_')
        file_name = f"{name}.xlsx"
        file_path = os.path.join(directory, file_name)

        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            workbook = writer.book

            # Description of the data and the collection process
            workbook.add_worksheet('Specimen Info').write('A1', f'Specimen Name: {name}')

            # if there is formatted data and hysteresis data, save both in same file
            if is_formatted_data and is_hysteresis_data:
                self._write_dataframe(writer, 'Formatted Data', self.formatted_data)
                self._write_dataframe(writer, 'Hysteresis Data', self.formatted_hysteresis_data)
            # if there is only formatted data, save it in a file
            elif is_formatted_data:
                self._write_dataframe(writer, 'Formatted Data', self.formatted_data)
            # else error make sure there fomatted data is computed first
            else:
                raise ValueError("No data available to save. Make sure the data is computed first.")
    
    def _write_dataframe(self, writer, sheet_name, dataframe):
        # Starting row for the data (after the headers)
        startrow = 3

        # Save the DataFrame to the specified sheet
        dataframe.to_excel(writer, sheet_name=sheet_name, startrow=startrow, index=False)

        # Get the xlsxwriter workbook and worksheet objects
        worksheet = writer.sheets[sheet_name]

        # Get the dimensions of the dataframe
        (max_row, max_col) = dataframe.shape
        column_settings = [{'header': column.capitalize()} for column in dataframe.columns]

        # Add a table to the worksheet
        worksheet.add_table(startrow, 0, startrow + max_row, max_col - 1, {
            'columns': column_settings,
            'style': 'Table Style Medium 6'
        })
