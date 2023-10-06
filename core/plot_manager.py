import tkinter as tk
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mtick
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.offsetbox import OffsetImage
from tkinter import filedialog

from PIL import Image
from .widget_manager import SliderManager
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.patches import Patch

OFFSET =0.002
LEFT = 'left'
MIDDLE = "middle"
RIGHT = 'right'

#set Lengend to top left corner when saving
class CustomToolbar(NavigationToolbar2Tk):
    #Custom toolbar class to Save figure with new size and DPI
    def save_figure(self, *args):
        filetypes = self.canvas.get_supported_filetypes().items()
        default_filetype = self.canvas.get_default_filetype()
        
        fname = filedialog.asksaveasfilename(
            defaultextension=default_filetype,
            filetypes=[*filetypes, ("All Files", "*.*")], )
        if fname:
            fname = self._ensure_supported_filetype(fname)
              # Store original size
            original_size = self.canvas.figure.get_size_inches()
            # Set new size
            self.canvas.figure.set_size_inches(8, 6)

            # Check if logo is inside or outside
            if self.ax.get_label() == 'logo_axes':
                LogoHelper.place_logo_with_inside(self.ax)
            elif self.ax.get_label() == 'logo_title':
                LogoHelper.place_logo_outside(self.ax)
            
            # Save with new DPI and size
            self.canvas.figure.savefig(fname, dpi=300)
            # Restore original size
            self.canvas.figure.set_size_inches(original_size)

            # successfull save message
            tk.messagebox.showinfo("Info", f"Successfully saved as {fname}")

    def set_ax(self,ax):
        self.ax = ax

    def _ensure_supported_filetype(self, fname):
        """
        Ensure that the file extension is supported. Default to .png if not.
        """
        # Get the file extension
        file_extension = fname.split('.')[-1]

        # Check if the file extension is in the supported file types or if it's not specified
        if not file_extension or file_extension not in self.canvas.get_supported_filetypes():
            fname += ".png"
            tk.messagebox.showinfo("Info", f"Unsupported file type. Saving as PNG.")
        
        return fname


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
        toolbar = CustomToolbar(canvas, toolbar_frame)
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

        self.legend = self.create_legends(ax, position)
        
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1))
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())

        ax.tick_params(axis='x', rotation=25)
        
        self.plateau_region_start_entry = self.app.widget_manager.prelim_group.range_entry_start
        self.plateau_region_end_entry = self.app.widget_manager.prelim_group.range_entry_end
        plateau_region_start = self.plateau_region_start_entry.get()
        plateau_region_end  = self.plateau_region_end_entry.get()

        if plateau_region_start and plateau_region_end:
            if plateau_region_start ==  self.plateau_region_start_entry.placeholder:
                plateau_region_start =0.2
            if plateau_region_end ==  self.plateau_region_end_entry.placeholder:
                plateau_region_end = 0.4    
            # ax.axvspan(float(plateau_region_start), float(plateau_region_end), facecolor='green', alpha=0.1)
            # ax.text((float(plateau_region_start) + float(plateau_region_end))/2, ax.get_ylim()[-1]*0.95, 'Plateau \nRegion', ha='center', va='top', fontsize=8, color='black')
      
        ax.axhline(0, color='black', linestyle='--')
        ax.axvline(0, color='black', linestyle='--')
        ax.grid()

        if position is not LEFT:
            self.fig.tight_layout()
        
        
        self.create_figure_canvas(fig, position)
        # Adjust styles based on toggle states
        self.set_plot_styles(self.ax, position)

        self.canvas.mpl_connect('button_press_event', self.on_plot_click)


    def set_plot_styles(self, ax, position):
        # Access the states of the toggle buttons
        is_internal_enabled = self.app.widget_manager.internal_plot_enabled.get()
        is_external_enabled = self.app.widget_manager.external_plot_enabled.get()

        def common_plot_styles(ax):
            locator = mtick.MaxNLocator(nbins=8)
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_locator(ticker.MultipleLocator(0.1))

        # Apply styles based on the toggle states
        if position in [MIDDLE, RIGHT]:
            # set the canvas ax to the current ax 
            self.toolbars[position].set_ax(ax)
            
            if is_internal_enabled and not is_external_enabled:
                common_plot_styles(ax)

                
            
            elif is_external_enabled and not is_internal_enabled:
                common_plot_styles(ax)

                # X-axis customization
                ax.set_xlim(0, 0.6)  # 0 to 60% strain
                ax.xaxis.set_major_locator(ticker.MultipleLocator(0.1))  # 10% major ticks
                ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.02))  # 2% minor ticks

                # Y-axis customization
                ax.set_ylim(0, 20)  # 0 to 20 MPa stress
                ax.yaxis.set_major_locator(ticker.MultipleLocator(2))  # 2 MPa major ticks
                ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.5))  # 0.5 MPa minor ticks

                ax.legend(loc='upper center', ncol=1, fontsize=6)

                # Add logo
                if position == RIGHT:
                    LogoHelper.place_logo_outside(ax)
                else: # MIDDLE
                    LogoHelper.place_logo_with_inside(ax)
                        
                # Add address in footer
                ax.figure.text(0.5, 0.02, 'Cymat Technologies Ltd. 6320-2 Danville Road Mississauga, Ontario, Canada, L5T 2L7', ha='center', va='bottom', fontsize=6, color='black')
          
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
            
            legend2 = ax.legend(handles=legend2_handles, loc='upper center', bbox_to_anchor=(0.45, -0.3), ncol=2) 
            ax.add_artist(legend2)

            #Lengnd 1 must come after legend 2 to update the legend labels
            legend1 = ax.legend(handles=legend1_handles, )
            ax.add_artist(legend1)  
            
            for text in legend1.get_texts():
                text.set_fontsize(6)
            for text in legend2.get_texts():
                text.set_fontsize(6)
            legend = legend1,legend2
            self.fig.subplots_adjust(bottom=0.32)
            self.display_modulus_values(ax, OFFSET=OFFSET)
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
        
        ESTIMATED_PLASTIC_INDEX_START = 'Start of Plastic Region'
        ESTIMATED_PLASTIC_INDEX_END = 'End of Plastic Region'
        
        for artist in ax.get_children()[:]: # create a copy of the list for iteration for removal
            if isinstance(artist, matplotlib.lines.Line2D):
                if artist.get_label() == ESTIMATED_PLASTIC_INDEX_START:
                    artist.set_xdata([strain_shifted[self.selected_points[0]]])
                if artist.get_label() == ESTIMATED_PLASTIC_INDEX_END:
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

        # update to work with split legend for left plot
            
        # TODO: exclue non scatter plots from this

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
    
    def display_modulus_values(self, ax, OFFSET=0.02):
        # Label to identify the offset stress-strain curve
        offset_label = f"{OFFSET*100}% Offset Stress-Strain Curve"

        # Iterate over all lines in the ax to find the one labeled with offset_label
        for artist in ax.get_children():
            if isinstance(artist, matplotlib.lines.Line2D) and artist.get_label() == offset_label:
                # Get the x and y data from the line
                x_data, y_data = artist.get_xdata(), artist.get_ydata()
                
                # Get two points from the data to calculate the slope (modulus value)
                x1, y1 = x_data[0], y_data[0]
                x2, y2 = x_data[1], y_data[1]

                # Calculate and print the slope (modulus value)
                try:
                    slope = (y2 - y1) / (x2 - x1)
                    print(f"The modulus value (slope) is: {slope}")
                    return
                except ZeroDivisionError:
                    print("The two points have the same x value; cannot calculate slope.")
                    return

        # If we reach here, the line with the offset label was not found
        print(f"No line found with label: {offset_label}")


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

