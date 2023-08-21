# process_control.py
import numpy as np
import pandas as pd
from control_chart import ControlChart, ControlProcessMetrics, ControlChartPlotter

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


def main():
    np.random.seed(0)
    
    df = pd.DataFrame({
        'Compressive Strength': np.random.normal(loc=7, scale=1, size=30),
        'Tensile Strength': np.random.normal(loc=15, scale=2, size=30),
        'Elastic Modulus': np.random.normal(loc=200, scale=10, size=30),
        'Thickness': np.random.normal(loc=27, scale=0.5, size=30),
        'Energy Absorption E20': np.random.normal(loc=50, scale=5, size=30),
        'Specific Energy Absorption E20': np.random.normal(loc=10, scale=1, size=30),
        'Stress at 20% Strain': np.random.normal(loc=500, scale=50, size=30)
    })

    control_properties = BaseControlSettings().create_settings('ML-RP-27.0-0.51')
    batch_control_chart_processor = BatchControlCharts(control_properties, df)
    batch_control_chart_processor.plot_chart()

@dataclass

class ControlPropertySettings:
    df_key: str
    title: str
    x_label: str = "Samples"
    y_label: str = 'Value'
    USL: Optional[float] = field(default=None, repr=False)  # repr=False ensures it won't show up in print statements, can be removed if not needed.
    LSL: Optional[float] = field(default=None, repr=False)
    tolerance_percentage: Optional[float] = field(default=None, repr=False)
    center: Optional[float] = field(default=None, repr=False)
    unit: str = ""
    use_sample_names: bool = False # If True, the x-axis will be the sample names instead of the sample number.
    filename: Optional[str] = None

    def __post_init__(self):
        # Ensure either tolerance_percentage is provided or USL and LSL but not both.
        if self.tolerance_percentage is not None:
            if self.USL is not None or self.LSL is not None:
                raise ValueError("If tolerance_percentage is provided, USL and LSL should be None.")
        elif self.USL is None or self.LSL is None:
            raise ValueError("Either provide tolerance_percentage or both USL and LSL.")

        # Ensure center is only provided with tolerance_percentage.
        if self.center is not None and self.tolerance_percentage is None:
            raise ValueError("Center can only be provided with tolerance_percentage.")
        
class BaseControlSettings:

    @staticmethod
    def extract_values_from_sku(sku):
        #SKU Example: ML-RP-27.0-0.51
        # Split by '-' and retrieve relevant values
        parts = sku.split('-')
        thickness = float(parts[2])
        density = float(parts[3])
        return thickness, density


    def create_settings(self, sku):
        self.sku = str(sku)
        self.date = datetime.today().strftime('%Y%m%d')
        thickness, density = self.extract_values_from_sku(sku)
        return [
        self._get_compressive_strength_settings(),
        self._get_tensile_strength_settings(),
        self._get_elastic_modulus_settings(),
        self._get_thickness_settings(thickness),
        self._get_energy_absorption_settings(),
        self._get_stress_at_20_settings(),
        self._get_density_settings(density)
    ]
    
    def _get_compressive_strength_settings(self):
        return ControlPropertySettings(
            df_key='Compressive Strength',
            title=f'{self.sku} : Compressive Strength Chart',
            y_label='Strength (MPa)',
            tolerance_percentage=10,
            unit='MPa',
            filename=f'{self.sku.replace("-","_")}_{self.date}_compressive_strength_control_chart.png'
        )
    
    def _get_tensile_strength_settings(self):
        return ControlPropertySettings(
            df_key='Tensile Strength',
            title=f'{self.sku} : Tensile Strength Chart',
            y_label='Strength (MPa)',
            tolerance_percentage=10,
            center=15,
            unit='MPa',
            filename=f'{self.sku.replace("-","_")}_{self.date}_tensile_strength_control_chart.png'
        )
    
    def _get_elastic_modulus_settings(self):
        return ControlPropertySettings(
            df_key='Elastic Modulus',
            title=f'{self.sku} : Elastic Modulus Chart',
            y_label='Modulus (MPa)',
            tolerance_percentage=10,
            unit='MPa',
            filename=f'{self.sku.replace("-","_")}_{self.date}_elastic_modulus_control_chart.png'
        )
    
    def _get_thickness_settings(self, thickness):
        USL = thickness + 1
        LSL = thickness - 1
        return ControlPropertySettings(
            df_key='Thickness',
            title=f'{self.sku} : Thickness Chart',
            y_label='Thickness (mm)',
            USL=USL,
            LSL=LSL,
            unit='mm',
            filename=f'{self.sku.replace("-","_")}_{self.date}_thickness_control_chart.png'
        )
    
    def _get_energy_absorption_settings(self):
        return ControlPropertySettings(
            df_key='Energy Absorption E20',
            title=f'{self.sku} : Energy Absorption E20 Chart',
            y_label='Energy (kJ/m^2)',
            tolerance_percentage=5,
            center=50,
            unit='kJ/m^2',
            filename=f'{self.sku.replace("-","_")}_{self.date}_energy_absorption_control_chart.png'
        )
    
    def _get_stress_at_20_settings(self):
        return ControlPropertySettings(
            df_key='Stress at 20% Strain',
            title=f'{self.sku} : Stress at 20% Strain Chart',
            y_label='Stress (MPa)',
            tolerance_percentage=10,
            unit='MPa',
            filename=f'{self.sku.replace("-","_")}_{self.date}_stress_at_20_control_chart.png'
        )
    
    def _get_density_settings(self, density):
        LSL, USL = self.calculate_density_LSL_USL(center_gcc= density, tolerance_RD=1)
        return ControlPropertySettings(
            df_key='Density',
            title=f'{self.sku} : Density Chart',
            y_label='Density (g/cc)',
            USL=USL,
            LSL=LSL,
            unit='g/cc',
            filename=f'{self.sku.replace("-","_")}_{self.date}_density_control_chart.png'
        )
    
    @staticmethod
    def calculate_density_LSL_USL(center_gcc, tolerance_RD = 1):
        # Convert center from g/cc to relative density
        center_relative_density = center_gcc / 2.7
        
        # Calculate relative density LSL and USL
        relative_density_LSL = center_relative_density - tolerance_RD 
        relative_density_USL = center_relative_density + tolerance_RD 
        
        # Convert relative density LSL and USL to g/cc
        LSL = 2.7 * relative_density_LSL
        USL = 2.7 * relative_density_USL
        
        return LSL, USL

