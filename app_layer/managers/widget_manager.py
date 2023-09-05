# app/app_layer/managers/widget_manager.py

from abc import ABC, abstractmethod

class WidgetManager(ABC):
    """
    Ordering of tkinter widgets 
    """
    @abstractmethod
    def create_widgets(self):
        """main function to create widgets"""
        pass