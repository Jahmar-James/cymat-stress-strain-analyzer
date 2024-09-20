import os
import sys

import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


print(sys.path)

from visualization.plot_config import PlotConfig
from visualization.plot_data import (
    AnnotationData,
    Coordinate,
    HorizontalLineData,
    ShadedRegionData,
    TextData,
    VerticalLineData,
)
from visualization.plot_manager import PlotManager


class AnalyzableEntity:
    def __init__(
        self,
    ):
        self.name = "Dummy Entity"
        self._strength = Coordinate(10, 20)

    """Dummy class to represent an entity that can be analyzed."""

    @property
    def stress(self) -> pd.Series:
        return pd.Series([1, 2, 3, 4, 5], name="stress")

    @property
    def strain(self) -> pd.Series:
        return pd.Series([1, 4, 9, 16, 25], name="strain")

    @property
    def force(self) -> pd.Series:
        return pd.Series([10, 20, 30, 40, 50], name="force")

    @property
    def displacement(self) -> pd.Series:
        return pd.Series([1, 2, 3, 4, 5], name="displacement")

    @property
    def is_sample_group(self) -> bool:
        return False

    @property
    def strength(self) -> "Coordinate":
        return self._strength

    @strength.setter
    def strength(self, value: "Coordinate") -> None:
        self._strength = value


