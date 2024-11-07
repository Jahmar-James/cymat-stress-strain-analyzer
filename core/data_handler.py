import glob
import json
import os
import string
import tempfile
import threading
import zipfile
from pathlib import Path
from tkinter import filedialog
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import trapz
from scipy.interpolate import interp1d
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import curve_fit
from scipy.signal import argrelextrema, medfilt
from tabulate import tabulate

from ms_file_handling.excel_exporter import ExcelExporter
from ms_file_handling.ms_word_exporter import WordExporter
from specimens.specimen import Specimen, SpecimenDataManager, SpecimenGraphManager
from standards.specimen_DIN import SpecimenDINAnalysis

DIN_PROPERTIES = ["Rplt", "Rplt_E", "ReH", "Ev", "Eff", "Aplt_E", "AeH", "m"]

DIN_PROPERTIES_OLD = ["Rplt", "Rplt_E", "ReH", "Ev", "Eff", "ReH_Rplt_ratio", "Aplt_E", "AeH", "Rp1", "m"]


def is_float(value: str) -> bool:
    return value.replace(".", "", 1).isdigit()


def moving_average(data, window_size):
    return data.rolling(window_size, min_periods=1).mean()


def median_filter(data, denoise_strength=21):
    return data.apply(lambda x: medfilt(x, denoise_strength))


def gaussian_smoothing(data, sigma):
    return data.apply(lambda x: gaussian_filter1d(x, sigma=sigma))


class DataValidator:
    REQUIRED_COLUMNS = {"stress_strain": ["stress", "strain"], "displacement_force": ["displacement", "force"]}

    COLUMN_MAPPING = {
        "stress": ["stress", "contrainte"],
        "strain": ["strain", "deformation"],
        "force": ["force", "load"],
        "displacement": [
            "displacement",
            "elongation",
            "extension",
        ],
        "Time": ["time", "temps", "Time"],
    }

    @staticmethod
    def validate_columns(data):
        if isinstance(data, pd.DataFrame) and not data.empty:
            print(f"Data has been imported successfully with the following columns: {list(data.columns)}")
            columns = [col.lower() for col in data.columns]
            if any(required in col for required in DataValidator.REQUIRED_COLUMNS["stress_strain"] for col in columns):
                print("Stress and strain data found.")
                return "stress_strain_df"
            elif any(
                required in col for required in DataValidator.REQUIRED_COLUMNS["displacement_force"] for col in columns
            ):
                print("Displacement and force data found. Further processing required.")
                return "displacement_force_df"
            else:
                raise ValueError(f"Data must contain columns related to either 'stress_strain' or 'displacement_force'")
        else:
            return None

    @staticmethod
    def remap_df_columns(df: pd.DataFrame, column_mapping: dict = None) -> pd.DataFrame:
        if column_mapping is None:
            column_mapping = DataValidator.COLUMN_MAPPING

        # Do necessary conversions
        original_columns = df.columns
        # strain_variations = column_mapping.get("strain", [])
        # for col in original_columns:
        #     if any(variation in col.lower() for variation in strain_variations) and "%" in col:
        #         df[col] = df[col].astype(float) * 100
        #         print(f"Converted strain from % to mm/mm for column: {col}")

        # Remap the columns
        remapped_columns = {}
        for standard_name, variations in column_mapping.items():
            for variation in variations:
                matching_columns = [col for col in df.columns if variation in col.lower()]
                if matching_columns:
                    remapped_columns[matching_columns[0]] = standard_name
                    break

        return df.rename(columns=remapped_columns)

    @staticmethod
    def merge_units_into_column_names_for_row(units_row: int = 0, data: pd.DataFrame = None):
        # Check if data is a DataFrame
        if not isinstance(data, pd.DataFrame):
            print("Error: The provided data is not a valid DataFrame.")
            return data

        # Check if units_row is an integer and within the valid range of DataFrame indices
        if not isinstance(units_row, int) or units_row < 0 or units_row >= len(data):
            print(f"Error: The units_row index {units_row} is not valid.")
            return data

        # Check units if they are numeric and not null
        units = data.iloc[units_row]
        if units.apply(lambda x: pd.to_numeric(x, errors="coerce")).notna().any():
            print("Warning: Units row contains numeric values. Returning the original DataFrame.")
            return data
        if units.isnull().all():
            print(f"Error: No units found in the row {units_row}.")
            return data

        # Create a copy of the DataFrame to avoid modifying the original
        updated_data = data.copy()

        # Merge the units with the column names
        updated_column_names = []
        for i, col in enumerate(updated_data.columns):
            unit = units[i] if pd.notnull(units[i]) else ""
            if unit:
                updated_column_names.append(f"{col} ({unit})")
            else:
                updated_column_names.append(col)

        # Update the column names
        updated_data.columns = updated_column_names

        # Drop the row with the units if necessary (optional)
        updated_data.drop(index=units_row, inplace=True)

        # Return the modified DataFrame
        return updated_data

