# app/service_layer/plotting/control_chart.py

# control_chart.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

def main():
    # User visual Test functions - Comment out when not in use
    # Unit and Integration tests to be added
    # ControlChart.test_centered_process()
    # ControlChart.test_process_closer_to_LSL()
    # ControlChart.test_process_closer_to_USL()
    # ControlChart.test_process_outside_USL()

    # Normal Usage
    np.random.seed(0)
    density = np.random.normal(loc=7, scale=1, size=30)  # Mean = 7, Standard Deviation = 1
    data_samples = density
    LSL = 20
    USL = 40
    data_prossecor= ControlProcessMetrics(data_samples, LSL=None, USL=None)
    chart_plotter = ControlChartPlotter()

    new_chart = ControlChart(data_samples, data_prossecor, chart_plotter, )
    new_chart.calculate_and_plot('Compressive Strength',tolerance_percentage=5, use_generated_ticks=True)
    print(f"The Cp is {new_chart.Cp:.4f} and the Cpk is {new_chart.Cpk:.4f}")
    print(f"The UCL is {new_chart.UCL:.2f} and the LCL is {new_chart.LCL:.2f}")
    print(f"The USL is {new_chart.USL:.2f} and the LSL is {new_chart.LSL:.2f}")

class ControlProcessMetrics:
    """Class responsible for calculating mean, standard deviation, capability indices, and specification limits."""
    
    def __init__(self, data=None, LSL=None, USL=None):
        self.original_data = data
        self.data = data[~np.isnan(data)]  # Ignore NaN values
        self.mean = self.calculate_mean() if data is not None else None
        self.sigma = self.calculate_sigma() if data is not None else None
        self.LSL = LSL
        self.USL = USL
        self.LCL = None
        self.UCL = None

    def set_data(self, data):
        self.data = data
        self.mean = self.calculate_mean()
        self.sigma = self.calculate_sigma()

    def set_specification_limits(self, LSL, USL):
        self.LSL = LSL
        self.USL = USL

    def set_control_limits(self):
        """Calculate control limits based on data's statistical properties."""
        self.LCL = self.mean - 3 * self.sigma
        self.UCL = self.mean + 3 * self.sigma

    def set_specification_limits_with_tolerance(self, tolerance_percentage, center):
        if center is None:
            mean = self.mean
        else:
            mean = center
        if self.LSL is None or self.USL is None:
            tolerance_factor = tolerance_percentage / 100.0
            self.LSL = mean * (1 - tolerance_factor)
            self.USL = mean * (1 + tolerance_factor)

    def calculate_mean(self):
        return np.mean(self.data)

    def calculate_sigma(self):
        return np.std(self.data)

    def calculate_Cp(self):
        return (self.USL - self.LSL) / (6 * self.sigma)

    def calculate_Cpk(self):
        return min(
            (self.USL - self.mean) / (3 * self.sigma),
            (self.mean - self.LSL) / (3 * self.sigma)
        )


class ControlChartPlotter:
    """Class responsible for plotting the process control chart."""
    
    def __init__(self):
        self.figure = None

    def plot(self, data, chart_data_processor, title=None, x_label=None, y_label=None, fig_size=(10, 6), custom_ticks=None, use_generated_ticks=False):
        plt.figure(figsize=fig_size)
        
        # Plot data and control limits
        plt.plot(data, marker='o', color='blue')
        plt.axhline(y=chart_data_processor.mean, color='red', linestyle='-')
        plt.axhline(y=chart_data_processor.UCL, color='green', linestyle='--')
        plt.axhline(y=chart_data_processor.LCL, color='green', linestyle='--')

        if chart_data_processor.LSL is not None:
            plt.axhline(y=chart_data_processor.LSL, color='orange', linestyle='-.', label='LSL')
        if chart_data_processor.USL is not None:
            plt.axhline(y=chart_data_processor.USL, color='orange', linestyle='-.', label='USL')

        data_size = len(data)
        if custom_ticks:
            plt.xticks(list(range(data_size)), custom_ticks, rotation='vertical')
        elif use_generated_ticks:
            auto_generated_ticks = [f'Sample {i+1}' for i in range(data_size)]
            plt.xticks(list(range(data_size)), auto_generated_ticks, rotation='vertical')
        if custom_ticks or use_generated_ticks:
            plt.subplots_adjust(bottom=0.2)
        
        # plt.ylim(bottom=0)
        plt.title(title if title else "")
        plt.xlabel(x_label if x_label else "Sample Number")
        plt.ylabel(y_label if y_label else "Value")

        plt.text(0, chart_data_processor.UCL + abs(chart_data_processor.UCL - chart_data_processor.LCL) * 0.1,
                 f'Cp = {chart_data_processor.calculate_Cp():.2f}, Cpk = {chart_data_processor.calculate_Cpk():.2f}')
        legend_elements = [
            Patch(facecolor='blue', label='Data'),
            Patch(facecolor='red', label='Mean'),
            Patch(facecolor='green', label='Control Limits')
        ]

        if chart_data_processor.LSL is not None or chart_data_processor.USL is not None:
            legend_elements.append(Patch(facecolor='orange', linestyle='-.', edgecolor='orange', label='Specification limits'))
    
        plt.legend(handles=legend_elements, loc='upper right')
        self.figure = plt.gcf()
        plt.show()

    def save(self, filename="plot.png"):
        if self.figure:
            self.figure.savefig(filename)
            plt.close(self.figure)



