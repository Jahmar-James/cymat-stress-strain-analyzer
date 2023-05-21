import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiPoint, Point


class Specimen:
    def __init__(self, name, data, length, width, thickness, weight):
        self.name = name
        self.length = float(length)
        self.width = float(width)
        self.thickness = float(thickness)
        self.weight = float(weight)
        self.calculate_properties()
        self.data_manager = SpecimenDataManager(
            self, data, self.cross_sectional_area, self.original_length)
        self.graph_manager = SpecimenGraphManager(self)
        self.manual_strain_shift = 0

    def calculate_properties(self):
        self.cross_sectional_area = self.length * self.width  # mm^2
        self.original_length = self.thickness  # mm
        volume = self.length * self.width * self.thickness  # mm^3
        self.density = self.weight / (volume * 10**(-3))

    def display_properties_in_label(self, label):
        properties_text = f"Specimen Properties\n\n"
        properties_text += f"Name: {self.name}\n"
        properties_text += f"Dim (L W t): \n{self.length:.2f} x {self.width:.2f} x {self.weight:.2f}(mm)\n"
        properties_text += f"Weight: {self.weight:.4f} g\n"
        properties_text += f"Density: {self.density:.4f} (g/cc)\n"
        properties_text += f"Cross-sectional: {self.cross_sectional_area} (mm^2)\n"
        properties_text += f"Original Length: {self.original_length:.2f} (mm)"
        label.config(text=properties_text)

    def process_data(self):
        self.data_manager.clean_data()
        self.data_manager.add_stress_and_strain()

    def find_IYS_align(self):
        # self.graph_manager.Calculate_IYS_Alignment(self.data_manager.formatted_data)
        self.graph_manager.Calculate_IYS_Alignment()

    def plot_stress_strain(self, ax):
        ax.plot(self.shifted_strain, self.stress, label=self.name)

    def plot_curves(self, ax, OFFSET=0.002, debugging=True):
        print(
            f"IN spec, ax is {ax}offset is {OFFSET} , debug mode is {debugging}")
        self.graph_manager.plot_curves(ax, OFFSET, debugging)

    @property
    def strain(self):
        return self.data_manager.formatted_data['strain']

    @property
    def stress(self):
        return self.data_manager.formatted_data['stress']

    @property
    def force(self):
        return self.data_manager.formatted_data['Force'] * -1

    @property
    def displacement(self):
        return self.data_manager.formatted_data['Displacement'] * -1

    @property
    def shifted_strain(self):
        return self.graph_manager.strain_shifted + self.manual_strain_shift

    @property
    def shifted_displacement(self):
        print("shift displcement")
        force = self.force
        displacement = self.displacement
        first_increase_index = self.graph_manager.find_first_significant_increase(
            force, displacement)
        return displacement - displacement[first_increase_index]

    @property
    def IYS(self):
        return self.graph_manager.IYS

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
        specimen.data_manager = SpecimenDataManager.from_dict(
            data['data_manager'], specimen, temp_dir=temp_dir)
        specimen.graph_manager = SpecimenGraphManager.from_dict(
            data['graph_manager'], specimen, temp_dir=temp_dir)

        return specimen


