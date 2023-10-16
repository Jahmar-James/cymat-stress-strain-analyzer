import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import datetime
import numpy as np

# To Do
# toolbox or round toggle for checkbuttons
# float button for export data to excel
# add buttons for iso and DIn mode

# widget_manager.py
class WidgetManager:
    """A class to manage widgets for the application."""
    def __init__(self, app):
        self.app = app
        self.slider_enabled = tk.BooleanVar(value=False)
        self.select_mode_enabled = tk.BooleanVar(value=False)
        self.internal_plot_enabled = tk.BooleanVar(value=False)  
        self.external_plot_enabled = tk.BooleanVar(value=False) 
        self.notebook = None
        self.reset_button = None
        self.buttons = []

    def set_button_actions(self, button_actions):
        self.button_actions = button_actions
        self.create_widgets()
        

    # Widget flow control
    def create_widgets(self):
        self.app.master.grid_columnconfigure(8, weight=1)
        self.app.master.grid_rowconfigure(7, weight=1)

        self.create_entry_group()
        self.create_properties_group()
        self.create_data_analysis_button_group()
        self.create_data_management_button_group()
        self.create_list_box_group()
        self.create_fifth_row_group()
        self.create_notebook()
        self.create_prelim_group()
        self.create_plot_title_entry_group()
        self.create_ticker_widgets()
        self.create_axis_set_widgets()

    def create_entry_group(self):
        labels_texts = [("Specimen Name:",''), ("Length:","mm"), ("Width:","mm"), ("Thickness:","mm") ,("Weight:","grams")]
        self.entry_group = EntryGroup(self.app.master, labels_texts)
        self.entry_group.grid(row=0, column=0, rowspan=5, sticky='ns')
        self.name_entry, self.length_entry,self.width_entry,self.thickness_entry, self.weight_entry = self.entry_group.entries

    def create_properties_group(self):
        self.properties_group = PropertiesGroup(self.app.master,width=400)
        self.properties_group.grid(row=0, column=1, rowspan=5, sticky='ns')
        self.specimen_properties_label =  self.properties_group.specimen_properties_label
        self.file_name_label =  self.properties_group.file_name_label

    def create_data_analysis_button_group(self):
        data_analysis_names = ["Submit", "Plot Current Specimen", "Plot Average", 
                               "Recalculate Specimen Variables", "Clear Specimen"]
        data_analysis_functions = [self.button_actions.submit, self.button_actions.plot_current_specimen, 
                                   self.button_actions.plot_average, self.button_actions.recalculate_specimen,
                                   self.button_actions.delete_selected_specimens]
        data_analysis_specs = list(zip(data_analysis_names, data_analysis_functions, 
                                       ['normal' if i == 0 else 'disabled' for i in range(len(data_analysis_names))]))

        self.data_analysis_button_group = ButtonGroup(self.app.master, data_analysis_specs)
        self.data_analysis_button_group.grid(row=0, column=2, rowspan=4, sticky='ns')
        self.data_analysis_buttons = self.data_analysis_button_group.buttons
        self.data_analysis_buttons[0].bind("<Return>", self.button_actions.submit)

    def create_data_management_button_group(self):
        data_management_names = ["Import Specimen Properties","Save Specimen", "Export Average to Excel", 
                                 "Update Plot", "Individual Excel Files"]
        data_management_functions = [self.button_actions.import_properties, self.button_actions.save_selected_specimens, self.button_actions.export_average_to_excel, 
                                     self.button_actions.update_plot, self.button_actions.export_indivdual_data]
        data_management_specs = list(zip(data_management_names, data_management_functions, 
                                         ['disabled' if i != 0 else 'normal' for i in range(len(data_management_names))]))

        self.data_management_button_group = ButtonGroup(self.app.master, data_management_specs)
        self.data_management_button_group.grid(row=0, column=3, rowspan=4, sticky='ns')
        self.data_management_buttons = self.data_management_button_group.buttons

    def create_list_box_group(self):

        self.list_box_group = ListBoxGroup(self.app.master, "Select specimens:", width=100)
        self.list_box_group.grid(row=0, column=4, rowspan=3, sticky='ns')

        self.specimen_listbox = self.list_box_group.specimen_listbox

        self.update_plot_dropdown_var = self.list_box_group.update_plot_dropdown_var
        self.PLOT_MAPPING_OPTIONS = self.list_box_group.PLOT_MAPPING
        self.specimen_dropdown = self.list_box_group.specimen_dropdown


    def create_fifth_row_group(self):
        self.fifth_row_group = FifthRowGroup(self.app.master, reset_callback=self.reset_sliders,
                                              import_callback=self.button_actions.import_data,
                                              enable_strain_callback=self.toggle_slider, 
                                              enable_select_callback=self.toggle_select_mode,
                                              ms_word_callback=self.button_actions.export_ms_data,    
                                              slider_enabled=self.slider_enabled,
                                              select_mode_enabled=self.select_mode_enabled,
                                              internal_plot_enabled=self.internal_plot_enabled, 
                                             external_plot_enabled=self.external_plot_enabled 
                                              )
        self.fifth_row_group.grid(row=5, column=0, columnspan=7, sticky='nsew')
        self.slider_checkbutton = self.fifth_row_group.toggle_button
        self.select_mode_checkbutton = self.fifth_row_group.select_mode_toggle_button
        self.offset_entry = self.fifth_row_group.offset_entry
        self.shift_entry = self.fifth_row_group.shift_entry
    
    def create_prelim_group(self):
        self.prelim_group = PrelimGroup(self.app.master,  app = self.app)
        self.prelim_group.grid(row=0, column=5, rowspan=3, sticky='ns')

    def create_plot_title_entry_group(self):
        self.plot_title_entry_group = PlotTitleEntryGroup(self.app.master)
        self.plot_title_entry_group.grid(row=0, column=6,rowspan=4, sticky='ns')

    def create_ticker_widgets(self):
        self.ticker_group = TickerConfigGroup(self.app.master)
        self.ticker_group.grid(row=5, column=5, sticky='ns', rowspan=2)

    def create_axis_set_widgets(self):
        self.axis_set_group = AxisConfigGroup(self.app.master)
        self.axis_set_group.grid(row=5, column=6, sticky='ns', rowspan=2)
        
    # Creation
    def create_notebook(self):
        self.notebook = ttk.Notebook(self.app.master)
        self.notebook.bind("<<NotebookTabChanged>>",self.update_specimen_properties_label)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.notebook.grid(row=7, column=0, columnspan=8, sticky='nsew')
        return self.notebook

    def create_new_tab(self, name):
        self.reset_toggle_button()
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text=name)
        self.notebook.select(tab)
        tab_id = self.notebook.select()
        return tab_id
   
    # State change
    def update_ui_elements(self, filename, specimen):
        specimen.display_properties_in_label(self.specimen_properties_label)
        self.file_name_label.config(text=f"File:\n{filename}")
        self.update_specimen_listbox(specimen.name)
        tk.messagebox.showinfo(
            "Data Import", f"Data has been imported successfully from {filename}!")

    def update_specimen_properties_label(self, event=None):
        selected_tab_index = self.notebook.index(self.notebook.select())
        if selected_tab_index < len(self.app.variables.specimens):
            specimen = self.app.variables.specimens[selected_tab_index]
            specimen.display_properties_in_label(
                self.specimen_properties_label)
        else:
            self.specimen_properties_label.config(text="No Specimen Selected")

    def update_specimen_listbox(self, specimen_name):
        self.specimen_listbox.insert(tk.END, specimen_name)
        # self.list_box.insert(tk.END, specimen_name)

    def enable_buttons(self):
        for button in self.data_analysis_buttons:
            button['state'] = 'normal'
        for button in self.data_management_buttons:
            button['state'] = 'normal'

    def on_tab_change(self, event):
        # updates the variables,resets the toggle button and the slider
        self.reset_toggle_button()

        current_tab_name = self.notebook.tab(self.notebook.select(), "text")
        self.app.variables.select_tab(current_tab_name)
        
        if len(self.app.variables.specimens) > 1:
                self.button_actions.plot_all_specimens()
                
       ###################### Temp fix for slider only workin on currnely plot ###########################################
        self.button_actions.plot_current_specimen()
    ####################################################################################################################
        
        # Update the slider for the current tab
        current_slider_manager = self.app.variables.current_slider_manager
        if current_slider_manager is not None:
            current_slider_manager.reset_slider()

    def toggle_select_mode(self, *args):
        if self.select_mode_enabled.get():  # if toggle button is checked
            self.app.plot_manager.enable_click_event = True
        else:
            # Disable the click event on plot
            self.app.plot_manager.enable_click_event = False
            # Reset the selected points list when exiting select mode
            self.app.plot_manager.selected_points = []

    def toggle_slider(self, *args):
        for slider_manager in [self.app.plot_manager.slider_managers['left'], self.app.plot_manager.slider_managers['middle']]:
            if slider_manager is not None:  # Right plot has no slider
                if self.slider_enabled.get():  # if toggle button is checked
                    slider_manager.slider.config(state="normal")  # enable slider
                else:
                    slider_manager.slider.config(state="disabled")  # disable slider
                    # update strain_shifted and reset manual_strain_shift
                    self.app.plot_manager.specimen.graph_manager.strain_shifted = self.app.plot_manager.specimen.shifted_strain 
                        # slider_manager.get_value()
                    self.app.plot_manager.specimen.manual_strain_shift = 0
                    slider_manager.reset_slider()

    def reset_sliders(self):
        for position in ['left', 'middle']:
            slider_manager = self.app.plot_manager.slider_managers[position]
            if slider_manager is not None:
                slider_manager.reset_slider()

    def reset_toggle_button(self):
        self.slider_enabled.set(False)
    
    def get_save_file_path(self):
        today = datetime.date.today().strftime('%Y_%m_%d')
        default_file_name = "_".join(self.app.variables.selected_specimen_names)
        return filedialog.asksaveasfilename(title="Save the average curve to an Excel file",
                                            filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*")),
                                            defaultextension=".xlsx",
                                            initialfile=f"{today}_Specimens_{default_file_name}_.xlsx")
    
    @property
    def offset_value(self):
        value = self.fifth_row_group.offset_entry.get()
        return value if value != "Set Offset (%) Default 1" else None

    @property
    def shift_value(self):
        value = self.fifth_row_group.shift_entry.get()
        return value if value != "Set Shift" else None
    
    @property
    def x_ticks(self):
        raw_value = self.ticker_group.x_tick_entry.get()
        if(self.ticker_group.x_tick_entry.placeholder == raw_value):
            return (10,2)
        else:
            try:
                major, minor = map(float, raw_value.strip("()").split(","))
                return (major, minor)
            except ValueError:
                return None

    @property
    def y_ticks(self):
        raw_value = self.ticker_group.y_tick_entry.get()
        if(self.ticker_group.y_tick_entry.placeholder == raw_value):
            return (2,0.5)
        else:
            try:
                major, minor = map(float, raw_value.strip("()").split(","))
                return (major, minor)
            except ValueError:
                return None
        
    @property
    def x_axis_limits(self):
        raw_value = self.axis_set_group.x_axis_entry.get()
        try:
            start, end = map(float, raw_value.strip("()").split(","))
            return (start, end)
        except ValueError:
            return None

    @property
    def y_axis_limits(self):
        raw_value = self.axis_set_group.y_axis_entry.get()
        try:
            start, end = map(float, raw_value.strip("()").split(","))
            return (start, end)
        except ValueError:
            return None

        
