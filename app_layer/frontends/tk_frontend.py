# app/app_layer/frontends/tk_frontend.py

from .app_backend import AppBackend

class TkAppBackend(AppBackend):
    """
    The backend specifically tailored for Tkinter.
    """
    def init_ui(self):
        self.widget_manager.create_tkinter_widgets()