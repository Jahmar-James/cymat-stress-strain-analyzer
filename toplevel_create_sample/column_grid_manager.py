import tkinter as tk
from collections import namedtuple
from typing import Optional, Union

# Define the layout configuration using a namedtuple
WidgetConfig = namedtuple("WidgetConfig", ["widget", "row", "rowspan", "weight", "sticky", "uniform", "padx", "pady"])


class ColumnGridManager:
    """
    Automated Layout Management,Centralized Configuration

    Assumptions:
    - Row-based Sequential Layout (Single Column Layout)
    - 0-based Row Indexing
    """

    def __init__(self, master: Union[tk.Frame, tk.Tk, tk.Toplevel]):
        self.master = master
        self.widgets_config: list[WidgetConfig] = []
        self.current_row = 0

    def add_widget(self, widget: tk.Widget, rowspan=1, weight=1, sticky="nsew", uniform=None, padx=0, pady=0) -> None:
        """Add a widget to the list without placing it in the grid immediately."""
        self.widgets_config.append(WidgetConfig(widget, self.current_row, rowspan, weight, sticky, uniform, padx, pady))
        self.current_row += rowspan

    def apply_layout(self, col_minsize: int = 0, row_minsize: int = 0) -> None:
        """Configure the grid after all widgets have been added."""
        self.master_columnconfigure(minsize=col_minsize)
        self.master_rowconfigure(minsize=row_minsize)

        for config in self.widgets_config:
            config.widget.grid(
                row=config.row,
                column=0,
                rowspan=config.rowspan,
                sticky=config.sticky,
                padx=config.padx,
                pady=config.pady,
            )

    def master_rowconfigure(
        self, weight: int = 1, minsize: int = 0, pad: int = 0, uniform: Optional[str] = "a"
    ) -> None:
        self.master.grid_rowconfigure(
            list(range(self.current_row)), weight=weight, minsize=minsize, pad=pad, uniform=uniform
        )

    def master_columnconfigure(
        self, weight: int = 1, minsize: int = 0, pad: int = 0, uniform: Optional[str] = "a"
    ) -> None:
        self.master.grid_columnconfigure(0, weight=weight, minsize=minsize, pad=pad, uniform=uniform)


class leftColumn(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.grid_manager = ColumnGridManager(self)
        self.create_widgets()

    def create_widgets(self) -> None:
        label = tk.Label(self, text="Left Column", bg="lightblue")
        button = tk.Button(self, text="Click Me", bg="lightblue")

        self.grid_manager.add_widget(
            widget=label, rowspan=1, weight=1, sticky="nsew", uniform="group1", padx=10, pady=10
        )
        self.grid_manager.add_widget(widget=button, rowspan=1, weight=1, sticky="nsew", uniform="group1")

        self.grid_manager.apply_layout()


class rightColumn(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.grid_manager = ColumnGridManager(self)
        self.create_widgets()

    def create_widgets(self) -> None:
        label = tk.Label(self, text="Right Column", bg="lightgreen")
        button = tk.Button(self, text="Click Me", bg="lightgreen")

        self.grid_manager.add_widget(widget=label, rowspan=1, weight=1, sticky="nsew", uniform="group1")
        self.grid_manager.add_widget(widget=button, rowspan=1, weight=1, sticky="nsew", uniform="group1")

        self.grid_manager.apply_layout()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("300x200")

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure((0, 1), weight=1)

    left_column = leftColumn(root)
    right_column = rightColumn(root)

    left_column.grid(row=0, column=0, sticky="nsew")
    right_column.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    root.mainloop()
