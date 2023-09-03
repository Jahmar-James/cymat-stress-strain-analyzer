# app/service_layer/excel_exporting.py

from typing import List

from ..data_layer.IO.excel.base_objects import ExcelSheet
from ..data_layer.IO.excel.excel_exporter import ExcelExporter, ExcelFormatter


class ExcelExportService:
    """Handles Excel sheet formatting and exporting"""
    def __init__(self, formatter: ExcelFormatter = None, excel_exporter: ExcelExporter = None):
        self.formatter = formatter or ExcelFormatter()
        self.exporter = excel_exporter or ExcelExporter()

    def format_sheet(self, excel_sheet: ExcelSheet, font_options=None, color_options=None):
        self.formatter.apply_table_formatting(excel_sheet)
        if font_options:
            self.formatter.set_font_styles(excel_sheet, font_options)
        if color_options:
            self.formatter.set_color_schemes(excel_sheet, color_options)

    def export_multiple_to_excel(self, excel_sheets: List[ExcelSheet], file_name: str):
        with self.exporter.exporting_process(excel_sheets, file_name):
            pass