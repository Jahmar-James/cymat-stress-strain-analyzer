import tkinter as tk
from tkinter import messagebox, filedialog
import pandas as pd


class ExcelProcessor(tk.Tk):
    def __init__(self, filepath):
        super().__init__()
        self.title("Excel Row Processor")
        self.geometry("400x100")

        # Load the generator
        self.data_generator = self.read_excel_row_by_row(filepath)

        # Setup the GUI
        process_button = tk.Button(self, text="Process Next Row", command=self.process_next_row)
        process_button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=20)

        skip_button = tk.Button(self, text="Skip Row", command=self.skip_row)
        skip_button.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=20)

        self.current_row = None

    def read_excel_row_by_row(self, filepath):
        # Read the Excel file
        df = pd.read_excel(filepath)
        for index, row in df.iterrows():
            yield row

    def process_next_row(self):
        try:
            self.current_row = next(self.data_generator)
            self.handle_row(self.current_row, process=True)
        except StopIteration:
            messagebox.showinfo("End of Data", "No more rows to process.")

    def skip_row(self):
        try:
            self.current_row = next(self.data_generator)
            self.handle_row(self.current_row, process=False)
        except StopIteration:
            messagebox.showinfo("End of Data", "No more rows to process.")

    def handle_row(self, row, process):
        if process:
            # Process the row (this can be your custom processing logic)
            messagebox.showinfo("Row Processed", f"Processed: {row.to_dict()}")
        else:
            # Just display a message if skipped
            messagebox.showinfo("Row Skipped", "Skipped a row")

if __name__ == "__main__":
    file_path = "Sample_test.xlsx"
    app = ExcelProcessor(file_path)
    app.mainloop()
