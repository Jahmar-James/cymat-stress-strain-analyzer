from collections import namedtuple
from enum import Enum

import pandas as pd

# Configuration named tuple for data cleaner settings
RawDataConfig = namedtuple(
    "RawDataConfig",
    ["headers_of_interest", "header_row_offset", "unit_row_offset", "data_start_offset", "marker", "invalid_data"],
)


# Enum to store standard configurations
class CoercerFormats(Enum):
    DEFAULT = RawDataConfig(
        headers_of_interest=["Time", "Force", "Displacement"],
        header_row_offset=1,
        unit_row_offset=2,
        data_start_offset=3,
        marker="Data Acquisition",
        invalid_data=["Data Acquisition"],
    )


# Base coercer class
class MTDataCoercer:
    registry = {}  # Class registry

    @classmethod
    def register(cls, key):
        def decorator(klass):
            cls.registry[key] = klass
            return klass

        return decorator

    @classmethod
    def create(cls, key, *args, **kwargs):
        if key in cls.registry:
            return cls.registry[key](*args, **kwargs)
        else:
            raise ValueError(f"No class found for {key}")


@MTDataCoercer.register(CoercerFormats.DEFAULT)
class TextDataCleaner:
    def __init__(self, config: RawDataConfig):
        self.config = config
        self.marker = config.marker
        self.invalid_data = config.invalid_data

    def create_df_from_txt_data(self, data) -> pd.DataFrame:
        headers, units, data_rows = self.process_data(data)
        return pd.DataFrame(data_rows, columns=headers)

    def process_data(self, data) -> tuple:
        headers, units, data_rows = [], [], []
        marker_found = self.locate_marker(data)

        for line_count, line in enumerate(data, start=1):
            if line_count == self.config.header_row_offset:
                headers = self.extract_headers(line)
            elif line_count == self.config.unit_row_offset:
                units = line.split()
            elif line_count >= self.config.data_start_offset:
                if self.should_ignore_line(line):
                    break
                data_rows.append(self.parse_data_line(line, headers))

        if not marker_found:
            raise ValueError(f"Marker '{self.marker}' not found in the data.")
        return headers, units, data_rows

    def locate_marker(self, data):
        for line in data:
            if self.marker in line:
                return True
        return False

    def extract_headers(self, line) -> list:
        return [header for header in line.split() if header in self.config.headers_of_interest]

    def should_ignore_line(self, line) -> bool:
        return any(line.startswith(invalid) for invalid in self.invalid_data)

    def parse_data_line(self, line, headers) -> list:
        if line.strip():
            return line.split()[: len(headers)]
        return None


if __name__ == "__main__":
    file_path = r"specimen.dat"

    with open(file_path, "r") as file:
        cleaner = MTDataCoercer.create(CoercerFormats.DEFAULT, config=CoercerFormats.DEFAULT.value)
        df = cleaner.create_df_from_txt_data(file)

    print(f"The first 5 from the dataframe: \n{df.head()}")  # The first 5 from the dataframe:
    print(f"The last 5 from the dataframe: \n{df.tail()}")  # The last 5 from the dataframe:
    print(f"The shape of the dataframe: \n{df.shape}")  # The shape of the dataframe:
    print("Now double check the data to ensure it's correct.")  # Now double check the data to ensure it's correct.
    print("Now double check the data to ensure it's correct.")  # Now double check the data to ensure it's correct.
