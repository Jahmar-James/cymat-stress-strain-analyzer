# app/app_layer/managers/tk_widget_manager.py

from .widget_manager import WidgetManager

class TkWidgetManager(WidgetManager):
    """
    Responsible for creating individual widgets and managing their specific states.
    It fine-tunes individual widget behaviors and properties, focusing on detailed 
    and granular control of widget elements within the Tkinter framework.
    
    It houses a collection of custom widgets and orchestrates their states and behaviors.
    
    Solely responsible for updating the widgets using the data it receives. 
    It remains unaware of the AppState, receiving all necessary information from TkinterUI
    """
    def create_widgets(self):
        """
        main function to create widgets.
        First method called by the UI.     
        """
       
        # create widgets etc ...
              
        self.app_state.register_observer(self)
        
    def update(self):
        """Updates individual widget states based on changes in the app state and command from 'TkAppBackend' """
        pass
    
    def update_labels_by_index(self, entity_type, data):
        """Updates the labels of the widgets based on the data passed."""
        # Implement the logic to update the labels of the widgets based on the data passed
        pass
 
    

# Archive class from before the refactoring
# A large part remians the same

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
        self.specimen_listbox_label = tk.Label(self, text=label_text)
        self.specimen_listbox_label.grid(row=0, column=0, padx=10, pady=10)
        self.specimen_listbox = tk.Listbox(self, selectmode=tk.MULTIPLE)
        self.specimen_listbox.grid(row=1, column=0, rowspan=2, padx=10, pady=2, sticky='ns')

class FifthRowGroup(tk.Frame):
    def __init__(self, master=None, reset_callback=None, import_callback=None, enable_strain_callback=None, enable_select_callback=None, ms_word_callback =None, slider_enabled = None, select_mode_enabled = None, **kwargs ):
        super().__init__(master, **kwargs)
        self.strain_variable = slider_enabled
        self.select_variable = select_mode_enabled
        self.create_reset_button(reset_callback)
        self.create_import_button(import_callback)
        self.create_strain_checkbox(enable_strain_callback)
        self.create_select_checkbox(enable_select_callback)
        self.create_word_button( ms_word_callback)

    def create_reset_button(self, callback):
        self.reset_button = tk.Button(self, text="Reset Strain Shift", command=callback)
        self.reset_button.grid(row=0, column=1, padx=10, pady=5, sticky='n')

    def create_import_button(self, callback):
        self.import_button = tk.Button(self, text="Import Specimen", command=callback)
        self.import_button.grid(row=0, column=3, padx=10, pady=5, sticky='n')

    def create_strain_checkbox(self, callback):
        self.toggle_button = tk.Checkbutton(self, text="Enable strain shift", variable=self.strain_variable, command=callback)
        self.toggle_button.grid(row=0, column=0, padx=10, pady=10, sticky='n')

    def create_select_checkbox(self, callback):
        self.select_mode_toggle_button = tk.Checkbutton(self, text="Enable Select Mode", variable=self.select_variable, command=callback)
        self.select_mode_toggle_button.grid(row=0, column=2, padx=10, pady=4, sticky='n')
    
    def create_word_button(self, callback):
        self.ms_button = tk.Button(self, text="MS word", command=callback)
        self.ms_button.grid(row=0, column=4, padx=10, pady=5, sticky='n')


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



"""
App contorller - Observer 

App state - Subject 

 Contain app states, provide validation. 
    The Subjet of Observer pattern. 

Controller
    Orchestrates the flow of the application by coordinating between the frontend and the backend.
    This class takes user input, processes the data via the backend and updates the UI.
    - app_backend
    - action_handler
    - app_state
    
    Role: 
    1. fetch data from app state and update the UI
    2. send data to app backend update functions 
    
TkAppBackend
    This class serves as the bridge between the frontend (UI) and the backend, 
    handling the integration between the user interface and the app's internal logic. 
    
    - widget_manager
    - ui
    
    Role:
    1. will do light processing of data and send it to the UI if necessary
    
TkinterUI
This class is responsible for initializing the broader layout of the user interface 
    and managing universal UI events. It acts as a manager for global UI configurations 
    and event handling, facilitating the layout organization and global event management 
    through the Tkinter framework
    - widget_manager
    
    Role:
    1. will update the widgets based on the data received from the app backend
    2. provide a abstraction layer for user overide 
    

"""