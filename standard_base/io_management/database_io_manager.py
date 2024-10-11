import json
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

from standard_base.io_management.serializer import IOStrategy


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

    def __init__(
        self,
        db_path: str = "mydatabase.db",
        connection: Optional[sqlite3.Connection] = None,
        cursor: Optional[sqlite3.Cursor] = None,
    ):
        self.base_path = db_path
        self.connection = connection
        self.cursor = cursor

    @staticmethod
    def create_tables(cursor, connection):
        """Create the main tables and output_name_map if they don't exist."""
        # Table for mapping internal attribute names to human-readable output names
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS output_name_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                internal_name TEXT UNIQUE,
                output_name TEXT,
                data_type TEXT 
            )
        """)

        # Table for core entity attributes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyzable_entities (
                id INTEGER PRIMARY KEY,
                entity_name TEXT,
                attribute_id INTEGER,
                value TEXT,  -- Use TEXT to allow flexibility for different value types (e.g., string, numeric)
                FOREIGN KEY (attribute_id) REFERENCES output_name_map(id)
            )
        """)

        # Table for data fields (large datasets like pandas DataFrame or Series)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER,
                column_id INTEGER,
                value TEXT,  -- Store both numeric and JSON data as TEXT
                FOREIGN KEY (entity_id) REFERENCES analyzable_entities(id),
                FOREIGN KEY (column_id) REFERENCES output_name_map(id)
            )
        """)
        connection.commit()

    def export(
        self, tracked_object: object, registry, output_dir: Optional[Path] = None, database_uri: Optional[str] = None
    ) -> bool:
        db_path = database_uri or self.base_path
        connection = sqlite3.connect(db_path) if self.connection is None else self.connection
        cursor = connection.cursor() if self.cursor is None else self.cursor
        self.create_tables(cursor, connection)
        if database_uri is None:
            raise ValueError("Database URI cannot be None. For exporting to a database, you must provide a valid URI.")

        success, message = DatabaseIOManager.export_to_database(cursor, connection, tracked_object, registry)
        return success

    def import_obj(
        self, return_class, instance_id: Optional[int] = None, instance_name: Optional[str] = "", **kwargs
    ) -> object:
        cursor = kwargs.get("cursor", self.cursor)
        connection = kwargs.get("connection", self.connection)

        if instance_id is None and instance_name == "":
            raise ValueError("You must provide either an entity ID or entity name to import from the database.")

        if instance_id is not None:
            cursor.execute("SELECT name FROM analyzable_entities WHERE id=?", (instance_id,))
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
    def export_to_database(cursor, connection, tracked_object, registry):
        """
        Export registered fields to a SQLite database.
        """
        try:
            # Export core attributes
            attributes_count = DatabaseIOManager._export_attributes(
                cursor, connection, tracked_object, registry["attributes"]
            )

            # Export data (complex objects like Series/DataFrame)
            data_count = DatabaseIOManager._export_data(cursor, connection, tracked_object, registry["data"])

            return True, f"{attributes_count} attributes and {data_count} data fields exported."
        except Exception as e:
            print(f"Error exporting entity '{tracked_object}': {e}")
            return False, None

    @staticmethod
    def _export_attributes(cursor, connection, tracked_object: object, attributes: dict[str, dict]) -> bool:
        """Export core attributes and store extra attributes using the output_name_map."""
        # Will need to remove all attributes with value as has a file path | Side effect from the FileOIManager
        entity_name = tracked_object.name if hasattr(tracked_object, "name") else tracked_object.__class__.__name__

        db_attributes = DatabaseIOManager._filter_attributes_for_database(attributes)
        for attribute_name, details in db_attributes.items():
            if (
                details["value"] is not None
                and isinstance(details["value"], str)
                and details["value"].endswith("_data.csv")
            ):
                del db_attributes[attribute_name]

            # invert the dictionary to have the output_name as the key and store the attribute_name as class_name
            output_name = details.get("output_name", attribute_name)
            attribute_value = details["value"]
            data_type = type(attribute_value).__name__

            # Get or create the mapping ID for this attribute
            attribute_id = DatabaseIOManager._get_or_create_output_name_id(
                cursor, connection, attribute_name, output_name, data_type
            )

            # Insert the attribute value into the analyzable_entities table
            cursor.execute(
                """
                INSERT INTO analyzable_entities (entity_name, attribute_id, value)
                VALUES (?, ?, ?)
            """,
                (entity_name, attribute_id, attribute_value),
            )

        connection.commit()

        return True

    @staticmethod
    def _export_data(cursor, connection, tracked_object, data: dict[str, dict]) -> bool:
        """Export complex data like pandas Series or DataFrame using the output_name_map."""
        entity_id = cursor.lastrowid  # Get the last inserted entity ID
        for data_name, data_details in data.items():
            value = data_details["value"]
            output_name = data_details.get("output_name", data_name)
            data_type = type(value).__name__

            # Get or create the mapping ID for this data field
            column_id = DatabaseIOManager._get_or_create_output_name_id(
                cursor, connection, data_name, output_name, data_type
            )

            if isinstance(value, pd.Series):
                series_data = {
                    "name": value.name,  # Store the Series name
                    "data": value.tolist(),  # Store the data as a list
                }
                json_value = json.dumps(series_data)  # Convert to JSO

            if isinstance(value, pd.DataFrame):
                # Convert DataFrame into a list of tuples (entity_id, column_id, value)
                json_value = value.to_json(orient="records")  # Convert DataFrame to JSON

            cursor.execute(
                """
                INSERT INTO entity_data (entity_id, column_id, value)
                VALUES (?, ?, ?)
            """,
                (entity_id, column_id, json_value),
            )

        connection.commit()
        return True

    @staticmethod
    def _filter_attributes_for_database(attributes: dict) -> dict:
        """Remove attributes that should not be exported to the database, like file paths."""
        filtered_attributes = {}
        for attribute_name, details in attributes.items():
            if isinstance(details["value"], str) and details["value"].endswith("_data.csv"):
                continue
            filtered_attributes[attribute_name] = details
        return filtered_attributes

    @staticmethod
    def _get_or_create_output_name_id(cursor, connection, internal_name: str, output_name: str, data_type) -> int:
        """Get the ID of the output_name in the map, or create it if it doesn't exist."""
        cursor.execute("SELECT id FROM output_name_map WHERE internal_name=?", (internal_name,))
        result = cursor.fetchone()

        if result:
            return result[0]  # Return the ID if it exists
        else:
            # Insert the mapping into the output_name_map and return the new ID
            cursor.execute(
                "INSERT INTO output_name_map (internal_name, output_name, data_type) VALUES (?, ?, ?)",
                (internal_name, output_name, data_type),
            )
            connection.commit()
            return cursor.lastrowid

    @staticmethod
    def _import_attributes_from_database(cursor, entity_name: str) -> dict:
        cursor.execute(
            """
            SELECT output_name_map.output_name, analyzable_entities.value, output_name_map.data_type
            FROM analyzable_entities
            JOIN output_name_map ON analyzable_entities.attribute_id = output_name_map.id
            WHERE analyzable_entities.entity_name = ?
        """,
            (entity_name,),
        )
        rows = cursor.fetchall()

        attributes = {}
        for output_name, value, data_type in rows:
            # Restore values based on their stored type
            attributes[output_name] = DatabaseIOManager._reasign_type(value, data_type, output_name)
        return attributes

    @staticmethod
    def _import_data_from_database(cursor, entity_name: str) -> dict:
        cursor.execute(
            """
            SELECT output_name_map.output_name, entity_data.value, output_name_map.data_type
            FROM entity_data
            JOIN output_name_map ON entity_data.column_id = output_name_map.id
            JOIN analyzable_entities ON entity_data.entity_id = analyzable_entities.id
            WHERE analyzable_entities.entity_name = ?
        """,
            (entity_name,),
        )
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
            return eval(f"{data_type}({repr(value)})")
        else:
            raise ValueError(f"Unsupported data type: {data_type} for attribute {output_name}")