def draw_error_band_y(ax, x, y, err, label=None, **kwargs):
    xp = np.concatenate([x, x[::-1]])  # Upper band then lower band
    yp = np.concatenate([y + err, y[::-1] - err[::-1]])  # Positive error then negative error

    vertices = np.column_stack([xp, yp])
    codes = np.ones(vertices.shape[0], dtype=Path.code_type) * Path.LINETO
    codes[0] = Path.MOVETO

    path = Path(vertices, codes)
    patch = PathPatch(path,label=label, **kwargs)
    ax.add_patch(patch)

def draw_error_band_y_modified(ax, x, upper_y, lower_y,label=None, **kwargs):
    xp = np.concatenate([x, x[::-1]])  # Upper band then lower band for x axis
    yp = np.concatenate([upper_y, lower_y[::-1]])  # Upper limit then lower limit

    vertices = np.column_stack([xp, yp])
    codes = np.ones(vertices.shape[0], dtype=Path.code_type) * Path.LINETO
    codes[0] = Path.MOVETO

    path = Path(vertices, codes)
    patch = PathPatch(path,label=label, **kwargs)
    ax.add_patch(patch)

class LogoHelper:
    @staticmethod
    def resize_logo(image_path, figure_area, area_fraction):
        # Load the original image and get its size
        original_image = Image.open(image_path)
        orig_width, orig_height = original_image.size
        
        # Determine the target area based on fraction of figure's area
        target_area = figure_area * area_fraction
        
        # Calculate the scaling factor
        scaling_factor = (target_area / (orig_width * orig_height)) ** 0.5
        
        # Resize the image
        new_width = int(orig_width * scaling_factor)
        new_height = int(orig_height * scaling_factor)
        resized_image = original_image.resize((new_width, new_height))
        
        # Convert to numpy array for figimage
        img_array = np.asarray(resized_image)
        
        return img_array
    
    def resize_logo_HW(image_path, target_width, target_height):
        original_image = Image.open(image_path)
        resized_image = original_image.resize((target_width, target_height), Image.LANCZOS)
        img_array = np.asarray(resized_image)
        return img_array
    

    @staticmethod
    def place_logo_with_inside(ax, area_fraction=0.05):
        logo_path = 'templates\CYM004-Cymat-logo.png'
        
        # Get the figure area for the resizing
        figure_area = ax.figure.bbox.width * ax.figure.bbox.height
        img_array = LogoHelper.resize_logo(logo_path, figure_area, area_fraction)

        # Check for existing logo and remove it
        LogoHelper._remove_existing_logo(ax.figure, 'logo_axes')
        LogoHelper._remove_existing_logo(ax.figure, 'logo_title')
        
        x_left_limit = ax.get_xlim()[0]
        x_right_limit = ax.get_xlim()[1]
        y_bottom_limit = ax.get_ylim()[0]
        y_top_limit = ax.get_ylim()[1]
        
        x_range = x_right_limit - x_left_limit
        y_range = y_top_limit - y_bottom_limit
        
        logo_margin_x = x_range * 0.01
        logo_margin_y = y_range * 0.01
        
        logo_width_data = x_range * 0.15
        logo_height_data = y_range * 0.15

        ax.imshow(img_array, aspect='auto', 
                  extent=[x_left_limit + logo_margin_x, x_left_limit + logo_width_data + logo_margin_x, 
                          y_top_limit - logo_height_data - logo_margin_y, y_top_limit - logo_margin_y], 
                  zorder=1, alpha=1, label='logo_axes')

    @staticmethod
    def place_logo_outside(ax, area_fraction=1):
        from mpl_toolkits.axes_grid1.inset_locator import inset_axes

        logo_path = 'templates\CYM004-Cymat-logo.png'
                
        dpi = ax.figure.dpi
        target_width = int(ax.figure.get_figwidth() * dpi * area_fraction)
        target_height = int(ax.figure.get_figheight() * dpi * area_fraction)
        
        img_array = LogoHelper.resize_logo_HW(logo_path, target_width, target_height)

        # Remove existing logos
        LogoHelper._remove_existing_logo(ax.figure, 'logo_axes')
        LogoHelper._remove_existing_logo(ax.figure, 'logo_title')

        # Adjust positioning based on feedback
        axins = inset_axes(ax, 
                           width="10%", 
                           height="10%", 
                           loc='upper left',
                           bbox_to_anchor=(-0.16, 0.1, 1, 1),  
                           bbox_transform=ax.transAxes, 
                           borderpad=0)
        
        axins.imshow(img_array)
        axins.axis('off')

    @staticmethod
    def _remove_existing_logo(figure, logo_label):
        """
        Helper method to remove existing logos based on their label.
        """
        existing_logo_axes = [a for a in figure.get_axes() if a.get_label() == logo_label]
        for logo_axes in existing_logo_axes:
            figure.delaxes(logo_axes)
            print(f"Removed existing {logo_label} logo")


