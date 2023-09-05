# app/service_layer/services.py

from typing import List, Optional, TYPE_CHECKING

from .excel_exporting import ExcelExporter
from .graphics_manager import GraphicsManager
from .data_io_manager import DataIOManager

class Service_layer():
    def __init__(self, data_io_manager: DataIOManager, graphics_manager: GraphicsManager, excel_exporter: ExcelExporter):
        self.data_io_manager = data_io_manager
        self.graphics_manager = graphics_manager
        self.excel_exporter = excel_exporter
        
        