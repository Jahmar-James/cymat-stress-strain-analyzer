import argparse

# Import your classes and services
from app_layer.app_controller import AppController
from app_layer.action_handler import ActionHandler
from app_layer.managers.tk_widget_manager import TkWidgetManager
from app_layer.managers.streamlit_widget_manager import StreamlitWidgetManager
from app_layer.app_state import AppState
from app_layer.frontends import  UI
from app_layer.frontends.app_backend_factory import AppBackendFactory


from service_layer.services import Service_layer 

def main():
    parser = argparse.ArgumentParser(description="Launch the app with a specific frontend.")
    parser.add_argument("--frontend", type=str, choices=["tkinter", "streamlit"], default="tkinter",
                        help="Choose the frontend to use for the app.")
    args = parser.parse_args()

    # Initialize service layer and handlers
    service_layer = Service_layer()  
    action_handler = ActionHandler(service_layer)

    # Initialize app state
    app_state = AppState()
    ui = UI()
    
    app_backend = AppBackendFactory.create_backend(args.frontend, ui)
    app_controller = AppController(app_backend, action_handler, app_state)
    app_controller.run()

if __name__ == "__main__":
    main()