class BatchControlCharts:
    """
    Class to create charts for key properties.

    Parameters:
    - properties: A dictionary that contains properties as the key with their respective USL, LSL, or 
                  tolerance_percentage. If the center is not provided, it will default to the mean of the data.
    - data: DataFrame with data to be plotted.
    """
    def __init__(self, properties, data):
        self.control_properties = properties
        self.data = data

    def prepare_data(self, control_property):
        """Prepare data and return essential details."""
        data_dict = {
            "column_data": self.data[control_property.df_key].values,
            "LSL": control_property.LSL,
            "USL": control_property.USL,
            "tolerance_percentage": control_property.tolerance_percentage,
            "center": control_property.center,
            "units": control_property.unit
        }
        return data_dict

    def display_statistics(self, chart_obj, key, units):
        """Display the statistics of the control chart."""   
        print(f"For {key}:")
        print(f"The Cp is {chart_obj.Cp:.4f} and the Cpk is {chart_obj.Cpk:.4f}")
        print(f"The UCL is {chart_obj.UCL:.2f} ({units}) and the LCL is {chart_obj.LCL:.2f} ({units})")
        print(f"The USL is {chart_obj.USL:.2f} ({units}) and the LSL is {chart_obj.LSL:.2f} ({units})\n")

    def plot_chart(self, save_plots=False, use_sample_names=False):
        for control_property in self.control_properties:
            if control_property.df_key in self.data.columns:
                property_data = self.prepare_data(control_property)

                data_processor = ControlProcessMetrics(property_data["column_data"], LSL=property_data["LSL"], USL=property_data["USL"])
                chart_plotter = ControlChartPlotter()
                
                if 'names' in self.data.columns:
                    custom_labels = self.generate_labels(control_property.df_key) if use_sample_names else None
                else:
                    custom_labels = None

                new_chart = ControlChart(property_data["column_data"], data_processor, chart_plotter)
                new_chart.calculate_and_plot(
                title=control_property.title,
                x_label=control_property.x_label,
                y_label=control_property.y_label,
                tolerance_percentage=control_property.tolerance_percentage,
                center=control_property.center,
                custom_ticks=custom_labels
            )
                
            if control_property.filename and save_plots is True:
                chart_plotter.save(control_property.filename)

            self.display_statistics(new_chart, control_property.df_key, control_property.unit)

    def generate_labels(self, column_name):
        """Generate custom labels based on non-NaN values in the given column."""
        # Filter rows where 'column_name' is not NaN
        filtered_df = self.data[self.data[column_name].notna()]

        # Extract the names for the non-NaN values
        return filtered_df['names'].tolist()


if __name__ == '__main__':
    main()


# to do
# create dataframe with real data
# format dict to stanard
# add units to plot
# save the plots
