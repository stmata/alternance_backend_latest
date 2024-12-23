from dotenv import load_dotenv
import os
from pymongo import MongoClient
from pymongo.collection import Collection
from typing import Optional

class MongoDBManager:
    """
    A class to manage MongoDB connections and operations.

    This class handles the connection to a MongoDB database, provides access to
    collections, and ensures proper connection management.

    Attributes:
        client (MongoClient): The MongoDB client instance.
        db (Database): The database instance.
    """

    def __init__(self):
        """
        Initialize the MongoDBManager.

        Loads environment variables, establishes a connection to MongoDB,
        and sets up the database instance.
        """
        load_dotenv()
        uri = os.getenv('MONGO_URI')
        db_name = os.getenv('MONGO_DB_NAME')
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a MongoDB collection.

        Args:
            collection_name (str): The name of the collection to retrieve.

        Returns:
            Collection: The requested MongoDB collection.
        """
        return self.db[collection_name]

    def close_connection(self) -> None:
        """
        Close the MongoDB connection.

        This method should be called when the connection is no longer needed.
        """
        if self.client:
            self.client.close()

    def __enter__(self) -> 'MongoDBManager':
        """
        Enter the runtime context for this object.

        This method is called when entering a 'with' statement.

        Returns:
            MongoDBManager: The MongoDBManager instance.
        """
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[object]) -> None:
        """
        Exit the runtime context for this object.

        This method is called when exiting a 'with' statement. It ensures that
        the database connection is closed properly.

        Args:
            exc_type (Optional[type]): The exception type if an exception was raised.
            exc_val (Optional[Exception]): The exception value if an exception was raised.
            exc_tb (Optional[object]): The traceback if an exception was raised.
        """
        self.close_connection()