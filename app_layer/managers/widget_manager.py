# app/app_layer/managers/widget_manager.py

from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app_layer.app_state import AppState

class WidgetManager(ABC):
    """
    Ordering of tkinter widgets 
    """
    @abstractmethod
    def create_widgets(self):
        """main function to create widgets"""
        pass
    