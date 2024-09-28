import numpy as np
import pandas as pd
from uncertainties import ufloat
from uncertainties import unumpy as unp

# Assuming the `calculate_derivative` method and CalculationResult are defined in the code provided

from standards.base.properties_calculators.base_standard_operator import BaseStandardOperator

# Create a simple data series with uncertainty
# For example, a linear relationship y = 2x with some uncertainty
independent_variable = pd.Series(np.linspace(0, 10, 11), name="x")
data_series = pd.Series(2 * independent_variable + 1, name="y")

uncertainty_y = [0.1] * len(data_series)


# derivative_methods = ["forward", "backward", "central"]

# # Basic Test Without Uncertainty
# for method in derivative_methods:
#     result = BaseStandardOperator.calculate_derivative(
#         data_series=data_series,
#         independent_variable=independent_variable,
#         # uncertainty_y=uncertainty_y,
#         order=1,
#         method=method,
#     )
#     derivative_series, uncertainty_series = result
#     print(f"Derivative Series with Uncertainty (Method: {method}):")
#     print(derivative_series)
#     print("\nUncertainty in Derivative:")
#     print(uncertainty_series)
#     print("\n")




def test_derivative_methods():
    def generate_test_data(function, x_range, num_points, spacing='even'):
        """
        Generate test data based on specified range, number of points, and spacing type.
        
        Parameters:
        - function: A callable function to generate y-values
        - x_range: A tuple defining the start and end of the x-values (e.g., (0, 10))
        - num_points: Number of points to generate
        - spacing: Type of spacing ('even' or 'uneven')
        
        Returns:
        - x_values: Generated x-values
        - y_values: Corresponding y-values
        """
        start, end = x_range
        
        if spacing == 'even':
            x_values = np.linspace(start, end, num_points)
        elif spacing == 'uneven':
            x_values = np.sort(np.random.uniform(start, end, num_points))
        else:
            raise ValueError("Invalid spacing type. Choose 'even' or 'uneven'.")
        
        y_values = function(x_values)
        return x_values, y_values
    
    # Define test configurations
    configurations = [
        {'range': (0, 10), 'points': 50, 'spacing': 'even'},
        {'range': (0, 10), 'points': 50, 'spacing': 'uneven'},
        {'range': (0, 10), 'points': 500, 'spacing': 'even'},
        {'range': (0, 10), 'points': 500, 'spacing': 'uneven'},
        {'range': (0, 100), 'points': 50, 'spacing': 'even'},
        {'range': (0, 100), 'points': 50, 'spacing': 'uneven'},
        {'range': (0, 100), 'points': 500, 'spacing': 'even'},
        {'range': (0, 100), 'points': 500, 'spacing': 'uneven'}
    ]
    
    # Functions to test
    functions = {
        'Linear': lambda x: 2 * x + 3, 
        'Quadratic': lambda x: x ** 2,
        'Sine': lambda x: np.sin(x),
        'Exponential': lambda x: np.exp(x)
    }
    
    for config in configurations:
        x_range = config['range']
        num_points = config['points']
        spacing = config['spacing']
        
        print(f"\nTesting with range {x_range}, {num_points} points, spacing '{spacing}'")
        
        results = []
        for func_name, func in functions.items():
            x_values, y_values = generate_test_data(func, x_range, num_points, spacing)
            x_values = pd.Series(x_values, name='x')
            y_values = pd.Series(y_values, name='y')
                 
            # Analytical derivatives for comparison
            if func_name == 'Linear':
                analytical_derivative = 2 * np.ones_like(x_values) # Derivative of 2x + 3 is 2
            elif func_name == 'Quadratic':
                analytical_derivative = 2 * x_values # Derivative of x^2 is 2x
            elif func_name == 'Sine':
                analytical_derivative = np.cos(x_values) # Derivative of sin(x) is cos(x)
            elif func_name == 'Exponential':
                analytical_derivative = np.exp(x_values) # Derivative of exp(x) is exp(x)
            else:
                analytical_derivative = np.zeros_like(x_values) # Placeholder for other functions
            
            # Calculate numerical derivatives using optimal step sizes
            central_derivative, central_deri_uncertainty = BaseStandardOperator.calculate_derivative(
                data_series=y_values,
                independent_variable=x_values,
                order=1,
                method='central'
            )
            forward_derivative, forward_deri_uncertainty = BaseStandardOperator.calculate_derivative(
                data_series=y_values,
                independent_variable=x_values,
                order=1,
                method='forward'
            )
            backward_derivative, backward_deri_uncertainty = BaseStandardOperator.calculate_derivative(
                data_series=y_values,
                independent_variable=x_values,
                order=1,
                method='backward'
            )
            
            # Calculate errors
            central_error = np.abs(central_derivative - analytical_derivative)
            forward_error = np.abs(forward_derivative - analytical_derivative)
            backward_error = np.abs(backward_derivative - analytical_derivative)

            # Print results for each function
            print(f"\nResults for {func_name} Function:")
            print(f"Mean Absolute Error - Central: {np.mean(central_error):.6e}")
            print(f"Mean Absolute Error - Forward: {np.mean(forward_error):.6e}")
            print(f"Mean Absolute Error - Backward: {np.mean(backward_error):.6e}")

                  
            # Store results
            results.append({
                'Function': func_name,
                'Configuration': f"Range: {x_range}, Points: {num_points}, Spacing: '{spacing}'",
                'Central Error': central_error,
                'Forward Error': forward_error,
                'Backward Error': backward_error,
            })
            
    return results


test_derivative_methods()