def cli_frontend() -> None:
    plot_manager = PlotManager()

    # Dummy data for testing
    x_data = np.linspace(0, 10, 100)
    y_data = np.sin(x_data) + random.uniform(-0.5, 0.5)

    # Simulate user choices
    while True:
        print("\n--- Dummy Plot Frontend ---")
        print("1. Create Line Plot")
        print("2. Create Scatter Plot")
        print("3. Display Plot")
        print("4. Exit")
        print("5. Add ax in direction")
        print("6. Add horizontal line")
        print("7. Add vertical line")
        print("8. Add shaded region")
        print("9. Add text annotation")
        print("10. Add arrow annotation")

        choice = input("Choose an option: ")

        entity_instance = AnalyzableEntity()
        plot_manager = PlotManager()

        if choice == "1":
            plot_name = input("Enter plot name for plot: ")
            plot = plot_manager.add_entity_to_plot(
                entity_instance,
                plot_name,
                x_data_key="strain",
                y_data_key="stress",
                plot_type="line",
                element_label="stress vs strain",
            )
            plot_manager.add_entity_to_plot(
                entity_instance, plot=plot, x_data_key="displacement", y_data_key="force", plot_type="line"
            )
            plot_manager.add_entity_to_plot(entity_instance, plot=plot, propperty_key="strength", plot_type="scatter")
            ax = plot.axes["main"]
            ax.set_title("Mixed Plot")
            print(f"Plot '{plot_name}' created! Polt has these elements: {plot_manager.list_plot_elements(plot_name)}")

            plotted_strength = plot_manager.get_plot_elements_data(plot_name, "strength")
            print(f"Plotted strength data is {plotted_strength}")

            plotte_stress = plot_manager.get_plot_elements_data(plot_name, "stress vs strain")
            print(f"Plotted stress vs strain data is {plotte_stress}")

            print(ax.lines)

        elif choice == "2":
            plot_name = input("Enter plot name for scatter plot: ")
            plot = plot_manager.add_entity_to_plot(
                entity_instance,
                plot_name=plot_name,
                propperty_key="strength",
                plot_type="scatter",
                element_label="strength",
            )
            ax = plot.axes["main"]
            ax.set_title("Scatter Plot")
            print(f"Scatter plot '{plot_name}' created!")
            updated_strength = Coordinate(10, 10)
            v_shifted_data = plot_manager.save_shifted_data_to_entity(
                entity_instance, "strength", updated_strength.x, updated_strength.y
            )
            old_strength = getattr(entity_instance, "Orignal_strength")
            print(
                f"Updated strength data saved to entity was {v_shifted_data}. The new strength data is {entity_instance.strength} and the old is {old_strength}."
            )
            plot_state = plot.plot_state
            y = float(input("Enter y value for horizontal line: "))
            # possible line styles: '-', '--', '-.', ':', 'None', ' ', '', 'solid', 'dashed', 'dashdot', 'dotted'
            annotation = HorizontalLineData(y, color="yellow", linestyle=None)
            print(f"Adding horizontal line to plot '{plot_name}' at y={y}...")
            print(f"The plot as the following elements and axes key: {plot_state.elements}, {plot.axes.keys()}")
            plot_state.add_horizontal_line(plot.axes["main"], annotation)
            x = float(input("Enter x value for vertical line: "))
            annotation: VerticalLineData = VerticalLineData(x, color="red", linestyle="--")
            print(f"Adding vertical line to plot '{plot_name}' at x={x}...")

            print(f"Adding shaded region to plot '{plot_name}'...")
            annotation = ShadedRegionData(2, 4, color="green", alpha=0.3)
            plot_manager.add_annotation_to_plot(plot_name, annotation)

            # updating plot element style - Change scatter plot to purple
            plot_state.update_plot_element_style("strength", color="purple")

        elif choice == "3":
            plt.show()
        elif choice == "4":
            print("Exiting...")
        elif choice == "5":
            plot_name = "Test Plot"
            test_config = PlotConfig(title="Test Plot", xlabel="X-axis", ylabel="Y-axis", grid=True)
            # plot fake entity data
            plot = plot_manager.add_entity_to_plot(
                entity_instance,
                propperty_key="strength",
                plot_type="scatter",
                plot_config=test_config,
                plot_name=plot_name,
            )
            plot = plot_manager.add_entity_to_plot(
                entity_instance, plot=plot, x_data_key="stress", y_data_key="force", plot_type="line"
            )
            # Fake data for testing
            arrow_data = AnnotationData(x=5, y=5, text_x=30, text_y=15, text="Arrow Annotation")
            # mofiy text
            arrow_data.text = "This is an arrow annotation"
            # add arrow annotation to the plot
            plot = plot_manager.add_annotation_to_plot(
                plot_name,
                arrow_data,
            )
            # add Text annotation
            text_data = TextData(x=5, y=5, text="This is a text annotation", fontsize=12)
            plot = plot_manager.add_annotation_to_plot(plot_name, text_data)
            plt.show()
            # get the plot objects and elements label
            plot_elements = plot_manager.list_plot_elements(plot_name)
            print(f"Plot elements are: {plot_elements}")

            # try tp extract the arrow data dyanmically when not defining element label then creating the object
            for element in plot_elements:
                if "arrow" in element:
                    arrow_data_from_plot = plot_manager.get_plot_elements_data(plot_name, element)
                    print(f"Arrow data from plot is: {arrow_data_from_plot}")

            # get the plot data for the text annotation and arrow annotation print it

            plot_state = plot.plot_state
            for element in plot_elements:
                style = plot_state.get_plot_element_style(element)
                print(f"Style for element '{element}' is: {style}")

            # hide the legend
            plot_state.hide_legend()
            # change the style of the text annotation to red and bold and update the plot
            plot_state.update_plot_element_style(element_label="TextData_4", color="red", fontsize=15)
            plt.show()

            # get all plot data for the plot and try to plot it
            fig, ax = plt.subplots()
            new_plot_name = "Test Plot 2"
            for element in plot_manager.list_plot_elements(plot_name):
                x, y = plot_manager.get_plot_elements_data(plot_name, element)
                print(f"Element data for element '{element}' is: {x}, {y}")
                ax.plot(x, y, label=element)
            plt.show()

            break
        else:
            print("Invalid choice. Please select a valid option.")


def gui_frontend():
    plot_manager = PlotManager()

    def plot_line():
        x_data = np.linspace(0, 10, 100)
        y_data = np.sin(x_data) + random.uniform(-0.5, 0.5)
        fig, ax = plot_manager.create_or_update_plot("line_plot", x_data, y_data, plot_type="line")
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def plot_scatter():
        x_data = np.linspace(0, 10, 100)
        y_data = np.random.rand(100)
        fig, ax = plot_manager.create_or_update_plot("scatter_plot", x_data, y_data, plot_type="scatter")
        ax.set_title("Scatter Plot")
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    root = Tk()
    root.title("Dummy GUI for PlotManager Testing")

    frame = Frame(root)
    frame.pack()

    btn_line = Button(root, text="Plot Line", command=plot_line)
    btn_line.pack()

    btn_scatter = Button(root, text="Plot Scatter", command=plot_scatter)
    btn_scatter.pack()


if __name__ == "__main__":
    import random
    from tkinter import Button, Frame, Tk

    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    cli_frontend()
    import random
    from tkinter import Button, Frame, Tk

    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    cli_frontend()