class SpecimenGraphManager:
    def __init__(self, specimen):
        self.specimen = specimen
        self.first_increase_index = None
        self.next_decrease_index = None
        self.IYS = None
        self.youngs_modulus = None

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
            print(
                "Warning: NaN values detected in stress or strain data. Please handle them.")

        stress_diff = np.diff(stress)
        strain_diff = np.diff(strain)
        print(f" Specimen{self.specimen.name}\n")

        strain_diff_masked = np.ma.masked_where(strain_diff == 0, strain_diff)
        rate_of_change = np.ma.divide(stress_diff, strain_diff_masked)
        rate_of_change = rate_of_change.filled(np.nan)

        max_abs_rate_of_change = np.nanmax(np.abs(rate_of_change))
        roc_normalized = np.divide(rate_of_change, max_abs_rate_of_change, out=np.zeros_like(
            rate_of_change), where=max_abs_rate_of_change != 0)

        # rate_of_change = stress_diff / strain_diff
        # roc_normalized = rate_of_change / np.max(np.abs(rate_of_change))

        print(
            f"\n Rate of chanage{rate_of_change} and\n roc norm : {roc_normalized}")

        # Find the index of the first significant increase in the rate of change within tolerance
        i = np.argmax((roc_normalized >= threshold) & (
            self.specimen.force[:-1] >= min_force) & (self.specimen.force[:-1] <= max_force))

        print(
            f"Index of {i}  verser argmax i {i} with threshold of the first significant increase in stress: {threshold}")
        # If the index is zero, find the first index greater than zero.
        if i == 0:
            i = np.argmax(self.specimen.force > 500)
            print(
                f"No first significant increase Found, using force lead to a index of {i}")

        if ((strain[0]-strain[i]) < (-0.04)):
            print("moved too much")
            i = np.argmax((strain > 0) & (self.specimen.force >= min_force) & (
                self.specimen.force <= max_force))

        if testing:
            x = np.arange(len(roc_normalized))
            plt.plot(x, roc_normalized, linestyle=":")
            plt.title("find_first_significant_increase")
            plt.show()

        print(
            f"First significant increase index: {i} has a stress of {stress[i]:.2f} MPa and strain of {strain[i]:.6f} and force of {self.specimen.force[i]} N")
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
            print(
                "Warning: NaN values detected in stress or strain data. Please handle them.")

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

        print(f"inside of next")
        print(f"roc is {rate_of_change} and roc norm = {roc_normalized}")
        # print(f"\n roc max is {np.nanmax(rate_of_change)} and roc norm  max = {np.nanmax(roc_normalized)}")

        print(
            f"threshold of the next significant decrease in stress after the given start index: {threshold}")

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

    def find_interaction_point(self, plot1, plot2, min_dist_from_origin=0.02, max_attempts=3):
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
                line2 = LineString([(x, y + shift_step)
                                   for x, y in line2.coords])
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
                    x_int, y_int = valid_intersection.coords[0]
                    return (x_int, y_int)
                else:
                    # Shift line2 and try again
                    line2 = LineString([(x, y + shift_step)
                                       for x, y in line2.coords])
                    attempts += 1

        return None, None

    # plotting calculations
    def calculate_shifted_strain(self, stress, strain):
        if self.first_increase_index is None:
            self.first_increase_index = self.find_first_significant_increase(
                stress, strain)
        self.strain_shifted = strain - strain[self.first_increase_index]

    def calculate_next_decrease_index(self, stress):
        if self.next_decrease_index is None:
            self.next_decrease_index = self.find_next_significant_decrease(
                stress, self.strain_shifted, self.first_increase_index + 1)

    def calculate_youngs_modulus(self, stress):
        if self.youngs_modulus is None and self.next_decrease_index is not None:
            self.youngs_modulus = (stress[self.next_decrease_index] - stress[self.first_increase_index]) / (
                self.strain_shifted[self.next_decrease_index] - self.strain_shifted[self.first_increase_index])
        print(
            f" youngs : {self.youngs_modulus} for first of {self.first_increase_index} and next of {self.next_decrease_index}")

    def calculate_offset_line(self, OFFSET):
        if self.youngs_modulus is not None:
            self.strain_offset = self.strain_shifted + OFFSET
            self.offset_line = self.strain_offset * self.youngs_modulus
        print(f" create offset line with offset at: {OFFSET}")

    def calculate_iys(self, stress):
        if self.youngs_modulus is not None:
            plot1 = (self.strain_offset, self.offset_line)
            plot2 = (self.strain_shifted, stress)
            iys_strain, iys_stress = self.find_interaction_point(plot1, plot2)
            self.IYS = (iys_strain, iys_stress)
        print(f" IYS : {self.IYS}")

    def Calculate_IYS_Alignment(self, OFFSET=0.002):
        # Check if youngs_modulus and IYS are already calculated
        if self.youngs_modulus is not None and self.IYS is not None:
            return

        stress = np.array(self.specimen.stress)  # MPa
        strain = np.array(self.specimen.strain)  # %

        self.calculate_shifted_strain(stress, strain)
        self.calculate_next_decrease_index(stress)
        self.calculate_youngs_modulus(stress)
        self.calculate_offset_line(OFFSET)
        self.calculate_iys(stress)

        print(
            f"Graph manger: IYS is {self.IYS}, youngs is {self.youngs_modulus} - IN Calculate_IYS_Alignment ")

    def plot_curves(self, ax=None, OFFSET=0.002, debugging=False):
        print(
            f"IYS is {self.specimen.IYS}, ax is {ax}, offset is {OFFSET} , debug mode is {debugging}")
        self.Calculate_IYS_Alignment()

        self.stress = np.array(self.specimen.stress.values)  # MPa
        self.strain = np.array(self.specimen.strain.values)  # %

        if ax is None:
            ax = plt.gca()
        ax.axhline(0, color='black', linestyle='--')
        ax.axvline(0, color='black', linestyle='--')
        ax.plot(self.strain_shifted, self.stress,
                label="Shifted Stress-Strain Curve")
        ax.plot(self.strain_offset, self.offset_line,
                label=f"{OFFSET*100}% Offset Stress-Strain Curve")
        if debugging:
            ax.plot(self.strain, self.stress, linestyle=':',
                    label="Original Stress-Strain Curve")
            ax.axvline(self.strain_shifted[self.first_increase_index],
                       color='r', linestyle='--', label='First Significant Increase')
            if self.next_decrease_index is not None:
                ax.axvline(self.strain_shifted[self.next_decrease_index],
                           color='g', linestyle='--', label='Next Significant Decrease')
        iys_strain, iys_stress = self.IYS
        if iys_strain is not None and iys_stress is not None:
            ax.scatter(iys_strain, iys_stress, c="red",
                       label=f"IYS: ({iys_strain:.6f}, {iys_stress:.6f})")
        ax.set_xlabel("Strain")
        ax.set_ylabel("Stress (MPa)")

    @classmethod
    def from_dict(cls, data, specimen, temp_dir=None):
        # Initialize the GraphManager with the data loaded from the CSV files
        manager = cls(specimen)
        for attr, csv_file in data.items():
            if isinstance(csv_file, str) and csv_file.endswith('_data.csv'):
                file_path = os.path.join(
                    temp_dir, csv_file) if temp_dir else csv_file
                array = np.loadtxt(file_path, delimiter=',')
                setattr(manager, attr, array)

        return manager


