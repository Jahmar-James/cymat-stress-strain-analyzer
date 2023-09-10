# app/app_layer/backends/app_backend.py

from abc import ABC, abstractmethod
from typing import Optional

from app_layer.managers.widget_manager import WidgetManager

from .ui.ui import UI


class FrontendInterface(ABC):
    """
    Shared interface for all frontends.

    This class provides a foundation for all frontend implementations. It does not 
    define any specific behaviors but serves as a marker interface for frontend classes.
    Derived classes are expected to adhere to the general structure and standards set 
    by this interface.
    """
    def __init__(self, widget_manager: Optional[WidgetManager] = None):
        self.widget_manager = widget_manager 
    
class AppBackend(FrontendInterface):
    """
    Abstract base class for application backends, adhering to the FrontendInterface.

    The AppBackend class provides the basic structure and common methods that every 
    frontend implementation (e.g., Tkinter, Streamlit) must follow. It ensures 
    consistency and provides a set of standardized methods for frontend operations. 
    Derived classes should override abstract methods to provide specific implementations 
    for their respective frontends.

    Attributes:
        <List common attributes here, if any>

    Methods:
        init_ui: Abstract method to initialize the user interface.
        <List other methods, abstract or otherwise, here>
    """
    def __init__(self, widget_manager : "WidgetManager", UI: 'UI' ):           
        # Initialize managers and state
        self.widget_manager = widget_manager 
        self.UI = UI

    @abstractmethod
    def init_ui(self):
        pass
    
    @abstractmethod
    def update_labels(self):
        pass
    