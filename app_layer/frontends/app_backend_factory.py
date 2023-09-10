# app_layer/frontends/app_backend_factory.py

from typing import Optional

from app_layer.managers.widget_manager import WidgetManager
from ui.ui import UI


from app_layer.managers.streamlit_widget_manager import StreamlitWidgetManager
from app_layer.managers.tk_widget_manager import TkWidgetManager

from .tk_frontend import TkAppBackend
from .web_frontend import StreamlitAppBackend
from .ui.tkinter_ui import TkinterUI
from .ui.streamlit_ui import StreamlitUI


class AppBackendFactory:
    @staticmethod
    def create_backend(frontend_type, widget_manager: Optional['WidgetManager'] = None , ui: Optional['UI'] = None):
        if frontend_type == "tkinter":
            return TkAppBackend( widget_manager or TkWidgetManager(), ui or TkinterUI())
        elif frontend_type == "streamlit":
            return StreamlitAppBackend(widget_manager or StreamlitWidgetManager(), ui or StreamlitUI())
        else:
            raise ValueError(f"Unsupported frontend: {frontend_type}")
