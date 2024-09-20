"""
Refactor plot , plot state and plot manager

PlotManager is the Orchestrator: Handles overall plot management
and delegates data normalization, configuration, and state tracking to Plot and PlotState

Methods:
    - list_available_plots() -> list[str]:
    - list_plot_elements() -> list[str]:
    - create_or_update_plot() -> Plot:
    - remove_plot() -> bool:
    - get_entity_data() -> pd.Series: [static]
    - get_entity_property() -> Coordinate: [static]
    - get_plot_elements_data() Union[tuple[pd.Series, pd.Series], Coordinate]: [static]
    - get_plot_element_derivative() -> pd.Series: [static] *entity.property_calcuator for computing derivative
    - get_plot_element_integral()-> pd.Series: [static] *entity.property_calcuator for computing integral
    - save_shifted_data_to_entity() -> bool: [static]
    - _normalize_data_for_plotting() -> Union[tuple[pd.Series, pd.Series], tuple[float, float] ]: [static]
    - _generate_element_label() -> str : [static]

Plot Manages the Data (Figure / Plot) and Configuration:
Methods:
    - add_plot_element():
    - set_style():
    - update_plot() -> Plot:
    - add_axis() -> tuple[plt.Figure, plt.Axes]:
    - remove_axis() - > bool:
    - apply_plot_config() -> plt.Axes:
    - save_plot() - > bool:
    - export_plot_data() - > bool:

PlotState Tracks the Plot's State: (Decople state and data)
Responsible for keeping track of elements (lines, scatter points) and ensuring the
where that data is comes is tracked, by recording (entitty), the properties on which axes
Methods:
    - add_plot_element() - > bool:
    - hide_plot_element() - > bool:
    - show_plot_element() - > bool:
    - remove_plot_element() - > bool:
    - update_plot_element() - > bool:
    - hide_legend() - > bool:
    - show_legend() - > bool:
    - set_active_axis() > plt.Axes:
    - _add_shaded_region( ) -> bool: Artist Patch
    - _add_text_annotation() -> bool: Artist Text
    - _add_arrow() -> bool: Artist
    - _add_image() -> bool: Artist Image
    - _add_patch() -> bool:

PlotConfig:
    - Stores the configuration of the plot (e.g., colors, labels, line styles)
    - Provides a default configuration if none is provided

PlotExporter
    -  Handles saving plots, exporting plot data, and configuration.

dataclass Coordinate:
    - Represents a point in 2D space
    - Used to store x, y coordinates for plotting

dataclass PlotElement:
    - Represents a single element in a plot (e.g., a line, scatter point)
    - Contains the plot object, x and y data, entity name, property name, and axis
"""
