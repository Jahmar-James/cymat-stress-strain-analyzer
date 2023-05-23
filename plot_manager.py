import tkinter as tk
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)

from widget_manager import SliderManager


LEFT = 'left'
MIDDLE = "middle"
RIGHT = 'right'
# Line manger class


class PlotManager:
    def __init__(self, master, app):
        self.master = master  # Notebook tab should be master
        self.app = app
        self.shared_var = tk.DoubleVar()

        self.ax = None
        self.canvas = None
        self.position_dictionary = {LEFT: 0, MIDDLE: 1, RIGHT: 2}
        self.frames = {LEFT: None, MIDDLE: None, RIGHT: None}
        self.plots = {LEFT: None, MIDDLE: None, RIGHT: None}
        self.toolbars = {LEFT: None, MIDDLE: None, RIGHT: None}
        self.slider_managers = {LEFT: None, MIDDLE: None}
        self.lines = {LEFT: None, MIDDLE: {}}

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

        if position in [LEFT,MIDDLE]:
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
        if self.lines[LEFT]:
            self.lines[LEFT].set_xdata(self.specimen.shifted_strain)
            self.lines[LEFT].set_ydata(self.specimen.stress)
            self.plots[LEFT].draw()

        # Middle plot contains lines for all specimens. We need to find and update the line for the current specimen.
        if self.specimen.name in self.lines[MIDDLE]:
            line = self.lines[MIDDLE][self.specimen.name]
            line.set_xdata(self.specimen.shifted_strain)
            line.set_ydata(self.specimen.stress)
            self.plots[MIDDLE].draw()

    def plot_and_draw(self, plot_function, title, position, specimen):
        self.specimen = specimen
        fig, ax = plt.subplots(figsize=(5, 4))

        plot_function(ax)
        ax.set_title(title)
        ax.set_xlabel("Strain")
        ax.set_ylabel("Stress (MPa)")
        legend = ax.legend(loc="upper right",framealpha=0.5)
        # bbox_to_anchor=(0.5, 1.6)

        self.ax = ax
        self.fig = fig
        self.fig.tight_layout()

        if position == LEFT:
            for text in legend.get_texts():
                text.set_fontsize(8)

                lines = ax.get_lines()
                for line in lines:
                    if line.get_label() == "Shifted Stress-Strain Curve":
                        self.lines[position] = line
                        break

        if position == MIDDLE:
            self.create_lines()
        self.create_figure_canvas(fig, position)
        self.canvas.mpl_connect('button_press_event', self.on_plot_click)

    def create_lines(self):
        # Create a line for each specimen
        for line in self.ax.get_lines():
            self.lines[MIDDLE][line.get_label()] = line
                  
    def update_lines_with_selected_points(self, ax):
        self.selected_points.sort()
        _, specimen = self.app.button_actions.get_current_tab()

        # Set the indices
        specimen.graph_manager.first_increase_index = self.selected_points[0]
        specimen.graph_manager.next_decrease_index = self.selected_points[1]

        # Recalculate
        specimen.graph_manager.youngs_modulus = None
        specimen.graph_manager.calculate_youngs_modulus(specimen.stress)
        specimen.graph_manager.calculate_offset_line(OFFSET=0.0002)
        specimen.graph_manager.calculate_iys(specimen.stress)
        iys_strain, iys_stress = specimen.IYS

        # Update the lines
        strain_shifted = specimen.graph_manager.strain_shifted
        strain_offset = specimen.graph_manager.strain_offset
        offset_line = specimen.graph_manager.offset_line
        OFFSET =0.002
        
        for artist in ax.get_children()[:]: # create a copy of the list for iteration for removal
            if isinstance(artist, matplotlib.lines.Line2D):
                if artist.get_label() == 'First Significant Increase':
                    artist.set_xdata([strain_shifted[self.selected_points[0]]]*2)
                if artist.get_label() == 'Next Significant Decrease':
                    artist.set_xdata([strain_shifted[self.selected_points[1]]]*2)
                if artist.get_label() == f"{OFFSET*100}% Offset Stress-Strain Curve":
                    artist.set_xdata(strain_offset)
                    artist.set_ydata(offset_line)
                # Remove vertical line
                if artist.get_label().startswith('Selected point'):
                    artist.remove()

            # Remove existing IYS scatter plot
            if isinstance(artist, matplotlib.collections.PathCollection) and artist.get_label().startswith('IYS:'):
                artist.remove()
            
        
        if iys_strain is not None and iys_stress is not None:
            print("IYS found")
            ax.scatter(iys_strain, iys_stress, c="red",label=f"IYS: ({iys_strain:.6f}, {iys_stress:.6f})")
            
        
        # Store the old legend's properties
        old_legend = ax.legend_
        loc = old_legend._loc
        bbox_to_anchor = old_legend.get_bbox_to_anchor().transformed(ax.transAxes.inverted())
        fontsize = old_legend.get_texts()[0].get_fontsize()
        framealpha = old_legend.get_frame().get_alpha()

        old_legend.remove()
        
        # Draw the new legend with the old properties
        ax.legend(loc=loc, bbox_to_anchor=bbox_to_anchor, fontsize=fontsize, framealpha=framealpha)

        
        # Clear the selected points list
        self.selected_points.clear()
        self.plots[LEFT].draw()

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

                        # Update the lines
                        if len(self.selected_points) == 2:
                            self.update_lines_with_selected_points(ax)

                        break

    @staticmethod
    def find_nearest_x(clicked_x, xdata):
        """Find the index of the nearest x value to 'clicked_x' in 'xdata'."""
        distances = np.abs(xdata - clicked_x)
        return np.argmin(distances)
