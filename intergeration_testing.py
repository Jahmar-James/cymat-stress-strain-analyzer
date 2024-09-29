import numpy as np
import pandas as pd
from uncertainties import ufloat
from uncertainties import unumpy as unp
from scipy import integrate

from standards.base.properties_calculators.base_standard_operator import BaseStandardOperator

# Test intergration of the BaseStandardOperator class



independent_variable = pd.Series(np.linspace(-50, 50, 100), name="x")
data_series = pd.Series([2] * len(independent_variable), name="y")  # Constant function y = 2

# Uncertainty settings
uncertainty_y = 0.1  # Constant uncertainty in y
uncertainty_x = 0.01  # Constant uncertainty in x

# Known solution for integral of y = 2 from 0 to 10 is 20
known_integral_constant = 2 * (10 - 0)  # 20

# Test the calculate_integral function with different methods
integration_methods = ["trapezoidal", "simpson"]

# Import BaseStandardOperator and CalculationResult
from standards.base.properties_calculators.base_standard_operator import BaseStandardOperator

# Run tests for each integration method
for method in integration_methods:
    result = BaseStandardOperator.calculate_integral(
        data_series=data_series,
        independent_variable=independent_variable,
        method=method,
        uncertainty_y=uncertainty_y,
        # uncertainty_x=uncertainty_x,
    )
    integral_value, integral_uncertainty = result
    print(f"Integration Result (Method: {method}):")
    print(f"Calculated Integral: {integral_value}")
    print(f"Known Integral: {known_integral_constant}")
    print(f"Integral Uncertainty: {integral_uncertainty}\n")

# Linear function test: y = 2x over x = [0, 10]
data_series_linear = pd.Series(2 * independent_variable, name="y")  # Linear function y = 2x

# Known solution for integral of y = 2x from 0 to 10 is 100
known_integral_linear = 10**2  # 100

# Run tests for each integration method
for method in integration_methods:
    result = BaseStandardOperator.calculate_integral(
        data_series=data_series_linear,
        independent_variable=independent_variable,
        method=method,
        uncertainty_y=uncertainty_y,
        # uncertainty_x=uncertainty_x,
    )
    integral_value, integral_uncertainty = result
    print(f"Integration Result (Method: {method}, Linear Function):")
    print(f"Calculated Integral: {integral_value}")
    print(f"Known Integral: {known_integral_linear}")
    print(f"Integral Uncertainty: {integral_uncertainty}\n")
    

# Define a Monte Carlo simulation function for Simpson's rule
from uncertainties.unumpy import nominal_values, std_devs

def monte_carlo_simpson(data, x_values, n_samples=10000):
    # Generate samples based on uncertainty
    y_samples = np.random.normal(nominal_values(data), std_devs(data), (n_samples, len(data)))
    x_samples = np.random.normal(nominal_values(x_values), std_devs(x_values), (n_samples, len(x_values)))
    
    # Compute Simpson's rule for each sample
    integrals = np.array([integrate.simps(y, x) for y, x in zip(y_samples, x_samples)])
    
    # Calculate mean and standard deviation of the integral
    mean_integral = np.mean(integrals)
    uncertainty_integral = np.std(integrals)
    
    return mean_integral, uncertainty_integral

# # Example usage:
# x_values = np.linspace(0, 10, 11)
# y_values = 2 * x_values  # Linear function y = 2x
# y_uncertainties = 0.1 * np.ones_like(y_values)

# # Create uncertainty arrays
# y_data = unp.uarray(y_values, y_uncertainties)
# x_data = unp.uarray(x_values, 0.01)

# # Monte Carlo estimation
# mc_mean, mc_uncertainty = monte_carlo_simpson(y_data, x_data)
# print(f"Monte Carlo Estimated Integral: {mc_mean} ± {mc_uncertainty}")



# Example usage
independent_variable = pd.Series(np.linspace(-50,50, 100), name="x")
data_series = pd.Series([2] * len(independent_variable), name="y")  # Constant function y = 2

# Known solution for cumulative integral: [0, 2, 4, ..., 20]
result_series, result_series_uncertainty = BaseStandardOperator.calculate_cumulative_integral(
    data_series=data_series,
    independent_variable=independent_variable,
    method="trapezoidal",
    # uncertainty_y=0.1,  
    # uncertainty_x=0.01
)

# Display results
print("Cumulative Integral Series:")
print(result_series)
print("\nCumulative Integral Uncertainty Series:")
print(result_series_uncertainty)

# Plotting the cumulative integral
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.plot(result_series.index, result_series, label="Cumulative Integral")
# plt.fill_between(result_series.index, result_series - result_series_uncertainty, result_series + result_series_uncertainty, color='gray', alpha=0.3, label="Uncertainty")
plt.xlabel('x')
plt.ylabel('Cumulative Integral')
plt.title('Cumulative Integral with Uncertainty')
plt.legend()
plt.show()