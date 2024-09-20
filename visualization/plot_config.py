from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Union

# import yaml


@dataclass
class PlotConfig:
    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    figsize: tuple[float, float] = (12, 8)
    line_style: str = "-"
    color: Optional[str] = None
    alpha: float = 1.0
    grid: bool = True
    show_origin: bool = False
    x_percent: bool = False  # Format x-axis as percentage
    x_rotation: Optional[float] = None  # Rotation angle for x-axis tick labels
    x_minor_locator: Optional[int] = None  # Number of minor ticks between major ticks on x-axis
    y_minor_locator: Optional[int] = None  # Number of minor ticks between major ticks on y-axis
    legend_position: str = "best"  # Default legend position
    # Additional parameters can be added as needed
    ncols: int = 1  # Number of columns for subplots
    nrows: int = 1  # Number of rows for subplots

    def to_dict(self) -> dict[str, any]:
        """
        Converts the PlotConfig to a dictionary.
        """
        return asdict(self)

    def __str__(self) -> str:
        return str(self.to_dict())

    @staticmethod
    def _normalize_path(path: Union[str, Path]) -> Path:
        if isinstance(path, str):
            return Path(path)
        else:
            raise ValueError("Invalid path type. Must be a string or Path object.")

    @classmethod
    def from_dict(cls, config_dict: dict[str, any]):
        """
        Creates a PlotConfig instance from a dictionary.
        """
        return cls(**config_dict)

    def to_yaml(self, file_path: Union[str, Path]) -> None:
        """
        Saves the PlotConfig to a YAML file.
        """
        file_path = self._normalize_path(file_path)
        with open(file_path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)

    @classmethod
    def from_yaml(cls, file_path: Union[str, Path]):
        """
        Loads the PlotConfig from a YAML file.
        """
        file_path = cls._normalize_path(file_path)

        with open(file_path, "r") as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)
