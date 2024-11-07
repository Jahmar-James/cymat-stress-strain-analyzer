import ttkbootstrap as tb

from core import StressStrainApp

# Run Application
if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = StressStrainApp(root)
    root.mainloop()
