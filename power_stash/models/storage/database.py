import datetime as dt
from abc import ABC
from typing import Any, Optional, Protocol, Type

from sqlmodel import JSON, Column, Field, SQLModel
from sqlmodel.sql.expression import Select, SelectOfScalar

from power_stash.models.request import BaseRequest, RequestStatusType


class BaseTableModel(ABC, SQLModel):
    uid: str = Field(
        default=None,
        primary_key=True,
        description="Assigned automatically model's fields.",
    )


class RequestStatus(BaseTableModel, table=True):
    name: str
    start: dt.datetime
    end: dt.datetime
    status: RequestStatusType | None
    request: dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    @classmethod
    def from_request(cls, request: BaseRequest) -> "RequestStatus":  # noqa: ANN102
        """Create a RequestStatusModel instance from a BaseRequest."""
        return cls(
            uid=f"{hash(request)!s}",
            name=type(request).__name__,
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

    def get_existing_uids(
        self,
        model_type: BaseTableModel,
        condition: bool | None = None,
    ) -> list[str]:
        """Return a list of unique identifier in a table."""
        pass

    def get(
        self,
        *,
        record_type: Type[BaseTableModel],
        record_uid: str,
    ) -> Optional[BaseTableModel]:
        """Get a record by uid."""
        pass

    def query(self, *, statement: Select | SelectOfScalar, return_df: bool = False) -> None:
        """Query a table."""
        pass
