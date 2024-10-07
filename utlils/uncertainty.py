"""

Calculate Type A Uncertainty - Use the standard deviation of repeated measurements
Estimate Type B Uncertainty - Gather information on instrument resolution, calibration, and environmental factors.
Combine Uncertainties - Combine Type A and Type B uncertainties to estimate the total uncertainty by take the square root of the sum of the squares of the individual uncertainties.



Default Uncertainty Values for a Typical Mechanical Testing Setup

Measurement	            Assumed Uncertainty	        Description
Force	                ±0.5% of measured value	    For load cell uncertainty
Displacement	        ±0.01 mm	                For extensometer or LVDT sensor
Length/Width/Thickness	±0.1 mm	                    For specimen dimensions
Diameter            	±0.05 mm	                For circular cross-sections
Cross-Sectional Area	±0.5% of calculated value	Based on dimensional measurements
Modulus of Elasticity	±1-2% of calculated value	Combined uncertainty from force and strain
Temperature         	±1°C	                    For standard laboratory conditions
Humidity            	±5% RH	                    For standard laboratory conditions


Based on Instrument Resolution, Calibration Uncertainty, Environmental Conditions, Repeatability and Reproducibility:
 assumptions
    - Instrument Resolutin | For load cells, extensometers, and displacement sensors, use the smallest increment the device can measure as the uncertainty.
    - Calibration Uncertainty | Assume a typical calibration uncertainty for well-maintained equipment.
    - Environmental Conditions | Assume standard laboratory conditions unless otherwise specified.
    - Repeatability and Reproducibility | If repeated measurements are not available, assume a reasonable repeatability based on equipment performance.


Propagation of uncertainty
    - partial derivatives of the function with respect to each variable

"""

# turn into a backend class
# provide calculation uncertainty for area, density
# display distribution of uncertainty for density
# refer to Toplevel propperies group  py as an example ( class SamplePropertiesProcessor)
# maybe just combine the two classes and save as backend sample properties processor

"""
std_dev = np.std(measurements, ddof=1)  # ddof=1 for sample standard deviation

# Step 2: Type B uncertainty components
resolution_uncertainty = 0.5 / np.sqrt(3)  # Instrument resolution
calibration_uncertainty = 1.0 / 2          # Calibration uncertainty

# Step 3: Combined uncertainty
combined_uncertainty = np.sqrt(std_dev**2 + resolution_uncertainty**2 + calibration_uncertainty**2)
"""
