import datetime as dt
from abc import ABC, abstractmethod

import pandas as pd
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


class BaseRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    start: dt.datetime
    end: dt.datetime

    @field_validator("start", "end")
    def validate_date(cls, v: dt.datetime) -> dt.datetime:
        """Validate dates of request."""
        if v.tzinfo is None:
            raise ValidationError(f"Expected a timezone info. for timestamp={v}")
        return v


class BaseRequestBuilder(ABC):
    @abstractmethod
    def build_default_requests(
        self,
        start: dt.datetime,
        end: dt.datetime,
    ) -> list[BaseRequest]:
        """Build a series of default requests compatible with a fetcher."""
        pass
