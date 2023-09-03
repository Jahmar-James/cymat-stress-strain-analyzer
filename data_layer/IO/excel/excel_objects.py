# app/data_layer/IO/excel/excel_objects.py

from collections import namedtuple 
from dataclasses import dataclass
from typing import List
from openpyxl.utils import get_column_letter
from pydantic import BaseModel, Field, root_validator

import pandas as pd

# Class to represent the position of a table or chart within a worksheet.
Position = namedtuple("Position", ["start_row", "start_col", "end_row", "end_col"])

@dataclass
class ExcelTable:
    """
    Class to represent a table within an Excel worksheet
    """
   
    headers: List[str]
    data: pd.DataFrame
    position: Position

    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, position: Position):
        # if only the "start_row", "start_col" are provided, then end row and end col are calculated
        # from the length of the dataframe
        headers = list(df.columns)
        data = df
        return cls(headers=headers, data=data, position=position)

@dataclass
class ExcelChart:
    data_range: Position
    position: Position

class SheetLayoutModel(BaseModel):
    """Class to represent the layout of a single worksheet with tables and charts"""
    data_tables: List[ExcelTable] = Field(default_factory=list)
    data_charts: List[ExcelChart] = Field(default_factory=list)

    @root_validator
    def validate_no_overlap(cls, layout_elements):
        all_positions = [table.position for table in layout_elements.get('data_tables', [])] + \
                        [chart.position for chart in layout_elements.get('data_charts', [])]

        if len(all_positions) != len(set(all_positions)):
            raise ValueError('Overlap detected.')
        return layout_elements

class ExcelSheet:
    """Class to represent a single worksheet with tables and charts"""
    def __init__(self, worksheet_name: str = "Sheet1"):
        self.worksheet_name = worksheet_name
        self.layout_model = SheetLayoutModel()

    def add_table(self, table: ExcelTable):
        self.layout_model.data_tables.append(table)
        self.layout_model = SheetLayoutModel(**self.layout_model.dict())

    def add_chart(self, chart: ExcelChart):
        self.layout_model.data_charts.append(chart)
        self.layout_model = SheetLayoutModel(**self.layout_model.dict())

    def generate_tables_for_worksheet(self, worksheet):
        for table in self.layout_model.data_tables:
            row_start, col_start, _, _ = table.position
            for row_idx, row_data in enumerate(table.data.iterrows(), start=row_start):
                for col_idx, cell_value in enumerate(row_data[1], start=col_start):
                    col_letter = get_column_letter(col_idx)
                    worksheet[f"{col_letter}{row_idx}"] = cell_value

    def generate_charts_for_worksheet(self, worksheet):
        # TODO: Implement chart population logic
        pass