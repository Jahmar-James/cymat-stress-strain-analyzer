# app_layer/controllers/app_controller.py

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .action_handler import ActionHandler
    from app_layer.frontends.app_backend import AppBackend 
    from app_layer.app_state import AppState
    from data_layer.models.analyzable_entity import AnalyzableEntity
    from data_layer.models import Specimen, SampleGroup
    
    
"""
Data flow:
    Upwards (callbacks): UI event → TkAppBackend → AppController → (potentially) ActionHandler → Update AppState
    Downwards (observer pattern): AppState (observes change) → Notify AppController → TkAppBackend → Update TkinterUI
"""

class AppController:
    """
    Orchestrates the flow of the application by coordinating between the frontend and the backend.
    This class observes the AppState and updates the UI accordingly. Moreover, it processes 
    user inputs via the app backend and action handler.
    
    Attributes:
        app_backend (AppBackend): The backend interface for the UI presentation.
        action_handler (ActionHandler): The handler for managing user-triggered actions.
        app_state (AppState): The current state of the application observed for changes..
    """
    def __init__(self, app_backend: AppBackend, action_handler: ActionHandler, app_state: AppState):
        self.app_backend = app_backend
        self.action_handler = action_handler
        self.app_state = app_state
        
        
        self.OBSERVED_ATTRIBUTES = {
            'current_specimen_index',
            'current_sample_group_index',
            # add other attributes as required
        }
        
    def initialize_app(self):
        """
        Initialize the app. This includes setting up the UI, loading initial data,
        and registering this class as an observer to the AppState to receive updates..
        """
        self.app_state.register_observer(self)
        self.app_backend.init_ui()
                
    def set_current_specimen(self, specimen: Optional['Specimen'] = None, index_of_specimen: Optional[int] = None):
        self.app_state.set_current_specimen(specimen, index_of_specimen)
    
    def set_current_sample_group(self, sample_group: Optional['SampleGroup'] = None, index_of_sample_group: Optional[int] = None):
        self.app_state.set_current_sample_group(sample_group, index_of_sample_group)
        
    def update(self):
        """
        Called when there's an update in the AppState. It fetches the necessary data 
        from the AppState and delegates the update to the appropriate method in the 
        app backend to further process the update and reflect it on the UI.
        """
        # Logic to fetch necessary data from AppState
        # Delegate to app backend to process and update UI
        # mapping to which self method to call based on the change in app state
            # ie. if there was a new specimen added, check current_specimen_index and 
            # call update_labels_by_index("specimen", current_specimen_index) if needed
            # limit to only the relevant changes
            
        changed_attributes = self.app_state.get_and_reset_changed_attributes()
        
        # Skip if not in White list of attributes to observe
        for attribute in changed_attributes: 
            if attribute not in self.OBSERVED_ATTRIBUTES:
                continue
            
            if attribute == 'current_specimen_index':
                self.update_labels_by_index("specimen", self.app_state.current_specimen_index)
            elif attribute == 'current_sample_group_index':
                self.update_labels_by_index("sample_group", self.app_state.current_sample_group_index)
            else:
                raise ValueError(f"Attribute ({attribute}) is not a valid attribute to observe. Check the OBSERVED_ATTRIBUTES list in 'AppController' and spelling")
        
    def update_labels_by_index(self, entity_type, index):
        """
        Calls the appropriate method in WidgetManager to update the labels based on index.
        
        Args:
            entity_type (str): The type of entity ('specimen' or 'sample_group') to update.
            index (int): The index of the entity to update.
        """
        # To update the labels get the whole entity for readability 
        data = self.get_data_from_app_state(entity_type, index)
        self.app_backend.update_labels(entity_type, data)
        
    def get_data_from_app_state(self, entity_type, index , attributes : Optional[list] = None) -> Optional[dict]:
        """Fetch the necessary data from app state."""
        # if attributes is provided get only those attributes of the entity
        # else return the whole entity
        if attributes:
            return self.app_state.get_data(entity_type, index, attributes, default = None)
        else:
            return self.app_state.get_data(entity_type, index, default = None)
        

        
    def _check_index(self):
        """Private method to check and update widget(s) based on the index value in the app state."""
        # Retrieve the current index values from the app state
        current_specimen_index = self.app_state.current_specimen_index
        current_sample_group_index = self.app_state.current_sample_group_index 
        
        # Check if the index values have changed and if yes, update the UI accordingly
        if current_specimen_index is not None:
            self.update_labels_by_index("specimen", current_specimen_index)
        if current_sample_group_index is not None:
            self.update_labels_by_index("sample_group", current_sample_group_index)
            
        return current_specimen_index, current_sample_group_index


    def handle_button_click(self, data_from_ui): 
        # Update app state based on data_from_ui
        self.app_state.some_attribute = data_from_ui["some_attribute"]
        
        # Maybe trigger some action
        self.action_handler.some_action(data_from_ui)
        raise NotImplementedError("This method is not implemented yet.")