import tkinter as tk

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)

from widget_manager import SliderManager


class PlotManager:
    def __init__(self, master, app):
        self.master = master  # Notebook tab should be master
        self.app = app
        self.shared_var = tk.DoubleVar()

        self.ax = None
        self.canvas = None
        self.position_dictionary = {'left': 0, 'middle': 1, 'right': 2}
        self.frames = {"left": None, "middle": None, "right": None}
        self.plots = {"left": None, "middle": None, "right": None}
        self.toolbars = {"left": None, "middle": None, "right": None}
        self.slider_managers = {"left": None, "middle": None}
        self.lines = {"left": None, "middle": {}}

        self.enable_click_event = False  # No click events on plots by default
        self.selected_points = []

    def create_figure_canvas(self, fig, position):
        tab = self.app.widget_manager.notebook.nametowidget(
            self.app.widget_manager.notebook.select())
        frame = tk.Frame(tab)
        self.frames[position] = frame
        frame.grid(row=7, column=2 * self.position_dictionary[position], columnspan=2)

        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()
        self.canvas = canvas

        toolbar_frame = tk.Frame(frame)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

        if position in ['left', 'middle']:
            slider_manager = SliderManager(
                self.frames[position], self.shared_var, self.app, self.update_plots_with_shift)
            self.slider_managers[position] = slider_manager
            current_tab_id = self.app.widget_manager.notebook.select()
            self.app.variables.set_slider_manager(
                current_tab_id, slider_manager)
            slider_manager.create_slider(frame)

        canvas.get_tk_widget().grid(row=0, column=0, sticky='n')
        toolbar_frame.grid(row=1, column=0, sticky='we')

        self.plots[position] = canvas
        self.toolbars[position] = toolbar

    def update_plots_with_shift(self, shift):
        self.specimen.manual_strain_shift = shift
        self.update_lines()

    def update_lines(self):
        # Update line data rather than recreating plot
        if self.lines["left"]:
            self.lines["left"].set_xdata(self.specimen.shifted_strain)
            self.lines["left"].set_ydata(self.specimen.stress)
            self.plots["left"].draw()

        # Middle plot contains lines for all specimens. We need to find and update the line for the current specimen.
        if self.specimen.name in self.lines["middle"]:
            line = self.lines["middle"][self.specimen.name]
            line.set_xdata(self.specimen.shifted_strain)
            line.set_ydata(self.specimen.stress)
            self.plots['middle'].draw()

    def plot_and_draw(self, plot_function, title, position, specimen):
        self.specimen = specimen
        fig, ax = plt.subplots(figsize=(5, 4))

        plot_function(ax)
        ax.set_title(title)
        ax.set_xlabel("Strain")
        ax.set_ylabel("Stress (MPa)")
        legend = ax.legend(loc="upper right")
        # bbox_to_anchor=(0.5, 1.6)

        self.ax = ax
        self.fig = fig
        self.fig.tight_layout()

        if position == 'left':
            for text in legend.get_texts():
                text.set_fontsize(8)

                lines = ax.get_lines()
                for line in lines:
                    if line.get_label() == "Shifted Stress-Strain Curve":
                        self.lines[position] = line
                        break

        if position == 'middle':
            self.create_lines()
        self.create_figure_canvas(fig, position)
        self.canvas.mpl_connect('button_press_event', self.on_plot_click)

    def create_lines(self):
        # Create a line for each specimen
        for line in self.ax.get_lines():
            self.lines["middle"][line.get_label()] = line

    def on_plot_click(self, event):
        if self.enable_click_event:
            ax = event.inaxes
            if ax is not None:
                # Iterate over lines in axes and find the one labeled 'Shifted Stress-Strain Curve'
                for line in ax.lines:
                    if line.get_label() == 'Shifted Stress-Strain Curve':
                        # Get the nearest index to the clicked point along the x-axis
                        xdata, ydata = line.get_xdata(), line.get_ydata()
                        clicked_point = event.xdata  # Only the x-coordinate matters
                        index = self.find_nearest_x(clicked_point, xdata)
                        print(f"index is {index}")

                        self.selected_points.append(index)

                        # If more than two points are selected, pop the first one (oldest)
                        if len(self.selected_points) > 2:
                            self.selected_points.pop(0)

                        # Visaul guide for user draw a vertical line at the selected point
                        ax.axvline(x=clicked_point, color='black', linestyle=':',
                                   linewidth=2.5, label=f'Selected point {len(self.selected_points)}')

                        # Redraw the lines
                        if len(self.selected_points) == 2:
                            self.selected_points.sort()
                            _, specimen = self.app.button_actions.get_current_tab()
                            # Set the indices
                            specimen.graph_manager.first_increase_index = self.selected_points[0]
                            specimen.graph_manager.next_decrease_index = self.selected_points[1]
                            print(
                                f"First index {specimen.graph_manager.first_increase_index } and last index {specimen.graph_manager.next_decrease_index}")
                            # Recalculate
                            specimen.graph_manager.youngs_modulus = None
                            specimen.graph_manager.calculate_youngs_modulus(
                                specimen.stress)
                            specimen.graph_manager.calculate_offset_line(
                                OFFSET=0.0002)
                            specimen.graph_manager.calculate_iys(
                                specimen.stress)
                            # Redraw
                            self.app.button_actions.plot_current_specimen()
                            # Clear the selected points list
                            self.selected_points.clear()

                        break

    @staticmethod
    def find_nearest_x(clicked_x, xdata):
        """Find the index of the nearest x value to 'clicked_x' in 'xdata'."""
        distances = np.abs(xdata - clicked_x)
        return np.argmin(distances)
