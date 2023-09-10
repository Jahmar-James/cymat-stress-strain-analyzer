# app/app_layer/frontends/tk_frontend.py

from typing import Optional, TYPE_CHECKING

from .app_backend import AppBackend

if TYPE_CHECKING:
    from app_layer.managers.tk_widget_manager import TkWidgetManager
    from app_layer.frontends.ui.tkinter_ui import TkinterUI

class TkAppBackend(AppBackend):
    """
    Serves as a bridge between the frontend (UI) and the backend, facilitating 
    the integration between the user interface and the internal logic of the app.
    It processes updates from the app controller and updates the UI accordingly.
    
    Attributes:
        widget_manager (TkWidgetManager): Manages individual widget states.
        ui (TkinterUI): Manages the broader layout and global UI configurations.
    """
    def __init__(self, widget_manager : 'TkWidgetManager' , ui : 'TkinterUI' ):
        super().__init__(widget_manager, ui)
        self.tk_ui = ui
        self.tk_widget_manager = widget_manager
        
    def init_ui(self):
        """
        Method to initialize the UI, set up all necessary widgets and start the app's main loop.
        """
        # Setting up the UI through widget manager and other necessary initializations.
        self.run()

    def run(self):
            # Start the Tkinter main loop
            self.tk_ui.run()
            
    def update_labels(self, entity_type, data):
        """
        Updates the labels of all widgets.
        """
        if entity_type == "specimen":
            self.tk_ui.update_specimen_labels(data)
        elif entity_type == "sample_group":
            self.tk_ui.update_sample_group_labels(data)
        else:
            raise ValueError(f"Entity type ({entity_type}) iss an invalid entity type.")
         
    def _update(self, data):
        """
        Receives update triggers from the app controller with the necessary data, 
        processes it lightly, if necessary, before delegating to the UI to update 
        the widgets.
        """

    def on_tab_change(self, event):
        ...
        # Your logic for the on_tab_change event

    def toggle_select_mode(self, *args):
        ...
        # Your logic for toggling the select mode
        


        