import ttkbootstrap as tb

from tkinter_frontend import StressStrainApp


def main() -> None:
    root = tb.Window(themename="darkly")
    app = StressStrainApp(root)
    root.mainloop()


def top_level_test() -> None:
    from tkinter_frontend.toplevel_create_sample.Test import App

    app = App()
    app.mainloop()


# Run Application
if __name__ == "__main__":
    # main()
    top_level_test()
