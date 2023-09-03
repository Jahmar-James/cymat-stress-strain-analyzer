# app/data_layer/I0/excel/base_objects.py

import tqdm
from contextlib import contextmanager
from abc import ABC, abstractmethod
from typing import List
from openpyxl import Workbook

from .excel_objects import ExcelSheet

class Events:
    def __init__(self):
        self.handlers = {}
    
    def on(self, event_name, handler):
        if event_name not in self.handlers:
            self.handlers[event_name] = []
        self.handlers[event_name].append(handler)
    
    def emit(self, event_name, *args, **kwargs):
        if event_name in self.handlers:
            for handler in self.handlers[event_name]:
                handler(*args, **kwargs)

class SpreadsheetExporter(ABC):
    def __init__(self, workbook = None):
        self.workbook = workbook or Workbook()
        self.sheets = []
        self.file_name = None
        self.events = Events()
        self.progress_bar = None
    
    def create_progress_bar(self, total):
        self.progress_bar = tqdm.tqdm(total=total, desc="Exporting Worksheets", position=0, leave=True)

    def update_progress_bar(self, value):
        if self.progress_bar:
            self.progress_bar.update(value)

    @contextmanager
    def exporting_process(self, sheets: List['ExcelSheet'], file_name: str):
        self.create_progress_bar(len(sheets))
        try:
            yield  # Control is transferred to the caller's block
            self.export_to_spreadsheet(sheets, file_name)
        finally:
            if self.progress_bar:
                self.progress_bar.close()

    @abstractmethod       
    def export_to_spreadsheet(self, sheets: List['ExcelSheet'], file_name: str) -> None:
        pass

class IFormatter(ABC):
    @abstractmethod
    def apply_table_formatting(self, sheet):
        pass
    
    @abstractmethod
    def set_font_styles(self, sheet, font_options):
        pass
    
    @abstractmethod
    def set_color_schemes(self, sheet, color_options):
        pass