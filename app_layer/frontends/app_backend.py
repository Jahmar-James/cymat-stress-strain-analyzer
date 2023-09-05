# app/app_layer/backends/app_backend.py

class FrontendInterface:
    """Shared interface for all frontends."""
    def load_samples_from_database(self, sample_id: list[int]):
        # Load sample from database
        # ...
        self.app_state.add_specimen(sample)

    def load_samples_from_files(self, file_paths: list[str]):
        # Load sample from files
        # ...
        self.app_state.add_specimen(sample)

class AppBackend(FrontendInterface):
    """
    The main backend class responsible for coordinating the different managers and app state.
    """
    def __init__(self, 
                 widget_manager: Optional[WidgetManager] = None,
                 data_io_manager: Optional[DataIOManager] = None,
                 graphics_manager: Optional[GraphicsManager] = None,
                 app_state: Optional[AppState] = None):
        
        # Initialize managers and state
        self.widget_manager = widget_manager or WidgetManager()
        self.data_io_manager = data_io_manager or DataIOManager()
        self.graphics_manager = graphics_manager or GraphicsManager()
        self.app_state = app_state or AppState()

    @abstractmethod
    def init_ui(self):
        pass