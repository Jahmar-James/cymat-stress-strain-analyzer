import pandas as pd

def calculate_kpi_statistics_transposed(self, KPI_df, usl=None, lsl=None):
    KPI_numerical = KPI_df.drop('Name', axis=1).transpose()
    stats_df = pd.DataFrame()

    for kpi in KPI_numerical.columns:
        # Separate the tuple into two series for processing
        series_1, series_2 = zip(*[process_kpi_value(value) for value in KPI_numerical[kpi]])
        series_1_stats = calculate_statistics(pd.Series(series_1), usl, lsl)
        series_2_stats = calculate_statistics(pd.Series(series_2), usl, lsl)
        
        # Combine the statistics of both series as tuples
        combined_stats = tuple(zip(series_1_stats, series_2_stats))
        stats_df[kpi] = combined_stats

    stats_df.index = ['Mean', 'Std', 'CV', 'UCL', 'LCL', 'Cp', 'Cpk']
    return stats_df

def process_kpi_value(value):
    return value if isinstance(value, tuple) else (value, value)

def calculate_statistics(series, usl, lsl):
    mean = series.mean()
    std = series.std()
    cv = std / mean if mean != 0 else 0
    ucl = mean + 3 * std
    lcl = mean - 3 * std
    cp = (usl - lsl) / (6 * std) if usl is not None and lsl is not None else 'N/A'
    cpk = min((usl - mean) / (3 * std), (mean - lsl) / (3 * std)) if usl is not None and lsl is not None else 'N/A'
    return mean, std, cv, ucl, lcl, cp, cpk

import customtkinter as ctk
from ttkbootstrap.widgets import DateEntry  # Import the DateEntry widget from ttkbootstrap
from ttkbootstrap.tooltip import ToolTip  # Import the ToolTip class from ttkbootstrap
from ttkbootstrap.toast import ToastNotification  # Import the ToastNotification class from ttkbootstrap

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # CustomTkinter window setup
        self.title("CTk and ttkbootstrap App")
        self.geometry('400x400')

        # Create widgets
        self.create_widgets()

    def create_widgets(self):
        # CustomTkinter button with tooltip
        self.ctk_button = ctk.CTkButton(self, 
                                        text="Click Me",
                                        command=self.on_ctk_button_click,
                                        corner_radius=5,
                                        fg_color=('#ffffff', '#007bff'),
                                        bg_color=('#007bff', '#007bff'),
                                        hover_color=('#0056b3', '#0056b3'),                                    
                                        )
        self.tooltip = ToolTip(self.ctk_button, text="This is a tooltip")  # Attach tooltip to CTkButton
        self.ctk_button.pack(pady=20)

        # ttkbootstrap DateEntry widget
        self.date_entry = DateEntry(master=self,)
        self.date_entry.pack(pady=20)

        #close the window
        self.close_button = ctk.CTkButton(self, text="Close", command=self.on_close_button_click)
        self.close_button.pack(pady=20)

    def on_ctk_button_click(self):
        # Display a toast notification on button click

        print("CustomTkinter Button Clicked")
        Toast =  ToastNotification(title="Notification", message="CustomTkinter Button Clicked", duration=3000, ) 
        Toast.show_toast()
        
    def on_close_button_click(self):
        #stop eveything and close the window
        self.destroy()

# Run the application
if __name__ == "__main__":
    app = App()
    app.mainloop()
