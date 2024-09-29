import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from standards.base.properties_calculators.base_standard_operator import BaseStandardOperator

# Example of usage with mock data
data = np.array([0, 1, 0, 2, 0, 1, 0, 3, 0, 1, 0, 4, 0])
peak_result = BaseStandardOperator.peak_finder(data, expected_peaks=2)
print(f"Peak Result: {peak_result}")


## plot the data and the peaks
fig_size = (10, 6)
fig, ax = plt.subplots(figsize=fig_size)
ax.plot(data, label='Data')
ax.scatter(peak_result.indices, peak_result.values, color='red', label='Peaks')
ax.set_xlabel('Index')
ax.set_ylabel('Value')
ax.set_title('Data with Peaks')
ax.legend()
plt.show()