class ProcessControlChart:
    
    def __init__(self, data, LCL, UCL):
        self.data = data
        self.LCL = LCL
        self.UCL = UCL
        self.center, self.sigma = self._calculate_process_parameters()
        self.Cp, self.Cpk = self._calculate_capability_indices()

    def _calculate_process_parameters(self):
        center = np.mean(self.data)
        sigma = np.std(self.data)
        return center, sigma

    def _calculate_capability_indices(self):
        Cp = (self.UCL - self.LCL) / (6 * self.sigma)
        Cpk = min((self.UCL - self.center) / (3 * self.sigma), (self.center - self.LCL) / (3 * self.sigma))
        return Cp, Cpk

    def plot_control_chart(self, title):
        plt.figure(figsize=(10, 6))
        plt.plot(self.data, marker='o', color='b', linestyle='None')
        plt.axhline(y=self.center, color='r', linestyle='-')  # Center line
        plt.axhline(y=self.UCL, color='g', linestyle='--')  # Upper Control Limit (UCL)
        plt.axhline(y=self.LCL, color='g', linestyle='--')  # Lower Control Limit (LCL)
        plt.ylim(bottom=0)
        plt.title(title)
        plt.xlabel('Sample')
        plt.ylabel('Value')
        plt.text(0, self.UCL + 0.5, f'Cp = {self.Cp:.2f}, Cpk = {self.Cpk:.2f}')
        legend_elements = [Patch(facecolor='blue', edgecolor='blue', label='Data'),
                           Patch(facecolor='red', edgecolor='red', label='Mean'),
                           Patch(facecolor='green', edgecolor='green', label='Control Limits')]
        plt.legend(handles=legend_elements, loc='upper right')
        plt.show()


# # Let's use the class for Compressive Strength and Density
# # Set the random seed for reproducibility
# np.random.seed(0)

# # Generate synthetic data for Compressive Strength and Density
# compressive_strength = np.random.normal(loc=50, scale=10, size=30)  # Mean = 50, Standard Deviation = 10
# density = np.random.normal(loc=7, scale=1, size=30)  # Mean = 7, Standard Deviation = 1

# # Assume specification limits for Compressive Strength are 70 and 30
# pcc1 = ProcessControlChart(compressive_strength, 30, 70)
# pcc1.plot_control_chart('Control Chart for Compressive Strength')

# # Assume specification limits for Density are 9 and 5
# pcc2 = ProcessControlChart(density, 5, 9)
# pcc2.plot_control_chart('Control Chart for Density')
