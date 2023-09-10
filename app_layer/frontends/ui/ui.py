# app/app_layer/frontends/ui/ui.py

from abc import ABC, abstractmethod

class UI(ABC):
    """
    Represents the User Interface of the application.   
    """
    def __init__(self):
        pass

    @abstractmethod
    def init_ui(self):
        pass
        
    @abstractmethod
    def run(self):
        pass