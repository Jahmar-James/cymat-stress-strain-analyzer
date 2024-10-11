"""
FRONTEND
main.py
/tkinter_frontend
    /core
    /top_level_create_sample
     - __init__.py
     -settings_top_level_create_sample.py
    /top_level_create_sample_group
    /top_level_plotting

BACKEND
/data_extraction -  Different formats of data fomart and styles
    - __init__.py
    - mechanical_test_data_preprocessor.py - Normalize data columns names and units
    /Cleaners - various ways to preprocess data ie. which columns to keep, which to drop, unit?, etc
        - __init__.py
        - default_data_cleaner.py
        - MTS_data_cleaner_2020.py
        - Element_data_cleaner.py
/stadards
    - __init__.py
    - sample_factory.py - Factory class to create samples
    /bases
        - __init__.py
        - analyzable_entity.py - inherited by sample and sample_group providing common methods and interface
        - base_standard_validator.py - ensure data adheres to standards
        - base_standard_operator.py - calculate sample propeties (sperating data and data processing) - will contain all methods use be default sample
        - base_standard_io_manager.py - store and load data into presistent storage. provide a remapping when needed
        - base_standard_group_io_manager.py - groups require a different way to store and load data and to consider the relationship between samples
    /default_sample - default sample class
        - __init__.py
        - sample.py - data storage, orchestrate sample creation and the nessary properties required for a sample
        - validator.py - unsure data meets standards so that sample can be created
        - sample_group.py - a collection of default samples. Possible with aggregation properties
    /visualizations_sample
    /iso_13314_2011
        - __init__.py
        - sample.py
/Visualization
    - plotting_manager.py
    - plot_data_helpers.py
/config
    - __init__.py
    /app_settings
    /workflow_settings
/tests
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from standards.base.analyzable_entity import AnalyzableEntity
from visualization.plot import Plot
from visualization.plot_data import HorizontalLineData, PlotData, VerticalLineData


def create_fake_sample() -> AnalyzableEntity:
    # Create a sample
    name = "Test Sample"
    length = 150.0  # mm
    width = 50.0  # mm
    thickness = 10.0  # mm
    mass = 300.0  # g

    # Generate force and displacement data (linear up to a point then plateau)
    displacement_data = pd.Series(np.linspace(0, 1, 100), name="Displacement")  # Displacement in mm
    force_data = pd.Series(
        np.concatenate([np.linspace(0, 500, 50), np.full(50, 500)]), name="Force"
    )  # Force in Newtons

    # Stress-Strain relationship (linear elastic behavior followed by plastic deformation)
    strain_data = pd.Series(np.linspace(0, 0.02, 100), name="Strain")  # Strain (dimensionless)
    stress_data = pd.Series(
        np.concatenate([np.linspace(0, 300, 50), np.linspace(300, 450, 50)]), name="Stress"
    )  # Stress in MPa

    # Create an instance of AnalyzableEntity
    return AnalyzableEntity(
        name,
        length,
        width,
        thickness,
        mass,
        force=force_data,
        displacement=displacement_data,
        stress=stress_data,
        strain=strain_data,
    )


def create_plot() -> "Plot":
    return Plot(
        name="Test Plot",
        plot_type="line",
    )


if __name__ == "__main__":
    # Intergated test
    plot = create_plot()
    sample = create_fake_sample()

    plot_1 = sample.plot_force_displacement(plot=plot, update_fig=True)
    plot_1.show()

    plot_2 = sample.plot_stress_strain(plot=plot, update_fig=True)
    plot_2.show()

    test_h_annotation = HorizontalLineData(y=500, color="red", linestyle="--")
    test_v_annotation = VerticalLineData(x=0.02, color="red", linestyle="--")

    plot_name = plot_2.name
    sample.plot_manager.add_annotation_to_plot(plot_name, test_h_annotation)
    sample.plot_manager.add_annotation_to_plot(plot_name, test_v_annotation)

    plot_2.show()
