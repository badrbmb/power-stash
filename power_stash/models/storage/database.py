import datetime as dt
from abc import ABC
from typing import Any, Protocol

from sqlmodel import JSON, Column, Field, SQLModel
from sqlmodel.sql.expression import Select, SelectOfScalar

from power_stash.models.request import BaseRequest, RequestStatus


class BaseTableModel(ABC, SQLModel):
    uid: str = Field(
        default=None,
        primary_key=True,
        description="Assigned automatically model's fields.",
    )


class RequestStatusModel(BaseTableModel):
    start: dt.datetime
    end: dt.datetime
    status: RequestStatus
    request: dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    @classmethod
    def from_request(cls, request: BaseRequest) -> "RequestStatusModel":  # noqa: ANN102
        """Create a RequestStatusModel instance from a BaseRequest."""
        if request.status is None:
            raise ValueError("Cannot define a request status model without status!")
        return cls(
            uid=f"{hash(request)!s}",
            start=request.start,
            end=request.end,
            status=request.status,
            request=request.model_dump(mode="json"),
        )


class DatabaseRepository(Protocol):
    """Generic interface for storing tabular data."""

    def init_db(self) -> None:
        """Initialise database."""
        pass

    def exists(self, *, record: BaseTableModel) -> None:
        """Check if the record already exists in database."""
        pass

    def add(self, *, record: BaseTableModel) -> None:
        """Add record to database."""
        pass

    def add_or_update(self, record: BaseTableModel) -> None:
        """Add or Update a record."""
        pass

    def bulk_add(self, *, records: list[BaseTableModel]) -> None:
        """Bulk add records, with update logic."""
        pass

    def query(self, *, statement: Select | SelectOfScalar, return_df: bool = False) -> None:
        """Query a table."""
        pass
