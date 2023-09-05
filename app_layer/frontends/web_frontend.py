# app/app_layer/frontends/streamlit_frontend.py

from .app_backend import AppBackend

class StreamlitAppBackend(AppBackend):
    """
    The backend specifically tailored for Streamlit.
    """
    def init_ui(self):
        self.widget_manager.create_streamlit_widgets()
