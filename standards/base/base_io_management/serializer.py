from collections import namedtuple
from typing import Optional, Union

import pandas as pd
from pathlib import Path

import tempfile
import json
import zipfile

AttributeField = namedtuple('AttributeField', ['attribute_name', 'value', 'unit', 'output_name', 'category'])
# db_colum

class Serializer:
    def __init__(self, tracked_object = None, export_strategy=None):
        self._registry = {
            'attributes': {},  # For storing attributes to be serialized into JSON
            'data': {}         # For storing data to be serialized into CSV
        }
        self.tracked_object = tracked_object
        self.export_strategy = export_strategy or FileOIManager()
          
    def register_list(self, data: list[AttributeField]) -> bool:
        """Register a list of fields for serialization/export."""
        return all(self.register_field(item) for item in data)
        
    def register_field(self, field:Union[AttributeField, tuple], tracked_object: Optional[object]= None) -> bool:
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
        
        if not isinstance(field, AttributeField) and len(field) == 5:
            field = AttributeField(*field)
        else:
            raise TypeError(
                    f"Expected 'AttributeField' or tuple of length 5, but got {type(field).__name__} with length {len(field)}. "
                    "Make sure you're passing a namedtuple 'AttributeField' or a valid tuple."
                )
        
        if not hasattr(self.tracked_object, field.attribute_name):
            raise AttributeError(
                f"'{self.tracked_object.__class__.__name__}' object has no attribute '{field.attribute_name}'. "
                "Ensure the attribute exists on the object being tracked. You passed an invalid field: "
                f"'{field.attribute_name}' is not present on '{self.tracked_object.__class__.__name__}'."
            )
        
        output_name = field.output_name or self._generate_output_name(field.attribute_name, field.unit)

        # If the field is in the 'data' category, store the file path
        if field.category == 'data':
            data_path = f"{field.attribute_name}_data.csv"
            # Register the file path in the 'attributes' registry
            self._registry['attributes'][f"{field.attribute_name}_file_path"] = {
                'value': data_path,
                'unit': None,  # File paths don't have a unit
                'output_name': f"{output_name} File Path",
                'data_type': type(field.value).__name__
            }
                 
        # Store the field in the correct category in the registry
        self._registry[field.category][field.attribute_name] = {
            'value': field.value,
            'unit': field.unit,
            'output_name': output_name,
            'data_type': type(field.value).__name__  
        }
        return bool( [field.category][field.attribute_name] in self._registry)
        
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
    
    
    def export(self,
               export_strategy: Optional["IOStrategy"] = None,
               tracked_object= None, 
               output_dir: Optional[Path] = None,
               database_uri: Optional[str] = None,
               ) -> bool:
        """Export the registered fields using the selected export strategy."""
        strategy = export_strategy or self.export_strategy
        if strategy is None:
            raise ValueError("No export strategy provided or set during initialization.")
        
        tracked_object = tracked_object or self.tracked_object
        if tracked_object is None:
            raise ValueError("No tracked object provided or set during initialization.")
        
        output_dir = output_dir or Path.cwd() / 'exported_data'

        # Call the export method of the chosen strategy
        return strategy.export(tracked_object, self._registry, output_dir=output_dir, database_uri=database_uri)
         
from abc import ABC, abstractmethod

class IOStrategy(ABC):
    """
    Abstract base class for all export strategies.
    """

    @abstractmethod
    def export(self, tracked_object: object, registry, **kwargs) -> bool:
        """
        Export the registered fields.
        """
        pass

    @abstractmethod
    def import_obj(self, id : Optional[int], name: Optional[str],return_class : object, **kwargs) -> object:
        """
        Import an object from the specified source.
        """
        pass
    
    @staticmethod
    def prepare_fields_for_initialization(cls, attributes, data) -> tuple[dict, dict]:
        import inspect
        init_signature = inspect.signature(cls.__init__)
        init_params = init_signature.parameters
        
        if not isinstance(attributes, dict) and not isinstance(data, dict):
            raise TypeError("Cannot prepare fields for initialization. Either Attributes or data must be a dictionary."
                            f"Received: {type(attributes).__name__}, {type(data).__name__} Respectively.")
        
        # Separate core attributes and extra attributes
        core_attributes = {k: v for k, v in {**attributes, **data}.items() if k in init_params}
        extra_attributes = {k: v for k, v in {**attributes, **data}.items() if k not in init_params}
        
        return core_attributes, extra_attributes
    
    @staticmethod
    def filter_and_instantiate( return_class , attributes, data,  allow_dynamic_attributes=False) -> object:
        core_attributes, extra_attributes = IOStrategy.prepare_fields_for_initialization(return_class, attributes, data)
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

