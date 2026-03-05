"""Abstract base class for all repositories."""

import sqlite3
from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

ModelT = TypeVar("ModelT")


class BaseRepository(ABC, Generic[ModelT]):
    """
    Abstract base repository providing standard CRUD operations.

    Subclasses must implement the abstract methods and define their target
    table and model type.

    Args:
        connection: An open :class:`~nira_backend.database.connection.DatabaseConnection`.
    """

    def __init__(self, connection: object) -> None:
        from nira_backend.database.connection import DatabaseConnection

        if not isinstance(connection, DatabaseConnection):
            raise TypeError("connection must be a DatabaseConnection instance")
        self._db = connection

    @abstractmethod
    def create(self, model: ModelT) -> int:
        """
        Persist a new model instance and return its auto-assigned ID.

        Args:
            model: The model instance to persist.

        Returns:
            The integer primary key of the newly created row.
        """

    @abstractmethod
    def get_by_id(self, record_id: int) -> Optional[ModelT]:
        """
        Retrieve a model by its primary key.

        Args:
            record_id: The integer primary key.

        Returns:
            The model instance, or None if not found.
        """

    @abstractmethod
    def get_all(self) -> list[ModelT]:
        """
        Return all rows as model instances.

        Returns:
            List of all model instances in the table.
        """

    @abstractmethod
    def update(self, record_id: int, model: ModelT) -> bool:
        """
        Update an existing row with values from the model.

        Args:
            record_id: The integer primary key of the row to update.
            model: The model instance containing new values.

        Returns:
            True if the row was found and updated, False otherwise.
        """

    @abstractmethod
    def delete(self, record_id: int) -> bool:
        """
        Delete a row by its primary key.

        Args:
            record_id: The integer primary key of the row to delete.

        Returns:
            True if the row was found and deleted, False otherwise.
        """

    def _row_exists(self, cursor: sqlite3.Cursor, table: str, record_id: int) -> bool:
        """Helper to check if a row exists by primary key."""
        cursor.execute(f"SELECT 1 FROM {table} WHERE id = ?", (record_id,))
        return cursor.fetchone() is not None