class SliderManager(tk.Frame):
    """A class to create custom widget"""
    def __init__(self, master, shared_var, app, callback=None):
        super().__init__(master)
        self.master = master
        self.slider = None
        self.shared_var = shared_var
        self.callback = callback

    def create_slider(self, frame):
        self.slider = tk.Scale(frame, from_=-0.1, to=0.1, resolution=0.0001, length=00,
                               orient=tk.HORIZONTAL,
                               variable=self.shared_var,
                               state="disabled",
                               command=self.update_linked_sliders
                               )
        self.slider.grid(row=2, column=0, padx=10, pady=2, sticky='esw')

    def update_linked_sliders(self, value):
        self.shared_var.set(value)
        if self.callback:
            self.callback(float(value))

    def get_value(self):
        return self.slider.get() if self.slider else 0

    def reset_slider(self):
        if self.slider:
            self.slider.set(0)
            self.shared_var.set(0)

class PlaceholderEntry(ttk.Entry):
    """A subclass of ttk.Entry to support placeholders."""
    def __init__(self, parent=None, placeholder="",textvar=None,**kwargs):
        super().__init__(parent,  textvariable=textvar, **kwargs)
        self.placeholder = placeholder
        self.style = ttk.Style()
        self.style.configure("Placeholder.TEntry", foreground="grey")
        
        self.configure(style="Placeholder.TEntry")
        self.insert(0, self.placeholder)
        
        self.bind('<FocusIn>', self.on_entry_click)
        self.bind('<FocusOut>', self.on_focusout)
        
    def on_entry_click(self, event):
        """Handles the event of a click on the entry."""
        if self.get() == self.placeholder:
            self.delete(0, 'end')
            self.configure(style="TEntry")
    
    def on_focusout(self, event):
        """Handles the event of losing focus on the entry."""
        if self.get() == '':
            self.insert(0, self.placeholder)
            self.configure(style="Placeholder.TEntry")

