import datetime as dt
import hashlib
from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


class RequestStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    NO_DATA = "no data"


class BaseRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    start: dt.datetime
    end: dt.datetime
    _status: RequestStatus | None = None

    @field_validator("start", "end")
    def validate_date(cls, v: dt.datetime) -> dt.datetime:
        """Validate dates of request."""
        if v.tzinfo is None:
            raise ValidationError(f"Expected a timezone info. for timestamp={v}")
        return v

    def __hash__(self) -> int:
        """Hashing method for base class."""
        serialized_data = self.model_dump_json().encode("utf-8")
        return int(hashlib.sha1(serialized_data).hexdigest(), 16)  # noqa: S324

    @property
    def status(self) -> RequestStatus | None:
        """The ingestion status of teh request."""
        return self._status

    @status.setter
    def status(self, value: RequestStatus) -> None:
        """Set the value of status using the provided value."""
        self._status = value


class BaseRequestBuilder(ABC):
    @abstractmethod
    def build_default_requests(
        self,
        start: dt.datetime,
        end: dt.datetime,
        chunk_months: int | None = None,
    ) -> list[BaseRequest]:
        """Build a series of default requests compatible with a fetcher."""
        pass
