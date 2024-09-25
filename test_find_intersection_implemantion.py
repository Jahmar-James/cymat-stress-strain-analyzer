import time

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import root_scalar
from shapely.geometry import GeometryCollection, LineString, MultiLineString, MultiPoint, Point

# Generate synthetic test data
np.random.seed(0)
x = np.linspace(0, 10, 7000)
y1 = np.sin(x) + 0.1 * np.random.normal(size=len(x))  # Curve 1: Sinusoidal with noise
y2 = np.cos(x) + 0.1 * np.random.normal(size=len(x))  # Curve 2: Cosinusoidal with noise


# Define numpy-based intersection function
def find_intersections_numpy(x1, y1, x2, y2, tolerance=1e-6):
    y_diff = y1 - y2
    sign_changes = np.where(np.diff(np.sign(y_diff)))[0]
    intersections = []
    for idx in sign_changes:
        x_intersect = (x1[idx] * y_diff[idx + 1] - x1[idx + 1] * y_diff[idx]) / (y_diff[idx + 1] - y_diff[idx])
        y_intersect = (y1[idx] + y1[idx + 1]) / 2
        intersections.append((x_intersect, y_intersect))
    return intersections


# Define scipy-based intersection function
def find_intersections_scipy(x1, y1, x2, y2, method="linear", tolerance=1e-6):
    interp1 = interp1d(x1, y1, kind=method, fill_value="extrapolate")
    interp2 = interp1d(x2, y2, kind=method, fill_value="extrapolate")

    def difference(x):
        return interp1(x) - interp2(x)

    intersections = []
    for i in range(1, len(x1)):
        if (difference(x1[i - 1]) * difference(x1[i])) <= 0:
            result = root_scalar(difference, bracket=[x1[i - 1], x1[i]], method="brentq", xtol=tolerance)
            if result.converged:
                x_intersect = result.root
                y_intersect = interp1(x_intersect)
                intersections.append((x_intersect, y_intersect))
    return intersections


# Define shapely-based intersection function
def find_intersections_shapely(x1, y1, x2, y2):
    # Create LineString objects for both curves
    line1 = LineString(np.column_stack((x1, y1)))
    line2 = LineString(np.column_stack((x2, y2)))

    # Find intersection points
    intersection = line1.intersection(line2)

    # Initialize an empty list to store the intersection points
    intersections = []

    # Handle different types of intersection geometries
    if isinstance(intersection, Point):
        # Single intersection point
        intersections.append((intersection.x, intersection.y))
    elif isinstance(intersection, MultiPoint):
        # Multiple intersection points
        for point in intersection.geoms:
            intersections.append((point.x, point.y))
    elif isinstance(intersection, MultiLineString) or isinstance(intersection, GeometryCollection):
        # For MultiLineString or GeometryCollection, extract points
        for geom in intersection.geoms:
            if isinstance(geom, Point):
                intersections.append((geom.x, geom.y))
            elif isinstance(geom, LineString):
                # Get all points on the LineString
                intersections.extend([(pt.x, pt.y) for pt in geom.coords])
    else:
        print(f"Unhandled intersection type: {type(intersection)}")

    return intersections


if __name__ == "__main__":
    # Number of iterations for averaging
    iterations = 30

    # Containers to store execution times
    numpy_times = []
    scipy_times = []
    shapely_times = []

    # Run each method 30 times and record the time taken
    for _ in range(iterations):
        # Test and time numpy implementation
        start_time = time.time()
        numpy_intersections = find_intersections_numpy(x, y1, x, y2)
        numpy_times.append(time.time() - start_time)

        # Test and time scipy implementation
        start_time = time.time()
        scipy_intersections = find_intersections_scipy(x, y1, x, y2)
        scipy_times.append(time.time() - start_time)

        # Test and time shapely implementation
        start_time = time.time()
        shapely_intersections = find_intersections_shapely(x, y1, x, y2)
        shapely_times.append(time.time() - start_time)

    # Test and time shapely implementation
    results = {
        "Numpy": {"mean": np.mean(numpy_times), "std": np.std(numpy_times)},
        "Scipy": {"mean": np.mean(scipy_times), "std": np.std(scipy_times)},
        "Shapely": {"mean": np.mean(shapely_times), "std": np.std(shapely_times)},
    }

    # Print results
    print(f"Numpy implementation time: {results['Numpy']['mean']:.8f} seconds", f"± {results['Numpy']['std']:.8f}")
    print(f"Scipy implementation time: {results['Scipy']['mean']:.8f} seconds", f"± {results['Scipy']['std']:.8f}")
    print(
        f"Shapely implementation time: {results['Shapely']['mean']:.8f} seconds", f"± {results['Shapely']['std']:.8f}"
    )
    print(f"Number of intersections found by numpy: {len(numpy_intersections)}")
    print(f"Number of intersections found by scipy: {len(scipy_intersections)}")
    print(f"Number of intersections found by shapely: {len(shapely_intersections)}")

    # Plot the intersection points
    plt.plot(x, y1, label="Curve 1", alpha=0.5, color="blue", linestyle="dashed")
    plt.plot(x, y2, label="Curve 2", alpha=0.5, color="orange", linestyle="dashed")
    for x_int, y_int in numpy_intersections:
        plt.scatter(
            x_int,
            y_int,
            color="red",
            alpha=0.5,
        )
    for x_int, y_int in scipy_intersections:
        plt.scatter(x_int, y_int, color="green", alpha=0.5)
    for x_int, y_int in shapely_intersections:
        plt.scatter(
            x_int,
            y_int,
            color="purple",
            alpha=0.5,
        )

    plt.legend()
    plt.title("Intersection Points Found by Numpy, Scipy, and Shapely")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.show()
