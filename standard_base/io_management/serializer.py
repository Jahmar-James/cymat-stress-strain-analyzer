import enum
from collections import namedtuple
from pathlib import Path
from typing import Optional, Union

import pint

AttributeField = namedtuple("AttributeField", ["attribute_name", "value", "unit", "output_name", "category"])


class Serializer:
    def __init__(self, tracked_object=None, export_strategy=None):
        self._registry = {
            "attributes": {},  # For storing attributes to be serialized into JSON
            "data": {},  # For storing data to be serialized into CSV
            "children": {},  # For storing child objects to be serialized into separate JSON files
        }
        self.tracked_object = tracked_object
        # Import here to avoid circular imports | for now as IOStrategy is here
        from standard_base.io_management.flle_io_manager import FileIOManager

        self.export_strategy = export_strategy or FileIOManager()

    def __repr__(self) -> str:
        return f"Serializer(tracked_object={self.tracked_object}, export_strategy={self.export_strategy})"

    def register_list(self, data: list[AttributeField]) -> bool:
        """Register a list of fields for serialization/export."""
        return all(self.register_field(item) for item in data)

    def register_field(self, field: Union[AttributeField, tuple], tracked_object: Optional[object] = None) -> bool:
        """
        Register a single field, ensuring that the attribute exists on the tracked object.
        """
        if tracked_object:
            self.tracked_object = tracked_object

        if self.tracked_object is None:
            raise ValueError(
                "Cannot register field because the tracked object is not set. "
                "Make sure to pass a valid object to the Serializer."
            )

        if isinstance(field, AttributeField):
            pass
        elif isinstance(field, tuple) and len(field) == len(AttributeField._fields):
            field = AttributeField(*field)
        else:
            raise TypeError(
                f"Expected 'AttributeField' or tuple of length 5, but got {type(field).__name__} with length {len(field)}."
                "Make sure you're passing a namedtuple 'AttributeField' or a valid tuple."
            )

        if not hasattr(self.tracked_object, field.attribute_name):
            raise AttributeError(
                f"'{self.tracked_object.__class__.__name__}' object has no attribute '{field.attribute_name}'. "
                "Ensure the attribute exists on the object being tracked. You passed an invalid field: "
                f"'{field.attribute_name}' is not present on '{self.tracked_object.__class__.__name__}'."
            )

        output_name = field.output_name or self._generate_output_name(field.attribute_name, field.unit)

        self._registry[field.category][field.attribute_name] = {
            "value": field.value,
            "unit": field.unit,
            "output_name": output_name,
        }

        return bool(field.attribute_name in self._registry.get(field.category, {}))
        
    def register_exportable_properties(self, tracked_object: Optional[object] = None) -> None:
        """Automatically register all properties marked as exportable."""
        if self.tracked_object is None:
            raise ValueError("Tracked object is not set.")
        
        for attr_name in dir(self.tracked_object):
            attr = getattr(self.tracked_object.__class__, attr_name, None)
            if isinstance(attr, property) and getattr(attr.fget, '_is_exportable', False):
                value = getattr(self.tracked_object, attr_name)
                metadata = attr.fget._export_metadata
                field = AttributeField(
                    attribute_name=attr_name,
                    value=value,
                    unit=metadata['unit'],
                    output_name=metadata['output_name'],
                    category=metadata['category']
                )
                self.register_field(field, tracked_object = tracked_object)
                
    def register_all_public_attributes(self, blacklist: Optional[list[str]] = None) -> None:
        """Automatically register all attributes that don't start with '_'."""
        if self.tracked_object is None:
            raise ValueError("Tracked object is not set.")
        
        for attr_name, attr_value in self.tracked_object.__dict__.items():
            if not attr_name.startswith("_") and attr_name not in (blacklist or []):
                field = AttributeField(
                    attribute_name=attr_name,
                    value=attr_value,
                    unit=None,
                    output_name=None,
                    category='attributes'
                )
                self.register_field(field)
    
    @staticmethod
    def _generate_output_name(name: str, unit: Optional[str]) -> str:
        """Generate a standardized output name, appending unit if provided."""
        return f'{name} ({unit})' if unit else name

    def export(
        self,
        export_strategy: Optional["IOStrategy"] = None,
        tracked_object=None,
        output_path: Optional[Path] = None,
        database_uri: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """Export the registered fields using the selected export strategy."""
        strategy = export_strategy or self.export_strategy
        if strategy is None:
            raise ValueError("No export strategy provided or set during initialization.")

        tracked_object = tracked_object or self.tracked_object
        if tracked_object is None:
            raise ValueError("No tracked object provided or set during initialization.")

        self.register_exportable_properties(tracked_object)

        registry = strategy.format_registry_to_strategy(self._registry, strategy)

        return strategy.export(tracked_object, registry, output_path=output_path, database_uri=database_uri)
         
from abc import ABC, abstractmethod


class IOStrategy(ABC):
    """
    Abstract base class for all export strategies.
    """

    STRATEGY_NAME = "Base"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} Strategy for {self.STRATEGY_NAME}"

    @abstractmethod
    def export(self, tracked_object: object, registry, **kwargs) -> bool:
        """
        Export the registered fields.
        """
        pass

    @abstractmethod
    def import_obj(self, id: Optional[int], name: Optional[str], return_class: object, **kwargs) -> object:
        """
        Import an object from the specified source.
        """
        pass

    @staticmethod
    def format_registry_to_strategy(registry, io_stratgey: "IOStrategy") -> dict:
        """
        Format the registry for the given field.
        """
        registry = registry.copy()
        for category, fields in registry.items():
            # Category are attributes, data, children
            for attribute_name, field_details in fields.items():
                registry = io_stratgey.format_registry_field(category, attribute_name, field_details, registry)

                value = field_details.get("value")
                data_type = type(value).__name__

                #  TODO: Move conversion to a separate method
                value, data_type, unit, output_name = convert_attribute_field_to_serializable(
                    value=value,
                    data_type=data_type,
                    unit=field_details.get("unit", None),
                    output_name=field_details.get("output_name", None),
                )

                # Store the field in the correct category in the registry
                registry[category][attribute_name].update(
                    {
                        "value": value,
                        "unit": unit,
                        "output_name": output_name,
                        "data_type": data_type,
                    },
                )

        return registry

    @staticmethod
    @abstractmethod
    def format_registry_field(category, attribute_name, field_details, registry) -> dict:
        """
        Format the registry for the given field.
        """
        pass

    @staticmethod
    def prepare_fields_for_initialization(cls, attributes, data) -> tuple[dict, dict]:
        import inspect

        init_signature = inspect.signature(cls.__init__)
        init_params = init_signature.parameters

        if not isinstance(attributes, dict) and not isinstance(data, dict):
            raise TypeError(
                "Cannot prepare fields for initialization. Either Attributes or data must be a dictionary."
                f"Received: {type(attributes).__name__}, {type(data).__name__} Respectively."
            )

        # Separate core attributes and extra attributes
        core_attributes = {k: v for k, v in {**attributes, **data}.items() if k in init_params}
        extra_attributes = {k: v for k, v in {**attributes, **data}.items() if k not in init_params}

        return core_attributes, extra_attributes

    @staticmethod
    def get_mechanical_test_standard(return_class, extra_attributes) -> object:
        if "analysis_standard" in extra_attributes and extra_attributes["analysis_standard"] is not None:
            # Impotant property but not required for initialization - to simplify class initialization
            # use the standard if not none to determine the class to be initialized
            from standard_base import MechanicalTestStandards
            from standard_base.sample_factory import standard_registry

            sample_standard = standard_registry.get(MechanicalTestStandards(extra_attributes["analysis_standard"]))
            if sample_standard is not None:
                return_class = sample_standard
            else:
                print(
                    f"Warning: Standard not found in the registry for {extra_attributes['analysis_standard']}",
                    "Using the provided class for initialization.",
                )
        return return_class

    @staticmethod
    def filter_and_instantiate(
        return_class,
        attributes,
        data,
        allow_dynamic_attributes=True,
        ignore_class_standard=False,
        ignore_class_validation=False,
        ignore_children=False,
    ) -> object:
        core_attributes, extra_attributes = IOStrategy.prepare_fields_for_initialization(return_class, attributes, data)

        if ignore_class_standard is False:
            return_class = IOStrategy.get_mechanical_test_standard(return_class, extra_attributes)

        if ignore_children is False and "children" in extra_attributes:
            # Check for children and instantiate them
            children = extra_attributes.pop("children")
            # Find the attribute name for the children
            attr_containing_children_names = [
                attr_name
                for attr_name, attr_value in extra_attributes.items()
                if isinstance(attr_value, list) and attr_name.endswith("_children")
            ]

            # For each attribute containing children, instantiate the all the children for that attribute
            for attr_name in attr_containing_children_names:
                extra_attributes[attr_name] = []  # Clear the list
                attr_name = attr_name.replace("_children", "")
                for child_name, child_data in children.items():
                    if child_name.endswith(attr_name):
                        # assume the same return class  as the parent class
                        core_child_attributes, extra_child_attributes = IOStrategy.prepare_fields_for_initialization(
                            return_class, child_data, {}
                        )
                        child_class = IOStrategy.get_mechanical_test_standard(return_class, extra_child_attributes)
                        child_instance = IOStrategy.filter_and_instantiate(
                            return_class=child_class,
                            attributes=core_child_attributes,
                            data={},
                            allow_dynamic_attributes=allow_dynamic_attributes,
                            ignore_children=True,
                        )
                        extra_attributes[attr_name].append(child_instance)
        try:
            # Instantiate the class with core attributes
            instance = return_class(**core_attributes)
        except TypeError as e:
            raise ValueError(f"Error initializing class {return_class.__name__}: {e}")

        if allow_dynamic_attributes:
            for attr_name, attr_value in extra_attributes.items():
                setattr(instance, attr_name, attr_value)
        else:
            if extra_attributes:
                print(f"Warning: Ignored extra attributes {extra_attributes}")

        return instance


def convert_attribute_field_to_serializable(
    value,
    data_type,
    unit,
    output_name,
) -> tuple:
    """
    Convert an attribute field to a serializable format.
    """
    # Convert Enum values to their serialized format -> string representation
    if isinstance(value, enum.Enum):
        value = value.value
        data_type = f"{type(value).__name__}_enum"
    else:
        data_type = type(value).__name__
    # Convert Pint unit quantities to their serialized format -> string representation
    if isinstance(value, pint.Quantity):
        value = value.magnitude
        unit = str(value.units)
        data_type = f"{type(value).__name__}_quantity"
    if isinstance(unit, pint.Unit):
        unit = str(unit)
    return value, data_type, unit, output_name