class FileOIManager(IOStrategy):    
    # Main Methods Export and Import
    def export(self, tracked_object, registry : dict, output_dir: Path, database_uri) -> bool:
        if registry is None and output_dir is None:
            raise ValueError("Registry and output_dir cannot be None. For exporting to a file, you must provide a registry and output directory.")
        return FileOIManager.export_to_file(registry, output_dir)
    
    def import_obj(self,  return_class : object, input_file : Union[str, Path], **kwargs) -> object:
        file = input_file or [value for key, value in kwargs.items() if "file" in key.lower()][0]
        if isinstance(file, str):
            file = Path(input_file)
        
        if not isinstance(file, Path) or not file.exists():
            raise FileNotFoundError(f"File '{file}' does not exist or is not a valid Path object.")
        
        # Check if it's a zip file
        if file.is_file() and file.suffix == ".zip":
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                self._unzip_file(file, temp_dir_path)
                
                # Unzip if necessary
                if file.suffix == ".zip":
                    self._unzip_file(file, temp_dir_path)
                    json_file = temp_dir_path / "attributes.json"
                elif file.is_dir():
                    json_file = file / "attributes.json"
                else:
                    raise ValueError(f"Input '{file}' should either be a zip file or directory.")
                
                # Load attributes and data from the extracted files
                attributes = self._import_fields(temp_dir_path, json_file)
                
                # Instantiate and return the object using core attributes and data
                return IOStrategy.filter_and_instantiate(return_class, attributes, {})
        else:
            raise ValueError(f"Input '{file}' is not a valid zip file.")
            
    # Export Helpers Methods
    
    @staticmethod
    def export_to_file(registry: dict, output_dir: Path) -> bool:
        """
        Exports registered fields to JSON and CSV files, and then compresses them into a zip file.
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Export attributes to JSON
                json_file_path = FileOIManager._export_attributes_to_json(temp_path, registry['attributes'])

                # Export data to CSV
                csv_export_success = FileOIManager._export_data_to_csv(temp_path, registry['data'])
    
                # Zip the exported files
                zip_file_path = FileOIManager._zip_folder(temp_path, output_dir)

                # Check if the zip file exists
                return bool(zip_file_path.exists())

        except Exception as e:
            print(f"Error during file export: {e}")
            return False
    
    @staticmethod
    def _export_attributes_to_json(temp_path: Path, attributes: dict) -> Path:
        """
        Exports registered attributes to a JSON file.
        """
        # Invert dict key to have the output_name as the key and store the attribute_name as class_name
        formatted_attributes = {}
        
        for class_name, class_attribute in attributes.items():
            output_key = class_attribute.get('output_name', class_name)  # Default to class_name if no output_name
            formatted_attributes[output_key] = {
                'value': class_attribute['value'],
                'class_name': class_name
            }
        
        # Save the formatted attributes to a JSON file
        json_file_path = temp_path / 'attributes.json'
        try:
            with open(json_file_path, 'w') as file:
                json.dump(attributes, file, indent=4)
            return json_file_path
        except Exception as e:
            raise OSError(f"Failed to export attributes to JSON: {e}")

    @staticmethod
    def _export_data_to_csv(temp_path: Path, data: dict) -> bool:
        """
        Exports registered data to CSV files.
        """
        try:
            for attribute_name, details in data.items():
                value = details['value']
                file_name = temp_path / f"{attribute_name}_data.csv"
                column_name = details.get('output_name', attribute_name)

                if isinstance(value, pd.Series):
                    value.name = column_name
                    value.to_csv(file_name, header=True, index=False)
                elif isinstance(value, pd.DataFrame):
                    # Handle DataFrame column renaming if output_name is a list of column names
                    if isinstance(column_name, list) and all(isinstance(name, str) for name in column_name):
                        value = value.copy()
                        value.rename(columns=dict(zip(value.columns, column_name)), inplace=True)
                    value.to_csv(file_name, header=True, index=True)
                else:
                    raise ValueError(f"Unsupported data type for CSV export: {type(value).__name__}")

            return True
        except Exception as e:
            print(f"Error exporting data to CSV: {e}")
            return False

    @staticmethod
    def _zip_folder(temp_path: Path, output_dir: Path) -> Path:
        """
        Create a zip file from the contents of a folder and return the zip file path.
        """
        zip_file_path = output_dir / f"{temp_path.name}.zip"
        try:
            with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)  # Relative path within the zip
                        zipf.write(file_path, arcname)
            return zip_file_path
        except Exception as e:
            raise OSError(f"Failed to zip folder: {e}")

    # Import Helpers Methods
    
    @staticmethod
    def _unzip_file(zip_file_path: Path, output_dir: Path) -> None:
        """
        Unzips the given zip file into the specified output directory.
        """
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
        except Exception as e:
            raise OSError(f"Failed to unzip file {zip_file_path}: {e}")

    @staticmethod
    def _import_fields(directory: Path, json_file: Path) -> dict:
        """
        Reads both attributes (from JSON) and data (from CSV) based on the registry in the JSON file.
        
        Returns:
        - A dictionary with correctly typed attributes and data.
        """
        try:
            # Load attributes and data from the JSON file
            with open(json_file, 'r') as file:
                attributes = json.load(file)
            
            # Loop through attributes and handle both regular attributes and data files
            for attribute_name, details in attributes.items():
                # Check if this attribute refers to a data file (CSV)
                if 'value' in details and isinstance(details['value'], str) and details['value'].endswith('_data.csv'):
                    csv_file_path = directory / details['value']
                    if csv_file_path.exists():
                        # Load the CSV and apply correct type
                        attributes[attribute_name] = pd.read_csv(csv_file_path)
                        
                        # Reassign the correct type for the data (usually Series or DataFrame)
                        attributes[attribute_name] = FileOIManager._reassign_type(
                            attributes[attribute_name], details['data_type'], attribute_name
                        )
                else:
                    # For non-data fields, reassign types if necessary
                    if 'value' in details and 'data_type' in details:
                        attributes[attribute_name]['value'] = FileOIManager._reassign_type(
                            details['value'], details['data_type'], attribute_name
                        )
            
            return attributes
        
        except Exception as e:
            raise OSError(f"Failed to load fields from {json_file}: {e}")
    
    @staticmethod
    def _reassign_type(value, data_type: str, attribute_name: str):
        """
        Reassigns the correct type to an attribute or data field based on its original class.
        
        Parameters:
        - value: The value to reassign a type to.
        - data_type: The string name of the original data type.
        - attribute_name: The name of the attribute for context in error handling.
        
        Returns:
        - The value with the correct type reassigned.
        """
        try:
            if hasattr(__builtins__, data_type):
                return getattr(__builtins__, data_type)(value)
            elif hasattr(pd, data_type):
                # If it's a pandas type (e.g., Series or DataFrame)
                if data_type == "Series":
                    return pd.Series(value)
                elif data_type == "DataFrame":
                    return pd.DataFrame(value)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
        except Exception as e:
            raise ValueError(f"Failed to reassign type for attribute '{attribute_name}': {e}")
    
    
import sqlite3

class DatabaseIOManager(IOStrategy):
    """
    DatabaseIOManager is responsible for exporting and importing AnalyzableEntity instances to and from a SQLite database.

    Design Decision:
    ----------------
    This design uses a unified interface where core attributes are stored as individual columns and extra, 
    version-specific attributes are stored in a JSON-encoded dictionary (extra_attributes). This approach 
    allows flexibility and extensibility for future versions of AnalyzableEntity, while keeping the structure 
    lightweight and simple.

    After considering alternative approaches, such as polymorphic ORM inheritance and raw SQL with a more rigid schema, 
    we opted for a dictionary-based approach for the following reasons:
    - **Simplicity**: The database schema remains simple and doesn't require complex table relationships or migrations.
    - **Extensibility**: Future versions of AnalyzableEntity can add or modify attributes easily without changing the schema.
    - **Flexibility**: Extra attributes are stored in a JSON field, which allows for dynamic data storage and easy retrieval 
      without needing to define strict models.
    - **Low Maintenance**: This approach minimizes ongoing schema changes and allows contributors to extend the functionality 
      without deep knowledge of ORMs or complex database schemas.
    """
    def __init__(self,
                 db_path:str ='mydatabase.db',
                 connection: Optional[sqlite3.Connection] = None,
                 cursor: Optional[sqlite3.Cursor] = None
                 ):
        self.base_path = db_path
        self.connection = connection
        self.cursor = cursor
        

    @staticmethod
    def create_tables(cursor, connection):
        """Create the main tables and output_name_map if they don't exist."""
        # Table for mapping internal attribute names to human-readable output names
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS output_name_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                internal_name TEXT UNIQUE,
                output_name TEXT,
                data_type TEXT 
            )
        ''')

        # Table for core entity attributes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyzable_entities (
                id INTEGER PRIMARY KEY,
                entity_name TEXT,
                attribute_id INTEGER,
                value TEXT,  -- Use TEXT to allow flexibility for different value types (e.g., string, numeric)
                FOREIGN KEY (attribute_id) REFERENCES output_name_map(id)
            )
        ''')

        # Table for data fields (large datasets like pandas DataFrame or Series)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entity_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER,
                column_id INTEGER,
                value TEXT,  -- Store both numeric and JSON data as TEXT
                FOREIGN KEY (entity_id) REFERENCES analyzable_entities(id),
                FOREIGN KEY (column_id) REFERENCES output_name_map(id)
            )
        ''')
        connection.commit()
        
    def export(self, tracked_object: object, registry, output_dir: Optional[Path] = None, database_uri: Optional[str] = None) -> bool:
        db_path = database_uri or self.base_path
        connection = sqlite3.connect(db_path) if self.connection is None else self.connection
        cursor = connection.cursor() if self.cursor is None else self.cursor
        self.create_tables( cursor, connection)
        if database_uri is None:
            raise ValueError("Database URI cannot be None. For exporting to a database, you must provide a valid URI.")
        
        success, message = DatabaseIOManager.export_to_database(cursor, connection,tracked_object,  registry)
        return success
    
    def import_obj(self, return_class , instance_id: Optional[int] = None, instance_name: Optional[str] = "",**kwargs) -> object:
        cursor = kwargs.get('cursor', self.cursor)
        connection = kwargs.get('connection', self.connection)
        
        if instance_id is None and instance_name == "":
            raise ValueError("You must provide either an entity ID or entity name to import from the database.")
        
        if instance_id is not None:
            cursor.execute('SELECT name FROM analyzable_entities WHERE id=?', (instance_id,))
            instance_name = cursor.fetchone()
            if not instance_name:
                raise ValueError(f"No entity found with ID {instance_id}.")
            instance_name = instance_name[0]
            
        if not instance_name:
            raise ValueError("No entity name provided for import.")
        
        attributes = DatabaseIOManager._import_attributes_from_database(cursor, instance_name)
        data = DatabaseIOManager._import_data_from_database(cursor, instance_name)
        return IOStrategy.filter_and_instantiate(return_class, attributes, data)
    
    @staticmethod
    def export_to_database(cursor, connection,tracked_object,  registry):
        """
        Export registered fields to a SQLite database.
        """
        try:
            # Export core attributes
            attributes_count = DatabaseIOManager._export_attributes(cursor, connection,tracked_object, registry['attributes'])

            # Export data (complex objects like Series/DataFrame)
            data_count = DatabaseIOManager._export_data(cursor, connection,tracked_object, registry['data'])

            return True, f"{attributes_count} attributes and {data_count} data fields exported."
        except Exception as e:
            print(f"Error exporting entity '{tracked_object}': {e}")
            return False, None
    
    @staticmethod
    def _export_attributes(cursor,connection, tracked_object: object, attributes: dict[str,dict]) -> bool:
        """Export core attributes and store extra attributes using the output_name_map."""
        # Will need to remove all attributes with value as has a file path | Side effect from the FileOIManager
        entity_name = tracked_object.name if hasattr(tracked_object, 'name') else tracked_object.__class__.__name__
        
        db_attributes = DatabaseIOManager._filter_attributes_for_database(attributes)
        for attribute_name, details in db_attributes.items():
            if details['value'] is not None and isinstance(details['value'], str) and details['value'].endswith('_data.csv'):
                    del  db_attributes[attribute_name]
            
            # invert the dictionary to have the output_name as the key and store the attribute_name as class_name        
            output_name = details.get('output_name', attribute_name)
            attribute_value = details['value']
            data_type = type(attribute_value).__name__
            
            # Get or create the mapping ID for this attribute
            attribute_id = DatabaseIOManager._get_or_create_output_name_id(cursor, connection, attribute_name, output_name, data_type)
                            
            # Insert the attribute value into the analyzable_entities table
            cursor.execute('''
                INSERT INTO analyzable_entities (entity_name, attribute_id, value)
                VALUES (?, ?, ?)
            ''', (entity_name, attribute_id, attribute_value))
        
        connection.commit()
        
        return True
    
    @staticmethod
    def _export_data(cursor, connection, tracked_object, data:  dict[str,dict]) -> bool:
        """Export complex data like pandas Series or DataFrame using the output_name_map."""
        entity_id = cursor.lastrowid  # Get the last inserted entity ID
        for data_name, data_details in data.items():
            value = data_details['value']
            output_name = data_details.get('output_name', data_name)
            data_type = type(value).__name__

            # Get or create the mapping ID for this data field
            column_id = DatabaseIOManager._get_or_create_output_name_id(cursor, connection, data_name, output_name, data_type)

            if isinstance(value, pd.Series):
                series_data = {
                    "name": value.name,     # Store the Series name
                    "data": value.tolist()  # Store the data as a list
                }
                json_value = json.dumps(series_data)  # Convert to JSO

            if isinstance(value, pd.DataFrame):
                # Convert DataFrame into a list of tuples (entity_id, column_id, value)
                json_value = value.to_json(orient='records')  # Convert DataFrame to JSON
                
            cursor.execute('''
                INSERT INTO entity_data (entity_id, column_id, value)
                VALUES (?, ?, ?)
            ''', (entity_id, column_id, json_value))
            
        connection.commit()
        return True
        
        
    @staticmethod
    def _filter_attributes_for_database(attributes: dict) -> dict:
        """Remove attributes that should not be exported to the database, like file paths."""
        filtered_attributes = {}
        for attribute_name, details in attributes.items():
            if (isinstance(details['value'], str) and details['value'].endswith('_data.csv')):
                continue
            filtered_attributes[attribute_name] = details
        return filtered_attributes
    
    @staticmethod
    def _get_or_create_output_name_id(cursor, connection, internal_name: str, output_name: str, data_type) -> int:
        """Get the ID of the output_name in the map, or create it if it doesn't exist."""
        cursor.execute('SELECT id FROM output_name_map WHERE internal_name=?', (internal_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]  # Return the ID if it exists
        else:
            # Insert the mapping into the output_name_map and return the new ID
            cursor.execute('INSERT INTO output_name_map (internal_name, output_name, data_type) VALUES (?, ?, ?)',
                           (internal_name, output_name, data_type))
            connection.commit()
            return cursor.lastrowid
    
    @staticmethod
    def _import_attributes_from_database( cursor,  entity_name: str) -> dict:
        cursor.execute('''
            SELECT output_name_map.output_name, analyzable_entities.value, output_name_map.data_type
            FROM analyzable_entities
            JOIN output_name_map ON analyzable_entities.attribute_id = output_name_map.id
            WHERE analyzable_entities.entity_name = ?
        ''', (entity_name,))
        rows = cursor.fetchall()

        attributes = {}
        for output_name, value, data_type in rows:
            # Restore values based on their stored type
            attributes[output_name] = DatabaseIOManager._reasign_type(value, data_type, output_name)
        return attributes
    
    @staticmethod
    def _import_data_from_database(cursor, entity_name: str) -> dict:
        cursor.execute('''
            SELECT output_name_map.output_name, entity_data.value, output_name_map.data_type
            FROM entity_data
            JOIN output_name_map ON entity_data.column_id = output_name_map.id
            JOIN analyzable_entities ON entity_data.entity_id = analyzable_entities.id
            WHERE analyzable_entities.entity_name = ?
        ''', (entity_name,))
        data_rows = cursor.fetchall()

        data = {}
        for output_name, value, data_type in data_rows:
            # Restore values based on their stored type
            data[output_name] = DatabaseIOManager._reasign_type(value, data_type, output_name)
        return data
    
    @staticmethod
    def _reasign_type(value, data_type, output_name):
        
        if data_type == "Series":
            series_data = json.loads(value)  # Load the JSON-encoded Series
            return pd.Series(series_data["data"], name=series_data["name"])  # Restore Series with its name

        elif data_type == "DataFrame":
            return pd.read_json(value)  # Restore DataFrame from JSON
           
        if hasattr(__builtins__, data_type):
            return eval(f'{data_type}({repr(value)})')
        else:
            raise ValueError(f"Unsupported data type: {data_type} for attribute {output_name}")
    