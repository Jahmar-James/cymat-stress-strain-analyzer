# app/data_layer/IO/excel/custom_excel_export.py

from .excel_exporter import ExcelExporter
from ...models.sample_group import SampleGroup

class SampleGroupExcelExporter(ExcelExporter):
    """Exports a SampleGroup to an Excel file"""
    def __init__(self, sample_group: SampleGroup):
        self.sample_group = sample_group
        super().__init__(self.sample_group)

    def generate_excel_sheet(self):
        """Generate an Excel sheet for the sample group."""
        pass