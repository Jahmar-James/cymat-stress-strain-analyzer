# app/data_layer/IO/PoI.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Callable, Optional

class PointsOfInterest(ABC):
    def __init__(self, data: Any, config: Dict = None):
        """
        Initialize the PointsOfInterest object with specimen data and optional configuration.
        
        :param data: The raw specimen data
        :param config: Optional configuration settings
        """
        self.data = data
        self.config = config if config is not None else {}
        self.points = {}  # To store the points of interest

    @abstractmethod
    def find_points(self, algorithm: Optional[Callable] = None) -> Dict:
        """
        Implement a method that takes an algorithm to find points of interest in the data.
        
        :param algorithm: The algorithm used to find points of interest
        :return: Dictionary containing points of interest
        """
        pass

    def get_point(self, point_name: str) -> Any:
        """
        Retrieve a specific point of interest by name.
        
        :param point_name: The name of the point of interest to retrieve
        :return: The point of interest
        """
        return self.points.get(point_name, None)

    def get_all_points(self) -> Dict:
        """
        Retrieve all points of interest.
        
        :return: All points of interest as a dictionary
        """
        return self.points
    
    def find_interaction_point(plot1, plot2, min_dist_from_origin=0.001, max_attempts=3):
        """ 
        Find the intersection point between two plots. 

        :return: intersection point value as tuple (x,y) and add to points_of_interest points dictionary
        
        """
        pass


class YoungModulusPointsOfInterest(PointsOfInterest):
    def find_points(self, start_algorithm: Optional[Callable] = None, end_algorithm: Optional[Callable] = None) -> Dict:
        """
        Find and store points of interest specific to Young's Modulus calculations.
        
        :param start_algorithm: The algorithm used to find the start index along strain
        :param end_algorithm: The algorithm used to find the end index along strain
        :return: Dictionary containing points of interest
        """
        start_algorithm = start_algorithm or self._start_algorithm_default
        end_algorithm = end_algorithm or self._end_algorithm_default

        self.points['start_idx_along_strain'] = start_algorithm(self.data, self.config.get('start_params', {}))
        self.points['end_idx_along_strain'] = end_algorithm(self.data, self.config.get('end_params', {}))

        return self.points
    
    def _start_algorithm_default(self, data, params):
        """
        Default algorithm for finding the start index along strain.
        
        :param data: The raw specimen data
        :param params: Optional configuration settings
        :return: Start index along strain
        """
        # Your default algorithm here
        return start_idx

    def _end_algorithm_default(self, data, params):
        """
        Default algorithm for finding the end index along strain.
        
        :param data: The raw specimen data
        :param params: Optional configuration settings
        :return: End index along strain
        """
        # Your default algorithm here
        return end_idx
    
class ZeroPointsOfInterest(PointsOfInterest):
    def find_points(self, algorithm: Optional[Callable] = None) -> Dict:
        """
        Find and store points of interest specific to zeroing the data.
        
        :param algorithm: The algorithm used to find the intercept
        :return: Dictionary containing points of interest
        """
        algorithm = algorithm or self._algorithm_default

        self.points['intercept'] = algorithm(self.data, self.config.get('params', {}))

        return self.points

    def _algorithm_default(self, data, params):
        """
        Default algorithm for finding the intercept.
        
        :param data: The raw specimen data
        :param params: Optional configuration settings
        :return: Intercept
        """
        # Your default algorithm here
        return intercept