class ControlChart:
    """(Facade Class) responsible for orchestrating the quality control chart generation."""
    def __init__(self, data, process_calculator , chart_plotter):
        self.data = data
        self.process_calculator = process_calculator
        self.chart_plotter = chart_plotter

    def calculate_and_plot(self, title, x_label=None, y_label=None, tolerance_percentage=5, LSL=None, USL=None, center = None, custom_ticks=None, use_generated_ticks=False):
        # Calculate specification limits if not provided
        if LSL is None and USL is None:
            self.process_calculator.set_specification_limits_with_tolerance(tolerance_percentage, center )

        self.process_calculator.set_control_limits()
        
        # Plot chart
        self.chart_plotter.plot(self.data, self.process_calculator, title, x_label, y_label, custom_ticks=custom_ticks, use_generated_ticks=use_generated_ticks)

    @property
    def Cp(self):
        return self.process_calculator.calculate_Cp()

    @property
    def Cpk(self):
        return self.process_calculator.calculate_Cpk()

    @property
    def UCL(self):
        return self.process_calculator.UCL
    
    @property
    def USL(self):
        return self.process_calculator.USL

    @property
    def LCL(self):
        return self.process_calculator.LCL
    
    @property
    def LSL(self):
        return self.process_calculator.LSL
    
    @property
    def mean(self):
        return self.process_calculator.mean
    
    @property
    def sigma(self):
        return self.process_calculator.sigma
    
    @staticmethod
    def test_centered_process():
        """Test function for scenario 1: Process mean is centered between LSL and USL."""
        LSL = 20
        USL = 40
        mean_centered = (LSL + USL) / 2
        sigma_centered = (USL - mean_centered) / 3
        data_centered = np.random.normal(loc=mean_centered, scale=sigma_centered, size=30)
        data_processor = ControlProcessMetrics(data_centered, LSL, USL)
        chart_plotter = ControlChartPlotter()
        chart = ControlChart(data_centered, data_processor, chart_plotter)
        chart.calculate_and_plot('Centered Process Data', tolerance_percentage=5)
        print("Scenario 1: Process mean is centered between LSL and USL.")
        print("Expected: The process mean is approximately centered, and Cp should be close to Cpk.\n")
        print(f"For Centered Process Data: Cp = {chart.Cp:.4f}, Cpk = {chart.Cpk:.4f}\n")

    @staticmethod
    def test_process_closer_to_LSL():
        """Test function for scenario 2: Process mean is closer to LSL."""
        LSL = 20
        USL = 40
        mean_closer_to_LSL = (LSL + (LSL + USL) / 2) / 2
        sigma_closer_to_LSL = (mean_closer_to_LSL - LSL) / 3
        data_closer_to_LSL = np.random.normal(loc=mean_closer_to_LSL, scale=sigma_closer_to_LSL, size=30)
        data_processor = ControlProcessMetrics(data_closer_to_LSL, LSL, USL)
        chart_plotter = ControlChartPlotter()
        chart = ControlChart(data_closer_to_LSL, data_processor, chart_plotter)
        chart.calculate_and_plot('Process Data Closer to LSL', tolerance_percentage=5)
        print("Scenario 2: Process mean is closer to LSL.")
        print("Expected: The process mean is nearer to the LSL, resulting in Cp > Cpk.\n")
        print(f"For Process Data Closer to LSL: Cp = {chart.Cp:.4f}, Cpk = {chart.Cpk:.4f}\n")

    @staticmethod
    def test_process_closer_to_USL():
        """Test function for scenario 3: Process mean is closer to USL."""
        LSL = 20
        USL = 40
        mean_closer_to_USL = (USL + (LSL + USL) / 2) / 2
        sigma_closer_to_USL = (USL - mean_closer_to_USL) / 3
        data_closer_to_USL = np.random.normal(loc=mean_closer_to_USL, scale=sigma_closer_to_USL, size=30)
        data_processor = ControlProcessMetrics(data_closer_to_USL, LSL, USL)
        chart_plotter = ControlChartPlotter()
        chart = ControlChart(data_closer_to_USL, data_processor, chart_plotter)
        chart.calculate_and_plot('Process Data Closer to USL', tolerance_percentage=5)
        print("Scenario 3: Process mean is closer to USL.")
        print("Expected: The process mean is nearer to the USL, resulting in Cp > Cpk.\n")
        print(f"For Process Data Closer to USL: Cp = {chart.Cp:.4f}, Cpk = {chart.Cpk:.4f}\n")

    @staticmethod
    def test_process_outside_USL():
        """Test function for scenario 4: Process mean is outside the USL."""
        LSL = 20
        USL = 40
        mean_outside_USL = USL + 5
        sigma_outside_USL = 3
        data_outside_USL = np.random.normal(loc=mean_outside_USL, scale=sigma_outside_USL, size=30)
        data_processor = ControlProcessMetrics(data_outside_USL, LSL, USL)
        chart_plotter = ControlChartPlotter()
        chart = ControlChart(data_outside_USL, data_processor, chart_plotter)
        chart.calculate_and_plot('Process Data Outside USL', tolerance_percentage=5)
        print("Scenario 4: Process mean is outside the USL.")
        print("Expected: The process mean lies beyond the USL, leading to a negative Cpk value.\n")
        print(f"For Process Data Outside USL: Cp = {chart.Cp:.4f}, Cpk = {chart.Cpk:.4f}\n")

if __name__ == '__main__':
    main()
