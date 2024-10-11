class Benchmark:
    def __init__(self, benchmarks: dict, properties_to_check: Optional[list] = None):
        self.benchmarks = benchmarks
        self.properties_to_check = properties_to_check or benchmarks.keys()
        
    def add_benchmark_property(self, property_name: str, target: float, tolerance: float):
        self.benchmarks[property_name] = (target, tolerance)
        self.properties_to_check.append(property_name)
        
    def add_benchmark_series(self, property_name: str, target: Union[np.ndarray, pd.Series], tolerance: Union[float, np.ndarray, pd.Series]):
        self.benchmarks[property_name] = (target, tolerance)
        self.properties_to_check.append(property_name)
    
    def check_sample(self, sample):  
        report = {}
        for prop, (target, tolerance) in self.benchmarks.items():
            if prop in self.properties_to_check:
                sample_value = getattr(sample, prop, None)
                if sample_value is not None:
                    if abs(sample_value - target) <= tolerance:
                        report[prop] = (True, 0)  # Passes the benchmark
                    else:
                        deviation = sample_value - target
                        report[prop] = (False, deviation)  # Fails, with deviation
                else:
                    report[prop] = (False, "Property not found in sample")

        return report