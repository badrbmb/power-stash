from abc import ABC
from typing import Protocol

import pandas as pd
from sqlmodel import Field, SQLModel


class BaseTableModel(ABC, SQLModel):
    uid: str = Field(
        default=None,
        primary_key=True,
        description="Assigned automatically using area and timestamp.",
    )


class DatabaseRepository(Protocol):
    """Generic interface for storing tabular data."""

    def init_db(self) -> None:
        """Initialise database."""
        pass

    def exists(self, *, record: BaseTableModel) -> bool:
        """Check if the record already exists in database."""
        pass

    def add(self, *, record: BaseTableModel) -> bool:
        """Add record to database."""
        pass

    def bulk_add(self, *, records: list[BaseTableModel]) -> bool:
        """Bulk add records, with update logic."""
        pass

    def query(self, *, table_name: str, query: str) -> pd.DataFrame:
        """Query a table."""
        pass
