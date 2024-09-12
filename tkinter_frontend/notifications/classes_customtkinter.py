import customtkinter as ctk


class CustomTkinterToast:
    def __init__(
        self,
        master: ctk.CTk,
        title="Notification",
        message="Your message here",
        duration=3000,
        position=("right", "bottom"),
        alert=False,
    ):
        """
        Initialize a toast notification.

        Args:
            master (ctk.CTk): The master widget.
            title (str): The title of the toast notification.
            message (str): The message of the toast notification.
            duration (int): How long to display the toast, in milliseconds.
            position (tuple): The position of the toast ('right'/'left', 'top'/'bottom').
            alert (bool): If True, the system bell will ring when the toast is shown.
        """
        self.master = master
        self.title = title
        self.message = message
        self.duration = duration
        self.position = position
        self.toast_window = None
        self.alert = alert
        self.toast_width = 300
        self.toast_height = 100
        self.bg_color = "#333333"

    def show_toast(self) -> None:
        """Create and show the toast window."""
        self.toast_window = ctk.CTkToplevel(self.master)
        self.toast_window.title(self.title)
        self.toast_window.attributes("-topmost", True)
        self.toast_window.attributes("-alpha", 0.95)
        self.toast_window.overrideredirect(True)  # Remove window decorations
        self.toast_window.configure(bg=self.bg_color)  # Set a consistent background color

        self.toast_window.update_idletasks()  # Update the window to get the actual width and height
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x_coordinate = screen_width - self.toast_width - 20 if self.position[0] == "right" else 20
        y_coordinate = screen_height - self.toast_height - 50 if self.position[1] == "bottom" else 50
        self.toast_window.geometry(f"{self.toast_width}x{self.toast_height}+{x_coordinate}+{y_coordinate}")

        title_font = ("Helvetica", 14, "bold")
        message_font = ("Helvetica", 12)
        title_label = ctk.CTkLabel(
            self.toast_window,
            text=self.title,
            wraplength=self.toast_width - 20,
            fg_color=self.bg_color,
            text_color="white",
            font=title_font,
        )
        message_label = ctk.CTkLabel(
            self.toast_window,
            text=self.message,
            wraplength=self.toast_width - 20,
            fg_color=self.bg_color,
            text_color="white",
            font=message_font,
        )

        title_label.pack(padx=10, pady=(10, 0), fill="both", expand=True)
        message_label.pack(padx=10, pady=(0, 10), fill="both", expand=True)

        if self.alert:
            self.master.bell()  # Ring the system bell

        self.toast_window.bind("<Button-1>", self.hide_toast)
        if self.duration:
            self.toast_window.after(self.duration, self.hide_toast)

    def hide_toast(self, event=None) -> None:
        """Fade out effect and close the toast window."""
        alpha = self.toast_window.attributes("-alpha")
        if alpha > 0.1:
            self.toast_window.attributes("-alpha", alpha - 0.1)
            self.toast_window.after(100, self.hide_toast)
        else:
            self.toast_window.destroy()


class CustomTkinterTooltip:
    def __init__(
        self,
        widget,
        text="Tooltip text",
        delay=500,
        autohide_delay=8000,
        fg_color="#333333",
        text_color="white",
        alpha=0.9,
        offset_x=20,
        offset_y=20,
        font=("Helvetica", 10),
        padding=(3, 2),
        label_padding=(1, 1),
    ):
        """
        Initialize a tooltip for CustomTkinter widgets.

        Args:
            widget (ctk.CTkWidget): The widget to attach the tooltip.
            text (str): The text displayed in the tooltip.
            delay (int): The delay in milliseconds before showing the tooltip.
            fg_color (str): The background color of the tooltip.
            text_color (str): The text color of the tooltip.
            alpha (float): The transparency level of the tooltip window.
            offset_x (int): The horizontal offset of the tooltip from the cursor.
            offset_y (int): The vertical offset of the tooltip from the cursor.
            font (tuple): The font of the tooltip text.
            padding (tuple): The padding inside the tooltip (horizontal, vertical).
            label_padding (tuple): The padding between the label and the Toplevel window (horizontal, vertical).
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.autohide_delay = autohide_delay
        self.fg_color = fg_color
        self.text_color = text_color
        self.alpha = alpha
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.font = font
        self.padding = padding
        self.label_padding = label_padding
        self.tooltip_window = None
        self.after_id = None

        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<Motion>", self.on_motion)

    def on_enter(self, event):
        self.schedule_tooltip()

    def on_leave(self, event):
        self.unschedule_tooltip()
        self.hide_tooltip()

    def on_motion(self, event):
        if self.tooltip_window:
            x = event.x_root + self.offset_x
            y = event.y_root + self.offset_y
            self.tooltip_window.geometry(f"+{x}+{y}")

    def schedule_tooltip(self):
        self.unschedule_tooltip()
        self.after_id = self.widget.after(self.delay, self.show_tooltip)

    def unschedule_tooltip(self):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

    def show_tooltip(self):
        if not self.tooltip_window:
            self.tooltip_window = ctk.CTkToplevel(self.widget)
            self.tooltip_window.overrideredirect(True)
            self.tooltip_window.attributes("-topmost", True)
            self.tooltip_window.attributes("-alpha", self.alpha)  # customizable transparency
            x = self.widget.winfo_pointerx() + self.offset_x
            y = self.widget.winfo_pointery() + self.offset_y

            self.tooltip_window.geometry(f"+{x}+{y}")

            frame = ctk.CTkFrame(self.tooltip_window, fg_color=self.fg_color)
            frame.pack(padx=self.label_padding[0], pady=self.label_padding[1])

            label = ctk.CTkLabel(frame, text=self.text, text_color=self.text_color, font=self.font)
            label.pack(padx=self.padding[0], pady=self.padding[1])

            self.tooltip_window.after(self.autohide_delay, self.hide_tooltip)

    def hide_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


if __name__ == "__main__":
    # Example usage
    # To use the CustomTkinterToast, you would create a root window and show the toast like this:
    root = ctk.CTk()
    root.geometry("400x400")
    btn = ctk.CTkButton(root, text="Hover over me")
    btn.pack(padx=20, pady=20)
    tooltip = CustomTkinterTooltip(btn, "This is a tooltip")
    toast = CustomTkinterToast(master=root, message="This is a toast message", alert=True)
    toast.show_toast()
    root.mainloop()
    root.mainloop()
