import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Create a canvas object and scrollbars for scrolling it
        self.canvas = tk.Canvas(self)
        self.v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        # Place the canvas and scrollbars in the frame
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Configure the grid to expand
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create a frame inside the canvas which will be scrolled
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Add the scrollable frame to the canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Configure the scroll region when the size of the scrollable frame changes
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)

        # Optional: Bind mousewheel scrolling
        self._bind_mousewheel()

    def _on_frame_configure(self, event):
        # Update scroll region to encompass the inner frame
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _bind_mousewheel(self):
        # Bind mousewheel events to the canvas
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows
        self.canvas.bind_all("<Shift-MouseWheel>", self._on_shift_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)  # Linux scroll up
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)  # Linux scroll down

    def _on_mousewheel(self, event):
        # Scroll vertically
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_shift_mousewheel(self, event):
        # Scroll horizontally when Shift key is held
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        # Scroll for Linux systems
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")


if __name__ == "__main__":
    import tkinter as tk
    from tkinter import ttk

    class Application(tk.Tk):
        def __init__(self):
            super().__init__()

            # Set the window title and size

            self.title("Horizontal and Vertical Scrollable Frame Example")
            self.geometry("600x400")

            # Create an instance of ScrollableFrame
            scrollable_frame = ScrollableFrame(self)
            scrollable_frame.pack(fill="both", expand=True)

            # Add content to the scrollable frame
            for row in range(20):
                for col in range(10):
                    label = ttk.Label(
                        scrollable_frame.scrollable_frame,
                        text=f"Row {row}, Col {col}",
                        borderwidth=1,
                        relief="solid",
                        width=15,
                        anchor="center",
                    )
                    label.grid(row=row, column=col, padx=5, pady=5)

            # Configure grid inside the scrollable_frame
            for col in range(10):
                scrollable_frame.scrollable_frame.grid_columnconfigure(col, weight=1)

    app = Application()
    app.mainloop()
