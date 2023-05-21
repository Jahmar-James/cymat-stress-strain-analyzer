import tkinter as tk
from tkinter import ttk


# widget_manager.py
class WidgetManager:
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

    def create_label_entry(self, parent, row, label_text):
        label = ttk.Label(parent, text=label_text)
        label.grid(row=row, column=0, padx=15, pady=10, sticky='w')

        entry = ttk.Entry(parent)
        entry.grid(row=row, column=1, padx=15, pady=10, sticky='e')

        return label, entry

    def create_buttons(self):
        button_names = ["Submit", "Plot Current Specimen",
                        "Plot Average", "Save Specimen", "Export Average to Excel"]
        button_functions = [self.button_actions.submit, self.button_actions.plot_current_specimen, self.button_actions.plot_average,
                            self.button_actions.save_selected_specimens, self.button_actions.export_average_to_excel]

        for i in range(len(button_names)):
            button = tk.Button(
                self.app.master, text=button_names[i], command=button_functions[i], state='disabled' if i != 0 else 'normal')
            self.buttons.append(button)

        self.reset_button = tk.Button(
            self.app.master, text="Reset Strain Shift", command=self.reset_sliders)
        self.reset_button.grid(row=5, column=2, padx=10, pady=2, sticky='e')
        # self.buttons.append(self.reset_button)

        self.import_button = tk.Button(
            self.app.master, text="Import Specimen", command=self.button_actions.import_data)
        self.import_button.grid(row=5, column=3, padx=10, pady=2, sticky='e')

        # self.buttons.append(self.import_button)
    
    def enable_buttons(self):
        for button in self.buttons:
            button['state'] = 'normal'

    def update_ui_elements(self,filename, specimen):
            specimen.display_properties_in_label(self.specimen_properties_label)
            self.file_name_label.config(text=filename)
            self.update_specimen_listbox(specimen.name)
            tk.messagebox.showinfo("Data Import", f"Data has been imported successfully from {filename}!")

    def create_specimen_listbox(self):
        self.specimen_listbox_label = tk.Label(
            self.app.master, text="Select specimens for averaging:")
        self.specimen_listbox_label.grid(
            row=0, column=4, padx=10, pady=10, sticky='w')

        self.specimen_listbox = tk.Listbox(
            self.app.master, selectmode=tk.MULTIPLE)
        self.specimen_listbox.grid(
            row=1, column=4, rowspan=4, padx=10, pady=10, sticky='we')

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

    def create_widgets(self):
        # Create the input fields
        self.name_label, self.name_entry = self.create_label_entry(
            self.app.master, 0, "Specimen Name:")
        self.length_label, self.length_entry = self.create_label_entry(
            self.app.master, 1, "Length:")
        self.width_label, self.width_entry = self.create_label_entry(
            self.app.master, 2, "Width:")
        self.thickness_label, self.thickness_entry = self.create_label_entry(
            self.app.master, 3, "Thickness:")
        self.weight_label, self.weight_entry = self.create_label_entry(
            self.app.master, 4, "Weight:")

        self.create_buttons()
        for i, button in enumerate(self.buttons):
            button.grid(row=i, column=3, padx=10, pady=2, sticky='e')
        self.create_toggle_button()

        self.specimen_properties_label = tk.Label(
            self.app.master, text="Specimen Properties", justify='left', anchor='n')
        self.specimen_properties_label.grid(
            row=0, rowspan=5, column=2, padx=10, pady=10, sticky='n')

        self.create_notebook()
        self.app.master.grid_columnconfigure(4, weight=1)
        self.app.master.grid_rowconfigure(5, weight=1)

        self.file_name_label = tk.Label(self.app.master, text="file name")
        self.file_name_label.grid(
            row=0, column=3, padx=10, pady=10, sticky='w')

        self.create_specimen_listbox()
        self.create_select_mode_toggle_button()

    def create_notebook(self):
        self.notebook = ttk.Notebook(self.app.master)
        self.notebook.bind("<<NotebookTabChanged>>",
                           self.update_specimen_properties_label)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.notebook.grid(row=7, column=0, columnspan=6, sticky='sw')
        return self.notebook

    def create_new_tab(self, name):
        self.reset_toggle_button()
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text=name)
        self.notebook.select(tab)
        tab_id = self.notebook.select()
        return tab_id

    def on_tab_change(self, event):
        self.reset_toggle_button()

        current_tab_name = self.notebook.tab(self.notebook.select(), "text")

        # Select the new tab in the app variables
        self.app.variables.select_tab(current_tab_name)

        # Update the slider for the current tab
        current_slider_manager = self.app.variables.current_slider_manager
        if current_slider_manager is not None:
            current_slider_manager.reset_slider()

    def create_toggle_button(self):
        self.slider_enabled.trace('w', self.toggle_slider)
        self.toggle_button = tk.Checkbutton(self.app.master, text="Enable strain shift",
                                            variable=self.slider_enabled)
        self.toggle_button.grid(row=5, column=0, padx=10, pady=2, sticky='e')

    def toggle_slider(self, *args):
        for slider_manager in [self.app.plot_manager.slider_managers['left'], self.app.plot_manager.slider_managers['middle']]:
            if slider_manager is not None:  # Right plot has no slider
                if self.slider_enabled.get():  # if toggle button is checked
                    slider_manager.slider.config(
                        state="normal")  # enable slider
                else:
                    slider_manager.slider.config(
                        state="disabled")  # disable slider
                    # update strain_shifted and reset manual_strain_shift
                    self.app.plot_manager.specimen.graph_manager.strain_shifted = self.app.plot_manager.specimen.shifted_strain + \
                        slider_manager.get_value()
                    self.app.plot_manager.specimen.manual_strain_shift = 0
                    slider_manager.reset_slider()

    def reset_sliders(self):
        for position in ['left', 'middle']:
            slider_manager = self.app.plot_manager.slider_managers[position]
            if slider_manager is not None:
                slider_manager.reset_slider()

    def reset_toggle_button(self):
        self.slider_enabled.set(False)

    def create_select_mode_toggle_button(self):
        self.select_mode_enabled.trace('w', self.toggle_select_mode)
        self.select_mode_toggle_button = tk.Checkbutton(self.app.master, text="Enable Select Mode",
                                                        variable=self.select_mode_enabled)
        self.select_mode_toggle_button.grid(
            row=5, column=1, padx=10, pady=2, sticky='e')

    def toggle_select_mode(self, *args):
        if self.select_mode_enabled.get():  # if toggle button is checked
            self.app.plot_manager.enable_click_event = True
        else:
            # Disable the click event on plot
            self.app.plot_manager.enable_click_event = False
            # Reset the selected points list when exiting select mode
            self.app.plot_manager.selected_points = []


class SliderManager(WidgetManager):
    def __init__(self, master, shared_var, app, callback=None):
        super().__init__(app)
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