class SpecimenDataManager:
    def __init__(self, specimen, raw_data, area, original_length):
        self.specimen = specimen
        self.data = None
        self.raw_data = raw_data
        self.data_shiftd = None
        self.cross_sectional_area = area
        self.original_length = original_length
        self.headers = []
        self.units = []

    def clean_data(self,):
        raw_data = self.raw_data

        # Find the row where 'Data Acquisition' starts
        for index, line in enumerate(raw_data):
            if line.startswith('Data Acquisition'):
                time_row = index
                break

        # Extract headers and units from raw data
        headers_row = raw_data[time_row + 1].split()
        units_row = raw_data[time_row + 2].split()

        self.headers = [header for header in headers_row if header in [
            'Displacement', 'Force', 'Time']]
        self.units = [unit for unit, header in zip(
            units_row, headers_row) if header in self.headers]

        # Extract data rows from raw data
        data_rows = []
        for line in raw_data[time_row + 3:]:
            if line.startswith('Data Acquisition'):
                continue
            if line.strip():  # Check if the line is not empty or contains only white spaces
                data_rows.append(line.split()[:3])

        # Format data rows into a DataFrame
        data = pd.DataFrame(data_rows, columns=self.headers)
        pattern = r'^\D*$'  # this pattern matches any string that does not contain digits
        mask = data['Displacement'].str.match(pattern)
        data = data[~mask]
        self.formatted_data = data.astype(
            {'Displacement': float, 'Force': float, 'Time': float})

        self.raw_data_df = pd.DataFrame({'Raw Data': raw_data})
        delimiter = '\t|\\n'
        self.split_raw_data_df = self.raw_data_df['Raw Data'].str.split(
            delimiter, expand=True)
        self.split_raw_data_df.columns = ['Column 1', 'Column 2', 'Column 3', 'Column 4',
                                          'Column 5', 'Column 6', 'Column 7', 'Column 8', 'Column 9', 'Column 10']

    def add_stress_and_strain(self):
        self.formatted_data['stress'] = (
            self.formatted_data['Force'] / self.cross_sectional_area)*-1
        self.formatted_data['strain'] = (
            (self.formatted_data['Displacement']) / self.original_length)*-1

    def export_to_excel(self, output_path):
        properties_df = pd.DataFrame({'Specimen Name': [self.specimen.name],
                                      'Density (g/cc)': [self.specimen.density],
                                      'Cross-sectional Area (mm^2)': [self.cross_sectional_area],
                                      'Original Length (mm)': [self.original_length],
                                      'Date of Export': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]})
        # Write properties DataFrame and data to Excel file
        if 'stress' not in self.formatted_data.columns:
            self.add_stress_and_strain()

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            properties_df.to_excel(
                writer, sheet_name=self.specimen.name, index=False)
            self.formatted_data.to_excel(
                writer, sheet_name=self.specimen.name, startrow=2, index=False)

    @classmethod
    def from_dict(cls, data, specimen, temp_dir=None):
        # Initialize the DataManager with the data loaded from the CSV files
        manager = cls(specimen, None,
                      data['cross_sectional_area'], data['original_length'])
        for attr, csv_file in data.items():
            if isinstance(csv_file, str) and csv_file.endswith('_data.csv'):
                file_path = os.path.join(
                    temp_dir, csv_file) if temp_dir else csv_file
                df = pd.read_csv(file_path)
                setattr(manager, attr, df)

        return manager