class PlaceholderEntryWithUnit(PlaceholderEntry):
    """A subclass of PlaceholderEntry to support placeholders with units."""
    def __init__(self, parent=None, placeholder="", unit='', **kwargs):
        super().__init__(parent, placeholder, **kwargs)
        self.unit = f" {unit}"
        # Update the displayed text to include the unit after the placeholder
        self.delete(0, 'end')
        self.insert(0, self.placeholder + self.unit)
    
    def on_entry_click(self, event):
        if self.get().strip() == self.placeholder:
            self.delete(0, 'end')
            self.insert(0, self.unit)
            self.icursor(0)
            self.configure(style="TEntry")
    
    def on_focusout(self, event):
        """Handles the event of losing focus on the entry."""
        if self.get() == self.unit or self.get() == '':
            self.delete(0, 'end')
            self.insert(0, self.placeholder + self.unit)
            self.configure(style="Placeholder.TEntry")

    def get(self):
        value = super().get()
        return value.replace(self.unit, '')

class EntryGroup(tk.Frame):
    def __init__(self, master=None, entries_data=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_rowconfigure(0, weight=1)  
        self.grid_columnconfigure(0, weight=1)
        self.entries_data = entries_data or []

        self.entries = []
        for i, (label, unit) in enumerate(self.entries_data):
            if unit:
                entry = PlaceholderEntryWithUnit(self, placeholder=label, unit=unit)
            else:
                entry = PlaceholderEntry(self, placeholder=label)
            self.entries.append(entry)
            entry.grid(row=i, column=0, padx=15, pady=8, sticky='e')

    def clear_entries(self):
        for entry in self.entries:
            entry.delete(0, 'end')  
            entry.on_focusout(None)

class PropertiesGroup(tk.Frame):
    def __init__(self, master=None, width=None, **kwargs):
        super().__init__(master, width=width, **kwargs)

        self.specimen_properties_label = tk.Label(self, text="Specimen Properties", justify='left', anchor='n')
        self.specimen_properties_label.grid(row=0, rowspan=3, column=0, padx=10, pady=5, sticky='n')
        self.file_name_label = tk.Label(self, text="file name", justify='left')
        self.file_name_label.grid(row=4, column=0, padx=10, pady=10, sticky='es')

class ButtonGroup(tk.Frame):
    def __init__(self, master=None, button_specs=None, **kwargs):
        super().__init__(master, **kwargs)
        self.button_specs = button_specs or []
        self.buttons  = []

        for i, (text, action, state) in enumerate(self.button_specs):
            button = tk.Button(self, text=text, command=action, state=state)
            button.grid(row=i, column=0, padx=10, pady=10, sticky='we')
            self.buttons.append(button)
        
class ListBoxGroup(tk.Frame):
    def __init__(self, master=None, label_text=None,width=None, **kwargs):
        super().__init__(master,  width=width,**kwargs)

        self._create_listbox(label_text)   
        self._create_dropdown()

    def _create_listbox(self, label_text):    
        self.specimen_listbox_label = tk.Label(self, text=label_text)
        self.specimen_listbox_label.grid(row=0, column=0, padx=10, pady=10)
        self.specimen_listbox = tk.Listbox(self, selectmode=tk.MULTIPLE)
        self.specimen_listbox.grid(row=1, column=0, rowspan=2, padx=10, pady=2, sticky='ns')

    def _create_dropdown(self):
        from .plot_manager import LEFT, MIDDLE, RIGHT
        options = ["Left current specimen", "Middle overlay of specimen", "Right avg of specimen"]    
        self.PLOT_MAPPING= {
            "Left current specimen": LEFT,
            "Middle overlay of specimen": MIDDLE,
            "Right avg of specimen": RIGHT
        }
        
        self.update_plot_dropdown_var = tk.StringVar(self)
        self.update_plot_dropdown_var .set(options[0])  # Set the default value
        self.specimen_dropdown = tk.OptionMenu(self, self.update_plot_dropdown_var ,*options)
        self.specimen_dropdown.grid(row=3, column=0, padx=10, pady=2)   

class FifthRowGroup(tk.Frame):
    def __init__(self, master=None, reset_callback=None, import_callback=None, 
                 enable_strain_callback=None, enable_select_callback=None, 
                 ms_word_callback=None, slider_enabled=None, 
                 select_mode_enabled=None, internal_plot_enabled=None, 
                 external_plot_enabled=None, **kwargs ):
        super().__init__(master, **kwargs)
        self.strain_variable = slider_enabled
        self.select_variable = select_mode_enabled
        self.internal_plot_variable = internal_plot_enabled  
        self.external_plot_variable = external_plot_enabled
        self.create_reset_button(reset_callback)
        self.create_import_button(import_callback)
        self.create_strain_checkbox(enable_strain_callback)
        self.create_select_checkbox(enable_select_callback)
        self.create_word_button( ms_word_callback)
        self.create_internal_plot_checkbox()
        self.create_external_plot_checkbox()
        self.create_offset_entry()
        self.create_shift_entry()

    def create_reset_button(self, callback):
        self.reset_button = tk.Button(self, text="Reset Strain Shift", command=callback)
        self.reset_button.grid(row=0, column=0, padx=10, pady=5, sticky='n')

    def create_import_button(self, callback):
        self.import_button = tk.Button(self, text="Import Specimen", command=callback)
        self.import_button.grid(row=0, column=1, padx=10, pady=5, sticky='n')

    def create_strain_checkbox(self, callback):
        self.toggle_button = tk.Checkbutton(self, text="Enable strain shift", variable=self.strain_variable, command=callback)
        self.toggle_button.grid(row=1, column=0, padx=10, pady=10, sticky='n')

    def create_select_checkbox(self, callback):
        self.select_mode_toggle_button = tk.Checkbutton(self, text="Enable Select Mode", variable=self.select_variable, command=callback)
        self.select_mode_toggle_button.grid(row=1, column=1, padx=10, pady=4, sticky='n')
    
    def create_word_button(self, callback):
        self.ms_button = tk.Button(self, text="MS word", command=callback)
        self.ms_button.grid(row=0, column=2, padx=10, pady=5, sticky='n')

    def create_internal_plot_checkbox(self):
        self.internal_plot_toggle_button = tk.Checkbutton(self, text="Internal Plot", variable=self.internal_plot_variable)
        self.internal_plot_toggle_button.grid(row=1, column=5, padx=10, pady=4, sticky='n')

    def create_external_plot_checkbox(self):
        self.external_plot_toggle_button = tk.Checkbutton(self, text="External Plot", variable=self.external_plot_variable)
        self.external_plot_toggle_button.grid(row=1, column=6, padx=10, pady=4, sticky='n')

    def create_offset_entry(self):
        self.offset_entry = PlaceholderEntry(self, placeholder="Set Offset (%) Default 1")
        self.offset_entry.grid(row=0, column=5, padx=10, pady=4, sticky='n')

    def create_shift_entry(self):
        self.shift_entry = PlaceholderEntry(self, placeholder="Set Shift")
        self.shift_entry.grid(row=0, column=6, padx=10, pady=4, sticky='n')


class PrelimGroup(tk.Frame):
    def __init__(self, master=None, app = None, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.prelim_mode = app.variables.prelim_mode
        self.grid_rowconfigure(0, weight=1)  
        self.grid_columnconfigure(0, weight=1)
        self.create_widgets()

    def create_widgets(self):
        self.create_prelim_toggle_button()
        self.create_plateau_stress_entry()
        self.create_range_entries()
        self.create_calculation_results_labels()
        self.create_trigger_forces_labels()

    def create_prelim_toggle_button(self):
        self.prelim_toggle_button = tk.Checkbutton(self, text="Enable Preliminary Mode", variable=self.prelim_mode)
        self.prelim_toggle_button.grid(row=0, column=0,columnspan=2, padx=10, pady=10, sticky='n')

    def create_plateau_stress_entry(self):
        self.plateau_stress_var = tk.StringVar()
        self.plateau_stress_entry = PlaceholderEntry(self, placeholder="Plateau Stress (MPa)",textvar=self.plateau_stress_var)
        self.plateau_stress_entry.grid(row=1, column=0,columnspan=2, padx=15, pady=8, sticky='we')
        self.plateau_stress_var.trace('w', lambda *args: self.update_calculation_results())
        self.plateau_stress_var.trace('w', lambda *args: self.update_trigger_forces_labels())

    def update_calculation_results(self):
        try:
            plateau_stress = float(self.plateau_stress_entry.get())
            self.calculation_results_label.config(text=f'Key Stress: 20%: {(plateau_stress * 0.2):.3f} 70%: {plateau_stress * 0.7:.3f} 130%: {plateau_stress * 1.3:.3f}')
        except ValueError:
            pass  # Handle non-numeric input here if necessary
    
    def update_trigger_forces_labels(self):
        if self.plateau_stress_var.get().isdigit() and self.app.variables.current_specimen:
            plateau_stress = float(self.plateau_stress_var.get())
            specimen = self.app.variables.current_specimen
            area = specimen.cross_sectional_area
            forces = [stress * area for stress in (0.2 * plateau_stress, 0.7 * plateau_stress, 1.3 * plateau_stress)]
            self.trigger_forces_label.config(text=f"Trigger Forces (MPa): {forces[0]:.2f}, {forces[1]:.2f}, {forces[2]:.2f}")

    def create_range_entries(self):
        self.range_start_var = tk.StringVar()
        self.range_end_var = tk.StringVar()

        self.range_entry_start = PlaceholderEntry(self, placeholder="Range Start - 0.2", textvar=self.range_start_var)
        self.range_entry_end = PlaceholderEntry(self, placeholder="Range End - 0.4", textvar=self.range_end_var)
        self.range_entry_start.grid(row=2, column=0, padx=15, pady=8, sticky='e')
        self.range_entry_end.grid(row=2, column=1, padx=15, pady=8, sticky='w')

        self.range_start_var.trace('w', lambda *args: self.calculate_and_display_average_stress())
        self.range_end_var.trace('w', lambda *args: self.calculate_and_display_average_stress())
    
    def create_calculation_results_labels(self):
        self.calculation_results_label = tk.Label(self, text="20% 70% and 1.3plt")
        self.calculation_results_label.grid(row=3, column=0,columnspan=2, padx=15, pady=8, sticky='we')

    def create_trigger_forces_labels(self):
        self.trigger_forces_label = tk.Label(self, text="Trigger Forces")
        self.trigger_forces_label.grid(row=4, column=0,columnspan=2, padx=15, pady=8, sticky='we')

    def calculate_and_display_average_stress(self):
       if not self.prelim_mode.get():
            if self.app.variables.current_specimen:
                if (self.range_start_var.get() != self.range_entry_start.placeholder) and (self.range_end_var.get() != self.range_entry_end.placeholder):
                    try:
                        range_start = float(self.range_start_var.get())
                        range_end = float(self.range_end_var.get())
                    except ValueError:
                        range_start = 0.2
                        range_end = 0.4
                        self.range_start_var.set(range_start)
                        self.range_end_var.set(range_end)
                        # tk.messagebox.showinfo("Invalid range", "Setting range to default values.")
                    plt_stress = self.calculate_average_stress(range_start, range_end)
                    if plt_stress:  # Ensure plt_stress is not None
                        self.plateau_stress_entry.delete(0, tk.END)
                        self.plateau_stress_entry.insert(0, f"Calculated Plt Stress {plt_stress:.3f}")
        
    def calculate_average_stress(self, range_start, range_end):
        if self.app.variables.current_specimen:
            stress = self.app.variables.current_specimen.stress
            strain = self.app.variables.current_specimen.strain

            idx_lower = (np.abs(strain - range_start)).argmin()
            idx_upper = (np.abs(strain - range_end)).argmin()

            return np.mean(stress[idx_lower:idx_upper])

class PlotTitleEntryGroup(tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_rowconfigure(0, weight=1)  
        self.grid_columnconfigure(0, weight=1)

        labels = ['Title for Current Specimen', 'Title for Specimens Overlayed', 'Title for Average of Specimens']
        placeholders = ['Current Specimen', 'Specimens Overlayed', 'Average of Specimens']

        iteration_length = len(labels)

        self.entries = []
        for i in range(iteration_length):
            label_widget = tk.Label(self, text=labels[i])
            label_widget.grid(row=2*i, column=0, sticky='w')
            entry = PlaceholderEntry(self, placeholder=placeholders[i])
            self.entries.append(entry)
            entry.grid(row=2*i + 1, column=0, padx=15, pady=8, sticky='e')

    def clear_entries(self):
        for entry in self.entries:
            entry.delete(0, 'end')  
            entry.on_focusout(None)


class AxisConfigGroup(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_axis_label()
        self.create_x_axis_configuration()
        self.create_y_axis_configuration()

    def create_axis_label(self):
        ttk.Label(self, text="Axes").grid(row=0, column=0, columnspan=2, sticky='w', pady=8)
    
    def create_x_axis_configuration(self):
        self.x_axis_label = ttk.Label(self, text="X-axis:")
        self.x_axis_label.grid(row=1, column=0, sticky='w')
        self.x_axis_entry = PlaceholderEntry(self, placeholder="(Start,End) e.g., (0,10)")
        self.x_axis_entry.grid(row=1, column=1, sticky='w')

    def create_y_axis_configuration(self):
        self.y_axis_label = ttk.Label(self, text="Y-axis:")
        self.y_axis_label.grid(row=2, column=0, sticky='w')
        self.y_axis_entry = PlaceholderEntry(self, placeholder="(Start,End) e.g., (0,5)")
        self.y_axis_entry.grid(row=2, column=1, sticky='w')


class TickerConfigGroup(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_ticker_label()
        self.create_x_ticker_configuration()
        self.create_y_ticker_configuration()

    def create_ticker_label(self):
        ttk.Label(self, text="Ticker (Major,Minor)").grid(row=0, column=0, columnspan=4, sticky='w', pady=8)

    def create_x_ticker_configuration(self):
        self.x_tick_label = ttk.Label(self, text="X-tick:",)
        self.x_tick_label.grid(row=1, column=0, sticky='w', pady=2)
        self.x_tick_entry = PlaceholderEntry(self, placeholder="(Major,Minor) e.g., (10,2)")
        self.x_tick_entry.grid(row=1, column=1, sticky='w')

    def create_y_ticker_configuration(self):
        self.y_tick_label = ttk.Label(self, text="Y-tick:")
        self.y_tick_label.grid(row=2, column=0, sticky='w', pady=2)
        self.y_tick_entry = PlaceholderEntry(self, placeholder="(Major,Minor) e.g., (2,0.5)")
        self.y_tick_entry.grid(row=2, column=1, sticky='w')
