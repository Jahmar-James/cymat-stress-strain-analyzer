import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import datetime

# To Do
# toolbox or round toggle for checkbuttons
# float button for export data to excel

# widget_manager.py
class WidgetManager:
    """A class to manage widgets for the application."""
    def __init__(self, app):
        self.app = app
        self.slider_enabled = tk.BooleanVar(value=False)
        self.select_mode_enabled = tk.BooleanVar(value=False)
        self.notebook = None
        self.reset_button = None
        self.buttons = []

    def set_button_actions(self, button_actions):
        self.button_actions = button_actions
        self.create_widgets()
        

    # Widget flow control
    def create_widgets(self):
        self.app.master.grid_columnconfigure(4, weight=1)
        self.app.master.grid_rowconfigure(6, weight=1)

        labels_texts = ["Specimen Name:", "Length:", "Width:", "Thickness:", "Weight:"]
        self.entry_group = EntryGroup(self.app.master, labels_texts)
        self.entry_group.grid(row=0, column=0, rowspan=5, sticky='ns')
        self.name_entry, self.length_entry,self.width_entry,self.thickness_entry, self.weight_entry = self.entry_group.entries

        self.properties_group = PropertiesGroup(self.app.master,width=400)
        self.properties_group.grid(row=0, column=1, rowspan=5, sticky='ns')
        self.specimen_properties_label =  self.properties_group.specimen_properties_label
        self.file_name_label =  self.properties_group.file_name_label

        button_names = ["Submit", "Plot Current Specimen",
                        "Plot Average", "Save Specimen", "Export Average to Excel"]
        button_functions = [self.button_actions.submit, self.button_actions.plot_current_specimen, self.button_actions.plot_average,
                            self.button_actions.save_selected_specimens, self.button_actions.export_average_to_excel]
        button_specs = list(zip(button_names, button_functions, ['disabled' if i != 0 else 'normal' for i in range(len(button_names))]))
        
        self.button_group = ButtonGroup(self.app.master, button_specs)
        self.button_group.grid(row=0, column=2, rowspan=5, sticky='ns')
        self.buttons = self.button_group.buttons
        self.buttons[0].bind("<Return>", self.button_actions.submit)

        self.list_box_group = ListBoxGroup(self.app.master, "Select specimens:", width=100)
        self.list_box_group.grid(row=0, column=3, rowspan=2, sticky='ns')
        self.specimen_listbox = self.list_box_group.specimen_listbox
      
        # Fifith Row 
        
        self.fifth_row_group = FifthRowGroup(self.app.master, reset_callback=self.reset_sliders,
                                              import_callback=self.button_actions.import_data,
                                              enable_strain_callback=self.toggle_slider, 
                                              enable_select_callback=self.toggle_select_mode,
                                              slider_enabled=self.slider_enabled,
                                              select_mode_enabled=self.select_mode_enabled)
        self.fifth_row_group.grid(row=5, column=0, columnspan=4, sticky='nsew')


        self.create_notebook()
        
    # Creation
    def create_notebook(self):
        self.notebook = ttk.Notebook(self.app.master)
        self.notebook.bind("<<NotebookTabChanged>>",
                           self.update_specimen_properties_label)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.notebook.grid(row=7, column=0, columnspan=6, sticky='nsew')
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

    def enable_buttons(self):
        for button in self.buttons:
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
    def __init__(self, parent=None, placeholder="", **kwargs):
        super().__init__(parent, **kwargs)
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

class EntryGroup(tk.Frame):
    def __init__(self, master=None, labels=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_rowconfigure(0, weight=1)  
        self.grid_columnconfigure(0, weight=1)
        self.labels = labels or []
        self.entries = [PlaceholderEntry(self, label) for label in self.labels]
        
        for i, entry in enumerate(self.entries):
            entry.grid(row=i, column=0, padx=15, pady=8, sticky='e')

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
    def __init__(self, master=None, reset_callback=None, import_callback=None, enable_strain_callback=None, enable_select_callback=None, slider_enabled = None, select_mode_enabled = None, **kwargs ):
        super().__init__(master, **kwargs)
        self.strain_variable = slider_enabled
        self.select_variable = select_mode_enabled
        self.create_reset_button(reset_callback)
        self.create_import_button(import_callback)
        self.create_strain_checkbox(enable_strain_callback)
        self.create_select_checkbox(enable_select_callback)

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

