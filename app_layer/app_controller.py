# app_layer/controllers/app_controller.py

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .action_handler import ActionHandler
    from app_layer.frontends.app_backend import AppBackend 

class AppContorller:
    """
    Orchestrates the flow of the application by coordinating between the frontend and the backend.
    This class takes user input, processes the data via the backend and updates the UI.
    """
    def __init__(self, app_backend: AppBackend, action_handler: ActionHandler):
        self.app_backend = app_backend
        self.action_handler = action_handler

        # initialize other services and state here

    def initialize_app(self):
        """
        Initialize the app. This could involve setting up the UI, loading initial data, etc.
        """
        self.app_backend.init_ui()

    def run(self):
        """
        Main loop for running the application. 
        In a GUI this might be your main event loop.
        """
        pass

    def load_specimen(self, specimen_id: int):
        """
        Load a specimen given its ID and update the frontend.
         High-level method to load a specimen.
        """
        self.app_backend.load_specimen(specimen_id)