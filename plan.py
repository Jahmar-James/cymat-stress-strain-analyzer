"""
project_root - Mechancial Properties calculater
    app
        controller - Init logic & frontend composer

        frontends
            frontend_manger.py - abstraction + Bridge event hanlder to backend
            CLI
            Tkinter
            PySide6

        backend
            data_extraction - preprocessoers and intructions to import in MT data in various formats
            standard_base
                default sample
                io_management
                properties calculator
                validation
                benckmark
            standards - specific sample based on quality system or desire mechanical propreties
            visulization
                plot_manager
                matpoltlib_widgets
            ms_file_handling
                templates

        Utilites - pure funcutions and unitilty cases to follow a convention

    assets
        theme
        style
        icons

    config

    output - defualt output if not provided

    test
    build
    documenations
        UX  - Plan and thinking
        Alogritms  - Explaintions of the key alg
        calcualtions_studies ( jupter notebooks testing calcultion accuraacy and uncertainty )
        General help and app docs

README.ME
main.py
"""


from abc import abstractmethod, ABC
from enum import Enum
from logging import Logger

class FrontendOptions(Enum):
    CLI =  0<<1
    Tkinter = 0<<2
    PyQt = 0<<3

class FrontendInterface(ABC):
    def __init__(self) -> None:
        super().__init__()
        self.frontend_manager = None
        self.user_options = None
        self.config_path = ""

    @abstractmethod
    def run(self):
        raise NotImplementedError("Must be implemented bu subclass")
    
class Controller:
    def __init__(self, fontend_mode: FrontendOptions ) -> None:
        """Main controller till control flow is apssed to the frontend"""
        # Backenfd conponets
        self.plot_manger = None
        self.frontend : FrontendInterface = self.compose_frontend(fontend_mode)
        self.event_handler = None

    def start(self): 
        if hasattr(self.frontend, "run"):
            self.frontend.run()
        else:
            Logger.warning(f"Frontend ''{self.frontend} has not impplements make sure using FrontendInterface")
        

    def compose_frontend(self, fontend_mode) -> FrontendInterface
        """Compostion of the fronend""" 
        return

    
if __name__ == "__main__":

    def init_app() -> None:
        choice  = input( "Enter the frontend for anaylsis: ")
        while True:
            choice = choice.lower()
            if choice in ['exit', 'quit', 'cancel', 'q']:
                break
            elif choice in ['qt', 'pyside6']:
                mode = FrontendOptions.PyQt
            elif choice in ['tk', 'tkinter']:
                mode = FrontendOptions.Tkinter
            elif choice in ['cli', 'command']:
                mode = FrontendOptions.CLI
            else:
                continue

            controller = Controller(mode)
            controller.start()

    init_app()