# data_handler.py
class DataHandler:
    """
    Handles data manipulation and management tasks for the application.

    Attributes:
    app (object): The main application object.
    excel_exporter (ExcelExporter): An ExcelExporter instance for exporting data to Excel.
    widget_manager (WidgetManager): Manages the GUI widgets of the application.
    button_actions (dict): Maps button names to their corresponding actions.
    properties_df (DataFame): df containing key properties for all selected speicmen
    """

    def __init__(self, app):
        self.app = app
        self.excel_exporter = ExcelExporter(self.app)
        self.word_exporter = WordExporter(self.app)
        self.general_properties = [
            "name",
            "length",
            "width",
            "thickness",
            "weight",
            "density",
            "youngs_modulus",
            "E20_kJ_m3",
            "E50_kJ_m3",
            "E80_kJ_m3",
            "E20_kJ_kg",
            "E50_kJ_kg",
            "E80_kJ_kg",
        ]
        self.data_manager_properties = ["toughness", "ductility", "resilience"]
        self.hysteresis_data_manager_properties = ["modulus", "compressive_proof_strength"]
        self.din_properties = DIN_PROPERTIES
        self.properties_df = pd.DataFrame()
        self.avg_20_pt = None
        self.avg_70_pt = None

        self.data_analysis_buttons = []  # First group
        self.data_management_buttons = []  # Second group

        self.SUPPORTED_FILE_TYPES = [("Supported types", "*.dat *.xls *.xlsx *.csv"), ("All files", "*.*")]

    def set_widget_manager(self, widget_manager):
        self.widget_manager = widget_manager

    def set_button_actions(self, button_actions):
        self.button_actions = button_actions

    @property
    def average_of_specimens(self):
        return self.app.variables.average_of_specimens

    def validate_and_import_data(self) -> Optional[str]:
        name, length, width, thickness, weight = self.get_specimen_properties()

        if not all([name, length, width, thickness, weight]):
            return "All fields must be filled."

        if not all([is_float(value) for value in [length, width, thickness, weight]]):
            return "Length, Width, Thickness, and Weight must be numbers."
        return None

    def process_file(self, file_path):
        def read_raw_data(file_path):
            with open(file_path, "r") as file:
                return file.readlines()

        if file_path:
            # Display file name above the 'Import Data' button
            raw_data = read_raw_data(file_path)
            return raw_data, None

    def process_excel(self, file_path):
        data = pd.read_excel(file_path)
        data = DataValidator.remap_df_columns(
            data,
        )
        data_fields = DataValidator.validate_columns(data)
        return data, data_fields

    def process_csv(self, file_path):
        data = pd.read_csv(file_path)

        # Temporary fix for units row ( New format) - will be migrating sample creation to a new pattern
        data = DataValidator.merge_units_into_column_names_for_row(units_row=0, data=data)
        # to numeric

        data = data.apply(pd.to_numeric, errors="ignore")
        data = DataValidator.remap_df_columns(data)
        data_fields = DataValidator.validate_columns(data)
        return data, data_fields

    def import_specimen_data(self):
        raw_data_list = []  # Create an empty list to store raw data
        condtion_list = []  # Create an empty list to store condtion data
        data_types = ["Pre-loading data", "General Full-Load data"]

        if self.app.variables.prelim_mode.get():
            file_path = self.ask_for_file()
            process_method = self.get_processing_method(file_path)
            raw_data, condtion = process_method(file_path)
            raw_data_list.append(raw_data)
            condtion_list.append(condtion)
        else:
            for data_type in data_types:
                file_path = self.ask_for_file(data_type)
                process_method = self.get_processing_method(file_path)
                raw_data, condtion = process_method(file_path)
                raw_data_list.append(raw_data)
                condtion_list.append(condtion)

        if file_path:
            # Now the list raw_data_list contains all the raw data. We can process it now.
            name, length, width, thickness, weight = self.get_specimen_properties()

            specimen = Specimen(name, raw_data_list, length, width, thickness, weight)
            specimen.calculate_properties()

            filename = Path(file_path).name
            self.widget_manager.update_ui_elements(filename, specimen)
            specimen.process_data(condtion_list)
            tab_id = self.widget_manager.create_new_tab(name)
            self.app.variables.add_specimen(tab_id, specimen)
            self.button_actions.clear_entries()
            # Run specimen.find_IYS_align() in a separate thread
            find_IYS_align_thread = threading.Thread(target=specimen.find_IYS_align)
            # Start the new thread
            find_IYS_align_thread.start()
            # Wait for the find_IYS_align_thread to finish
            find_IYS_align_thread.join()
            if len(self.app.variables.specimens) > 1:
                self.button_actions.plot_all_specimens()

    def get_processing_method(self, file_path):
        if file_path is None:
            return None
        if file_path.endswith(".dat"):
            return self.process_file
        elif file_path.endswith((".xls", ".xlsx")):
            return self.process_excel
        elif file_path.endswith(".csv"):
            return self.process_csv
        else:
            raise ValueError("Unsupported file type")

    def ask_for_file(self, data_type=None):
        file_extension, _ = self.SUPPORTED_FILE_TYPES
        title = (
            f"Select {data_type} file"
            if data_type
            else f"Select a data file from the supported types ({file_extension})"
        )
        return filedialog.askopenfilename(title=title, filetypes=self.SUPPORTED_FILE_TYPES)

    def get_specimen_properties(self):
        name = self.widget_manager.name_entry.get()
        length = self.widget_manager.length_entry.get()
        width = self.widget_manager.width_entry.get()
        thickness = self.widget_manager.thickness_entry.get()
        weight = self.widget_manager.weight_entry.get()
        return name, length, width, thickness, weight

    def split_hysteresis_data(self, data):
        # Cymat Data had historical Negative values for force
        max_force_index = np.argmax(-data["force"].values)
        # if not a negative value, then find the max value
        if not max_force_index:
            max_force_index = np.argmax(data["force"].values)
        return data[: max_force_index + 1], data[max_force_index + 1 :]

    def clean_split_hysteresis_data_by_force(self, data):
        return data[data["force"].abs() > 50]

    def get_common_force(self, split_data_1, split_data_2):
        min_force_1 = max(abs(data["force"].min()) for data in split_data_1)
        min_force_2 = min(abs(data["force"].max()) for data in split_data_2)

        max_force_1 = min(abs(data["force"].max()) for data in split_data_1)
        max_force_2 = max(abs(data["force"].min()) for data in split_data_2)

        max_force_common = min(max_force_1, max_force_2)
        min_force_common = max(min_force_1, min_force_2)

        max_num_points_1 = max(len(data) for data in split_data_1)
        max_num_points_2 = max(len(data) for data in split_data_2)

        common_force_1 = np.linspace(min_force_common, max_force_common, num=max_num_points_1)
        common_force_2 = np.linspace(max_force_common, min_force_common, num=max_num_points_2)
        common_force_2 = common_force_2[::-1]  # Reverse array for second half

        return common_force_1, common_force_2

    def interpolate_data(self, data, common_force, cross_sectional_area, original_length, testing_interpolation=False):
        # Select only the required columns
        df = data.loc[:, ["stress", "strain", "shiftd strain"]]
        data = data.loc[:, ["force", "displacement", "Time"]]

        # Create interpolating functions
        f_displacement = interp1d(abs(data["force"]), data["displacement"])
        f_time = interp1d(abs(data["force"]), data["Time"])

        # Remove out of bounds values
        common_force = np.clip(common_force, np.min(abs(data["force"])), np.max(abs(data["force"])))

        # Perform the interpolation
        interpolated_displacement = f_displacement(common_force)
        interpolated_time = f_time(common_force)

        # Calculate stress and strain
        stress = common_force / cross_sectional_area
        strain = (interpolated_displacement / original_length) * -1

        f_shiftd_strain = interp1d(abs(data["force"]), df["shiftd strain"])
        interpolated_shiftd_strain = f_shiftd_strain(common_force)

        if testing_interpolation:
            # Testing interpolation difference
            f_stress = interp1d(abs(data["force"]), df["stress"])
            f_strain = interp1d(abs(data["force"]), df["strain"])
            f_shiftd_strain = interp1d(abs(data["force"]), df["shiftd strain"])

            interpolated_stress = f_stress(common_force)
            interpolated_strain = f_strain(common_force)
            interpolated_shiftd_strain = f_shiftd_strain(common_force)

            # Calculate difference between new and old stress/strain
            stress_diff = stress - interpolated_stress
            strain_diff = strain - interpolated_strain
            shifted_strain_diff = strain - interpolated_shiftd_strain

            offset = np.mean(df["strain"] - df["shiftd strain"])
            shifted_strain = strain - offset
            shifted_strain_inter = interpolated_strain - offset

            # Plot the difference between the old and new stress/strain
            fig, ax = plt.subplots(2, 2, figsize=(10, 7))
            ax[0, 0].plot(common_force, stress_diff, label="Stress Difference", alpha=0.6)
            ax[0, 0].plot(common_force, strain_diff, label="Strain Difference", alpha=0.6)
            ax[0, 0].plot(common_force, shifted_strain_diff, label="Shifted Strain Difference", alpha=0.6)
            ax[0, 0].set_title("Stress and strain Difference")
            ax[0, 0].set_xlabel("Force")
            ax[0, 0].set_ylabel("Difference")
            ax[0, 0].legend()

            ax[0, 1].plot(data["force"], data["displacement"], label="Original Displacement")
            ax[0, 1].plot(common_force, interpolated_displacement, label="Interpolated Displacement")
            ax[0, 1].set_title("Force vs Displacement")
            ax[0, 1].set_xlabel("Force")
            ax[0, 1].set_ylabel("Displacement")
            ax[0, 1].legend()

            ax[1, 0].plot(df["strain"], df["stress"], label="Original Stress and Strain", alpha=0.6)
            ax[1, 0].plot(strain, stress, label="Derived Interpolated Stress and Strain", alpha=0.6)
            ax[1, 0].plot(interpolated_strain, interpolated_stress, label="Interpolated Stress and Strain", alpha=0.6)
            ax[1, 0].set_xlabel("Strain")
            ax[1, 0].set_ylabel("Stress")
            ax[1, 0].set_title("Stress vs Strain")
            ax[1, 0].legend()

            ax[1, 1].plot(df["strain"], df["stress"], label="Original Stress and Strain", alpha=0.6)
            ax[1, 1].plot(
                df["shiftd strain"], df["stress"], label=" Original Stress and Shifted Strain", alpha=0.6
            )  # okay to use
            ax[1, 1].plot(
                shifted_strain, interpolated_stress, label="Interpolated Stress with Shifted Strain", alpha=0.6
            )
            ax[1, 1].plot(
                shifted_strain_inter,
                interpolated_stress,
                label="Interpolated Stress with inter Shifted Strain",
                alpha=0.6,
            )  # okay to use
            ax[1, 1].plot(
                interpolated_shiftd_strain,
                interpolated_stress,
                label="Intepolated Stress and Intepolated Shifted Strain",
                alpha=0.6,
            )  # okay to use
            ax[1, 1].set_xlabel("Strain")
            ax[1, 1].set_ylabel("Stress")
            ax[1, 1].set_title("Stress vs shifted Strain")
            ax[1, 1].legend()

            plt.tight_layout()
            plt.show()

        return pd.DataFrame(
            {
                "Force": common_force,
                "Displacement": interpolated_displacement,
                "Time": interpolated_time,
                "Stress": stress,
                "Strain": interpolated_shiftd_strain,
            }
        )

    def process_hysteresis_data(
        self,
        selected_specimens=None,
        testing=False,
        smoothing=True,
        window_size=31,
        denoise_strength=21,
        sigma=6,
        all_plots=False,
    ):
        if selected_specimens is None:
            selected_indices = self.widget_manager.specimen_listbox.curselection()
            selected_specimens = self.get_selected_specimens(selected_indices)

        temp_data = {}

        # Create split_data_1 and split_data_2 once and reuse it
        split_data = [self.split_hysteresis_data(specimen.processed_hysteresis_data) for specimen in selected_specimens]

        def process_data(self, selected_specimens, split_data):
            split_data_1 = [self.clean_split_hysteresis_data_by_force(data[0]) for data in split_data]
            split_data_2 = [self.clean_split_hysteresis_data_by_force(data[1]) for data in split_data]

            common_force_1, common_force_2 = self.get_common_force(split_data_1, split_data_2)

            interpolated_data_1 = [
                self.interpolate_data(data, common_force_1, specimen.cross_sectional_area, specimen.original_length)
                for specimen, data in zip(selected_specimens, split_data_1)
            ]
            interpolated_data_2 = [
                self.interpolate_data(data, common_force_2, specimen.cross_sectional_area, specimen.original_length)
                for specimen, data in zip(selected_specimens, split_data_2)
            ]

            average_data_1 = pd.concat(interpolated_data_1).groupby("Force").mean()
            average_data_2 = pd.concat(interpolated_data_2).groupby("Force").mean()

            average_data = pd.concat([average_data_1, average_data_2.iloc[::-1]]).reset_index()
            average_data["Time"] = average_data["Time"] - average_data["Time"].min()

            return average_data

        temp_data["unsmoothed data"] = process_data(self, selected_specimens, split_data)
        average_data = temp_data["unsmoothed data"]

        if smoothing and len(selected_specimens) > 1:
            if all_plots:
                # Define a dictionary of smoothing functions for testing
                smoothing_functions = {
                    "moving_average": lambda data: moving_average(data, window_size),
                    "median_filter": lambda data: median_filter(data, denoise_strength),
                    "gaussian_smoothing": lambda data: gaussian_smoothing(data, sigma),
                }

                for name, func in smoothing_functions.items():
                    temp_data[f"1x after avg smooth with {name}"] = func(temp_data["unsmoothed data"])
                    split_data = [
                        self.split_hysteresis_data(func(specimen.processed_hysteresis_data))
                        for specimen in selected_specimens
                    ]
                    temp_data[f"1x smooth with {name}"] = process_data(self, selected_specimens, split_data)
                    temp_data[f"2x smooth with {name}"] = func(temp_data[f"1x smooth with {name}"])

                average_data = (
                    temp_data["1x smooth with median_filter"]
                    if (len(selected_specimens) > 1)
                    else temp_data["unsmoothed data"]
                )
            else:
                temp_data["1x smooth after avg med"] = median_filter(
                    temp_data["unsmoothed data"], denoise_strength=denoise_strength
                )
                temp_data["2x smooth after avg med followed by moving"] = moving_average(
                    temp_data["1x smooth after avg med"], window_size=3
                )
                temp_data["2x smooth after avg med followed by gussian"] = gaussian_smoothing(
                    temp_data["1x smooth after avg med"], sigma=1
                )

                average_data = (
                    temp_data["1x smooth after avg med"]
                    if (len(selected_specimens) > 1)
                    else temp_data["unsmoothed data"]
                )
        self.app.variables.average_of_specimens_hysteresis = average_data
        self.app.variables.average_of_specimens_hysteresis_sm = temp_data

        if testing:

            def calculate_total_variation(temp_data):
                total_variation_dict = {}
                for key in temp_data:
                    total_variation = temp_data[key]["Stress"].diff().abs().sum()
                    total_variation_dict[key] = total_variation
                normalized_dict = {
                    key: value / total_variation_dict["unsmoothed data"] for key, value in total_variation_dict.items()
                }
                return normalized_dict

            total_variation_dict = calculate_total_variation(temp_data)
            print(tabulate(total_variation_dict.items(), headers=["Data Type", "Total Variation"], tablefmt="pretty"))

            self._plot_avg_temp_data(temp_data, title="with smooth", alpha=0.6, all_plots=all_plots)

    def process_hysteresis_data_with_median_filter(self, selected_specimens=None, denoise_strength=21):
        if selected_specimens is None:
            selected_indices = self.widget_manager.specimen_listbox.curselection()
            selected_specimens = self.get_selected_specimens(selected_indices)

        # Create split_data once and reuse it
        split_data = [self.split_hysteresis_data(specimen.processed_hysteresis_data) for specimen in selected_specimens]

        # Process data
        processed_data = self._process_split_data(selected_specimens, split_data)

        # Apply median filter
        median_filtered_data = median_filter(processed_data, denoise_strength=denoise_strength)

        return median_filtered_data

    def _process_split_data(self, selected_specimens, split_data):
        split_data_1 = [self.clean_split_hysteresis_data_by_force(data[0]) for data in split_data]
        split_data_2 = [self.clean_split_hysteresis_data_by_force(data[1]) for data in split_data]

        common_force_1, common_force_2 = self.get_common_force(split_data_1, split_data_2)

        interpolated_data_1 = [
            self.interpolate_data(data, common_force_1, specimen.cross_sectional_area, specimen.original_length)
            for specimen, data in zip(selected_specimens, split_data_1)
        ]
        interpolated_data_2 = [
            self.interpolate_data(data, common_force_2, specimen.cross_sectional_area, specimen.original_length)
            for specimen, data in zip(selected_specimens, split_data_2)
        ]

        average_data_1 = pd.concat(interpolated_data_1).groupby("Force").mean()
        average_data_2 = pd.concat(interpolated_data_2).groupby("Force").mean()

        average_data = pd.concat([average_data_1, average_data_2.iloc[::-1]]).reset_index()
        average_data["Time"] = average_data["Time"] - average_data["Time"].min()

        return average_data

    def _plot_avg_temp_data(self, temp_data, title="", alpha=0.6, all_plots=False, pts=None):
        if all_plots:
            smoothing_functions = ["moving_average", "median_filter", "gaussian_smoothing"]
            fig, axs = plt.subplots(len(smoothing_functions), 1, figsize=(8, 4 * len(smoothing_functions)))

            for i, func in enumerate(smoothing_functions):
                ax = axs[i]
                ax.plot(
                    temp_data["unsmoothed data"]["Strain"],
                    temp_data["unsmoothed data"]["Stress"],
                    label="unsmoothed data",
                    alpha=alpha,
                )
                for key in temp_data:
                    if func in key:  # Plot data only if the smoothing function was applied
                        ax.plot(temp_data[key]["Strain"], temp_data[key]["Stress"], label=key, alpha=alpha)

                    ax.set_title(f"Stress vs Strain {title}")
                    ax.set_xlabel("Strain")
                    ax.set_ylabel("Stress")
                    ax.grid(True)
                    ax.legend()
        else:
            fig, ax = plt.subplots(figsize=(10, 7))

            if isinstance(temp_data, dict):
                for key in temp_data:
                    ax.plot(temp_data[key]["Strain"], temp_data[key]["Stress"], label=key, alpha=alpha)
            else:
                ax.plot(temp_data["Strain"], temp_data["Stress"], label="unsmoothed data", alpha=alpha)

            ax.set_title(f"Stress vs Strain {title}")
            ax.set_xlabel("Strain")
            ax.set_ylabel("Stress")
            ax.grid(True)
            ax.legend()

            if pts:
                for scattter_pts in pts:
                    ax.scatter(scattter_pts[0], scattter_pts[1], s=50, marker="x", label="20% and 70% stress points")

        plt.tight_layout()
        plt.show()

    def _closest_point_and_error(self, data, key_strain, key_stress, start_index=0):
        column_names = data.columns
        if "Strain" in column_names or "Stress" in column_names:
            strain_key = "Strain"
            stress_key = "Stress"
        else:
            strain_key = "strain"
            stress_key = "stress"

        distances = np.sqrt(
            (data[strain_key].iloc[start_index:] - key_strain) ** 2
            + (data[stress_key].iloc[start_index:] - key_stress) ** 2
        )
        min_distance_index = distances.idxmin()
        closest_strain, closest_stress = (
            data[strain_key].iloc[min_distance_index],
            data[stress_key].iloc[min_distance_index],
        )
        error = np.sqrt((closest_strain - key_strain) ** 2 + (closest_stress - key_stress) ** 2)
        return error, (closest_strain, closest_stress), min_distance_index

    def _filter_end_points(self, temp_data, key="unsmoothed data", show_plot=False):
        if len(self.specimens_with_hysteresis_data) == 1:
            return temp_data
        strain_70, stress_70 = zip(
            *[specimen.data_manager.pt_70_plt for specimen in self.specimens_with_hysteresis_data]
        )
        stress_20 = [
            specimen.data_manager.formatted_hysteresis_data["stress"].iloc[-1]
            for specimen in self.specimens_with_hysteresis_data
        ]
        strain_20 = [
            specimen.data_manager.formatted_hysteresis_data["strain"].iloc[-1]
            for specimen in self.specimens_with_hysteresis_data
        ]

        mean_stress_70 = np.mean(stress_70)
        mean_strain_70 = np.mean(strain_70)

        mean_stress_20 = np.mean(stress_20)
        mean_strain_20 = np.mean(strain_20)

        pts = [(mean_strain_70, mean_stress_70), (mean_strain_20, mean_stress_20)]
        self.app.variables.avg_pleatue_stress = np.mean([mean_stress_70 / 0.7, mean_stress_20 / 0.2])

        def error_at_key_point(data, key_points):
            error = {}
            start_index = 0
            for pts in key_points:
                key_strain, key_stress = pts
                error[pts], point, start_index = self._closest_point_and_error(
                    data, key_strain, key_stress, start_index
                )
                if pts == (mean_strain_70, mean_stress_70):
                    self.avg_70_pt = {"point": point, "index": start_index}
                elif pts == (mean_strain_20, mean_stress_20):
                    self.avg_20_pt = {"point": point, "index": start_index}
                    data = data.loc[:start_index]  # Only keep the data up to the point closest to the 20% stress level

            total_error = {key: abs(value) for key, value in error.items()}
            return total_error, data

        error = {}
        truncated_data = {}
        if isinstance(temp_data, dict):
            for key in temp_data:
                error[key], truncated_data[key] = error_at_key_point(temp_data[key], pts)

            error_table = tabulate(error.items(), headers=["Key", "Error"], tablefmt="pretty")
            print(error_table)
            truncated_data["unsmoothed data no cut"] = temp_data["unsmoothed data"]
        else:
            error, truncated_data = error_at_key_point(temp_data, pts)
            print(f"Error - Distance from avg points is: {error}")

        if show_plot:
            pts.extend([self.avg_20_pt["point"], self.avg_70_pt["point"]])
            self._plot_avg_temp_data(truncated_data, title="with smooth & truncated", alpha=0.4, pts=pts)

        return truncated_data

    def shift_hysteresis_data(self, data=None, filtering=False, test_filtering=False, key="1x smooth after avg med"):
        if data is None:
            data = self.app.variables.average_of_specimens_hysteresis
            avg_data = self.app.variables.average_of_specimens

        max_stress_hysteresis, max_stress_index = self._find_max_stress_hysteresis(data)
        closest_stress_index_raw, closest_strain, closest_stress = self._find_closest_stress(
            avg_data, max_stress_hysteresis
        )
        data = self._shift_strain(data, max_stress_index, closest_strain)

        if filtering and len(self.specimens_with_hysteresis_data) > 1:
            data = self._filter_end_points(data, show_plot=False)  # Add Filtering
            stain_at_70, stress_at_70 = self.avg_70_pt["point"]
            closest_stress_index, closest_strain_value, closest_stress_values = self._find_closest_stress(
                self.average_of_specimens, stress_at_70
            )
            self.app.variables.average_of_specimens_hysteresis = self._shift_strain(
                data, self.avg_70_pt["index"], closest_strain_value
            )
            stain_at_20, stress_at_20 = self.avg_20_pt["point"]
            modulus = (stress_at_70 - stress_at_20) / (stain_at_70 - stain_at_20)
            print(f"Modulus is: {modulus}")
            x, y = self._generate_linear_line(avg_data["Strain"].to_numpy(), modulus)
            # self.app.variables.average_of_specimens_hysteresis = data
        else:
            modulus_by_stress = self._calculate_modulus_by_stress(data, max_stress_index)
            print(f"Modulus is: {modulus_by_stress}")
            x, y = self._generate_linear_line(avg_data["Strain"].to_numpy(), modulus_by_stress, offset=0.01)

        if test_filtering:
            data_set = {}
            for key in self.app.variables.average_of_specimens_hysteresis_sm:
                data_set[key] = self._shift_strain(
                    self.app.variables.average_of_specimens_hysteresis_sm[key], max_stress_index, closest_strain
                )
            truncated_data = self._filter_end_points(data_set, show_plot=False)
            self.app.variables.average_of_specimens_hysteresis = truncated_data["1x smooth after avg med"]

            modulus_set = {}
            for key in truncated_data:
                modulus_set[key] = self._calculate_modulus_by_stress(truncated_data[key], max_stress_index)
                modulus_set[f"plot pts of {key}"] = self._generate_linear_line(
                    avg_data["Strain"].to_numpy(), modulus_set[key]
                )
            self.app.variables.hyst_avg_linear_plot_filtered = modulus_set
            print(f"Modulus is: {modulus_set}")
        else:
            self.app.variables.hyst_avg_linear_plot_filtered = None

        self.app.variables.hyst_avg_linear_plot = x, y
        self.app.variables.hyst_avg_linear_plot_by_mod = None
        self.app.variables.hyst_avg_linear_plot_secant = None
        self.app.variables.hyst_avg_linear_plot_best_fit = None
        ss_plot = avg_data["Strain"].to_numpy(), avg_data["Stress"].to_numpy()

        ps_method = self._calculate_strength_from_intercept(ss_plot, (x, y))
        print(f"\nThe first method of finding the proof strength is: {ps_method}")

        if ps_method is [(None, None)]:
            # if any(ps_method):
            print("No intercept found, trying to simplify the calculation")
            self.simplify_modulus_calculation_by_avg(x)
            self.simplify_modulus_calculation_secant(x)
            self.simplify_modulus_calculation_best_fit(x)

            for plot in [
                self.app.variables.hyst_avg_linear_plot_by_mod,
                self.app.variables.hyst_avg_linear_plot_secant,
                self.app.variables.hyst_avg_linear_plot_best_fit,
            ]:
                ps_method.append(SpecimenGraphManager.find_interaction_point(ss_plot, plot))

        self.app.variables.avg_compressive_proof_strength_from_hyst = ps_method

    def _find_max_stress_hysteresis(self, data):
        max_stress_index = np.argmax(data["Stress"].values)
        return data["Stress"].iloc[max_stress_index], max_stress_index

    def __find_closest_stress(self, data, stress_value):
        closest_stress_index = (data["Stress"] - stress_value).abs().idxmin()
        return (
            closest_stress_index,
            data["Strain"].iloc[closest_stress_index],
            data["Stress"].iloc[closest_stress_index],
        )

    def _find_closest_stress(self, data, stress_value):
        first_stress_index_at_max = np.argwhere(data["Stress"] > stress_value)

        if first_stress_index_at_max.size > 0:
            first_stress_index_at_max = first_stress_index_at_max[0][0]

            # Determine the local maximum stress after the point where the stress exceeds the input stress_value
            local_maxima_indices = argrelextrema(data.iloc[first_stress_index_at_max:]["Stress"].values, np.greater)
            if local_maxima_indices[0].size > 0:
                # Adjust the index to match the original dataframe
                local_max_index = local_maxima_indices[0][0] + first_stress_index_at_max
            else:
                # If there's no local maximum, find the closest stress index as before
                local_max_index = (data["Stress"] - stress_value).abs().idxmin()

            # Find the closest corresponding stress in the masked raw data
            closest_stress_index = (data.iloc[:local_max_index]["Stress"] - stress_value).abs().idxmin()
        else:
            # If there's no stress greater than the input stress_value, find the closest stress index as before
            closest_stress_index = (data["Stress"] - stress_value).abs().idxmin()

        closest_strain = data["Strain"].iloc[closest_stress_index]
        closest_stress = data["Stress"].iloc[closest_stress_index]

        return closest_stress_index, closest_strain, closest_stress

    def _shift_strain(self, data, max_stress_index, closest_strain):
        strain_offset = data["Strain"].iloc[max_stress_index] - closest_strain
        data.loc[:, "Strain"] = data["Strain"] - strain_offset
        return data

    def _calculate_modulus_by_stress(self, data, max_stress_index):
        peak_pt_by_stress = data["Strain"].iloc[max_stress_index], data["Stress"].iloc[max_stress_index]
        end_pt_by_stress = data["Strain"].iloc[-1], data["Stress"].iloc[-1]
        return (peak_pt_by_stress[1] - end_pt_by_stress[1]) / (peak_pt_by_stress[0] - end_pt_by_stress[0])

    def _generate_linear_line(
        self, strain_range, modulus, offset=0.01
    ):  ######################################################## SET OFFSET TO 0.01 1% of strain  ##########################################
        # if offset is not specified from widget manager, use the default offset of 0.01 based on the ISO standard
        if self.widget_manager.offset_value is not None:
            offset = float(self.widget_manager.offset_value) / 100
            print(f"Warning: None ISO compliant Offset of: {offset}")

        max_strain = max(strain_range)
        num_points = len(strain_range)
        x = np.linspace(0, max_strain, num=num_points)
        y = modulus * (x - offset)
        return x, y

    def _calculate_strength_from_intercept(self, ss_plot, linear_plot):
        ps_strain, ps_stress = SpecimenGraphManager.find_interaction_point(ss_plot, linear_plot)
        return [(ps_strain, ps_stress)]

    def simplify_modulus_calculation_by_avg(self, x):
        strain_range = x
        avg_modulus = np.mean([specimen.data_manager.modulus for specimen in self.specimens_with_hysteresis_data])
        self.avg_modulus = avg_modulus
        print(f"Average modulus: {avg_modulus} from simplified calculation by average of moduluses")
        x, y = self._generate_linear_line(strain_range, avg_modulus)
        self.app.variables.hyst_avg_linear_plot_by_mod = x, y

    def simplify_modulus_calculation_secant(self, x):
        strain_range = x
        mean_stresses = self._calculate_avg_stress_values()
        closest_indices, closest_strains, closest_stresses = zip(
            *[
                self._find_closest_stress(data=self.app.variables.average_of_specimens, stress_value=mean_stresses[key])
                for key in ["20%", "70%"]
            ]
        )

        if self.avg_20_pt is None or self.avg_70_pt is None:
            self.avg_20_pt, self.avg_70_pt = [
                (
                    self.app.variables.average_of_specimens["Strain"].iloc[idx],
                    self.app.variables.average_of_specimens["Stress"].iloc[idx],
                )
                for idx in closest_indices
            ]

        self.avg_modulus_secant = (self.avg_20_pt[1] - self.avg_70_pt[1]) / (self.avg_20_pt[0] - self.avg_70_pt[0])
        print(f"Average modulus: {self.avg_modulus_secant} from simplified calculation by secant of 70% and 20% points")

        self.app.variables.hyst_avg_linear_plot_secant = self._generate_linear_line(
            strain_range, self.avg_modulus_secant
        )

    def simplify_modulus_calculation_best_fit(self, x):
        self.app.variables.hyst_avg_linear_plot_best_fit

        if self.app.variables.avg_pleatue_stress is None:
            mean_stresses = self._calculate_avg_stress_values()
            closest_indices, closest_strains, closest_stresses = zip(
                *[
                    self._find_closest_stress(
                        data=self.app.variables.average_of_specimens, stress_value=mean_stresses[key]
                    )
                    for key in ["30%", "60%"]
                ]
            )
            closest_30_stress_index, closest_60_stress_index = closest_indices
        else:
            closest_30_stress_index = self._find_closest_stress(
                self.app.variables.average_of_specimens, self.app.variables.avg_pleatue_stress * 0.3
            )[0]
            closest_60_stress_index = self._find_closest_stress(
                self.app.variables.average_of_specimens, self.app.variables.avg_pleatue_stress * 0.6
            )[0]

        strain_range = self.app.variables.average_of_specimens["Strain"][
            closest_30_stress_index:closest_60_stress_index
        ]
        stress_range = self.app.variables.average_of_specimens["Stress"][
            closest_30_stress_index:closest_60_stress_index
        ]

        self.avg_modulus_best_fit = self._fit_linear_model(strain_range, stress_range)
        print(f"Average modulus: {self.avg_modulus_best_fit} from simplified calculation by linear best fit\n")

        self.app.variables.hyst_avg_linear_plot_best_fit = self._generate_linear_line(x, self.avg_modulus_best_fit)

    def _calculate_avg_stress_values(self):
        mean_stresses = {}

        if self.app.variables.avg_pleatue_stress is None:
            strain_70, stress_70 = zip(
                *[specimen.data_manager.pt_70_plt for specimen in self.specimens_with_hysteresis_data]
            )
            stress_20 = [
                specimen.data_manager.formatted_hysteresis_data["stress"].iloc[-1]
                for specimen in self.specimens_with_hysteresis_data
            ]

            mean_stress_70 = np.mean(stress_70)
            mean_stress_20 = np.mean(stress_20)

            self.app.variables.avg_pleatue_stress = np.mean([mean_stress_70 / 0.7, mean_stress_20 / 0.2])

            mean_stresses["70%"] = mean_stress_70
            mean_stresses["20%"] = mean_stress_20
            mean_stresses["60%"] = self.app.variables.avg_pleatue_stress * 0.6
            mean_stresses["30%"] = self.app.variables.avg_pleatue_stress * 0.3
        else:
            mean_stresses["20%"] = self.app.variables.avg_pleatue_stress * 0.2
            mean_stresses["30%"] = self.app.variables.avg_pleatue_stress * 0.3
            mean_stresses["60%"] = self.app.variables.avg_pleatue_stress * 0.6
            mean_stresses["70%"] = self.app.variables.avg_pleatue_stress * 0.7

        return mean_stresses

    def _fit_linear_model(self, strain_range, stress_range):
        def linear_func(x, a, b):
            return a * x + b

        popt, _ = curve_fit(linear_func, strain_range, stress_range)
        return popt[0]

    def get_common_strain(self, selected_specimens):
        max_strain = max(specimen.shifted_strain.max() for specimen in selected_specimens)
        max_num_points = max(len(specimen.shifted_strain) for specimen in selected_specimens)
        common_strain = np.linspace(-0.05, max_strain, num=max_num_points)

        return common_strain

    def get_interpolated_stresses(self, selected_specimens, common_strain, mode="default"):
        return SpecimenInterpolator.interpolate_stresses(
            selected_specimens=selected_specimens, common_strain=common_strain, mode=mode
        )
    def get_common_displacement(self, selected_specimens):
        max_displacement = max(specimen.shifted_displacement.max() for specimen in selected_specimens)
        max_num_points = max(len(specimen.shifted_displacement) for specimen in selected_specimens)
        common_displacement = np.linspace(0, max_displacement, num=max_num_points)
        return common_displacement

    def get_interpolated_forces(self, selected_specimens, common_displacement):
        interpolated_forces = [
            np.interp(common_displacement, specimen.shifted_displacement, specimen.force)
            for specimen in selected_specimens
        ]
        return interpolated_forces

    def get_selected_specimens(self, selected_indices=None):
        if selected_indices is None:
            selected_indices = self.widget_manager.specimen_listbox.curselection()
            self.app.variables.selected_indices = selected_indices

        selected_specimens = [self.app.variables.specimens[index] for index in selected_indices]
        return selected_specimens

    def average_of_selected_specimens(self, selected_indices=None, control_limit_L=3):
        """Calculate the average of the selected specimens."""
        print("\nCalculating Average of the selected specimens, please wait...")
        selected_specimens = self.get_selected_specimens(selected_indices)
        if not selected_specimens:
            return

        self.app.variables.selected_specimen_names = [specimen.name for specimen in selected_specimens]
        condtions = [specimen.data_manager.import_condition for specimen in selected_specimens]

        print(condtions)
        skip_force = False
        # for condtion in condtions:
        #     if 'df' in str(condtion) and 'force' not in str(condtion):
        #         print("One of the data samples does not have force data. Will attemp to avg only with stress and strain ")
        #         skip_force = True
        #         #empty force  and displacement data
        #         average_displacement =pd.DataFrame()
        #         average_force = pd.DataFrame()

        if not skip_force:
            common_displacement = self.get_common_displacement(selected_specimens)
            interpolated_forces = self.get_interpolated_forces(selected_specimens, common_displacement)

            average_force = np.mean(interpolated_forces, axis=0)
            average_displacement = common_displacement

        common_strain = self.get_common_strain(selected_specimens)
        interpolated_stresses = self.get_interpolated_stresses(selected_specimens, common_strain)
        std_strain = np.std(common_strain)

        average_stress = np.mean(interpolated_stresses, axis=0)
        std_dev_stress = np.std(interpolated_stresses, axis=0)
        max_stress = np.max(interpolated_stresses, axis=0)
        min_stress = np.min(interpolated_stresses, axis=0)
        UCL_stress = average_stress + (control_limit_L * std_dev_stress)
        LCL_stress = average_stress - (control_limit_L * std_dev_stress)
        # Cpk = np.min(((average_stress-LCL_stress)/(3*std_dev_stress)),((UCL_stress-average_stress)/(3*std_dev_stress)))

        average_strain = common_strain

        specimens_with_hysteresis_data = []

        for specimen in selected_specimens:
            if specimen.processed_hysteresis_data is not None and not specimen.processed_hysteresis_data.empty:
                specimens_with_hysteresis_data.append(specimen)

        # If the list is not empty, process the hysteresis data
        if specimens_with_hysteresis_data:
            self.specimens_with_hysteresis_data = specimens_with_hysteresis_data
            # self.process_hysteresis_data(specimens_with_hysteresis_data) # used for testing all the filters
            self.app.variables.average_of_specimens_hysteresis = self.process_hysteresis_data_with_median_filter(
                specimens_with_hysteresis_data
            )  # stremlined approach

        # get the shift value for widget manager
        shift_value = float(self.widget_manager.shift_value) if self.widget_manager.shift_value else 0

        self.app.variables.average_of_specimens = pd.DataFrame(
            {
                "Displacement": average_displacement,
                "Force": average_force,
                "Strain": average_strain + shift_value,  # is the offset when needed
                "Stress": average_stress,
                "std Stress": std_dev_stress,
                "std Strain": std_strain,
                "max Stress": max_stress,
                "min Stress": min_stress,
                "UCL Stress": UCL_stress,
                "LCL Stress": LCL_stress,
            }
        )

        if (
            self.app.variables.average_of_specimens_hysteresis is not None
            and not self.app.variables.average_of_specimens_hysteresis.empty
        ):
            self.shift_hysteresis_data()

    def calculate_summary_stats(self, values, control_limit_L=3):
        if np.any(np.equal(values, None)):
            return None, None, None, None, None
        average_value = np.mean(values)
        std_value = np.std(values)
        cv_value = (std_value / average_value) * 100 if average_value != 0 else 0
        UCL_value = average_value + (control_limit_L * std_value) if std_value != 0 else "N/A"
        LCL_value = average_value - (control_limit_L * std_value) if std_value != 0 else "N/A"
        return average_value, std_value, cv_value, UCL_value, LCL_value

    def summary_statistics(self):
        """Calculate summary statistics for each property."""
        summary_df = self.create_summary_df(self.properties_df)
        return summary_df

    def create_summary_df(self, properties_df):
        """Create a summarized DataFrame of their average with the corresponding STD and CV."""
        summary_stats = []

        for prop in properties_df.columns:
            if prop != "name":  # skip over 'name' column
                avg, std, cv, ucl, lcl = self.calculate_summary_stats(properties_df[prop].values)
                summary_stats.append(
                    {"Property": prop, "Average": avg, "Std Dev": std, "CV %": cv, "UCL": ucl, "LCL": lcl}
                )

        summary_stats_df = pd.DataFrame(summary_stats)
        summary_stats_df.set_index("Property", inplace=True)

        return summary_stats_df

    def create_properties_df(self, selected_specimens=None):
        """Create a DataFrame with all properties for each specimen."""
        selected_specimens = self.get_selected_specimens() if selected_specimens is None else selected_specimens

        properties_dfs = []

        for specimen in selected_specimens:
            specimen_properties = self.get_specimen_full_properties(specimen)
            specimen_df = pd.DataFrame(specimen_properties, index=[specimen.name])
            properties_dfs.append(specimen_df)

        properties_df = pd.concat(properties_dfs)

        return properties_df

    def get_specimen_full_properties(self, specimen):
        """Extracts the properties of a specimen."""
        specimen.calculate_general_KPI()
        properties = {}

        # Get general properties
        for prop in self.general_properties:
            properties[prop] = getattr(specimen, prop)

        # Get DIN analysis properties
        if self.app.variables.DIN_Mode == True:
            for prop in self.din_properties:
                try:
                    properties[prop] = getattr(specimen.din_analyzer, prop)
                except AttributeError:
                    print(f"Error: din_analyzer not initialized for specimen: {specimen}")

        # Get data manager properties
        for prop in self.data_manager_properties:
            properties[prop] = getattr(specimen.data_manager, prop)

        # Get hysteresis data manager properties
        for prop in self.hysteresis_data_manager_properties:
            if specimen.processed_hysteresis_data is not None and not specimen.processed_hysteresis_data.empty:
                properties[prop] = getattr(specimen.data_manager, prop)

        return properties

    def update_properties_df(self, selected_indices):
        selected_specimens = self.get_selected_specimens(selected_indices)

        if self.app.variables.DIN_Mode:
            for specimen in selected_specimens:
                specimen.set_analyzer() if specimen.din_analyzer is None else None

        self.properties_df = self.create_properties_df(selected_specimens)

    def export_individual_kpi(self, selected_indices):
        selected_specimens = self.get_selected_specimens(selected_indices)
        KPI_df = self.generate_kpi_table(selected_specimens)
        transposed_df_reset = KPI_df.set_index("Name").transpose().reset_index()
        self.generate_kpi_for_csv(selected_specimens)

        print("\nQuality Control KPIs for Indivdual:")

        self.print_KPI_chunked_tables(transposed_df_reset)

        # KPI_stats = self.process_kpi_with_control_metrics(KPI_df)

    def generate_kpi_for_csv(self, selected_specimens):
        from datetime import datetime

        # Initialize the DataFrame with specimen names as columns
        rows = []
        for specimen in selected_specimens:
            # Calculate the KPIs for each specimen (uncomment the line below if needed)
            # specimen.calculate_quality_control_KPIs()

            # Retrieve and flatten KPIs for the current specimen
            KPIs_flattened = {"Name": specimen.name}
            for prop, info in specimen.qc_manager.property_dict.items():
                value = info["value"]
                if isinstance(value, tuple):
                    # Create a separate column for each element of the tuple
                    for i, v in enumerate(value):
                        KPIs_flattened[f"{prop}_G{i+1} {info['unit']}"] = v
                else:
                    KPIs_flattened[f"{prop} {info['unit']}"] = value

            # Append the specimen's flattened KPIs to the DataFrame
            rows.append(KPIs_flattened)
        KPI_csv_df = pd.DataFrame(rows)

        # Set the 'Name' column as the DataFrame's index
        KPI_csv_df.set_index("Name", inplace=True)

        # Save the transposed DataFrame to a CSV file
        timestamp = datetime.now().strftime("%Y-%m-%d %H_%M_%S")
        csv_filename = f"KPI_Time_{timestamp}.csv"
        KPI_csv_df.to_csv(csv_filename)

        print(f"KPI DataFrame saved as {csv_filename}")
        # self.plot_surface_for_each_property(KPI_csv_df)

        return KPI_csv_df

    def plot_surface_for_each_property(self, df):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from mpl_toolkits.mplot3d import Axes3D
        from scipy.interpolate import griddata

        df.reset_index(inplace=True)

        # Extract 'M' and 'G' values from the 'Name' column
        df["M_value"] = df["Name"].str.extract(r"M(\d+)").astype(int)
        df["G_value"] = df["Name"].str.extract(r"G(\d+)").astype(int)

        # Loop through each property except 'Name', 'M_value', and 'G_value'
        for column in df.columns.drop(["Name", "M_value", "G_value"]):
            # Prepare the data for the scatter plot
            x = df["M_value"]
            y = df["G_value"]
            z = df[column]

            # Creating grid points for interpolation
            xi = np.linspace(x.min(), x.max(), 100)
            yi = np.linspace(y.min(), y.max(), 100)
            X, Y = np.meshgrid(xi, yi)

            # Interpolate Z values on grid
            Z = griddata((x, y), z, (X, Y), method="linear")

            # Create the plot
            fig = plt.figure()
            ax = fig.add_subplot(111, projection="3d")

            # Plot the surface
            surf = ax.plot_surface(X, Y, Z, cmap="viridis")

            # Labels
            ax.set_xlabel("M Value")
            ax.set_ylabel("G Value")
            ax.set_zlabel(column)

            # Add a color bar which maps values to colors
            # fig.colorbar(surf, shrink=0.5, aspect=5)

            # Show the plot
            import tkinter as tk

            window = tk.Toplevel(self.app.master)
            window.title(f"Surface Plot for {column}")
            canvas = FigureCanvasTkAgg(fig, master=window)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def generate_kpi_table(self, selected_specimens, standard_name="ISO_13314:2011(E)"):
        KPI_table = []

        for specimen in selected_specimens:
            specimen.calculate_quality_control_KPIs(standard_name)

            KPIs_with_units = {}
            for prop, info in specimen.qc_manager.property_dict.items():
                value = info["value"]
                if isinstance(value, tuple):
                    # Format each numeric part of the tuple to 4 decimal places
                    formatted_values = tuple(f"{float(v):.4f}" if isinstance(v, (int, float)) else v for v in value)
                    KPIs_with_units[prop] = f"{formatted_values} {info['unit']}"
                else:
                    # Format single numeric values to 4 decimal places
                    KPIs_with_units[prop] = (
                        f"{float(value):.4f} {info['unit']}" if isinstance(value, (int, float)) else value
                    )

            # KPIs_with_units = {prop: f"{float(info['value']):.4f} {info['unit']}"
            #                 for prop, info in specimen.qc_manager.property_dict.items()}
            KPI_table.append({"Name": specimen.name, **KPIs_with_units})

        return pd.DataFrame(KPI_table)

    def print_KPI_chunked_tables(self, df, max_columns_per_table=4):
        num_tables = (len(df.columns) - 1) // max_columns_per_table + 1

        for i in range(num_tables):
            start_col = 1 + i * max_columns_per_table
            end_col = min(start_col + max_columns_per_table, len(df.columns))
            chunk = df.iloc[:, [0] + list(range(start_col, end_col))]
            print(tabulate(chunk, headers="keys", tablefmt="psql", showindex=False))
            print("\n")

    def process_kpi_with_control_metrics(self, KPI_df, LSLs=None, USLs=None):
        from control_chart import ControlProcessMetrics

        KPI_stats = pd.DataFrame()
        for kpi in KPI_df.columns.drop("Name"):
            kpi_data = KPI_df[kpi].dropna()  # Assuming NaN values should be dropped

            # Check if data is a tuple
            if isinstance(kpi_data.iloc[0], tuple):
                kpi_data_1 = np.array([x[0] for x in kpi_data])
                kpi_data_2 = np.array([x[1] for x in kpi_data])

                # Create instances for each part of the tuple
                cp_metrics_1 = ControlProcessMetrics(
                    kpi_data_1, LSLs.get(kpi, [None, None])[0], USLs.get(kpi, [None, None])[0]
                )
                cp_metrics_2 = ControlProcessMetrics(
                    kpi_data_2, LSLs.get(kpi, [None, None])[1], USLs.get(kpi, [None, None])[1]
                )

                # Calculate and store statistics as tuples
                KPI_stats[kpi] = [
                    (cp_metrics_1.mean, cp_metrics_2.mean),
                    (cp_metrics_1.sigma, cp_metrics_2.sigma),
                    (cp_metrics_1.cv, cp_metrics_2.cv),
                    (cp_metrics_1.UCL, cp_metrics_2.UCL),
                    (cp_metrics_1.LCL, cp_metrics_2.LCL),
                    (cp_metrics_1.Cp, cp_metrics_2.Cp),
                    (cp_metrics_1.Cpk, cp_metrics_2.Cpk),
                ]
            else:
                # Single value data
                cp_metrics = ControlProcessMetrics(kpi_data, LSLs.get(kpi), USLs.get(kpi))
                KPI_stats[kpi] = [
                    cp_metrics.mean,
                    cp_metrics.sigma,
                    cp_metrics.cv,
                    cp_metrics.UCL,
                    cp_metrics.LCL,
                    cp_metrics.Cp,
                    cp_metrics.Cpk,
                ]

        KPI_stats.index = ["Mean", "Std", "CV", "UCL", "LCL", "Cp", "Cpk"]  # Update as per available metrics
        return KPI_stats

    def calculate_avg_KPI(self, lower_strain=0.2, upper_strain=0.4):
        def calculate_plt(strain, lower_strain, upper_strain):
            idx_lower = (np.abs(strain - lower_strain)).argmin()
            idx_upper = (np.abs(strain - upper_strain)).argmin()
            return np.mean(stress[idx_lower:idx_upper])

        def calculate_plt_end(self, stress):
            return (np.abs(stress - 1.3 * self.app.variables.average_plt)).argmin()

        def calculate_energy(self, strain, stress):
            def calculate_Ev(stress, strain, compression):
                # strain = strain[strain < 0]
                # stress = stress[strain < 0]
                idx = (np.abs(strain - compression)).argmin()
                return trapz(stress[:idx], strain[:idx])

            E20 = calculate_Ev(stress, strain, 0.2)
            E50 = calculate_Ev(stress, strain, 0.5)
            dense_index = strain[self.app.variables.average_plt_end_id]
            E_dense = calculate_Ev(stress, strain, dense_index)
            return E20, E50, E_dense

        if self.app.variables.average_of_specimens is not None:
            strain = self.average_of_specimens["Strain"].to_numpy()
            stress = self.average_of_specimens["Stress"].to_numpy()
            self.lower_strain = lower_strain
            self.upper_strain = upper_strain
            self.app.variables.average_plt = calculate_plt(strain, lower_strain, upper_strain)
            self.app.variables.average_plt_end_id = calculate_plt_end(self, stress)
            self.app.variables.average_E20, self.app.variables.average_E50, self.app.variables.average_E_dense = (
                calculate_energy(self, strain, stress)
            )

    def export_average_to_excel(self, selected_indices, file_path, track_export=False):
        self.update_properties_df(selected_indices)

        if track_export is False:
            export_thread = threading.Thread(
                target=self.excel_exporter.export_data_to_excel(selected_indices, file_path)
            )
        else:
            export_thread = threading.Thread(
                target=self.excel_exporter.profile_export_average_to_excel, args=(selected_indices, file_path)
            )

        try:
            export_thread.start()
            print("Starting export thread")
            self.app.variables.export_in_progress = True
        except Exception as e:
            self.app.variables.export_in_progress = False

    def format_specimen_name_for_file(self, specimen_name):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = "".join(c for c in specimen_name if c in valid_chars)
        specimen_filename = filename.replace(" ", "_")  # replace spaces with underscore
        if len(filename) > 50:  # check if filename is too long
            specimen_filename = filename[:50]
        return specimen_filename

    def export_DIN_to_word(self, selected_indices, file_path):
        self.update_properties_df(selected_indices)

        print("Starting export thread")
        export_thread = threading.Thread(target=self.word_exporter.export_report(selected_indices, file_path))

    def recalculate_specimen(self, selected_indices):
        selected_specimens = self.get_selected_specimens(selected_indices)
        for specimen in selected_specimens:
            print("Recalculating specimen: ", specimen.name)
            specimen.calculate_general_KPI()
            specimen.graph_manager.plot_one_pnt_line(None, specimen.data_manager.modulus, recalculating=True)

        pass

    def save_specimen_data(self, specimen, output_directory):
        """
        Saves the specimen data to a temporary directory and then zips the files.

        Args:
        specimen (Specimen): The specimen to save.
        output_directory (str): The directory where to save the zipped file.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Serialize specimen properties to JSON
            properties_dict = specimen.__dict__
            with open(os.path.join(temp_dir, "specimen_properties.json"), "w") as json_file:
                json.dump(properties_dict, json_file, cls=SpecimenDataEncoder, export_dir=temp_dir)

            # Zip all generated files
            specimen_file_name = self.format_specimen_name_for_file(specimen.name)
            zip_file_path = os.path.join(output_directory, f"{specimen_file_name}_analyzer_data.zip")
            with zipfile.ZipFile(zip_file_path, "w") as zip_file:
                for file in glob.glob(os.path.join(temp_dir, "*")):
                    zip_file.write(file, os.path.basename(file))

    def load_specimen_data(self, file_path):
        """
        Loads the specimen data from a zipped file.

        Args:
        file_path (str): The path to the zipped file containing the specimen data.
        """
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Unzip the file
            with zipfile.ZipFile(file_path, "r") as zipf:
                zipf.extractall(temp_dir)

            # Load properties from the JSON file
            with open(os.path.join(temp_dir, "specimen_properties.json"), "r") as fp:
                properties_dict = json.load(fp)

            # Reconstruct the Specimen object
            specimen = Specimen.from_dict(properties_dict, temp_dir=temp_dir)

            if specimen.data_manager.formatted_data is not None and isinstance(
                specimen.data_manager.formatted_data, pd.DataFrame
            ):
                specimen.data_manager.formatted_data = DataValidator.remap_df_columns(
                    specimen.data_manager.formatted_data
                )

            if specimen.data_manager.formatted_hysteresis_data is not None and isinstance(
                specimen.data_manager.formatted_hysteresis_data, pd.DataFrame
            ):
                specimen.data_manager.formatted_hysteresis_data = DataValidator.remap_df_columns(
                    specimen.data_manager.formatted_hysteresis_data
                )

            # Add to GUI
            tab_id = self.widget_manager.create_new_tab(specimen.name)
            self.app.variables.add_specimen(tab_id, specimen)
            self.widget_manager.enable_buttons()
            filename = Path(file_path).name
            self.widget_manager.update_ui_elements(filename, specimen)
        return


class SpecimenDataEncoder(json.JSONEncoder):
    """
    Custom JSONEncoder subclass that knows how to encode custom specimen data types.

    Attributes:
    export_dir (str): Directory where data files are exported.
    """

    def __init__(self, *args, **kwargs):
        # accept the export directory as an argument
        self.export_dir = kwargs.pop("export_dir", ".")
        super().__init__(*args, **kwargs)

    def default(self, obj):
        """
        Overrides the default method of json.JSONEncoder.

        Args:
        obj (object): The object to convert to JSON.

        Returns:
        dict or list or str or int or float or bool or None: The JSON-serializable representation of obj.
        """
        from standards.Compression_standard_ISO import SpecimenQCManager

        if isinstance(obj, SpecimenDINAnalysis) or isinstance(obj, SpecimenQCManager):
            return  # return None or skip if the object is an instance of SpecimenDINAnalysis
        elif isinstance(obj, SpecimenDataManager) or isinstance(obj, SpecimenGraphManager):
            return self.encode_dict(obj.__dict__)
        else:
            return super().default(obj)
        # try:
        #     return super().default(obj)
        # except TypeError:
        #     if isinstance(obj, dict):
        #         return self.encode_dict(obj)
        #     elif hasattr(obj, '__dict__'):
        #         return self.encode_dict(obj.__dict__)
        #     else:
        #         raise

    def encode_dict(self, obj_dict):
        """
        Encodes a dictionary into a JSON-friendly format.

        Args:
        obj_dict (dict): The dictionary to encode.

        Returns:
        dict: The encoded dictionary.
        """
        encoded_dict = {}
        for attr, value in obj_dict.items():
            if attr == "raw_data" or attr == "specimen":
                continue  # Skip raw_data and specimen
            elif isinstance(value, dict):
                encoded_dict[attr] = self.encode_dict(value)  # recursively handle nested dictionaries
            elif isinstance(value, np.int64) or isinstance(value, pd.Int64Dtype):
                encoded_dict[attr] = int(value)  # Convert np.int64 to int
            elif isinstance(value, (pd.DataFrame, pd.Series, np.ndarray)):
                csv_filename = f"{attr}_data.csv"
                csv_filepath = os.path.join(self.export_dir, csv_filename)
                if isinstance(value, pd.DataFrame):
                    value.to_csv(csv_filepath, index=False)
                else:
                    np.savetxt(csv_filepath, value, delimiter=",")
                encoded_dict[attr] = os.path.basename(csv_filename)
            else:
                encoded_dict[attr] = value
        return encoded_dict


from scipy.interpolate import CubicSpline


class SpecimenInterpolator:
    @staticmethod
    def interpolate_stresses(selected_specimens, common_strain, mode="default"):
        """
        Interpolates stress values for a list of specimens based on the specified mode.

        Parameters:
        - selected_specimens: List of specimen objects containing shifted_strain and stress attributes.
        - common_strain: Array of strain values to interpolate stresses at.
        - mode: Interpolation mode - "default", "ignore", "linear", or "spline".

        Returns:
        - List of interpolated stress arrays, one for each specimen.
        """
        if mode == "default":
            return SpecimenInterpolator._default_interpolation(selected_specimens, common_strain)
        elif mode == "ignore":
            return SpecimenInterpolator._ignore_outside_range(selected_specimens, common_strain)
        elif mode == "linear":
            return SpecimenInterpolator._linear_extrapolation(selected_specimens, common_strain)
        elif mode == "spline":
            return SpecimenInterpolator._spline_interpolation(selected_specimens, common_strain)
        else:
            raise ValueError(f"Invalid mode: {mode}")

    @staticmethod
    def _default_interpolation(selected_specimens, common_strain):
        # Interpolates using default settings with no extrapolation.
        return [np.interp(common_strain, specimen.shifted_strain, specimen.stress) for specimen in selected_specimens]

    @staticmethod
    def _ignore_outside_range(selected_specimens, common_strain):
        # Interpolates with NaN for values outside the strain range.
        return [
            np.interp(common_strain, specimen.shifted_strain, specimen.stress, left=np.nan, right=np.nan)
            for specimen in selected_specimens
        ]

    @staticmethod
    def _linear_extrapolation(selected_specimens, common_strain):
        # Performs linear extrapolation beyond known data range.
        interpolated_stresses = []
        for specimen in selected_specimens:
            strain = specimen.shifted_strain
            stress = specimen.stress

            if isinstance(strain, pd.Series):
                strain = strain.to_numpy()
            if isinstance(stress, pd.Series):
                stress = stress.to_numpy()

            if len(strain) < 2 or len(stress) < 2:
                print("Insufficient data for linear extrapolation. Filling with NaN.")
                interpolated_stresses.append(np.full_like(common_strain, np.nan))
                continue

            # Interpolate within range
            max_stain = strain.max()
            interp_values = np.interp(common_strain, strain, stress, left=0)
            # By default, right extrapolation is not performed but extended wit last value ( horizontal line)

            # Calculate the slope only for right extrapolation
            try:
                slope_right = SpecimenInterpolator._calculate_slope_with_fallback(stress, strain)
            except Exception as e:
                print(f"Error calculating right slope: {e}")
                slope_right = np.nan

            # Right extrapolation using calculated slope
            right_extrapolation = stress[-1] + slope_right * (common_strain[common_strain > strain[-1]] - strain[-1])

            # Replace the right horizontal line with the extrapolated values
            interp_values[common_strain > strain[-1]] = right_extrapolation

            interpolated_stresses.append(interp_values)

        return interpolated_stresses

    @staticmethod
    def _calculate_slope_with_fallback(
        stress: np.ndarray,
        strain: np.ndarray,
    ):
        for i in range(len(stress) - 1, 0, -1):
            if (stress[i] != stress[i - 1]) and (strain[i] != strain[i - 1]):
                try:
                    slope = (stress[i] - stress[i - 1]) / (strain[i] - strain[i - 1])
                    if not np.isinf(slope) and not np.isnan(slope):
                        return slope
                    else:
                        print("Invalid slope value (inf or NaN). Returning slope of 0.")
                        return 0
                except ZeroDivisionError:
                    print("ZeroDivisionError in slope calculation. Returning slope of 0.")
                    return 0
        print("No valid non-zero differences found for right slope. Returning slope of 0.")
        return 0

    @staticmethod
    def _spline_interpolation(selected_specimens, common_strain):
        # Uses cubic spline interpolation, with fallback to linear if strains are not strictly increasing.
        interpolated_stresses = []
        for specimen in selected_specimens:
            # Remove duplicates and ensure strictly increasing order

            strain_stress_df = pd.DataFrame({"strain": specimen.shifted_strain, "stress": specimen.stress})
            strain_stress_df = strain_stress_df.drop_duplicates(subset="strain")

            # Extract cleaned, strictly increasing strain and stress values
            sorted_strain = strain_stress_df["strain"].values
            sorted_stress = strain_stress_df["stress"].values

            if len(sorted_strain) < 2:
                print("Insufficient unique data points for spline interpolation. Filling with NaN.")
                interpolated_stresses.append(np.full_like(common_strain, np.nan))
                continue

            # Append interpolated values using cubic spline
            interpolated_stresses.append(
                SpecimenInterpolator._cubic_spline_interpolation(sorted_stress, sorted_strain, common_strain)
            )

        return interpolated_stresses

    @staticmethod
    def _calculate_slope(y_values, x_values, index1, index2):
        # Helper to calculate slope between two points.
        return (y_values[index2] - y_values[index1]) / (x_values[index2] - x_values[index1])

    @staticmethod
    def _cubic_spline_interpolation(y_values, x_values, common_x):
        # Initialize the cubic spline with extrapolation enabled
        spline = CubicSpline(x_values, y_values, extrapolate=True)
        return spline(common_x)
