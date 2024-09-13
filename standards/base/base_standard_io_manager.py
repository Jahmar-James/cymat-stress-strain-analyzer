class BaseStandardIOManager:
    """
    Manages the conversion of sample objects to and from persistent storage (e.g., files or databases).

    Responsibilities:
    - Maps sample objects to a suitable format for storage.
    - Handles saving data to Zip file and databases (SQL_:ite, Postgress).
    - Provides helper functions to serialize and deserialize sample objects, possibly using Pydantic for validation.

    Assumptions:
    - Data will primarily be saved in Human readable formats (e.g., JSON, CSV) as data will be shared with other team members.
    - Sample objects can be serialized into flat or minimally nested structures for persistence.
    - Complex relationships (e.g., deeply nested samples or real-time synchronization) are out of scope for this design.

    Methods:
    - save_sample: Save a sample object to persistent storage give sample object and destination. Return True if successful.
    - load_sample: Load a sample object from persistent storage given a source. Return the deserialized sample object.
    - remap_sample: Provide a mapping between the sample object and the storage format. Return the remapped sample object.
    """

    def __init__(self) -> None:
        self._file_manager = None
        self._db_manager = None
        raise NotImplementedError("This class is not implemented yet.")


from pathlib import Path


class FileOIManager:
    """
    Handles saving and loading of sample data to and from the file system (e.g., JSON, CSV, ZIP).

    Responsibilities:
    - Saves serialized sample objects to human-readable file formats (e.g., JSON, CSV).
    - Loads and deserializes sample data from files.
    - Ensures file integrity during read and write operations.

    Assumptions:
    - The file path provided will be valid and accessible for read/write operations.
    - Data will primarily be saved in formats that are easy to share and view (e.g., JSON, CSV, ZIP).
    """

    def __init__(self, file_path: Path) -> bool:
        raise NotImplementedError("This class is not implemented yet.")


class DatabaseIOManager:
    """
    Manages the saving and loading of sample data to and from a database (e.g., SQLite, PostgreSQL).

    Responsibilities:
    - Saves serialized sample objects to database tables.
    - Loads and deserializes sample data from database records.
    - Provides basic database management operations, such as creating tables and handling connections.

    Assumptions:
    - The database URI provided will be valid and the database schema will align with the sample object structure.
    - The primary focus is on SQL-based databases (SQLite, PostgreSQL).
    """

    def __init__(self, db_uri: str) -> bool:
        raise NotImplementedError("This class is not implemented yet.")
