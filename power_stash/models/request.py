import datetime as dt
import hashlib
from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


class BaseRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    start: dt.datetime
    end: dt.datetime

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


class BaseRequestBuilder(ABC):
    @abstractmethod
    def build_default_requests(
        self,
        start: dt.datetime,
        end: dt.datetime,
    ) -> list[BaseRequest]:
        """Build a series of default requests compatible with a fetcher."""
        pass
