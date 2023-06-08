import tkinter as tk
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mtick
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)

from widget_manager import SliderManager
from matplotlib.path import Path
from matplotlib.patches import PathPatch

OFFSET =0.002
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
        self.lines = {LEFT: {}, MIDDLE: {},RIGHT: {}}

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

    def plot_and_draw(self, plot_function, title, position, specimen):
        self.specimen = specimen
        fig, ax = plt.subplots(figsize=(5, 4))

        plot_function(ax)
        ax.set_title(title)
        ax.set_xlabel(r"Strain - $\varepsilon$ (%)")
        ax.set_ylabel(r"Stress - $\sigma$ (MPa)")
        self.ax = ax
        self.fig = fig
        
        self.legend = self.create_legends( ax, position)
        
        ax.xaxis.set_major_formatter(mtick.PercentFormatter())
        locator = mtick.MaxNLocator(nbins=6)
        ax.xaxis.set_major_locator(locator)
        ax.tick_params(axis='x', rotation=25)
    
        ax.axvspan(0, .2, facecolor='yellow', alpha=0.1)
        ax.axvspan(0.2, .4, facecolor='green', alpha=0.1)
        ax.text(0.1, ax.get_ylim()[-1]*0.95, 'Elastic \nRegion', ha='center', va='top', fontsize=8, color='black')
        ax.text(0.3, ax.get_ylim()[-1]*0.95, 'Plastic \nRegion', ha='center', va='top', fontsize=8, color='black')  
        
        ax.axhline(0, color='black', linestyle='--')
        ax.axvline(0, color='black', linestyle='--')
        ax.grid()

        self.fig.tight_layout()
        self.create_figure_canvas(fig, position)
        self.canvas.mpl_connect('button_press_event', self.on_plot_click)
          
    def update_lines(self):
        # Update line data rather than recreating plot
        if self.lines[LEFT]["Shifted Stress-Strain Curve"]:
            self.lines[LEFT]["Shifted Stress-Strain Curve"].set_xdata(self.specimen.shifted_strain)
            self.lines[LEFT]["Shifted Stress-Strain Curve"].set_ydata(self.specimen.stress)
            self.plots[LEFT].draw()

        # Middle plot contains lines for all specimens. We need to find and update the line for the current specimen.
        if self.specimen.name in self.lines[MIDDLE]:
            line = self.lines[MIDDLE][self.specimen.name]
            line.set_xdata(self.specimen.shifted_strain)
            line.set_ydata(self.specimen.stress)
            self.plots[MIDDLE].draw()
        
    def create_legends(self, ax, position):
     
        self.get_plot_lines(position)
            
        if position == LEFT:
            #scatter
            legend1_handles = [col for col in ax.collections]
            # lines
            legend2_handles = [line for line in ax.lines]
            
            legend1 = ax.legend(handles=legend1_handles, )
            ax.add_artist(legend1)  # add legend1 manually
            
            legend2 = ax.legend(handles=legend2_handles, loc='upper center', bbox_to_anchor=(0.45, -0.1), ncol=3)
            
            ax.add_artist(legend2)
            
            for text in legend1.get_texts():
                text.set_fontsize(6)
            for text in legend2.get_texts():
                text.set_fontsize(6)
            legend = legend1,legend2
            self.fig.subplots_adjust(bottom=0.3)
        else:
            # for the other positions, use the default legend
            legend = ax.legend()
            for text in legend.get_texts():
                text.set_fontsize(6)

        return legend

    def get_plot_lines(self, position):
        for line in self.ax.get_lines():
            self.lines[position][line.get_label()] = line
                  
    def update_lines_with_selected_points(self, ax):
        self.selected_points.sort()
        _, specimen = self.app.button_actions.get_current_tab()

        # Set the indices
        specimen.graph_manager.first_increase_index = self.selected_points[0]
        specimen.graph_manager.next_decrease_index = self.selected_points[1]

        # Recalculate
        specimen.graph_manager.youngs_modulus = None
        specimen.graph_manager.calculate_youngs_modulus(specimen.stress, specimen.strain)
        specimen.graph_manager.calculate_strength(specimen.stress, specimen.shifted_strain, offset=OFFSET)
        iys_strain, iys_stress = specimen.IYS
        ys_strain, ys_stress = specimen.YS

        # Update the lines
        strain_shifted = specimen.graph_manager.strain_shifted
        if specimen.graph_manager.strain_offset is not None:
            strain_offset = specimen.graph_manager.strain_offset
        if specimen.graph_manager.offset_line is not None:
            offset_line = specimen.graph_manager.offset_line
        
        
        for artist in ax.get_children()[:]: # create a copy of the list for iteration for removal
            if isinstance(artist, matplotlib.lines.Line2D):
                if artist.get_label() == 'First Significant Increase':
                    artist.set_xdata([strain_shifted[self.selected_points[0]]])
                if artist.get_label() == 'Next Significant Decrease':
                    artist.set_xdata([strain_shifted[self.selected_points[1]]])
                if artist.get_label() == f"{OFFSET*100}% Offset Stress-Strain Curve":
                    artist.set_xdata(strain_shifted)
                    artist.set_ydata(offset_line)
                # Remove vertical line
                if artist.get_label().startswith('Selected point'):
                    artist.remove()

            # Remove existing IYS scatter plot
            if isinstance(artist, matplotlib.collections.PathCollection) and artist.get_label().startswith('IYS:'):
                artist.remove()
            if isinstance(artist, matplotlib.collections.PathCollection) and artist.get_label().startswith('YS:'):
                artist.remove()
            
        
        if iys_strain is not None and iys_stress is not None:
            print("IYS found")
            ax.scatter(iys_strain, iys_stress, c="red",label=f"IYS: ({iys_strain:.3f}, {iys_stress:.3f})")
        
        if ys_strain is not None and ys_stress is not None:
            print("YS found")
            ax.scatter(ys_strain, ys_stress, c="blue",label=f"YS: ({ys_strain:.3f}, {ys_stress:.3f})")
            
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

def draw_error_band_xy(ax, x, y, xerr, yerr, **kwargs):
    # Calculate normals via centered finite differences
    dx = np.concatenate([[x[1] - x[0]], x[2:] - x[:-2], [x[-1] - x[-2]]])
    dy = np.concatenate([[y[1] - y[0]], y[2:] - y[:-2], [y[-1] - y[-2]]])
    l = np.hypot(dx, dy)
    nx = dy / l
    ny = -dx / l

    # End points of errors
    xp = x + nx * xerr
    yp = y + ny * yerr
    xn = x[::-1] - nx[::-1] * xerr[::-1]
    yn = y[::-1] - ny[::-1] * yerr[::-1]

    vertices = np.block([[xp, xn], [yp, yn]]).T
    codes = np.ones(vertices.shape[0], dtype=Path.code_type) * Path.LINETO
    codes[0] = Path.MOVETO

    path = Path(vertices, codes)
    ax.add_patch(PathPatch(path, **kwargs))

def draw_error_band_y(ax, x, y, err, **kwargs):
    xp = np.concatenate([x, x[::-1]])  # Upper band then lower band
    yp = np.concatenate([y + err, y[::-1] - err[::-1]])  # Positive error then negative error

    vertices = np.column_stack([xp, yp])
    codes = np.ones(vertices.shape[0], dtype=Path.code_type) * Path.LINETO
    codes[0] = Path.MOVETO

    path = Path(vertices, codes)
    patch = PathPatch(path, **kwargs)
    ax.add_patch(patch)
