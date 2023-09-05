import argparse

# Import your classes and services
from app_layer.app_controller import AppContorller
from app_layer.action_handler import ActionHandler
from app_layer.managers.tk_widget_manager import TkWidgetManager
from app_layer.managers.streamlit_widget_manager import StreamlitWidgetManager
from app_layer.app_state import AppState
from app_layer.frontends import AppBackend, TkAppBackend, StreamlitAppBackend


from service_layer.your_service_layer import YourServiceLayer  # Replace with your actual service layer

def main():
    parser = argparse.ArgumentParser(description="Launch the app with a specific frontend.")
    parser.add_argument("--frontend", type=str, choices=["tkinter", "streamlit"], default="tkinter",
                        help="Choose the frontend to use for the app.")
    args = parser.parse_args()

    # Initialize service layer and handlers
    service_layer = YourServiceLayer()  # Replace with your actual service layer
    action_handler = ActionHandler(service_layer)

    # Initialize app state
    app_state = AppState()

    # Create the appropriate widget manager based on the frontend choice
    if args.frontend == "tkinter":
        widget_manager = TkWidgetManager()
        app_backend = TkAppBackend(widget_manager, ..., app_state)  # Fill in the ...
        app_controller = AppController(app_backend)
        app_controller.run()  # or however you start your Tkinter loop
    elif args.frontend == "streamlit":
        widget_manager = StreamlitWidgetManager()
        app_backend = StreamlitAppBackend(widget_manager, ..., app_state)  # Fill in the ...
        app_controller = AppController(app_backend)
        app_controller.run_streamlit()  # or however you start your Streamlit app
    else:
        raise ValueError(f"Unsupported frontend: {args.frontend}")

if __name__ == "__main__":
    main()
