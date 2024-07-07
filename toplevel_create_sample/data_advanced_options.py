import customtkinter as ctk
import pandas as pd


# Adcanced Data Options Window
class AdvancedDataOptions(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Custom Configuration Window")
        self.geometry("900x500")

        # File type selection
        ctk.CTkLabel(self, text="Select File Type:").grid(row=0, column=0, padx=10, pady=10)
        self.file_type_var = ctk.StringVar(value="Excel")
        self.file_type_dropdown = ctk.CTkComboBox(self, variable=self.file_type_var, values=["Excel", "CSV"])
        self.file_type_dropdown.grid(row=0, column=1, padx=10, pady=10)
        self.file_type_dropdown.bind("<<ComboboxSelected>>", self.on_file_type_change)

        # pandas.read_excel flags
        self.excel_options = {
            "sheet_name": None,
            "header": 0,
            "names": None,
            "index_col": None,
            "usecols": None,
            "squeeze": False,
            "dtype": None,
            "engine": None,
            "converters": None,
            "true_values": None,
            "false_values": None,
            "skiprows": None,
            "nrows": None,
            "na_values": None,
            "keep_default_na": True,
            "na_filter": True,
            "verbose": False,
            "parse_dates": False,
            "date_parser": None,
            "thousands": None,
            "decimal": ".",
            "comment": None,
            "skipfooter": 0,
            "convert_float": True,
            "mangle_dupe_cols": True,
        }

        # pandas.read_csv flags
        self.csv_options = {
            "sep": ",",
            "delimiter": None,
            "header": "infer",
            "names": None,
            "index_col": None,
            "usecols": None,
            "squeeze": False,
            "prefix": None,
            "mangle_dupe_cols": True,
            "dtype": None,
            "engine": None,
            "converters": None,
            "true_values": None,
            "false_values": None,
            "skipinitialspace": False,
            "skiprows": None,
            "nrows": None,
            "na_values": None,
            "keep_default_na": True,
            "na_filter": True,
            "verbose": False,
            "skip_blank_lines": True,
            "parse_dates": False,
            "infer_datetime_format": False,
            "keep_date_col": False,
            "date_parser": None,
            "dayfirst": False,
            "cache_dates": True,
            "iterator": False,
            "chunksize": None,
            "compression": "infer",
            "thousands": None,
            "decimal": ".",
            "lineterminator": None,
            "quotechar": '"',
            "quoting": 0,
            "doublequote": True,
            "escapechar": None,
            "comment": None,
            "encoding": None,
            "dialect": None,
            "error_bad_lines": True,
            "warn_bad_lines": True,
            "delim_whitespace": False,
            "low_memory": True,
            "memory_map": False,
            "float_precision": None,
        }

        self.option_vars = {}
        self.boolean_vars = {}
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.options_frame.grid_rowconfigure(0, weight=1)
        self.options_frame.grid_columnconfigure(0, weight=1)

        self.update_options(self.excel_options)

    def on_file_type_change(self, event) -> None:
        file_type = self.file_type_var.get()
        if file_type == "Excel":
            self.update_options(self.excel_options)
        else:
            self.update_options(self.csv_options)

    def update_options(self, options) -> None:
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        self.option_vars.clear()
        self.boolean_vars.clear()
        row = 0
        col = 0
        for option, default_value in options.items():
            if isinstance(default_value, bool):
                ctk.CTkLabel(self.options_frame, text=option).grid(row=row, column=col * 2, padx=10, pady=5)
                var = ctk.BooleanVar(value=default_value)
                toggle_button = ctk.CTkSwitch(self.options_frame, text="", variable=var)
                toggle_button.grid(row=row, column=col * 2 + 1, padx=10, pady=5)
                self.boolean_vars[option] = var
            else:
                ctk.CTkLabel(self.options_frame, text=option).grid(row=row, column=col * 2, padx=10, pady=5)
                var = ctk.StringVar(value=str(default_value))
                entry = ctk.CTkEntry(self.options_frame, textvariable=var)
                entry.grid(row=row, column=col * 2 + 1, padx=10, pady=5)
                self.option_vars[option] = var

            row += 1
            if row % 10 == 0:  # Adjust this number to fit the desired layout
                row = 0
                col += 1

    def get_options(self) -> None:
        options = {k: v.get() for k, v in self.option_vars.items()}
        options.update({k: v.get() for k, v in self.boolean_vars.items()})
        return options


# Example of using the CustomToplevel
def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    print(f"{pd.read_excel.__dir__}")

    root = ctk.CTk()
    root.geometry("200x100")
    ctk.CTkButton(root, text="Open Config Window", command=lambda: AdvancedDataOptions(root)).pack(pady=20)
    root.mainloop()


if __name__ == "__main__":
    main()
    main()
